"""
Search API Views - REST API endpoints.

This module provides REST API views for search functionality:
- Unified search across multiple models (NewsAndEvents, Programs, Courses, Quizzes)
- Search suggestions for autocomplete
- JSON responses for API consumers

All views require authentication and are rate-limited.
API URL namespace: api:v1:search:resource-name
"""

from datetime import date
from itertools import chain

from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import NewsAndEvents
from course.models import Program, Course
from quiz.models import Quiz
from School_System.throttles import SearchRateThrottle
from .serializers import UnifiedSearchResultSerializer
from .utils import execute_search


SEARCH_MAX_RESULTS = getattr(settings, 'SEARCH_MAX_RESULTS', 100)
VALID_SEARCH_TYPES = ('all', 'news', 'programs', 'courses', 'quizzes')


def _parse_date(date_string):
    """Parse a YYYY-MM-DD string into a date object, or return None."""
    if not date_string:
        return None
    try:
        parts = date_string.split('-')
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None


def _parse_limit(raw_value, default):
    """Parse and clamp a limit parameter to [1, SEARCH_MAX_RESULTS]."""
    try:
        limit = int(raw_value)
    except (ValueError, TypeError):
        limit = default
    return max(1, min(limit, SEARCH_MAX_RESULTS))


# ============================================================================
# SEARCH API VIEWS
# ============================================================================

class SearchAPIView(APIView):
    """
    Unified search API endpoint.

    GET /api/v1/search/query/?q=<search_term>

    Searches across:
    - NewsAndEvents
    - Programs
    - Courses
    - Quizzes

    Query Parameters:
    - q: Search query string (required, min 2 chars)
    - limit: Maximum results to return (default: 50, max: SEARCH_MAX_RESULTS)
    - search_type: Filter by content type (all/news/programs/courses/quizzes)
    - date_from: Filter results from this date (YYYY-MM-DD)
    - date_to: Filter results until this date (YYYY-MM-DD)

    Returns:
        200: Search results with count
        400: Missing/invalid query parameter
        403: No tenant context
    """

    throttle_classes = [SearchRateThrottle]

    def get(self, request):
        """Handle search query and return unified results."""
        # Tenant guard
        if not getattr(request, 'tenant', None):
            return Response(
                {'error': 'No tenant context available'},
                status=status.HTTP_403_FORBIDDEN
            )

        query = request.GET.get('q', '').strip()
        limit = _parse_limit(request.GET.get('limit', 50), default=50)

        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse advanced search params
        search_type = request.GET.get('search_type', 'all')
        if search_type not in VALID_SEARCH_TYPES:
            search_type = 'all'

        date_from = _parse_date(request.GET.get('date_from'))
        date_to = _parse_date(request.GET.get('date_to'))

        if date_from and date_to and date_from > date_to:
            return Response(
                {'error': 'date_from must be before date_to'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Execute search
        results = execute_search(
            query,
            search_type=search_type,
            date_from=date_from,
            date_to=date_to,
        )[:limit]

        # Serialize results
        serializer = UnifiedSearchResultSerializer(results, many=True)

        return Response({
            'query': query,
            'count': len(results),
            'results': serializer.data
        })


class SearchSuggestionsAPIView(APIView):
    """
    Search suggestions/autocomplete API endpoint.

    GET /api/v1/search/suggestions/?q=<partial_term>

    Returns top suggestions for autocomplete based on partial query.

    Query Parameters:
    - q: Partial search term (required)
    - limit: Maximum suggestions (default: 10, max: SEARCH_MAX_RESULTS)

    Returns:
        200: List of suggestions with titles
        400: Missing query parameter
        403: No tenant context
    """

    throttle_classes = [SearchRateThrottle]

    def get(self, request):
        """Return search suggestions for autocomplete."""
        # Tenant guard
        if not getattr(request, 'tenant', None):
            return Response(
                {'error': 'No tenant context available'},
                status=status.HTTP_403_FORBIDDEN
            )

        query = request.GET.get('q', '').strip()
        limit = _parse_limit(request.GET.get('limit', 10), default=10)

        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get suggestions from each model
        news_suggestions = NewsAndEvents.objects.filter(
            Q(title__icontains=query) | Q(summary__icontains=query)
        ).values_list('title', flat=True)[:limit]

        program_suggestions = Program.objects.filter(
            Q(title__icontains=query) | Q(summary__icontains=query)
        ).values_list('title', flat=True)[:limit]

        course_suggestions = Course.objects.filter(
            Q(title__icontains=query) | Q(summary__icontains=query)
        ).values_list('title', flat=True)[:limit]

        quiz_suggestions = Quiz.objects.filter(
            Q(title__icontains=query)
        ).values_list('title', flat=True)[:limit]

        # Combine and deduplicate while preserving order
        all_suggestions = list(chain(
            news_suggestions,
            program_suggestions,
            course_suggestions,
            quiz_suggestions
        ))

        seen = set()
        unique_suggestions = []
        for item in all_suggestions:
            if item not in seen:
                seen.add(item)
                unique_suggestions.append(item)

        return Response({
            'query': query,
            'suggestions': unique_suggestions[:limit]
        })
