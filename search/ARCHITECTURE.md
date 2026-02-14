# Search App - Architecture Document

## Overview

The `search` app provides unified full-text search across the School Management
System. It searches four content models -- `NewsAndEvents`, `Program`, `Course`,
and `Quiz` -- and exposes results through both a server-rendered HTML frontend
and a REST API with autocomplete support. The app defines no database models of
its own; it is a pure query layer that delegates to custom `Manager.search()`
methods on the target models.

---

## File Inventory

| File | Purpose |
|------|---------|
| `models.py` | Empty -- no app-specific models |
| `utils.py` | Shared `execute_search()` and `_apply_date_filter()` helpers |
| `views_frontend.py` | `SearchView` (Django `ListView`, HTML) |
| `views_api.py` | `SearchAPIView`, `SearchSuggestionsAPIView` (DRF) |
| `urls.py` | Frontend + API URL routing |
| `forms.py` | `SearchForm`, `AdvancedSearchForm` |
| `serializers.py` | `UnifiedSearchResultSerializer` and per-model serializers |
| `templatetags/class_name.py` | `class_name` template filter |
| `admin.py` | Empty -- nothing to register |
| `apps.py` | `SearchConfig` (app label `search`) |

---

## Model Relationships

The search app queries external models but owns none. The four searchable
models and their key fields are:

```
+---------------------------------------------+
|  core.models.NewsAndEvents                  |
|---------------------------------------------|
|  id              PK (auto)                  |
|  title           CharField(200)             |
|  summary         TextField(200)             |
|  posted_as       CharField (News / Event)   |
|  upload_time     DateTimeField (auto_add)   |  <-- date filter field
|  updated_date    DateTimeField (auto)       |
|                                             |
|  Manager: NewsAndEventsManager              |
|    .search(query) -> icontains on           |
|       title, summary, posted_as             |
+---------------------------------------------+

+---------------------------------------------+
|  course.models.Program                      |
|---------------------------------------------|
|  id              PK (auto)                  |
|  title           CharField(150)             |
|  summary         TextField                  |
|                                             |
|  Manager: ProgramManager                    |
|    .search(query) -> icontains on           |
|       title, summary                        |
+---------------------------------------------+
         |
         | FK (program)
         v
+---------------------------------------------+
|  course.models.Course                       |
|---------------------------------------------|
|  id              PK (auto)                  |
|  slug            SlugField (unique)         |
|  title           CharField(200)             |
|  code            CharField(200, unique)     |
|  credit          IntegerField               |
|  summary         TextField(200)             |
|  program         FK -> Program              |
|  level           CharField                  |
|  year            IntegerField               |
|  semester        CharField                  |
|  is_elective     BooleanField               |
|                                             |
|  Manager: CourseManager                     |
|    .search(query) -> icontains on           |
|       title, summary, code, slug            |
+---------------------------------------------+
         |
         | FK (course)
         v
+---------------------------------------------+
|  quiz.models.Quiz                           |
|---------------------------------------------|
|  id              PK (auto)                  |
|  title           CharField(60)              |
|  slug            SlugField (unique)         |
|  description     TextField                  |
|  category        CharField (assignment/     |
|                    exam/practice)            |
|  course          FK -> Course               |
|  random_order    BooleanField               |
|  answers_at_end  BooleanField               |
|  exam_paper      BooleanField               |
|  single_attempt  BooleanField               |
|  pass_mark       SmallIntegerField          |
|  draft           BooleanField               |
|  time_limit      PositiveIntegerField       |
|  timestamp       DateTimeField (auto)       |  <-- date filter field
|                                             |
|  Manager: QuizManager                       |
|    .search(query) -> icontains on           |
|       title, description, category, slug    |
+---------------------------------------------+
```

### Relationship Diagram (ASCII)

```
                          search app
                    (no models of its own)
                              |
               +--------------+--------------+
               |              |              |
         reads from      reads from     reads from
               |              |              |
               v              v              v
       NewsAndEvents      Program ----< Course ----< Quiz
       (core)             (course)      (course)     (quiz)
```

The arrow `----<` means "has many" (FK from right to left). The search app
performs read-only queries against all four models.

---

## URL Routing

### Registration in main urlconf (`School_System/urls.py`)

```
Frontend:  /search/           ->  frontend_urlpatterns  (namespace: frontend:search)
API:       /api/v1/search/    ->  api_urlpatterns       (namespace: api:search)
```

### Frontend URLs (`search/urls.py` -- `frontend_urlpatterns`)

| Pattern | View | Name |
|---------|------|------|
| `/search/` | `SearchView` (ListView) | `frontend:search:query` |

### API URLs (`search/urls.py` -- `api_urlpatterns`)

| Pattern | View | Name |
|---------|------|------|
| `/api/v1/search/query/` | `SearchAPIView` | `api:search:query` |
| `/api/v1/search/suggestions/` | `SearchSuggestionsAPIView` | `api:search:suggestions` |

---

## View Access Patterns Per Role

### Authentication Requirements

| Endpoint | Auth Mechanism | Restriction |
|----------|---------------|-------------|
| Frontend `SearchView` | `LoginRequiredMixin` | Any authenticated user |
| API `SearchAPIView` | DRF default (`IsAuthenticated`) | Any authenticated user + rate limit |
| API `SearchSuggestionsAPIView` | DRF default (`IsAuthenticated`) | Any authenticated user + rate limit |

### Role-Based Access Matrix

The search app does **not** implement role-based filtering. All authenticated
users see the same results regardless of role. No permission classes beyond
authentication are applied.

| Role | Frontend Search | API Search | API Suggestions | Notes |
|------|:-:|:-:|:-:|-------|
| **student** | Yes | Yes | Yes | Can search all public content |
| **professor** | Yes | Yes | Yes | Same access as student |
| **direction** | Yes | Yes | Yes | Same access as all roles |
| **parent** | Yes | Yes | Yes | Same access as all roles |
| **admin** | Yes | Yes | Yes | Same access as all roles |
| **prefet** | Yes | Yes | Yes | Same access as all roles |
| **accountant** | Yes | Yes | Yes | Same access as all roles |
| **secretary** | Yes | Yes | Yes | Same access as all roles |
| **librarian** | Yes | Yes | Yes | Same access as all roles |
| **registrar** | Yes | Yes | Yes | Same access as all roles |
| **anonymous** | No | No | No | Redirected to login |

All ten roles have identical search capabilities. The only gate is
`LoginRequiredMixin` (frontend) or DRF's default `IsAuthenticated`
permission (API). Draft quizzes are **not** filtered out by the search app
itself -- the `QuizManager.search()` method returns them if they match.

### Rate Limiting

Both API views use `SearchRateThrottle` (scope: `search`), configured in
`base.py` at **50 requests/hour** per authenticated user.

---

## Business Logic Workflows

### 1. Frontend Search Flow

```
User (browser)
  |
  |  GET /search/?q=<term>&search_type=<type>&date_from=<d>&date_to=<d>
  v
SearchView.get_queryset()
  |
  |-- Tenant guard: if no request.tenant -> return empty queryset
  |-- Validate q (must be >= 2 chars after strip)
  |-- Instantiate AdvancedSearchForm(request.GET) to parse filters
  |-- Call execute_search(query, search_type, date_from, date_to)
  |      |
  |      |-- Determine model_keys from SEARCH_TYPE_MODEL_MAP
  |      |-- For each included model:
  |      |      Model.objects.search(query)
  |      |      + _apply_date_filter() if model has a date field
  |      |-- chain() all querysets
  |      |-- sorted(combined, key=pk, reverse=True)
  |      +-- return list
  |
  |-- self.count = len(results)
  |-- paginate_by = 20
  v
Template: search/search_view.html
  |-- Uses {% load class_name %} to identify result type
  |-- Renders icon + badge per type (Course / Program / Quiz / News)
  |-- Shows title, summary/description (truncated to 30 words)
  |-- Pagination with query params preserved
```

### 2. API Search Flow

```
Client (JS / mobile / external)
  |
  |  GET /api/v1/search/query/?q=<term>&limit=50&search_type=all&date_from=&date_to=
  v
SearchAPIView.get()
  |
  |-- Tenant guard -> 403 if missing
  |-- Validate q -> 400 if empty
  |-- Validate search_type against VALID_SEARCH_TYPES
  |-- Parse date_from / date_to via _parse_date()
  |-- Validate date_from < date_to -> 400 if reversed
  |-- Parse & clamp limit via _parse_limit() [1..SEARCH_MAX_RESULTS]
  |-- Call execute_search(query, search_type, date_from, date_to)[:limit]
  |-- Serialize with UnifiedSearchResultSerializer
  v
JSON Response:
  {
    "query": "...",
    "count": N,
    "results": [
      { "id": .., "title": .., "type": .., "url": .., "summary": .., "created_at": .. },
      ...
    ]
  }
```

### 3. Autocomplete / Suggestions Flow

```
Client
  |
  |  GET /api/v1/search/suggestions/?q=<partial>&limit=10
  v
SearchSuggestionsAPIView.get()
  |
  |-- Tenant guard -> 403 if missing
  |-- Validate q -> 400 if empty
  |-- Parse & clamp limit
  |-- Direct icontains queries on title + summary for each model:
  |      NewsAndEvents  -> title, summary
  |      Program        -> title, summary
  |      Course         -> title, summary
  |      Quiz           -> title only
  |-- chain() results, deduplicate preserving order
  |-- Truncate to limit
  v
JSON Response:
  {
    "query": "...",
    "suggestions": ["Title 1", "Title 2", ...]
  }
```

Note: The suggestions endpoint does **not** use the shared `execute_search()`
utility. It performs its own lighter queries (`.values_list('title', flat=True)`)
and does not support date filtering or search_type filtering.

### 4. Search Query Execution (`utils.py`)

```
execute_search(query, search_type, date_from, date_to)
  |
  |-- Look up model_keys in SEARCH_TYPE_MODEL_MAP:
  |     'all'      -> ['news', 'programs', 'courses', 'quizzes']
  |     'news'     -> ['news']
  |     'programs' -> ['programs']
  |     'courses'  -> ['courses']
  |     'quizzes'  -> ['quizzes']
  |
  |-- For each key in model_keys:
  |     news:     NewsAndEvents.objects.search(query) + date filter on upload_time
  |     programs: Program.objects.search(query)       (no date field)
  |     courses:  Course.objects.search(query)        (no date field)
  |     quizzes:  Quiz.objects.search(query)          + date filter on timestamp
  |
  |-- _apply_date_filter(qs, field_name, date_from, date_to):
  |     if date_from: qs.filter(<field>__date__gte=date_from)
  |     if date_to:   qs.filter(<field>__date__lte=date_to)
  |
  |-- chain(*results_lists)
  |-- sorted(combined, key=lambda obj: obj.pk, reverse=True)
  +-- return list (materialized, not a queryset)
```

---

## Data Flow Diagrams

### End-to-End Frontend Data Flow

```
+----------+     HTTP GET         +-----------------+
|  Browser | ------------------> | Django WSGI      |
+----------+   /search/?q=math   | URL Router       |
                                  +--------+--------+
                                           |
                                  frontend:search:query
                                           |
                                  +--------v--------+
                                  | SearchView      |
                                  | (ListView)      |
                                  +--------+--------+
                                           |
                              +------------+------------+
                              |                         |
                     AdvancedSearchForm           execute_search()
                     validates & cleans                  |
                     q, search_type,         +-----------+-----------+
                     date_from, date_to      |           |           |
                                             v           v           v
                                      NewsAndEvents  Program     Course    Quiz
                                      .search()      .search()  .search() .search()
                                             |           |           |       |
                                             +-----+-----+-----+----+
                                                   |
                                            chain + sort by pk desc
                                                   |
                                          +--------v--------+
                                          | Template        |
                                          | search_view.html|
                                          +--------+--------+
                                                   |
                                          HTML response with
                                          paginated results
                                          (20 per page)
```

### End-to-End API Data Flow

```
+----------+     HTTP GET         +-----------------+
| API      | ------------------> | DRF Router       |
| Client   |  /api/v1/search/   | URL Router       |
+----------+  query/?q=math      +--------+--------+
                                           |
                                  api:search:query
                                           |
                                  +--------v----------+
                                  | SearchAPIView     |
                                  | (APIView)         |
                                  | SearchRateThrottle|
                                  +--------+----------+
                                           |
                                  execute_search()
                                           |
                                  +--------v----------+
                                  | UnifiedSearch     |
                                  | ResultSerializer  |
                                  +--------+----------+
                                           |
                                  JSON response:
                                  { query, count, results[] }
```

---

## Dependencies

### Upstream Dependencies (search imports from)

```
search
  |
  +-- core.models
  |     NewsAndEvents         (searched model)
  |     NewsAndEventsManager  (.search() method)
  |
  +-- course.models
  |     Program               (searched model)
  |     ProgramManager        (.search() method)
  |     Course                (searched model)
  |     CourseManager         (.search() method)
  |
  +-- quiz.models
  |     Quiz                  (searched model)
  |     QuizManager           (.search() method)
  |
  +-- School_System.throttles
  |     SearchRateThrottle    (API rate limiting, scope='search', 50/hour)
  |
  +-- django.contrib.auth.mixins
  |     LoginRequiredMixin    (frontend auth)
  |
  +-- rest_framework
        APIView, Response, serializers, status
```

### Downstream Dependencies (other apps importing from search)

**None.** The search app is a leaf node in the dependency graph. No other
application module imports from `search.*`. Only test files reference search
components:

- `tests/test_forms_all.py` imports `SearchForm`, `AdvancedSearchForm`
- `tests/test_permissions_serializers.py` imports `class_name` templatetag

### Dependency Direction Diagram

```
                 core                course              quiz
                  |                    |                   |
      NewsAndEvents,          Program, Course,          Quiz,
      NewsAndEventsManager    ProgramManager,         QuizManager
                  |           CourseManager              |
                  +------------+   +--------------------+
                               |   |
                               v   v
                          +-------------+
                          | search app  |
                          +-------------+
                               |
                          (leaf node --
                           nothing imports
                           from search)

  School_System.throttles
       |
       +---> SearchRateThrottle ---> search.views_api
```

### Django Settings Dependencies

| Setting | Location | Default | Used By |
|---------|----------|---------|---------|
| `SEARCH_MAX_RESULTS` | `base.py` | `100` | `views_api.py` -- clamps `limit` param |
| `DEFAULT_THROTTLE_RATES['search']` | `base.py` | `50/hour` | `SearchRateThrottle` |

---

## Forms

### `SearchForm`

| Field | Type | Validation |
|-------|------|------------|
| `q` | `CharField(max_length=200)` | Required, min 2 chars |

### `AdvancedSearchForm`

| Field | Type | Validation |
|-------|------|------------|
| `q` | `CharField(max_length=200)` | Required |
| `search_type` | `ChoiceField` | Choices: `all`, `news`, `programs`, `courses`, `quizzes` |
| `date_from` | `DateField` | Optional |
| `date_to` | `DateField` | Optional, must be >= `date_from` |

The frontend `SearchView` uses `AdvancedSearchForm` exclusively. `SearchForm`
is defined but not referenced in any view -- it is available for simpler
use cases or widget embedding.

---

## Serializers

### `UnifiedSearchResultSerializer`

A non-model serializer that normalizes heterogeneous model instances into a
uniform JSON shape using `SerializerMethodField`:

| Output Field | Source Logic |
|-------------|-------------|
| `id` | `obj.pk` |
| `title` | `obj.title` or `str(obj)` |
| `type` | Class name mapping: `newsandevents` -> `news`, `program` -> `program`, `course` -> `course`, `quiz` -> `quiz` |
| `url` | `obj.slug` if present, else `None` |
| `summary` | `obj.summary` or `obj.description` or `None` |
| `created_at` | `obj.created_at` or `obj.upload_time` (NewsAndEvents) or `obj.timestamp` (Quiz) |

### Model-Specific Serializers (defined but unused)

| Serializer | Model | Fields |
|------------|-------|--------|
| `NewsSearchSerializer` | `NewsAndEvents` | `id`, `title`, `summary`, `created_at`, `updated_at` |
| `ProgramSearchSerializer` | `Program` | `id`, `title`, `summary`, `created_at` |
| `CourseSearchSerializer` | `Course` | `id`, `title`, `code`, `slug`, `summary`, `created_at` |
| `QuizSearchSerializer` | `Quiz` | `id`, `title`, `description`, `created_at` |

These are not currently referenced in any view. They exist for potential future
use if per-type serialization is needed.

---

## Template Tags

### `class_name` filter (`templatetags/class_name.py`)

```python
{{ result|class_name }}  ->  "Course", "Program", "Quiz", "NewsAndEvents"
```

Used in `search_view.html` to render type-specific icons and badges:

| Class Name | Icon | Badge Color |
|-----------|------|-------------|
| `Course` | `bi-book` | `bg-primary` |
| `Program` | `bi-mortarboard` | `bg-success` |
| `Quiz` | `bi-question-circle` | `bg-warning` |
| `NewsAndEvents` (fallback) | `bi-newspaper` | `bg-info` |

---

## Multi-Tenancy

Both the frontend view and API views include a **tenant guard**:

- **Frontend** (`SearchView.get_queryset`): Returns `NewsAndEvents.objects.none()`
  if `request.tenant` is not set.
- **API** (`SearchAPIView.get`, `SearchSuggestionsAPIView.get`): Returns HTTP
  403 with `{"error": "No tenant context available"}` if `request.tenant` is
  not set.

In production (multi-tenant mode with `django-tenants`), each tenant's schema
isolates its data. The search queries run within the active tenant's schema
automatically. In development mode (single-tenant), the tenant attribute may
not exist on the request, which is why the guard returns an empty result rather
than raising an error.

---

## Key Design Decisions

1. **No dedicated search index.** Search uses Django ORM `icontains` lookups
   via each model's custom `Manager.search()` method. There is no Elasticsearch,
   Solr, or PostgreSQL full-text search integration.

2. **Materialized list, not queryset.** `execute_search()` chains multiple
   querysets and sorts in Python (`sorted(..., key=pk, reverse=True)`),
   returning a plain `list`. This means results cannot benefit from database-
   level `LIMIT`/`OFFSET` for pagination -- the entire result set is loaded
   into memory before the `ListView` paginates it.

3. **No role-based filtering.** All authenticated users see identical results.
   Draft quizzes, unpublished content, and role-restricted resources are not
   filtered in the search layer.

4. **Suggestions bypass `execute_search()`.** The autocomplete endpoint uses
   direct `icontains` queries with `.values_list('title', flat=True)` for
   lighter database operations and does not support type or date filtering.

5. **Sorting by PK descending.** Results are sorted by primary key in
   descending order as a proxy for recency, since the searched models use
   different timestamp field names (or have no timestamp at all).
