# Quiz App - Architecture

## Overview

The quiz app is a self-contained Django application that provides a course-based assessment system. It follows a dual-interface pattern: traditional server-rendered Django views for the frontend and a REST API powered by Django REST Framework for programmatic access. The app depends on the `course` app for course associations and the `accounts` app for role-based access control.

## Layer Diagram

```text
+------------------------------------------------------------------+
|                        URL Router (urls.py)                      |
|   frontend_urlpatterns  ──>  views_frontend.py (CBVs / FBVs)    |
|   api_urlpatterns       ──>  views_api.py (DRF ViewSets)        |
+------------------------------------------------------------------+
        |                               |
        v                               v
+-------------------+       +------------------------+
| Forms (forms.py)  |       | Serializers            |
| - QuizAddForm     |       |   (serializers.py)     |
| - QuestionForm    |       | - QuizSerializer       |
| - EssayForm       |       | - MCQuestionSerializer |
| - MCQuestionForm  |       | - SittingSerializer    |
| - MCQuestionForm- |       | - ProgressSerializer   |
|   Set (inline)    |       +------------------------+
| - EssayQuestion-  |                   |
|   Form            |                   |
| - TrueFalseQues-  |                   |
|   tionForm        |                   |
+-------------------+                   |
        |                               |
        +---------------+---------------+
                        |
                        v
+------------------------------------------------------------------+
|                     Models (models.py)                            |
|                                                                  |
|  Quiz ──< Question (abstract, InheritanceManager)                |
|              |── MCQuestion ──< Choice                           |
|              |── EssayQuestion                                   |
|              |── TrueFalseQuestion                               |
|                                                                  |
|  Sitting (user + quiz + course, tracks attempt state)            |
|  Progress (user, CSV score accumulator)                          |
+------------------------------------------------------------------+
        |                               |
        v                               v
+-------------------+       +------------------------+
| course.Course     |       | accounts (User model,  |
| (FK target)       |       |  decorators,           |
|                   |       |  permissions)           |
+-------------------+       +------------------------+
```

## Model Relationships

```text
Course (course app)
  |
  |  1:N
  v
Quiz
  |
  |  M:N (via question_set)
  v
Question (abstract base, InheritanceManager)
  |── MCQuestion
  |     |
  |     | 1:N
  |     v
  |   Choice
  |── EssayQuestion
  |── TrueFalseQuestion

User (accounts app)
  |
  |── 1:1 ──> Progress (score CSV per category)
  |
  |── 1:N ──> Sitting
                |── FK ──> Quiz
                |── FK ──> Course
```

### Key Model Details

**Quiz**: Central entity tied to a `Course`. Contains configuration flags (`random_order`, `answers_at_end`, `exam_paper`, `single_attempt`, `draft`) and assessment parameters (`pass_mark`, `time_limit`). The slug is auto-generated via a `pre_save` signal using `core.utils.unique_slug_generator`.

**Question (base)**: Abstract polymorphic model using `model_utils.InheritanceManager`. The M2M relationship to Quiz means a single question can belong to multiple quizzes. Fields: `content` (text), `explanation` (shown post-answer), `figure` (optional image). Subclasses must implement `check_if_correct(guess)`, `get_answers()`, `get_answers_list()`, and `answer_choice_to_string(guess)`.

**MCQuestion**: Extends Question with `choice_order` (content/random/none). Related `Choice` objects store possible answers with a `correct` boolean flag.

**EssayQuestion**: Extends Question with no extra fields. `check_if_correct()` always returns `False` because essays require manual grading.

**TrueFalseQuestion**: Extends Question with a `correct_answer` BooleanField. Automatic grading compares the student's guess to the stored boolean.

**Sitting**: Tracks a single quiz attempt. Stores question ordering and remaining questions as comma-separated ID strings. `user_answers` is a JSON-encoded dict mapping question IDs to guesses. The `SittingManager` handles creating new sittings and enforcing single-attempt logic.

**Progress**: One-to-one with User. The `score` field is a CSV string encoding cumulative scores per quiz/category in the format `quiz_title,earned,possible,` repeated. The `update_score()` method uses regex to find and update entries.

## Request Flow

### Frontend: Student Takes a Quiz

```text
1. Student visits /<course-slug>/quizzes/
   --> quiz_list (FBV) --> renders quiz_list.html

2. Student clicks "Take Quiz"
   --> QuizTake.dispatch()
       - Loads Quiz by slug, Course by pk
       - Checks if questions exist (redirects if empty)
       - Calls SittingManager.user_sitting()
           - If single_attempt and completed sitting exists --> returns False --> redirect
           - If incomplete sitting exists --> returns it (resume)
           - Otherwise --> creates new Sitting via new_sitting()
       - Sets self.question (first question) and self.progress

3. QuizTake.get() renders question.html with current question
   - If MCQuestion --> QuestionForm with radio choices
   - If EssayQuestion --> EssayForm with textarea

4. Student submits answer (POST)
   --> QuizTake.form_valid()
       --> form_valid_user()
           - Gets/creates Progress for user
           - Calls question.check_if_correct(guess)
           - Updates Sitting score and Progress score
           - Stores answer in Sitting.user_answers JSON
           - Removes answered question from question_list
       - If more questions remain --> re-render with next question
       - If no questions remain --> final_result_user()
           - Calls sitting.mark_quiz_complete()
           - Renders result.html with score/percentage
           - If not exam_paper --> deletes sitting
```

### Frontend: Lecturer Marks an Essay

```text
1. Lecturer visits /marking_list/
   --> QuizMarkingList (ListView)
       - Filters Sitting.objects where complete=True
       - If not superuser: further filters by courses allocated to lecturer

2. Lecturer clicks a sitting
   --> QuizMarkingDetail (DetailView)
       - Displays all questions with user answers

3. Lecturer toggles correct/incorrect (POST)
   --> QuizMarkingDetail.post()
       - Gets question by ID from POST data
       - If question is in incorrect_questions --> removes it (adds 1 point)
       - If question is not in incorrect_questions --> adds it (subtracts 1 point)
```

### API: Start and Complete a Quiz

```text
1. Client: POST /api/quizzes/{id}/start_quiz/
   --> QuizViewSet.start_quiz()
       - Checks single_attempt constraint
       - Creates new Sitting
       - Returns SittingSerializer data

2. Client: POST /api/sittings/{id}/submit_answer/
   --> SittingViewSet.submit_answer()
       - Validates sitting is not complete
       - Calls sitting.add_user_answer(question_id, answer)

3. Client: POST /api/sittings/{id}/complete/
   --> SittingViewSet.complete()
       - Calls sitting.mark_quiz_complete()
       - Sets end timestamp, calculates time_spent
       - Returns final SittingSerializer data
```

## Access Control Architecture

### Frontend Views

Access control is enforced using decorators from `accounts.decorators`:

- `@login_required` -- all views require authentication
- `@lecturer_required` -- quiz CRUD, question CRUD, marking views
- `@student_required` -- quiz taking, progress viewing

Additionally, `_check_course_ownership()` is a helper that verifies the logged-in lecturer is allocated to the course (via `course.allocated_course.filter(lecturer=user)`). Superusers bypass this check.

### API Views

Access control uses DRF permission classes:

- `IsAuthenticated` -- all endpoints require authentication
- `IsLecturerUser` -- write operations (create, update, delete) on quizzes and questions
- Queryset-level filtering -- students see only their own sittings and progress; lecturers see all

### Role Matrix

```text
Action                    | student | professor | direction | admin
--------------------------|---------|-----------|-----------|------
View quiz list            |   Yes   |    Yes    |    Yes    |  Yes
Take quiz                 |   Yes   |    No*    |    No*    |  Yes
View own progress         |   Yes   |    No     |    No     |  Yes
Create/edit/delete quiz   |   No    |    Yes    |    Yes    |  Yes
Create/edit questions     |   No    |    Yes    |    Yes    |  Yes
View marking list         |   No    |    Yes**  |    Yes    |  Yes
Mark essays               |   No    |    Yes**  |    Yes    |  Yes
API read (quizzes)        |   Yes   |    Yes    |    Yes    |  Yes
API write (quizzes)       |   No    |    Yes    |    Yes    |  Yes

*  Quiz taking requires @student_required decorator
** Lecturers see only sittings for their allocated courses
```

## Data Flow: Score Tracking

### Per-Question Scoring (Sitting)

```text
Student answers question
  |
  +--> question.check_if_correct(guess)
  |       |
  |       +--> True:  sitting.add_to_score(1)
  |       |           progress.update_score(question, 1, 1)
  |       |
  |       +--> False: sitting.add_incorrect_question(question)
  |                   progress.update_score(question, 0, 1)
  |
  +--> sitting.add_user_answer(question, guess)
       (stored as JSON: {"question_id": "guess_value"})
```

### Cumulative Progress (Progress.score CSV)

The `Progress.score` field stores cumulative data as a CSV string:

```text
Format: "quiz_title,earned_score,possible_score,"
Example: "Math Quiz,3,5,History Quiz,8,10,"
```

The `update_score()` method uses regex to find an existing entry for the quiz and increments the earned/possible values. If no entry exists, it appends a new one.

## Internationalization

The app uses `django-modeltranslation` to provide translatable fields:

| Model | Translated Fields |
| --- | --- |
| Quiz | title, description |
| Question | content, explanation |
| Choice | choice_text |
| MCQuestion | (inherits from Question) |
| EssayQuestion | (inherits from Question) |
| TrueFalseQuestion | (inherits from Question) |

Registration is in `translation.py`. The admin uses `TranslationAdmin` from `modeltranslation.admin` to expose translated fields in the Django admin interface.

## Template Tags

The `quiz_tags.py` module in `templatetags/` provides:

- `correct_answer_for_all` -- inclusion tag that renders `quiz/correct_answer.html`, showing the correct answer and whether the user answered incorrectly
- `answer_choice_to_string` -- template filter that converts a guess value to its display string via `question.answer_choice_to_string()`

## Key Design Decisions

1. **Polymorphic Questions via InheritanceManager**: Instead of a single Question model with a `type` field, the app uses Django model inheritance with `model_utils.InheritanceManager`. This allows each question type to have its own fields and methods while queries like `quiz.question_set.all().select_subclasses()` return the correct subclass instances.

2. **CSV String Storage for Ordering**: `Sitting.question_order`, `question_list`, and `incorrect_questions` use comma-separated ID strings rather than M2M relationships or JSON arrays. This is a legacy design that simplifies ordering (pop from front, append to list) but limits scalability and makes queries harder.

3. **JSON String for User Answers**: `Sitting.user_answers` stores a JSON-encoded dict rather than using a JSONField. This is compatible with all database backends (including SQLite in development) but loses database-level JSON querying.

4. **Exam Paper vs Practice Mode**: When `exam_paper=True`, the Sitting is preserved after completion for marking. When `False`, the Sitting is deleted after showing results. `single_attempt=True` forces `exam_paper=True` automatically in `Quiz.save()`.

5. **Dual Interface Pattern**: The app exposes both traditional Django views (server-rendered HTML) and a DRF REST API. The frontend views use Django forms and template rendering, while the API views use serializers and JSON responses. Both share the same models and business logic.

6. **Course Ownership Checks**: Lecturer access is scoped to courses they are allocated to via `course.allocated_course.filter(lecturer=user)`. This prevents lecturers from modifying quizzes in courses they do not teach. Superusers bypass this check.
