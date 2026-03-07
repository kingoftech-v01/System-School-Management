# Quiz App

Course-based quiz system with multiple choice, essay, and true/false question types, timed sittings, automatic scoring, progress tracking, and manual marking.

## Description

The quiz app provides a comprehensive assessment system tied to courses. Lecturers create quizzes and add multiple choice, essay, and true/false questions. Students take quizzes with sequential question display, progress tracking, and answer feedback. The app supports timed sittings with automatic expiration, automatic scoring for MC and true/false questions, manual marking for essays, and per-category progress tracking. A full REST API is provided alongside the traditional Django frontend views.

## Main Features

- **Quiz CRUD**: Create, update, delete quizzes tied to courses (lecturer only)
- **MC Questions**: Create and edit multiple choice questions with inline choice formsets
- **Essay Questions**: Create essay-style questions that require manual grading
- **True/False Questions**: Create true/false questions with automatic scoring
- **Quiz Taking**: Sequential question display with progress tracking and answer feedback
- **Timed Sittings**: Configurable time limits with automatic expiration tracking
- **Automatic Scoring**: MC and true/false questions scored automatically
- **Manual Marking**: Lecturer marks essay questions with score override capability
- **Progress Tracking**: Student progress scores per category
- **Single Attempt**: Enforce one attempt per student per quiz
- **Draft Mode**: Hide quizzes from students until ready to publish
- **Internationalization**: Full i18n support via django-modeltranslation for Quiz, Question, and Choice fields
- **REST API**: Complete CRUD API with filtering, search, and ordering via DRF

## User Roles

| Role | Quiz Permissions |
|------|-----------------|
| student | Take quizzes, view own progress and completed sittings |
| professor | Create/edit/delete quizzes and questions, view marking list, grade essays, view all sittings for owned courses |
| direction | Full access to all quizzes, questions, marking, and progress across all courses |
| parent | No direct quiz access (views student progress through parent dashboard) |
| admin | Full superuser access: all CRUD operations, view all marking entries, manage via Django admin |
| prefet | No direct quiz permissions (discipline-focused role) |
| accountant | No direct quiz permissions (finance-focused role) |
| secretary | No direct quiz permissions (administrative role) |
| librarian | No direct quiz permissions (library-focused role) |
| registrar | No direct quiz permissions (enrollment-focused role) |

Note: The `lecturer_required` and `student_required` decorators from `accounts.decorators` gate frontend views. The `IsLecturerUser` permission from `accounts.permissions` gates API write operations. Superusers bypass all permission checks.

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Quiz | Yes (frontend + API) | Yes (list per course) | Yes (frontend + API) | Yes (frontend + API) |
| MCQuestion | Yes (frontend + API) | Via quiz (frontend + API) | Yes (frontend + API) | API only |
| EssayQuestion | Yes (frontend + API) | Via quiz (API) | API only | API only |
| TrueFalseQuestion | Yes (frontend) | Via quiz | No | No |
| Sitting | Automatic on quiz start | Yes (marking list, API) | Yes (score override via marking) | Auto-deleted for non-exam papers |
| Progress | Automatic on first quiz | Yes (student progress view, API) | Automatic (score updates) | N/A |

## Models

- `Quiz` -- course FK, title, slug, description, category (assignment/exam/practice), random_order, answers_at_end, exam_paper, single_attempt, pass_mark, draft, time_limit (minutes), timestamp
- `Progress` -- user OneToOne, score (CSV string encoding per-category scores)
- `Sitting` -- user FK, quiz FK, course FK, question_order, question_list, incorrect_questions, current_score, complete, user_answers (JSON), start, end, time_spent (DurationField)
- `Question` (abstract base) -- quiz M2M, figure (ImageField), content, explanation; uses `InheritanceManager` from `model_utils`
- `MCQuestion` extends Question -- choice_order (content/random/none)
- `Choice` -- question FK (to MCQuestion), choice_text, correct (boolean)
- `EssayQuestion` extends Question -- no extra fields, `check_if_correct` always returns False (requires manual grading)
- `TrueFalseQuestion` extends Question -- correct_answer (BooleanField)

## Frontend URL Patterns

All frontend URLs are under the `frontend:quiz:` namespace.

| URL Pattern | View | Name | Access |
|-------------|------|------|--------|
| `<slug>/quizzes/` | `quiz_list` | `quiz_index` | login_required |
| `progress/` | `QuizUserProgressView` | `quiz_progress` | student_required |
| `marking_list/` | `QuizMarkingList` | `quiz_marking` | lecturer_required |
| `marking/<int:pk>/` | `QuizMarkingDetail` | `quiz_marking_detail` | lecturer_required |
| `<int:pk>/<slug>/take/` | `QuizTake` | `quiz_take` | student_required |
| `<slug>/quiz_add/` | `QuizCreateView` | `quiz_create` | lecturer_required |
| `<slug>/<int:pk>/add/` | `QuizUpdateView` | `quiz_update` | lecturer_required |
| `<slug>/<int:pk>/delete/` | `quiz_delete` | `quiz_delete` | lecturer_required |
| `mc-question/add/<slug>/<int:quiz_id>/` | `MCQuestionCreate` | `mc_create` | lecturer_required |
| `mc-question/edit/<slug>/<int:pk>/` | `MCQuestionEdit` | `mc_edit` | lecturer_required |
| `essay-question/add/<slug>/<int:quiz_id>/` | `EssayQuestionCreate` | `essay_create` | lecturer_required |
| `tf-question/add/<slug>/<int:quiz_id>/` | `TFQuestionCreate` | `tf_create` | lecturer_required |

## API Endpoints

All API endpoints are under the `api:v1:quiz:` namespace, served by DRF ViewSets with a `DefaultRouter`.

### Quizzes (`/api/quizzes/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/quizzes/` | List quizzes (students see non-draft only) | IsAuthenticated |
| POST | `/api/quizzes/` | Create a new quiz | IsLecturerUser |
| GET | `/api/quizzes/{id}/` | Retrieve quiz detail with question count | IsAuthenticated |
| PUT/PATCH | `/api/quizzes/{id}/` | Update a quiz | IsLecturerUser |
| DELETE | `/api/quizzes/{id}/` | Delete a quiz | IsLecturerUser |
| GET | `/api/quizzes/{id}/questions/` | Get all MC and essay questions for a quiz | IsAuthenticated |
| POST | `/api/quizzes/{id}/start_quiz/` | Start a new sitting for the quiz | IsAuthenticated |
| GET | `/api/quizzes/my_quizzes/` | List quizzes for enrolled courses | IsAuthenticated |

**Filtering**: `course`, `category`, `draft`
**Search**: `title`, `description`
**Ordering**: `title`, `timestamp` (default: `-timestamp`)

### MC Questions (`/api/mc-questions/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/mc-questions/` | List MC questions | IsAuthenticated |
| POST | `/api/mc-questions/` | Create MC question | IsLecturerUser |
| GET | `/api/mc-questions/{id}/` | Retrieve MC question | IsAuthenticated |
| PUT/PATCH | `/api/mc-questions/{id}/` | Update MC question | IsLecturerUser |
| DELETE | `/api/mc-questions/{id}/` | Delete MC question | IsLecturerUser |

**Filtering**: `quiz`
**Ordering**: `order`

### Essay Questions (`/api/essay-questions/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/essay-questions/` | List essay questions | IsAuthenticated |
| POST | `/api/essay-questions/` | Create essay question | IsLecturerUser |
| GET | `/api/essay-questions/{id}/` | Retrieve essay question | IsAuthenticated |
| PUT/PATCH | `/api/essay-questions/{id}/` | Update essay question | IsLecturerUser |
| DELETE | `/api/essay-questions/{id}/` | Delete essay question | IsLecturerUser |

**Filtering**: `quiz`
**Ordering**: `order`

### Sittings (`/api/sittings/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/sittings/` | List sittings (students see own only, lecturers see all) | IsAuthenticated |
| GET | `/api/sittings/{id}/` | Retrieve sitting detail | IsAuthenticated |
| POST | `/api/sittings/{id}/submit_answer/` | Submit answer for a question | IsAuthenticated |
| POST | `/api/sittings/{id}/complete/` | Mark sitting as complete | IsAuthenticated |

**Filtering**: `quiz`, `user`, `complete`
**Ordering**: `start`, `end` (default: `-start`)

### Progress (`/api/progress/`)

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/api/progress/` | List progress records (students see own only) | IsAuthenticated |
| GET | `/api/progress/{id}/` | Retrieve progress detail | IsAuthenticated |

**Filtering**: `user`
**Ordering**: `timestamp`, `score`

## File Structure

```
quiz/
  __init__.py
  admin.py               # TranslationAdmin for Quiz, MCQuestion, EssayQuestion, Progress, Sitting
  apps.py                # Django app config
  forms.py               # QuizAddForm, QuestionForm, EssayForm, MCQuestionForm, MCQuestionFormSet,
                         #   EssayQuestionForm, TrueFalseQuestionForm
  models.py              # Quiz, Progress, Sitting, Question (base), MCQuestion, Choice,
                         #   EssayQuestion, TrueFalseQuestion + managers
  serializers.py         # DRF serializers: QuizSerializer, QuizListSerializer, QuizCreateSerializer,
                         #   MCQuestionSerializer, EssayQuestionSerializer, SittingSerializer,
                         #   SittingListSerializer, ProgressSerializer
  translation.py         # modeltranslation: Quiz (title, description), Question (content, explanation),
                         #   Choice (choice_text) + pass-through for MC/Essay/TF subclasses
  urls.py                # api_router (DefaultRouter), api_urlpatterns, frontend_urlpatterns
  utils.py               # Empty utility module (placeholder)
  views_api.py           # DRF ViewSets: QuizViewSet, MCQuestionViewSet, EssayQuestionViewSet,
                         #   SittingViewSet, ProgressViewSet
  views_frontend.py      # Django CBVs/FBVs: QuizCreateView, QuizUpdateView, quiz_delete, quiz_list,
                         #   MCQuestionCreate, MCQuestionEdit, EssayQuestionCreate, TFQuestionCreate,
                         #   QuizUserProgressView, QuizMarkingList, QuizMarkingDetail, QuizTake
  templatetags/
    __init__.py
    quiz_tags.py         # Template tags: correct_answer_for_all (inclusion tag),
                         #   answer_choice_to_string (filter)
  tests/
    __init__.py
    test_admin.py        # Admin registration and configuration tests
    test_forms.py        # Form validation tests (QuizAddForm, MCQuestionFormSet, etc.)
    test_models.py       # Model creation and method tests
    test_models_extended.py  # Extended model tests (managers, edge cases)
    test_serializers.py  # DRF serializer validation tests
    test_templatetags.py # Template tag output tests
    test_views_api.py    # API endpoint integration tests
    test_views_frontend.py   # Frontend view integration tests
  migrations/
    __init__.py
    0001_initial.py
```

## Known Issues

- `MCQuestionCreate.form_valid` uses non-namespaced redirect `"mc_create"` instead of `"frontend:quiz:mc_create"` (line ~191 in views_frontend.py). This was fixed in later views but the original redirect pattern should be verified.
- `TrueFalseQuestion` has no API ViewSet registered -- only MC and Essay question types are exposed via the REST API.
- `utils.py` is an empty placeholder file with no utility functions.
- Admin `MCQuestionAdmin` has a malformed `fieldsets` string concatenation on line 69 of admin.py (`"figure" "quiz" "choice_order"` is concatenated into `"figurequizchoice_order"`).

## Dependencies

- `course` app -- `Course` model (FK from Quiz and Sitting)
- `accounts` app -- `lecturer_required`, `student_required` decorators; `IsLecturerUser` DRF permission
- `core` app -- `unique_slug_generator` utility for Quiz slug auto-generation
- `model_utils` -- `InheritanceManager` for polymorphic Question queries (`select_subclasses()`)
- `modeltranslation` -- i18n field registration for Quiz, Question, Choice
- `django-ratelimit` -- rate limiting (listed as dependency, not yet applied to views)
- `djangorestframework` -- REST API views and serializers
- `django-filter` -- `DjangoFilterBackend` for API query filtering

## URL Namespace

- Frontend: `frontend:quiz:<view_name>`
- API: `api:v1:quiz:<resource-name>`
