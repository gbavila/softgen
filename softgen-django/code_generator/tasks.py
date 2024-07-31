import json
from datetime import datetime
from celery import shared_task
from .models import Software, Deployment
from django.conf import settings
from .services.openai import openai_client
from .services.github import git_manager, upload_software_to_github, update_software_files
from .services.vercel import vercel_manager
from .serializers import FileSerializer, DeploymentSerializer
import time
from .utils import (
    process_file_list, check_already_generated, json_load_message, 
    get_latest_openai_messages, save_llm_run_stats
)

@shared_task
def test_celery_task(software_id):
    # Simula uma operação de longa duração
    time.sleep(10)  # Espera 10 segundos

    # Atualiza um campo no modelo Software
    software = Software.objects.get(pk=software_id)
    software.llm_thread_id = "Task completed"
    software.save()

@shared_task
def create_files_task(software_id):
    software = Software.objects.get(pk=software_id)
    thread_id = None #settings.THREAD_ID
    failed_files = []
    
    time_start = datetime.now()
    assistant = openai_client.assistant(settings.ASSISTANT_ID)
    assistant.send_message(
        #prompt=software.processed_specs + ' Include necessary files for the project to be executable with the docker-compose up --build command.',
        prompt=software.processed_specs + ' Include necessary files for the project to be deployed in Vercel platform, vercel.json file must be in project root.',
        thread_id=thread_id,
        #instructions='Add the necessary files for the project to be executable with the docker-compose up --build command. Add the github actions files in order to the project to be deployed on heroku with secrets.HEROKU_API_KEY saved on the github repository. The response should be in json format given in the main instructions.'
    )

    # Update software with LLM info
    software.llm_assistant_id = assistant.get_assistant_id()
    software.llm_thread_id = assistant.get_thread_id()
    software.save()

    # Wait OpenAI run
    messages = assistant.wait_for_run_completion()
    #print(messages)
    
    analysis = check_already_generated(messages.data)
    # analysis = {'framework': 'Django', 
    #             'failed': False, 
    #             'generated': [{'file': '...', 'instructions': '...', 'content': '...'}, ..., {'file': '...', 'instructions': '...', 'content': '...'}], 
    #             'files': ['file_1', ..., 'file_n']}
    
    if analysis['failed']:
        software.delete()
        raise ValueError(f"Generation request failed:\n{analysis}\n\n{messages}")
    
    file_list = process_file_list(analysis['files'])
    print(f'Filtered file list: {file_list}')
    generated_files = [msg['file'] for msg in analysis['generated']]

    for file_path in file_list:
        if file_path not in generated_files:
            assistant.send_message(
                prompt=f'Generate the content for: {file_path}',
                thread_id=thread_id
            )
            # Wait OpenAI run
            messages = assistant.wait_for_run_completion()
            response = json_load_message(messages.data[0].content[0].text.value)
        else:
            print(f'File already generated by LLM: {file_path}')
            response = [msg for msg in analysis['generated'] if msg['file'] == file_path][0]
        #print(f'Content for {file_path}: \n{response}\n')
        file_content = response.get('content')
        if file_content is None:
            print(f'(SKIPPING) Null Content for {file_path}: \n{response}\n')
            continue
        elif isinstance(file_content, dict): # .json files case
            file_content = json.dumps(file_content, indent=4)

        try:
            instructions = response.get('instructions')[:72]
        except Exception as ex:
            print(ex)
            instructions = ""

        file = {'software': software.id,
                'path': file_path if file_path[0] != '/' else file_path[1:], # remove initial / to avoid github api error
                'version': 1,
                'content': file_content,
                'instructions': instructions}
        serializer = FileSerializer(data=file)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
            failed_files.append({'file':file_path, 'llm_response': response})
    
    software.generation_finished = True
    software.save()

    if failed_files:
        print(f'Creation errors ({len(failed_files)}/{len(file_list)}): {failed_files}')
    else:
        print('Code generated successfully.')
        save_llm_run_stats(software_id, time_start)

        project_name = f"softgen-{software_id}"
        upload_software_to_github(project_name, software_id)
        software = Software.objects.get(pk=software_id)

        vercel_response = vercel_manager.create_project(name = project_name, 
                                                        github_repo = project_name)
        print('Vercel project created successfully.')

        vercel_project_id = vercel_response.get('id')
        vercel_repoId = vercel_response.get('link').get('repoId')
        
        software.vercel_project_id = vercel_project_id
        software.save()

        # Since the code is uploaded before the Vercel project creation, we need to trigger manually the deployment
        vercel_deployment = vercel_manager.create_deployment(vercel_project_id, vercel_repoId, target='production')
        print('Vercel deployment created successfully.')

        deployment = {'id': vercel_deployment.get('id'),
                      'software': software.id,
                      'vercel_repoId': vercel_repoId,
                      'status': vercel_deployment.get('status')}
        serializer = DeploymentSerializer(data=deployment)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
            raise Exception(f'Error creating deployment in database: {serializer.errors}')
        
        print(f'First {project_name} run attempt successfully started.')

@shared_task
def fix_software_task(software_id, deployment_id):
    software = Software.objects.get(pk=software_id)
    current_files = software.files.all()
    current_file_paths = [file.path for file in current_files]
    next_version = current_files.order_by('-version').first().version + 1

    threshold = 10
    if next_version > threshold:
        print(f'Max re-generation retries reached ({threshold}).')
        return

    logs = [event['payload']['text'] for event in vercel_manager.get_deployment_logs(deployment_id)]
    if not logs:
        raise Exception('Empty Vercel deployment logs')
    
    logs = ';\n'.join(logs)
    time_start = datetime.now()
    assistant = openai_client.assistant(software.llm_assistant_id)
    assistant.send_message(
        prompt=f'Vercel deployment resulted in error. Following, you will receive the deployment logs, analyze and return the files that need to be fixed, added or removed in order to get the deployment running correctly. Remember to use the expected json format, responses with content for each file separately and you must answer with a json containing 3 fields: "file", "instructions" and "content". If a file needs to be removed, just return the content field null. Logs:\n {logs}',
        thread_id=software.llm_thread_id
    )

    # Wait OpenAI run
    messages = assistant.wait_for_run_completion()
    #messages = assistant.get_thread_messages(software.llm_thread_id)

    # Retrieve msgs given in response to last prompt
    target_messages = get_latest_openai_messages(messages.data)

    analysis = check_already_generated(target_messages)
    print(analysis)

    if analysis['failed']:
        raise ValueError(f"Re-generation request failed:\n{analysis}\n\n{messages}")
    
    generated_files = [msg['file'] for msg in analysis['generated']]
    # When regenerating, usually LLM does not send that first message with file list and framework
    file_list = process_file_list(analysis['files']) if analysis['files'] else generated_files
    print(f'Filtered file list: {file_list}')
    
    failed_files = []

    for file_path in file_list:
        if file_path not in generated_files:
            assistant.send_message(
                prompt=f'Generate the content for: {file_path}',
                thread_id=software.llm_thread_id
            )
            # Wait OpenAI run
            messages = assistant.wait_for_run_completion()
            response = json_load_message(messages.data[0].content[0].text.value)
        else:
            print(f'File already generated by LLM: {file_path}')
            response = [msg for msg in analysis['generated'] if msg['file'] == file_path][0]

        file_content = response.get('content')
        if file_content is None:
            if file_path in current_file_paths:
                file_content = ''
            else:
                print(f'(SKIPPING) Null Content for {file_path}: \n{response}\n')
                continue
        elif isinstance(file_content, dict): # .json files case
            file_content = json.dumps(file_content, indent=4)

        try:
            instructions = response.get('instructions')[:72]
        except Exception as ex:
            print(ex)
            instructions = ""

        cleaned_file_path = file_path if file_path[0] != '/' else file_path[1:]

        if cleaned_file_path in current_file_paths:
            file = current_files.filter(path=cleaned_file_path)[0]
            file.version = next_version
            file.content = file_content
            file.instructions = instructions
            try:
                file.save()
            except Exception as ex:
                print(ex)
                failed_files.append({'file':file_path, 'llm_response': response})
        else:
            file = {'software': software.id,
                    'path': cleaned_file_path, # remove initial / to avoid github api error
                    'version': 1,
                    'content': file_content,
                    'instructions': instructions}
            serializer = FileSerializer(data=file)
            if serializer.is_valid():
                serializer.save()
            else:
                print(serializer.errors)
                failed_files.append({'file':file_path, 'llm_response': response})

    if failed_files:
        print(f'Re-generation errors ({len(failed_files)}/{len(file_list)}): {failed_files}')
    else:
        print('Code re-generated successfully.')
        save_llm_run_stats(software_id, time_start)
        update_software_files(software_id, next_version)

        print("Listing Vercel's deployments (5 retries)")
        retries = 5
        while retries > 0:
            latest_deployment = vercel_manager.list_deployments(software.vercel_project_id)['deployments'][0]  
            try:
                deployment = Deployment.objects.get(id=latest_deployment.get('uid'))
                if retries != 1:
                    print(f'Could not find new Vercel deployment. {retries} retries left.')
                    time.sleep(4)
                else:
                    raise Exception(f'Could not find a new deployment for software {software_id}')
            except Deployment.DoesNotExist:
                break
            retries -= 1

        deployment = {'id': latest_deployment.get('uid'),
                      'software': software.id,
                      'vercel_repoId': latest_deployment.get('githubRepoId'),
                      'status': latest_deployment.get('state')} # for some reason this endpoint does not have status, maybe because its a /v6
        serializer = DeploymentSerializer(data=deployment)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
            raise Exception(f'Error creating deployment in database: {serializer.errors}')
        
        print(f'New deployment for {f"softgen-{software_id}"} successfully started.')
