"""
Monitoring API Views - REST API endpoints.

This module provides API endpoints for:
- Dashboard statistics (students, professors, enrollment)
- Library statistics
- Discipline statistics
- Export functionality

All views return JSON responses.
API URL namespace: api:v1:monitoring:endpoint-name
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from accounts.models import User
from accounts.permissions import IsDirectionUser


# ============================================================================
# DASHBOARD API VIEWS
# ============================================================================

@method_decorator(ratelimit(key='user', rate='100/h'), name='dispatch')
class DashboardStatsAPIView(APIView):
    """
    GET: Return all dashboard statistics in JSON format.

    Returns:
    - User counts (students, professors, parents)
    - Enrollment statistics
    - Gender distribution
    - Library statistics (if available)
    - Discipline statistics (if available)
    """
    permission_classes = [IsAuthenticated, IsDirectionUser]

    def get(self, request):
        tenant = request.tenant

        # User statistics
        stats = {
            'users': {
                'students': User.objects.filter(tenant=tenant, role='student').count(),
                'professors': User.objects.filter(tenant=tenant, role='professor').count(),
                'parents': User.objects.filter(tenant=tenant, role='parent').count(),
            },
            'gender_distribution': list(
                User.objects.filter(tenant=tenant, role='student')
                .values('gender')
                .annotate(count=Count('id'))
            ),
        }

        # Enrollment statistics
        try:
            from enrollment.models import RegistrationForm
            stats['enrollment'] = list(
                RegistrationForm.objects.filter(tenant=tenant)
                .values('status')
                .annotate(count=Count('id'))
            )
        except ImportError:
            stats['enrollment'] = []

        # Library statistics
        try:
            from library.models import Book, BorrowRecord
            stats['library'] = {
                'total_books': Book.objects.filter(tenant=tenant).count(),
                'borrowed': BorrowRecord.objects.filter(tenant=tenant, status='borrowed').count(),
                'overdue': BorrowRecord.objects.filter(tenant=tenant, status='overdue').count(),
            }
        except ImportError:
            stats['library'] = None

        # Discipline statistics
        try:
            from discipline.models import DisciplinaryAction
            stats['discipline'] = {
                'total': DisciplinaryAction.objects.filter(tenant=tenant).count(),
                'unresolved': DisciplinaryAction.objects.filter(tenant=tenant, is_resolved=False).count(),
            }
        except ImportError:
            stats['discipline'] = None

        return Response(stats)


@method_decorator(ratelimit(key='user', rate='100/h'), name='dispatch')
class EnrollmentStatsAPIView(APIView):
    """
    GET: Return detailed enrollment statistics.
    """
    permission_classes = [IsAuthenticated, IsDirectionUser]

    def get(self, request):
        try:
            from enrollment.models import RegistrationForm
            stats = list(
                RegistrationForm.objects.filter(tenant=request.tenant)
                .values('status', 'level')
                .annotate(count=Count('id'))
            )
            return Response({'stats': stats})
        except ImportError:
            return Response(
                {'error': 'Enrollment app not installed'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


@method_decorator(ratelimit(key='user', rate='100/h'), name='dispatch')
class LibraryStatsAPIView(APIView):
    """
    GET: Return detailed library statistics.
    """
    permission_classes = [IsAuthenticated, IsDirectionUser]

    def get(self, request):
        try:
            from library.models import Book, BorrowRecord

            stats = {
                'books_by_category': list(
                    Book.objects.filter(tenant=request.tenant)
                    .values('category')
                    .annotate(count=Count('id'))
                ),
                'borrow_status': list(
                    BorrowRecord.objects.filter(tenant=request.tenant)
                    .values('status')
                    .annotate(count=Count('id'))
                ),
            }
            return Response(stats)
        except ImportError:
            return Response(
                {'error': 'Library app not installed'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


@method_decorator(ratelimit(key='user', rate='50/h'), name='dispatch')
class ExportDashboardAPIView(APIView):
    """
    GET: Export dashboard data in JSON format.
    """
    permission_classes = [IsAuthenticated, IsDirectionUser]

    def get(self, request):
        tenant = request.tenant

        export_data = {
            'exported_at': request.tenant.created_at.isoformat() if hasattr(request.tenant, 'created_at') else None,
            'metrics': {
                'students': User.objects.filter(tenant=tenant, role='student').count(),
                'professors': User.objects.filter(tenant=tenant, role='professor').count(),
                'parents': User.objects.filter(tenant=tenant, role='parent').count(),
            }
        }

        return Response(export_data)
