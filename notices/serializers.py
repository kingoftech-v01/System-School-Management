"""
Notices Serializers - DRF serializers for notices API.
"""

from rest_framework import serializers
from .models import Notice, NotifyGroup, NoticeDocument, NoticeResponse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
        read_only_fields = fields
    def get_full_name(self, obj):
        return obj.get_full_name if hasattr(obj, 'get_full_name') else obj.username

class NoticeSerializer(serializers.ModelSerializer):
    uploaded_by = UserMinimalSerializer(read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    class Meta:
        model = Notice
        fields = ['id', 'title', 'content', 'uploaded_by', 'priority', 'priority_display', 'notify_groups', 'expires_at', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'uploaded_by', 'created_at', 'updated_at']

class NoticeListSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    class Meta:
        model = Notice
        fields = ['id', 'title', 'uploaded_by_name', 'priority', 'priority_display', 'is_active', 'created_at']
        read_only_fields = fields

class NoticeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'priority', 'notify_groups', 'expires_at', 'is_active']
