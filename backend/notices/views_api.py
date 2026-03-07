"""
Notices API Views - REST API endpoints.
"""

from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Notice
from .serializers import NoticeSerializer, NoticeListSerializer, NoticeCreateSerializer

class NoticeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['priority', 'is_active']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']
    lookup_field = 'pk'

    def get_queryset(self):
        return Notice.objects.all().select_related('uploaded_by')

    def get_serializer_class(self):
        if self.action == 'list':
            return NoticeListSerializer
        elif self.action == 'create':
            return NoticeCreateSerializer
        return NoticeSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.get_queryset().filter(is_active=True)
        serializer = NoticeListSerializer(queryset, many=True)
        return Response(serializer.data)
