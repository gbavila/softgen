from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Technology, Code
from .serializers import TechnologySerializer, CodeSerializer
#from openai import OpenAI

def index(request):
    return HttpResponse("Hello, world. You're at the Code Generator App.")

def playground(request):
    #client = OpenAI()
    return HttpResponse("Hello, world. You're at the Code Generator App.")

@api_view(['GET'])
def getCode(request):
    code = Code.objects.all()
    serializer = CodeSerializer(code, many=True)
    return Response(serializer.data)
    # person = {'name': 'Dennis', 'age': 28}
    # return Response(person)

@api_view(['POST'])
def addCode(request):
    serializer = CodeSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    else:
        print("Failed")
    return Response(serializer.data)