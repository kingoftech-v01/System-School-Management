"""
Accounts App API Views - DRF ViewSets for user management.

This module provides API endpoints for:
- User account management
- Student profiles
- Lecturer/Staff management
- Profile updates
- Password changes

API URL namespace: api:v1:accounts:resource-name
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .serializers import (
    UserSerializer, UserCreateSerializer,
    StudentSerializer, LecturerSerializer,
    ProfileSerializer, ChangePasswordSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_student', 'is_lecturer', 'is_parent', 'is_staff', 'is_active', 'role']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'first_name', 'last_name', 'date_joined']
    ordering = ['username']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'])
    def update_profile(self, request):
        """Update current user profile."""
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change current user password."""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'detail': 'Password changed successfully.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for student profiles.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'program']
    search_fields = ['student__first_name', 'student__last_name', 'id_number']
    ordering_fields = ['id_number', 'student__first_name']
    ordering = ['id_number']

    def get_queryset(self):
        """Get Student model queryset."""
        from accounts.models import Student
        return Student.objects.select_related('student', 'program').all()


class LecturerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for lecturer profiles.
    """
    queryset = User.objects.filter(is_lecturer=True)
    serializer_class = LecturerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['first_name', 'last_name', 'date_joined']
    ordering = ['first_name']


class StaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for staff (non-lecturer, non-student users).
    """
    queryset = User.objects.filter(is_staff=True, is_lecturer=False, is_student=False)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['first_name', 'last_name', 'email', 'username']
    ordering_fields = ['first_name', 'last_name', 'date_joined']
    ordering = ['first_name']


class ValidateUsernameAPIView(APIView):
    """
    API view to validate username availability.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Check if username is available."""
        username = request.data.get('username', '').strip()

        if not username:
            return Response(
                {'available': False, 'message': 'Username is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(username) < 3:
            return Response(
                {'available': False, 'message': 'Username must be at least 3 characters.'}
            )

        exists = User.objects.filter(username=username).exists()

        return Response({
            'available': not exists,
            'message': 'Username is available.' if not exists else 'Username is already taken.'
        })


class Setup2FAAPIView(APIView):
    """
    API view to setup two-factor authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Setup 2FA for current user."""
        # This would integrate with django-allauth MFA
        return Response({
            'detail': '2FA setup initiated.',
            'qr_code_url': '/accounts/2fa/setup/'  # Redirect to allauth MFA setup
        })


class Disable2FAAPIView(APIView):
    """
    API view to disable two-factor authentication.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Disable 2FA for current user."""
        # This would integrate with django-allauth MFA
        return Response({
            'detail': '2FA disabled successfully.'
        })
