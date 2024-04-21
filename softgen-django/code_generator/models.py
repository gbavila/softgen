import datetime
from django.db import models
from django.utils import timezone
from django.conf import settings

class Software(models.Model):
    name = models.CharField(max_length=255)
    creation_date = models.DateTimeField(auto_now_add=True)
    specs = models.TextField()
    processed_specs = models.TextField(blank=True, null=True)
    llm_assistant_id = models.CharField(max_length=255, null=True)
    llm_thread_id = models.CharField(max_length=255, null=True)
    generation_finished = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class File(models.Model):
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='files') 
    # related_name='files' permite acessar todos os arquivos de um software usando software.files
    path = models.CharField(max_length=255)
    version = models.IntegerField()
    content = models.TextField()

    def __str__(self):
        return f"{self.path} (Versão {self.version})"
