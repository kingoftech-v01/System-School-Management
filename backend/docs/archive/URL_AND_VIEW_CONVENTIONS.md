# URL and View Conventions - Zumodra Platform

**Version**: 2.0
**Last Updated**: 2026-01-17
**Status**: MANDATORY - All new apps MUST follow this convention

---

## Table of Contents

1. [Overview](#overview)
2. [URL Structure](#url-structure)
3. [Namespace Convention](#namespace-convention)
4. [View Organization](#view-organization)
5. [URL Patterns](#url-patterns)
6. [File Structure](#file-structure)
7. [Implementation Checklist](#implementation-checklist)
8. [Examples](#examples)

---

## Overview

Zumodra uses a **dual-layer architecture** separating:
- **Frontend Views** (HTML templates with HTMX/Alpine.js) - For human users
- **API Views** (REST JSON endpoints with DRF) - For programmatic access

**CRITICAL RULE**: Every app MUST have BOTH frontend and API views configured, even if one layer is minimal.

---

## URL Structure

### Standard URL Pattern

```
# Frontend URLs (HTML responses)
/app-name/feature-name/
/app-name/feature-name/<uuid:pk>/
/app-name/feature-name/<uuid:pk>/action/

# API URLs (JSON responses)
/api/v1/app-name/resource-name/
/api/v1/app-name/resource-name/<uuid:pk>/
/api/v1/app-name/resource-name/<uuid:pk>/action/
```

### URL Naming Conventions

| Layer | URL Style | Example |
|-------|-----------|---------|
| **Frontend** | Kebab-case, descriptive | `/jobs/job-postings/create/` |
| **API** | Kebab-case, resource-oriented | `/api/v1/jobs/job-postings/` |

---

## Namespace Convention

### Nested Namespace Structure

All URLs MUST use nested namespaces for organization:

```python
# Format: layer:app:view-name
'frontend:jobs:job_list'              # Frontend HTML view
'api:v1:jobs:job-list'                # API endpoint (DRF uses hyphens)

# Examples across different apps
'frontend:hr:employee-directory'     # Frontend
'api:v1:hr:employees'                # API

'frontend:dashboard:index'           # Frontend
'api:v1:dashboard:quick-stats'       # API
```

### Namespace Levels

1. **Layer**: `frontend` or `api`
2. **Version** (API only): `v1`, `v2`, etc.
3. **App**: `ats`, `hr`, `accounts`, etc.
4. **View**: Specific view name

---

## View Organization

### Directory Structure (MANDATORY)

Every app MUST have this structure:

```
app_name/
├── models.py                    # Database models
├── forms.py                     # ⭐ Django forms (ModelForms, Forms)
├── views_frontend.py            # ⭐ Frontend HTML views
├── views_api.py                 # ⭐ API views (DRF ViewSets/APIViews)
├── serializers.py               # DRF serializers for API
├── urls.py                      # ⭐ URL configuration (includes BOTH)
├── templates/
│   └── app_name/
│       ├── list.html
│       ├── detail.html
│       └── form.html
└── api/                         # Optional: Complex API structure
    ├── serializers.py
    ├── viewsets.py
    └── permissions.py
```

### File Purposes

| File | Purpose | When to Use |
|------|---------|-------------|
| `forms.py` | Django forms (ModelForms, Forms) | ALWAYS - Every app |
| `views_frontend.py` | HTML views that render templates | ALWAYS - Every app |
| `views_api.py` | REST API views (ViewSets, APIViews) | ALWAYS - Every app |
| `serializers.py` | DRF serializers for JSON responses | ALWAYS - Every app |
| `urls.py` | URL routing for BOTH frontend and API | ALWAYS - Every app |

---

## URL Patterns

### urls.py Structure (MANDATORY Template)

Every app's `urls.py` MUST follow this structure:

```python
"""
App Name URLs - Frontend and API routing.

This module configures URL patterns for:
- Frontend HTML views (template_views.py)
- REST API endpoints (views.py with DRF)

URL Namespaces:
- Frontend: frontend:app_name:view_name
- API: api:v1:app_name:resource-name
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import template_views  # Frontend HTML views
from . import views           # API views

# ============================================================================
# API ROUTER (DRF ViewSets)
# ============================================================================

api_router = DefaultRouter()

# Register all ViewSets here
# Format: api_router.register(r'resource-name', ViewSetClass, basename='resource-name')

api_router.register(
    r'resources',              # URL path segment
    views.ResourceViewSet,     # ViewSet class
    basename='resource'        # Used for reverse() - singular form
)

# Example: Job postings
# api_router.register(r'job-postings', views.JobPostingViewSet, basename='job-posting')


# ============================================================================
# API URLPATTERNS (Non-ViewSet API views)
# ============================================================================

api_urlpatterns = [
    # Include router URLs
    path('', include(api_router.urls)),

    # Additional API endpoints (non-ViewSet)
    # Format: path('custom-action/', views.CustomAPIView.as_view(), name='custom-action')

    # Example: Custom action endpoint
    # path('bulk-import/', views.BulkImportAPIView.as_view(), name='bulk-import'),
]


# ============================================================================
# FRONTEND URLPATTERNS (HTML Template Views)
# ============================================================================

frontend_urlpatterns = [
    # List view (index)
    path(
        '',
        template_views.resource_list,
        name='resource_list'
    ),

    # Detail view
    path(
        '<uuid:pk>/',
        template_views.resource_detail,
        name='resource_detail'
    ),

    # Create view
    path(
        'create/',
        template_views.resource_create,
        name='resource_create'
    ),

    # Update view
    path(
        '<uuid:pk>/edit/',
        template_views.resource_update,
        name='resource_update'
    ),

    # Delete view
    path(
        '<uuid:pk>/delete/',
        template_views.resource_delete,
        name='resource_delete'
    ),

    # Custom action views
    # Format: path('<uuid:pk>/action-name/', template_views.custom_action, name='action_name')

    # Example: Archive action
    # path('<uuid:pk>/archive/', template_views.resource_archive, name='resource_archive'),
]


# ============================================================================
# APP URL CONFIGURATION
# ============================================================================

app_name = 'app_name'  # Used in namespace: frontend:app_name:view_name

urlpatterns = [
    # API URLs: /api/v1/app-name/
    path('api/', include((api_urlpatterns, 'api'))),

    # Frontend URLs: /app-name/
    path('', include((frontend_urlpatterns, 'frontend'))),
]
```

---

## File Structure

### template_views.py Structure (MANDATORY)

```python
"""
App Name Template Views - Frontend HTML views.

This module provides template-based views for human users:
- List views with filtering/pagination
- Detail views with related data
- Create/Update forms
- Custom action views

All views render HTML templates using Django's render().
Uses HTMX for dynamic interactions and Alpine.js for client-side reactivity.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from .models import Resource
from .forms import ResourceForm


# ============================================================================
# LIST VIEWS
# ============================================================================

@login_required
def resource_list(request):
    """
    List all resources with filtering, search, and pagination.

    Features:
    - Search by name/description
    - Filter by status/category
    - Pagination (20 items per page)
    - Sort by created_at, name, etc.

    Template: app_name/resource_list.html
    Context:
        - resources: Paginated queryset
        - search: Search query string
        - filters: Applied filter values
    """
    # Get query parameters
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status')
    category_filter = request.GET.get('category')
    sort_by = request.GET.get('sort', '-created_at')
    page = request.GET.get('page', 1)

    # Base queryset
    resources = Resource.objects.all()

    # Apply search
    if search:
        resources = resources.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    # Apply filters
    if status_filter:
        resources = resources.filter(status=status_filter)

    if category_filter:
        resources = resources.filter(category=category_filter)

    # Apply sorting
    resources = resources.order_by(sort_by)

    # Pagination
    paginator = Paginator(resources, 20)
    resources_page = paginator.get_page(page)

    context = {
        'resources': resources_page,
        'total_count': paginator.count,
        'search': search,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'page_title': _('Resources'),
        'meta_description': _('Browse all resources'),
    }

    return render(request, 'app_name/resource_list.html', context)


# ============================================================================
# DETAIL VIEWS
# ============================================================================

@login_required
def resource_detail(request, pk):
    """
    Display detailed information for a single resource.

    Includes:
    - All resource fields
    - Related objects (prefetched)
    - Activity history
    - Action buttons (edit, delete, custom actions)

    Template: app_name/resource_detail.html
    Context:
        - resource: Resource instance
        - related_items: Related objects
        - can_edit: Permission check
        - can_delete: Permission check
    """
    resource = get_object_or_404(
        Resource.objects.select_related('category', 'owner'),
        pk=pk
    )

    # Permission checks
    can_edit = request.user == resource.owner or request.user.is_staff
    can_delete = request.user == resource.owner or request.user.is_staff

    # Get related data
    related_items = resource.related_items.all()[:10]

    context = {
        'resource': resource,
        'related_items': related_items,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'page_title': resource.name,
        'meta_description': resource.description[:160],
    }

    return render(request, 'app_name/resource_detail.html', context)


# ============================================================================
# CREATE/UPDATE VIEWS
# ============================================================================

@login_required
def resource_create(request):
    """
    Create a new resource.

    GET: Display empty form
    POST: Validate and save new resource

    Template: app_name/resource_form.html
    Context:
        - form: ResourceForm instance
        - form_title: "Create Resource"
        - submit_text: "Create"
    """
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.owner = request.user
            resource.save()
            form.save_m2m()

            messages.success(request, _('Resource created successfully'))
            return redirect('app_name:frontend:resource_detail', pk=resource.pk)
    else:
        form = ResourceForm()

    context = {
        'form': form,
        'form_title': _('Create Resource'),
        'submit_text': _('Create'),
        'cancel_url': 'app_name:frontend:resource_list',
    }

    return render(request, 'app_name/resource_form.html', context)


@login_required
def resource_update(request, pk):
    """
    Update an existing resource.

    GET: Display pre-filled form
    POST: Validate and save changes

    Template: app_name/resource_form.html
    Context:
        - form: ResourceForm instance with current data
        - resource: Resource being edited
        - form_title: "Edit Resource"
        - submit_text: "Save Changes"
    """
    resource = get_object_or_404(Resource, pk=pk)

    # Permission check
    if resource.owner != request.user and not request.user.is_staff:
        messages.error(request, _('You do not have permission to edit this resource'))
        return redirect('app_name:frontend:resource_detail', pk=pk)

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, _('Resource updated successfully'))
            return redirect('app_name:frontend:resource_detail', pk=resource.pk)
    else:
        form = ResourceForm(instance=resource)

    context = {
        'form': form,
        'resource': resource,
        'form_title': _('Edit Resource'),
        'submit_text': _('Save Changes'),
        'cancel_url': 'app_name:frontend:resource_detail',
    }

    return render(request, 'app_name/resource_form.html', context)


# ============================================================================
# DELETE VIEWS
# ============================================================================

@login_required
def resource_delete(request, pk):
    """
    Delete a resource (with confirmation).

    GET: Display confirmation page
    POST: Delete resource and redirect

    Template: app_name/resource_confirm_delete.html
    Context:
        - resource: Resource to be deleted
        - related_count: Count of related objects that will be affected
    """
    resource = get_object_or_404(Resource, pk=pk)

    # Permission check
    if resource.owner != request.user and not request.user.is_staff:
        messages.error(request, _('You do not have permission to delete this resource'))
        return redirect('app_name:frontend:resource_detail', pk=pk)

    if request.method == 'POST':
        resource_name = resource.name
        resource.delete()
        messages.success(request, _('Resource "%(name)s" deleted successfully') % {'name': resource_name})
        return redirect('app_name:frontend:resource_list')

    # Get related objects count
    related_count = resource.related_items.count()

    context = {
        'resource': resource,
        'related_count': related_count,
        'page_title': _('Delete Resource'),
    }

    return render(request, 'app_name/resource_confirm_delete.html', context)


# ============================================================================
# CUSTOM ACTION VIEWS
# ============================================================================

@login_required
def resource_archive(request, pk):
    """
    Archive a resource.

    POST only: Mark resource as archived

    Redirects to: resource_detail
    """
    resource = get_object_or_404(Resource, pk=pk)

    # Permission check
    if resource.owner != request.user and not request.user.is_staff:
        messages.error(request, _('You do not have permission to archive this resource'))
        return redirect('app_name:frontend:resource_detail', pk=pk)

    if request.method == 'POST':
        resource.status = 'archived'
        resource.save(update_fields=['status'])
        messages.success(request, _('Resource archived successfully'))

    return redirect('app_name:frontend:resource_detail', pk=resource.pk)
```

### views.py Structure (API - MANDATORY)

```python
"""
App Name API Views - REST API endpoints.

This module provides REST API views using Django Rest Framework:
- ViewSets for CRUD operations
- Custom actions for specific business logic
- Filtering, search, and pagination
- Permission-based access control

All views return JSON responses.
API URL namespace: api:v1:app_name:resource-name
"""

from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Resource
from .serializers import (
    ResourceSerializer,
    ResourceCreateSerializer,
    ResourceUpdateSerializer,
    ResourceListSerializer
)
from .permissions import IsOwnerOrReadOnly


# ============================================================================
# VIEWSETS
# ============================================================================

class ResourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Resource CRUD operations.

    Provides:
    - list: GET /api/v1/app-name/resources/
    - retrieve: GET /api/v1/app-name/resources/{uuid}/
    - create: POST /api/v1/app-name/resources/
    - update: PUT /api/v1/app-name/resources/{uuid}/
    - partial_update: PATCH /api/v1/app-name/resources/{uuid}/
    - destroy: DELETE /api/v1/app-name/resources/{uuid}/

    Custom actions:
    - archive: POST /api/v1/app-name/resources/{uuid}/archive/
    - restore: POST /api/v1/app-name/resources/{uuid}/restore/
    - stats: GET /api/v1/app-name/resources/stats/

    Filtering:
    - ?status=active
    - ?category=web-development
    - ?owner=<user_id>

    Search:
    - ?search=keyword (searches name, description)

    Ordering:
    - ?ordering=created_at
    - ?ordering=-name
    """

    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'owner']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']
    lookup_field = 'pk'  # UUID primary key

    def get_queryset(self):
        """
        Return queryset based on user permissions.

        - Authenticated users: All resources they own + public resources
        - Anonymous users: Only public resources
        - Staff users: All resources
        """
        user = self.request.user

        if user.is_staff:
            # Staff sees everything
            return Resource.objects.all().select_related('owner', 'category')

        if user.is_authenticated:
            # Authenticated users see their own + public
            from django.db.models import Q
            return Resource.objects.filter(
                Q(owner=user) | Q(is_public=True)
            ).select_related('owner', 'category')

        # Anonymous users see only public
        return Resource.objects.filter(is_public=True).select_related('category')

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ResourceListSerializer
        elif self.action == 'create':
            return ResourceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ResourceUpdateSerializer
        return ResourceSerializer

    def perform_create(self, serializer):
        """Set owner to current user on create."""
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """Update modified timestamp on update."""
        serializer.save(updated_at=timezone.now())

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive a resource.

        POST /api/v1/app-name/resources/{uuid}/archive/

        Returns:
            200: Resource archived successfully
            403: No permission
            404: Resource not found
        """
        resource = self.get_object()

        # Permission check (only owner or staff)
        if resource.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to archive this resource'},
                status=status.HTTP_403_FORBIDDEN
            )

        resource.status = 'archived'
        resource.save(update_fields=['status'])

        serializer = self.get_serializer(resource)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore an archived resource.

        POST /api/v1/app-name/resources/{uuid}/restore/

        Returns:
            200: Resource restored successfully
            403: No permission
            404: Resource not found
        """
        resource = self.get_object()

        # Permission check
        if resource.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to restore this resource'},
                status=status.HTTP_403_FORBIDDEN
            )

        resource.status = 'active'
        resource.save(update_fields=['status'])

        serializer = self.get_serializer(resource)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get overall statistics for resources.

        GET /api/v1/app-name/resources/stats/

        Returns:
            200: Statistics object with counts and aggregates
        """
        from django.db.models import Count, Avg

        queryset = self.get_queryset()

        stats = {
            'total_count': queryset.count(),
            'active_count': queryset.filter(status='active').count(),
            'archived_count': queryset.filter(status='archived').count(),
            'by_category': list(
                queryset.values('category__name')
                .annotate(count=Count('id'))
                .order_by('-count')
            ),
        }

        return Response(stats)


# ============================================================================
# CUSTOM API VIEWS (Non-ViewSet)
# ============================================================================

from rest_framework.views import APIView

class BulkImportAPIView(APIView):
    """
    Bulk import resources from CSV/JSON.

    POST /api/v1/app-name/bulk-import/

    Request body:
        {
            "format": "csv" | "json",
            "data": [...]
        }

    Returns:
        201: Import successful with import summary
        400: Validation errors
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Handle bulk import."""
        import_format = request.data.get('format')
        data = request.data.get('data', [])

        if import_format not in ['csv', 'json']:
            return Response(
                {'error': 'Invalid format. Must be "csv" or "json"'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process import
        created_count = 0
        errors = []

        for item in data:
            try:
                serializer = ResourceCreateSerializer(data=item)
                if serializer.is_valid():
                    serializer.save(owner=request.user)
                    created_count += 1
                else:
                    errors.append({
                        'item': item,
                        'errors': serializer.errors
                    })
            except Exception as e:
                errors.append({
                    'item': item,
                    'errors': str(e)
                })

        return Response({
            'success': True,
            'created_count': created_count,
            'error_count': len(errors),
            'errors': errors[:10]  # Return first 10 errors
        }, status=status.HTTP_201_CREATED)
```

---

## Implementation Checklist

When creating a new app or feature, ALWAYS complete this checklist:

### ✅ Models & Business Logic
- [ ] Create models in `models.py`
- [ ] Add model methods and properties
- [ ] Create migrations
- [ ] Apply migrations

### ✅ API Layer (MANDATORY)
- [ ] Create serializers in `serializers.py`
- [ ] Create ViewSets/APIViews in `views.py`
- [ ] Register ViewSets in `urls.py` API router
- [ ] Add custom actions if needed
- [ ] Configure filtering, search, ordering
- [ ] Set proper permissions

### ✅ Frontend Layer (MANDATORY)
- [ ] Create template views in `template_views.py`
- [ ] Add URL patterns in `urls.py` frontend section
- [ ] Create templates (list, detail, form, delete confirm)
- [ ] Add HTMX attributes for dynamic interactions
- [ ] Add Alpine.js for client-side reactivity

### ✅ URL Configuration
- [ ] Follow namespace convention: `layer:app:view_name`
- [ ] Use kebab-case for URLs
- [ ] Use snake_case for view names
- [ ] Include BOTH api and frontend urlpatterns

### ✅ Admin Interface
- [ ] Register models in `admin.py`
- [ ] Configure list_display, filters, search
- [ ] Add custom actions if needed

### ✅ Tests
- [ ] Unit tests for models
- [ ] API tests for ViewSets
- [ ] Integration tests for workflows
- [ ] Create demo data fixtures

### ✅ Documentation
- [ ] Add docstrings to all views
- [ ] Document API endpoints
- [ ] Add comments explaining complex logic

---

## Examples

### Example 1: FreelancerProfile (Just Completed)

**URLs Configuration**:
```python
# accounts/urls.py

# API ViewSet registration
router.register(r'freelancer-profiles', FreelancerProfileViewSet, basename='freelancer-profile')

# URL namespaces:
# - API: api:v1:accounts:freelancer-profile-list
# - API: api:v1:accounts:freelancer-profile-detail
# - API: api:v1:accounts:freelancer-profile-me (custom action)
```

**API View**:
```python
# accounts/views.py
class FreelancerProfileViewSet(viewsets.ModelViewSet):
    """API ViewSet for freelancer profiles."""
    # Full CRUD + custom actions
    @action(detail=False, methods=['get', 'post', 'patch'])
    def me(self, request):
        # GET/POST/PATCH /api/v1/accounts/freelancer-profiles/me/
        ...
```

### Example 2: ATS Job Postings

**Frontend URLs**:
```
/jobs/job-postings/                          → frontend:ats:job_list
/jobs/job-postings/create/                   → frontend:ats:job_create
/jobs/job-postings/<uuid>/                   → frontend:ats:job_detail
/jobs/job-postings/<uuid>/edit/              → frontend:ats:job_update
/jobs/job-postings/<uuid>/duplicate/         → frontend:ats:job_duplicate
```

**API URLs**:
```
/api/v1/jobs/job-postings/                   → api:v1:jobs:job-posting-list
/api/v1/jobs/job-postings/<uuid>/            → api:v1:jobs:job-posting-detail
/api/v1/jobs/job-postings/<uuid>/publish/    → api:v1:jobs:job-posting-publish
```

---

## Summary

**KEY PRINCIPLES**:

1. ✅ **Dual Layer**: ALWAYS create both frontend and API views
2. ✅ **Separation**: `template_views.py` (HTML) vs `views.py` (API)
3. ✅ **Namespaces**: `frontend:app:view` and `api:v1:app:resource`
4. ✅ **URLs File**: Single `urls.py` with both API and frontend patterns
5. ✅ **Comments**: Extensive documentation in all view files
6. ✅ **Dynamic Data**: All views must handle filtering, search, pagination
7. ✅ **Permissions**: Proper access control on all views
8. ✅ **HTML Optional**: Templates can be minimal/skipped, but URL/view structure is mandatory

**NEVER**:
- ❌ Skip creating API views
- ❌ Skip creating frontend URL patterns
- ❌ Use flat namespace (always use nested)
- ❌ Hard-code data in templates
- ❌ Create views without docstrings

---

**This convention is MANDATORY for all new development in Zumodra.**
