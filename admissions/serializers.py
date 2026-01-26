from rest_framework import serializers
from .models import AdmissionStudent, AdmissionSession

class AdmissionSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionSession
        fields = '__all__'

class AdmissionStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionStudent
        fields = '__all__'
