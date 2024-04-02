import datetime
from django.db import models
from django.utils import timezone

# Create your models here.
class Technology(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Code(models.Model):
    code_text = models.CharField(max_length=20000)
    code_path = models.CharField(max_length=200)
    release_date = models.DateTimeField(auto_now_add=True)
    technology = models.ForeignKey(Technology, on_delete=models.CASCADE)

    def __str__(self):
        return self.code_text
    
    def was_published_recently(self):
        return self.release_date >= timezone.now() - datetime.timedelta(days=1)
