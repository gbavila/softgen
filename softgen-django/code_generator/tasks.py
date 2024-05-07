import json
from celery import shared_task
from .models import Software
from django.conf import settings
from .services.openai import openai_client
from .services.github import upload_software_to_github
from .serializers import FileSerializer
import time
from .utils import process_file_list

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
        prompt=software.processed_specs,
        thread_id=thread_id
    )

    # Atualizar software com informações do LLM
    software.llm_assistant_id = assistant.get_assistant_id()
    software.llm_thread_id = assistant.get_thread_id()
    software.save()

    # Esperar fim da run pela OpenAI
    messages = assistant.wait_for_run_completion()
    print(messages)
    last_message = messages.data[0].content[0].text.value
    data = json.loads(last_message)
    original_file_list = data.get('files')
    if original_file_list is None or not original_file_list: # original_file_list = None, []
        software.delete()
        raise ValueError("Campo 'files' não retornado na resposta do LLM. Software removido da base.")
    
    print(f'Lista gerada pelo LLM: {original_file_list}')
    file_list = process_file_list(original_file_list)
    print(f'Lista processada: {file_list}')

    for file_path in file_list:
        assistant.send_message(
            prompt=f'Generate the content for: {file_path}',
            thread_id=thread_id
        )
        # Esperar fim da run pela OpenAI
        messages = assistant.wait_for_run_completion()
        last_message = messages.data[0].content[0].text.value
        response = json.loads(last_message, strict=False)
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
                'path': file_path,
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
        print(f'Erros na criação ({len(failed_files)}/{len(file_list)}): {failed_files}')
    else:
        print(f'Code generated successfully.')
        upload_software_to_github(software_id)
