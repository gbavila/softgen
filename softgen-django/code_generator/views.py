import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Software, File, Deployment
from .serializers import SoftwareSerializer, FileSerializer, DeploymentSerializer
from .services.openai import openai_client
from .services.github import git_manager
from .services.vercel import vercel_manager
from .tasks import create_files_task, fix_software_task

def index(request):
    return HttpResponse("Hello, world. You're at the Code Generator App.")

class VercelPlayground(APIView):
    def get(self, request, *args, **kwargs):
        # repository = "teste-api-vercel"
        # git_manager.create_repository(repository, "Teste API Vercel", private=True)
        # project_response = vercel_manager.create_project('softgen-auto', repository)
        # print('Create Project Response:', project_response)

        # project_id = project_response.get('id')
        # print(f'Generated project_id: {project_id}')

        project_id = ''

        deployments = vercel_manager.list_deployments(project_id)
        print(f'List Deployments Response: {deployments}')

        # Get a specific deployment by ID
        if deployments and deployments['deployments']:
            for deployment in deployments['deployments']:
                deployment_id = deployment['uid']
                updated_deployment = vercel_manager.get_deployment_by_id(deployment_id) # just testing the method
                print(f'Get Deployment by ID Response: {updated_deployment}')

                # Check if a deployment was successful
                status = vercel_manager.check_deployment_status(deployment_id)
                print(f'Check Deployment Status Response: {status}')

                # Get deployment events and print error texts
                error_events = vercel_manager.get_deployment_errors(deployment_id)
                print(f'Error Events: {error_events}')

                # Get deployment logs
                logs = vercel_manager.get_deployment_logs(deployment_id)
                print(f'Deployment Logs: {logs}')

        return Response({"status": 'OK'})

class GitPlayground(APIView):
    def get(self, request, *args, **kwargs):
        repository = "softgen-teste-v5"
        r1 = git_manager.create_repository(repository, "Teste API Github", private=True)
        print(r1)
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
        # assistant.send_message(
        #     prompt="I want an api with a route /square?number=n which returns me the square of any given number n. Do it using Django framework, but remember to not return me any file content yet, i will ask you later.",
        #     #thread_id=settings.THREAD_ID
        # )
        # response = assistant.wait_for_run_completion()
        # print(f'Response 1 : {response}')

        assistant.send_message(
            prompt="Generate content for third file.",
            thread_id=settings.THREAD_ID
        )
        response2 = assistant.wait_for_run_completion()
        print(f'Response 2 : {response2}')
        data = json.loads(response2)

        return Response({"text": data['content']})

class Playground(APIView):
    def get(self, request, *args, **kwargs):
        software = Software.objects.get(pk=37)
        software.vercel_project_id = ''
        software.save()

        # Since the code is uploaded before the Vercel project creation, we need to trigger manually the deployment
        vercel_deployment = vercel_manager.create_deployment('', 0)

        deployment = {'id': vercel_deployment.get('id'),
                      'software': software.id,
                      'status': vercel_deployment.get('status')}
        serializer = DeploymentSerializer(data=deployment)
        if serializer.is_valid():
            serializer.save()
        else:
            print(serializer.errors)
            raise Exception(f'Error creating deployment in database: {serializer.errors}')
        return Response({"Response": 'OK'})

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

            #preview_content = "PREVIEW DO SOFTWARE"
            # Armazenar response_content na sessão
            #request.session['preview_content'] = preview_content
            create_files_task.delay_on_commit(software.id) # async

            return redirect(f'/preview?software_id={software.id}')
            #return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PreviewView(APIView):
    def get(self, request, *args, **kwargs):
        software_id = request.query_params.get('software_id')
        software = Software.objects.get(pk=software_id)
        #preview_content = request.session.get('preview_content', 'Preview não disponível.')
        # limpar o preview_content da sessão após o uso
        #request.session.pop('preview_content', None)

        return render(request, 'preview.html', {'software': software}) #, 'preview_content': preview_content

class CheckGenerationView(APIView):
    def get(self, request, *args, **kwargs):
        software_id = request.query_params.get('software_id')
        try:
            software = Software.objects.get(pk=software_id)
        except Software.DoesNotExist:
            return Response({'error': 'Software not found'}, status=404)
        
        status = software.generation_finished
        repo_url = software.github_repo_url
        vercel_url = None
        deployment_status = None

        vercel_project_id = software.vercel_project_id        
        if vercel_project_id:
            deployments = software.deployments
            if not deployments or deployments == None:
                print('There is still no deployment created.')
            else:
                current_deployment = deployments.order_by('-created_at').first()
                updated_deployment = vercel_manager.get_deployment_by_id(current_deployment.id)
                new_status = updated_deployment['status']
                deployment_status = new_status

                if new_status != current_deployment.status:
                    current_deployment.status = new_status
                    if new_status == 'READY':
                        url = updated_deployment['url']
                        vercel_url = url
                        current_deployment.url = url
                    elif new_status == 'ERROR':
                        print(f'Deployment {current_deployment.id} failed. Sending back to LLM.')
                        fix_software_task.delay_on_commit(software_id, current_deployment.id) # async
                    current_deployment.save()

        return Response({'generation_finished': status, 'github_url': repo_url, 'deployment_status': deployment_status, 'vercel_url': vercel_url})
    
# Criar endpoint para correção quando o dep dá ready mas o user quer mudar alguma coisa ou vê manualmente que algo deu errado

class DeleteSoftwareView(APIView):
    def delete(self, request, *args, **kwargs):
        software_id = request.query_params.get('software_id')
        software = get_object_or_404(Software, pk=software_id)
        if software.vercel_project_id:
            vercel_manager.delete_project(software.vercel_project_id)
        if software.github_repo_url:
            git_manager.delete_repo_by_url(software.github_repo_url)

        software.delete()

        return Response({'message': f'Software {software_id} and its associated files and deployments were deleted successfully.'}) #, 'preview_content': preview_content
    