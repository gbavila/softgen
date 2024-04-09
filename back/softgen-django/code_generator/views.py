from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Software, File
from .serializers import SoftwareSerializer, FileSerializer
from .services.openai import openai_client

def index(request):
    return HttpResponse("Hello, world. You're at the Code Generator App.")

class Playground(APIView):
    def get(self, request, *args, **kwargs):
        # if not prompt:
        #     return Response({"error": "O prompt é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)
        assistant = openai_client.assistant()
        assistant.create(
            name="Software Generator",
            instructions="You are a software engineer. Write and run working code to meet given specifications.",
            model="gpt-3.5-turbo-0125"
        )
        assistant.send_message(
            prompt="What is your name?"
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

        return render(request, 'preview.html', {'software': software, 'preview_content': preview_content})
    