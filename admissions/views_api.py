from rest_framework import viewsets, permissions
from .models import AdmissionStudent, AdmissionSession
from .serializers import AdmissionStudentSerializer, AdmissionSessionSerializer

class AdmissionSessionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = AdmissionSessionSerializer
    queryset = AdmissionSession.objects.filter(is_active=True)

class AdmissionStudentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AdmissionStudentSerializer
    def get_queryset(self):
        return AdmissionStudent.objects.all()
