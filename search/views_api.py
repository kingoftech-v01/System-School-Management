"""
Search API Views - REST API endpoints.

This module provides REST API views for search functionality:
- Unified search across multiple models (NewsAndEvents, Programs, Courses, Quizzes)
- Search suggestions for autocomplete
- JSON responses for API consumers

All views return JSON responses.
API URL namespace: api:v1:search:resource-name
"""

from itertools import chain
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Q

from core.models import NewsAndEvents
from course.models import Program, Course
from quiz.models import Quiz
from .serializers import UnifiedSearchResultSerializer


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
    - q: Search query string (required)
    - limit: Maximum results to return (default: 50)

    Returns:
        200: Search results with count
        400: Missing query parameter
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Handle search query and return unified results."""
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 50))

        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Search across all models
        news_events_results = NewsAndEvents.objects.search(query)
        program_results = Program.objects.search(query)
        course_results = Course.objects.search(query)
        quiz_results = Quiz.objects.search(query)

        # Combine querysets
        queryset_chain = chain(
            news_events_results,
            program_results,
            course_results,
            quiz_results
        )

        # Sort by pk (most recent first)
        results = sorted(
            queryset_chain,
            key=lambda instance: instance.pk,
            reverse=True
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
    - limit: Maximum suggestions (default: 10)

    Returns:
        200: List of suggestions with titles
        400: Missing query parameter
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Return search suggestions for autocomplete."""
        query = request.GET.get('q', '').strip()
        limit = int(request.GET.get('limit', 10))

        if not query:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        suggestions = []

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

        # Combine and deduplicate
        all_suggestions = list(chain(
            news_suggestions,
            program_suggestions,
            course_suggestions,
            quiz_suggestions
        ))

        # Remove duplicates while preserving order
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
