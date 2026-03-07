from rest_framework import serializers
from .models import Alumni, AlumniEvent

class AlumniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alumni
        fields = '__all__'

class AlumniEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlumniEvent
        fields = '__all__'
