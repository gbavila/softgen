from .models import Technology, Code
from rest_framework import serializers

class TechnologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Technology
        fields = '__all__'#['url', 'Technologyname', 'email', 'groups']


class CodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Code
        fields = '__all__'