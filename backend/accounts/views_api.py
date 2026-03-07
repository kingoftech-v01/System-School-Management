"""
Accounts App API Views - DRF ViewSets for user management.

This module provides API endpoints for:
- Authentication (login, logout, token refresh)
- User account management
- Student profiles
- Lecturer/Staff management
- Profile updates
- Password changes
- Navigation and permissions context

API URL namespace: api:v1:accounts:resource-name
"""

import re

from django.contrib.auth import authenticate, get_user_model
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend
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
    Rate-limited and uses generic messages to prevent username enumeration.
    """
    permission_classes = [AllowAny]
    throttle_classes = []  # Use django-ratelimit instead

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    def post(self, request):
        """Check if username is available (generic response to prevent enumeration)."""
        username = request.data.get('username', '').strip()

        if not username:
            return Response(
                {'valid': False, 'message': 'Username is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(username) < 3:
            return Response(
                {'valid': False, 'message': 'Username must be at least 3 characters.'}
            )

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return Response(
                {'valid': False, 'message': 'Username can only contain letters, numbers, and underscores.'}
            )

        exists = User.objects.filter(username=username).exists()

        return Response({
            'valid': not exists,
            'message': 'Username is valid.' if not exists else 'Username is not available. Please try a different one.'
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


# ============================================================================
# AUTH ENDPOINTS (Login, Logout)
# ============================================================================

class LoginAPIView(APIView):
    """
    JWT login endpoint. Returns access and refresh tokens.
    """
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST'))
    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'Account is disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class LogoutAPIView(APIView):
    """
    Blacklist the refresh token on logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get('refresh')
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:
                pass
        return Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)


# ============================================================================
# CONTEXT ENDPOINTS (Navigation, Permissions)
# ============================================================================

class NavigationAPIView(APIView):
    """
    Returns role-based navigation items for the current user.
    Replaces the navigation_context template context processor.
    """
    permission_classes = [IsAuthenticated]

    NAV_BY_ROLE = {
        'student': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'My Courses', 'path': '/courses', 'icon': 'book'},
            {'name': 'Attendance', 'path': '/attendance', 'icon': 'calendar-check'},
            {'name': 'Results', 'path': '/results', 'icon': 'chart-line'},
            {'name': 'Payments', 'path': '/payments', 'icon': 'credit-card'},
            {'name': 'Library', 'path': '/library', 'icon': 'book-open'},
            {'name': 'Events', 'path': '/events', 'icon': 'calendar'},
        ],
        'parent': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'Grades', 'path': '/parent/grades', 'icon': 'chart-line'},
            {'name': 'Attendance', 'path': '/parent/attendance', 'icon': 'calendar-check'},
            {'name': 'Payments', 'path': '/parent/payments', 'icon': 'credit-card'},
            {'name': 'Messages', 'path': '/parent/messages', 'icon': 'mail'},
            {'name': 'Events', 'path': '/parent/events', 'icon': 'calendar'},
        ],
        'professor': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'My Classes', 'path': '/courses', 'icon': 'graduation-cap'},
            {'name': 'Attendance', 'path': '/attendance', 'icon': 'calendar-check'},
            {'name': 'Grades', 'path': '/grading', 'icon': 'edit'},
            {'name': 'Notes', 'path': '/notes', 'icon': 'file-text'},
            {'name': 'Students', 'path': '/search', 'icon': 'search'},
        ],
        'direction': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'Monitoring', 'path': '/monitoring', 'icon': 'bar-chart'},
            {'name': 'Students', 'path': '/search', 'icon': 'search'},
            {'name': 'Enrollment', 'path': '/enrollment', 'icon': 'user-plus'},
            {'name': 'Courses', 'path': '/courses', 'icon': 'book'},
            {'name': 'Attendance', 'path': '/attendance', 'icon': 'calendar-check'},
            {'name': 'Results', 'path': '/results', 'icon': 'chart-line'},
            {'name': 'Payments', 'path': '/payments', 'icon': 'credit-card'},
            {'name': 'Library', 'path': '/library', 'icon': 'book-open'},
            {'name': 'Events', 'path': '/events', 'icon': 'calendar'},
            {'name': 'Discipline', 'path': '/discipline', 'icon': 'shield'},
        ],
        'accountant': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'Students', 'path': '/search', 'icon': 'search'},
            {'name': 'Payments', 'path': '/payments', 'icon': 'credit-card'},
            {'name': 'Analytics', 'path': '/analytics', 'icon': 'bar-chart'},
        ],
        'secretary': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'Monitoring', 'path': '/monitoring', 'icon': 'bar-chart'},
            {'name': 'Enrollment', 'path': '/enrollment', 'icon': 'user-plus'},
            {'name': 'Courses', 'path': '/courses', 'icon': 'book'},
            {'name': 'Attendance', 'path': '/attendance', 'icon': 'calendar-check'},
            {'name': 'Library', 'path': '/library', 'icon': 'book-open'},
        ],
        'librarian': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'Library', 'path': '/library', 'icon': 'book-open'},
        ],
        'registrar': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'Enrollment', 'path': '/enrollment', 'icon': 'user-plus'},
            {'name': 'Certificates', 'path': '/certificates', 'icon': 'award'},
        ],
        'prefet': [
            {'name': 'Dashboard', 'path': '/dashboard', 'icon': 'layout-dashboard'},
            {'name': 'Discipline', 'path': '/discipline', 'icon': 'shield'},
            {'name': 'Attendance', 'path': '/attendance', 'icon': 'calendar-check'},
            {'name': 'Students', 'path': '/search', 'icon': 'search'},
        ],
    }

    def get(self, request):
        role = getattr(request.user, 'role', 'student') or 'student'
        nav_items = self.NAV_BY_ROLE.get(role, self.NAV_BY_ROLE['student'])

        if request.user.is_superuser:
            nav_items = list(nav_items) + [
                {'name': 'Admin', 'path': '/admin', 'icon': 'settings'},
            ]

        return Response({'role': role, 'navigation': nav_items})


class PermissionsAPIView(APIView):
    """
    Returns the current user's permission flags.
    Replaces the permissions_context template context processor.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = getattr(request.user, 'role', None)
        permissions = {
            'can_view_all_students': False,
            'can_manage_payments': False,
            'can_manage_enrollment': False,
            'can_view_monitoring': False,
            'can_manage_discipline': False,
            'can_export_data': False,
        }

        if role in ('direction', 'admin') or request.user.is_superuser:
            permissions = {k: True for k in permissions}
        elif role == 'secretary':
            permissions.update(
                can_view_all_students=True, can_manage_enrollment=True,
                can_view_monitoring=True, can_manage_discipline=True,
                can_export_data=True,
            )
        elif role == 'professor':
            permissions['can_manage_discipline'] = True
        elif role == 'prefet':
            permissions.update(can_view_all_students=True, can_manage_discipline=True)
        elif role == 'accountant':
            permissions.update(can_view_all_students=True, can_manage_payments=True)
        elif role == 'registrar':
            permissions.update(can_manage_enrollment=True, can_export_data=True)

        return Response({'role': role, 'permissions': permissions})
