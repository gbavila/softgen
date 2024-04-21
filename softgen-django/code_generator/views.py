from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Software, File
from .serializers import SoftwareSerializer, FileSerializer
from .services.openai import openai_client
from .services.github import git_manager
from .tasks import long_running_task

def index(request):
    return HttpResponse("Hello, world. You're at the Code Generator App.")

class GitPlayground(APIView):
    def get(self, request, *args, **kwargs):
        repository = "softgen-teste-v4"
        # r1 = git_manager.create_repository(repository, "Teste API Github", private=True)
        # print(r1)
        r2 = git_manager.create_file(repository, "test3.txt", "Adiciona test3.txt", "Teste API")
        print(r2)
        r3 = git_manager.update_file(repository, "test3.txt", "Atualiza test3.txt", "Teste API v2")
        print(r3)
        r4 = git_manager.get_commits(repository)
        print(r4)
        return Response({"retornos": f'create_file: {r2}, update_file: {r3}'})

class OpenAIPlayground(APIView):
    def get(self, request, *args, **kwargs):
        # if not prompt:
        #     return Response({"error": "O prompt é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        assistant = openai_client.assistant(settings.ASSISTANT_ID)
        # assistant.create(
        #     name="Software Generator",
        #     instructions="You are a software engineer. Write and run working code to meet given specifications.",
        #     model="gpt-3.5-turbo-0125"
        # )
        assistant.send_message(
            prompt="9 + 9 = ?",
            thread_id=settings.THREAD_ID
        )
        response = assistant.wait_for_run_completion()

        return Response({"text": response})

@api_view(['GET'])
def getFiles(request):
    file = File.objects.all()
    serializer = FileSerializer(file, many=True)
    return Response(serializer.data)

class SubmitSpecsView(APIView):
    def get(self, request, *args, **kwargs):
        return render(request, 'spec_form.html')
    
    def post(self, request, *args, **kwargs):
        serializer = SoftwareSerializer(data=request.data)
        if serializer.is_valid():
            software = serializer.save()

            preview_content = "PREVIEW DO SOFTWARE"
            # Armazenar response_content na sessão
            request.session['preview_content'] = preview_content

            return redirect(f'/preview?software_id={software.id}')
            #return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PreviewView(APIView):
    def get(self, request, *args, **kwargs):
        software_id = request.query_params.get('software_id')
        software = Software.objects.get(pk=software_id)
        preview_content = request.session.get('preview_content', 'Preview não disponível.')
        # limpar o preview_content da sessão após o uso
        request.session.pop('preview_content', None)

        long_running_task.delay_on_commit(software_id=software_id)

        return render(request, 'preview.html', {'software': software, 'preview_content': preview_content})

class CheckUpdateView(APIView):
    def get(self, request, *args, **kwargs):
        software_id = request.query_params.get('software_id')
        software = Software.objects.get(pk=software_id)
        updated_content = software.llm_thread_id

        return Response({'updatedContent': updated_content})
    