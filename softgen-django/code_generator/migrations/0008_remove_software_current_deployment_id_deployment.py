# Generated by Django 5.0.3 on 2024-05-20 23:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('code_generator', '0007_software_current_deployment_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='software',
            name='current_deployment_id',
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('status', models.CharField(max_length=255, null=True)),
                ('errors', models.TextField(blank=True, null=True)),
                ('software', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deployments', to='code_generator.software')),
            ],
        ),
    ]