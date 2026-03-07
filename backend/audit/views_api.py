from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Student

from .services import StudentTimelineService


class StudentTimelineAPIView(APIView):
    """
    GET /api/v1/audit/students/{student_id}/timeline/

    Query params:
    - event_types: comma-separated (e.g., "discipline,attendance")
    - date_from: ISO date (e.g., "2024-01-01")
    - date_to: ISO date
    - severity: info|warning|critical
    - page: page number (default 1)
    - page_size: entries per page (default 50, max 100)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        student = get_object_or_404(Student, pk=student_id)

        event_types = request.query_params.get('event_types')
        if event_types:
            event_types = [t.strip() for t in event_types.split(',')]

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        severity = request.query_params.get('severity')
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 50)), 100)

        service = StudentTimelineService(
            student=student,
            tenant=getattr(request, 'tenant', None),
        )

        result = service.get_timeline(
            event_types=event_types,
            date_from=date_from,
            date_to=date_to,
            severity=severity,
            page=page,
            page_size=page_size,
        )

        return Response(result)
