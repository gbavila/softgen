from django.shortcuts import render
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
        
        prompt = "How much is 1+1?"
        generated_text = openai_client.generate_text(prompt, max_tokens=50)
        
        return Response({"text": generated_text})

@api_view(['GET'])
def getCode(request):
    file = File.objects.all()
    serializer = FileSerializer(file, many=True)
    return Response(serializer.data)
    # person = {'name': 'Dennis', 'age': 28}
    # return Response(person)

@api_view(['POST'])
def addCode(request):
    serializer = FileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    else:
        print("Failed")
    return Response(serializer.data)

class SubmitSpecsView(APIView):
    def get(self, request, *args, **kwargs):
        return render(request, 'code_generator/spec_form.html')
    
    def post(self, request, *args, **kwargs):
        serializer = SoftwareSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
