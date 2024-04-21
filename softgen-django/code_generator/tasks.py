from celery import shared_task
from .models import Software
import time

@shared_task
def long_running_task(software_id):
    # Simula uma operação de longa duração
    time.sleep(10)  # Espera 10 segundos

    # Atualiza um campo no modelo Software
    software = Software.objects.get(pk=software_id)
    software.llm_thread_id = "Task completed"
    software.save()