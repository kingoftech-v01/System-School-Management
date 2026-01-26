from rest_framework import viewsets, permissions
from .models import Alumni, AlumniEvent
from .serializers import AlumniSerializer, AlumniEventSerializer

class AlumniViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AlumniSerializer
    def get_queryset(self):
        return Alumni.objects.filter(is_active=True)

class AlumniEventViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AlumniEventSerializer
    queryset = AlumniEvent.objects.all()
