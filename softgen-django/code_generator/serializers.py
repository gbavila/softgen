from .models import Software, File, Deployment, LLM_Run_Stats
from rest_framework import serializers

class SoftwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Software
        fields = '__all__' # or list with fields
        extra_kwargs = {'processed_specs': {'required': False},
                        'llm_assistant_id': {'required': False},
                        'llm_thread_id': {'required': False},
                        'generation_finished': {'required': False}
                        }
        
    def create(self, validated_data):
        validated_data['processed_specs'] = validated_data.get('specs', '')
        return super().create(validated_data)
    
    # def update(self, instance, validated_data):
    #     validated_data['processed_specs'] = validated_data.get('specs', '')
    #     return super().update(instance, validated_data)

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deployment
        fields = '__all__'

class LLM_Run_StatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLM_Run_Stats
        fields = '__all__'
        