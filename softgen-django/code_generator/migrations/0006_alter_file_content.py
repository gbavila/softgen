# Generated by Django 5.0.3 on 2024-05-14 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('code_generator', '0005_file_instructions_software_github_repo_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='content',
            field=models.TextField(blank=True),
        ),
    ]
