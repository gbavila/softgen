# Generated by Django 5.0.3 on 2024-04-21 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('code_generator', '0003_software_llm_assistant_id_software_llm_thread_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='software',
            name='generation_finished',
            field=models.BooleanField(default=False),
        ),
    ]
