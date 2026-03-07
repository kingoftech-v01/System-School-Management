"""
Search utilities - shared query logic for frontend and API views.
"""

from itertools import chain

from core.models import NewsAndEvents
from course.models import Program, Course
from quiz.models import Quiz


# Maps search_type values to the model keys they include
SEARCH_TYPE_MODEL_MAP = {
    'all': ['news', 'programs', 'courses', 'quizzes'],
    'news': ['news'],
    'programs': ['programs'],
    'courses': ['courses'],
    'quizzes': ['quizzes'],
}

# Maps model keys to their date field name (None if model has no date field)
MODEL_DATE_FIELD = {
    'news': 'upload_time',
    'programs': None,
    'courses': None,
    'quizzes': 'timestamp',
}


def execute_search(query, search_type='all', date_from=None, date_to=None):
    """
    Execute search across models with optional type and date filters.

    Args:
        query: Search string (already validated, min 2 chars).
        search_type: One of 'all', 'news', 'programs', 'courses', 'quizzes'.
        date_from: Optional date object for range start.
        date_to: Optional date object for range end.

    Returns:
        list of model instances sorted by pk descending.
    """
    model_keys = SEARCH_TYPE_MODEL_MAP.get(search_type, SEARCH_TYPE_MODEL_MAP['all'])
    results_lists = []

    if 'news' in model_keys:
        qs = NewsAndEvents.objects.search(query)
        qs = _apply_date_filter(qs, 'upload_time', date_from, date_to)
        results_lists.append(qs)

    if 'programs' in model_keys:
        qs = Program.objects.search(query)
        # Program has no date field — skip date filtering
        results_lists.append(qs)

    if 'courses' in model_keys:
        qs = Course.objects.search(query)
        # Course has no date field — skip date filtering
        results_lists.append(qs)

    if 'quizzes' in model_keys:
        qs = Quiz.objects.search(query)
        qs = _apply_date_filter(qs, 'timestamp', date_from, date_to)
        results_lists.append(qs)

    combined = chain(*results_lists)
    return sorted(combined, key=lambda instance: instance.pk, reverse=True)


def _apply_date_filter(queryset, field_name, date_from, date_to):
    """Apply date range filter to a queryset if dates are provided."""
    if date_from:
        queryset = queryset.filter(**{f'{field_name}__date__gte': date_from})
    if date_to:
        queryset = queryset.filter(**{f'{field_name}__date__lte': date_to})
    return queryset
