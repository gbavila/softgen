from celery import shared_task
from .models import Software
from django.conf import settings
from .services.openai import openai_client
from .services.github import git_manager, upload_software_to_github
from .services.vercel import vercel_manager
from .serializers import FileSerializer, DeploymentSerializer
import time
from .utils import process_file_list, check_already_generated, json_load_message

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

    assistant = openai_client.assistant(settings.ASSISTANT_ID)
    assistant.send_message(
        #prompt=software.processed_specs + ' Include necessary files for the project to be executable with the docker-compose up --build command.',
        prompt=software.processed_specs + ' Include necessary files for the project to be deployed in Vercel platform.',
        thread_id=thread_id,
        #instructions='Add the necessary files for the project to be executable with the docker-compose up --build command. Add the github actions files in order to the project to be deployed on heroku with secrets.HEROKU_API_KEY saved on the github repository. The response should be in json format given in the main instructions.'
    )

    # Update software with LLM info
    software.llm_assistant_id = assistant.get_assistant_id()
    software.llm_thread_id = assistant.get_thread_id()
    software.save()

    # Wait OpenAI run
    messages = assistant.wait_for_run_completion()
    print(messages)
    
    analysis = check_already_generated(messages)
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
            response =  [msg for msg in analysis['generated'] if msg['file'] == file_path][0]
        #print(f'Content for {file_path}: \n{response}\n')
        file_content = response.get('content')
        if file_content is None:
            print(f'(SKIPPING) Null Content for {file_path}: \n{response}\n')
            continue

        try:
            instructions = response.get('instructions')[:72]
        except:
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

        project_name = f"softgen-{software_id}"
        upload_software_to_github(project_name, software_id)
        # Adicionar delete repo se algo falhar

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
