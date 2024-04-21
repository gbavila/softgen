import json
from celery import shared_task
from .models import Software
from django.conf import settings
from .services.openai import openai_client
from .serializers import FileSerializer
import time

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
    files_list = json.loads(assistant.wait_for_run_completion())['files']
    print(files_list)

    for file_path in files_list:
        assistant.send_message(
            prompt=f'Generate the content for: {file_path}',
            thread_id=thread_id
        )
        # Esperar fim da run pela OpenAI
        response = json.loads(assistant.wait_for_run_completion())
        print(f'Content for {file_path}: \n{response}\n')
        file_content = response['content']

        file = {'software': software.id,
                'path': file_path,
                'version': 1,
                'content': file_content}
        serializer = FileSerializer(data=file)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
            failed_files.append({'file':file_path, 'llm_response': response})
    
    software.generation_finished = True
    software.save()
    print(f'Erros na criação ({len(failed_files)}/{len(files_list)}): {failed_files}')
