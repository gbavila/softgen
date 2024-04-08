from .models import Software, File
from rest_framework import serializers

class SoftwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Software
        fields = '__all__'#['url', 'name', 'email', 'groups']
        extra_kwargs = {'processed_specs': {'required': False}}


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'