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
    github_repo_url = models.CharField(max_length=255, null=True)
    vercel_project_id = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name

class File(models.Model):
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='files') 
    # related_name='files' allows files from a software to be accessed through software.files
    path = models.CharField(max_length=255)
    version = models.IntegerField()
    last_run_version_change = models.IntegerField(default=1)
    content = models.TextField(blank=True)
    instructions = models.CharField(max_length=72, null=True) # this will be used as github commit message

    def __str__(self):
        return f"{self.path} (Version: {self.version})"

class Deployment(models.Model):
    id = models.CharField(max_length=100, primary_key=True) # Vercel deployment id
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='deployments')
    created_at = models.DateTimeField(auto_now_add=True)
    vercel_repoId = models.IntegerField(null=True)
    status = models.CharField(max_length=255, null=True)
    errors = models.TextField(blank=True, null=True) # from deployment events
    url = models.CharField(max_length=255, null=True)

    def __str__(self):
        return f"{self.name}: {self.status}"

class LLM_Run_Stats(models.Model):
    model = models.CharField(max_length=255, default='gpt-4o-mini')
    time_elapsed = models.DurationField(null=True) # currently stores as seconds * 1000000
    run_number = models.IntegerField(default=1)
    manual_trigger = models.BooleanField(default=False) # In order to know when a re generation was manually triggered
    success = models.BooleanField(default=True)
    specs_proc_run = models.BooleanField(default=False)
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='llm_runs')

    def __str__(self):
        return f'LLM Run {self.run_number}: {self.time_elapsed}'
    