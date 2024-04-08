# Generated by Django 5.0.3 on 2024-04-07 23:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Software',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('specs', models.TextField()),
                ('processed_specs', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=255)),
                ('version', models.IntegerField()),
                ('content', models.TextField()),
                ('software', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='code_generator.software')),
            ],
        ),
    ]
