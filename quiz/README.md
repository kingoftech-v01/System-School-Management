# Quiz App

Course-based quiz system with multiple choice, essay, and true/false question types, timed sittings, automatic scoring, progress tracking, and manual marking.

## Description

The quiz app provides a comprehensive assessment system tied to courses. Lecturers create quizzes and multiple choice questions with inline formsets for choices. Students take quizzes with sequential question display, progress tracking, and answer feedback. The app supports timed sittings, automatic scoring for MC questions, manual marking for essays, and student progress tracking per category.

## Main Features

- **Quiz CRUD**: Create, update, delete quizzes tied to courses (lecturer only)
- **MC Questions**: Create multiple choice questions with inline choice formsets
- **Quiz Taking**: Sequential question display with progress tracking and answer feedback
- **Timed Sittings**: Automatic quiz completion when time expires
- **Automatic Scoring**: MC questions scored automatically
- **Manual Marking**: Lecturer marks essay questions with score override
- **Progress Tracking**: Student progress scores per category
- **Single Attempt**: Enforce one attempt per student per quiz

## User Roles

| Role | Permissions |
|------|------------|
| lecturer | Create/edit/delete quizzes, create MC questions, view marking list, grade essays |
| student | Take quizzes, view progress |
| superuser | View all marking entries |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Quiz | Yes | Yes (list per course) | Yes | Yes |
| MCQuestion | Yes (with choices) | Via quiz | No | No |
| EssayQuestion | No views | Via quiz | No | No |
| TrueFalseQuestion | No views | Via quiz | No | No |
| Sitting | Automatic | Yes (marking) | Yes (score override) | No |
| Progress | Automatic | Yes | N/A | N/A |

## Models

- `Quiz` -- course FK, title, description, slug, category, random_order, max_questions, pass_mark, time_limit, single_attempt
- `Progress` -- user FK, score (CSV string per category)
- `Sitting` -- user FK, quiz FK, course FK, question_order, current_score, complete, start/end time
- `Question` (base) -- quiz M2M, content, explanation (uses InheritanceManager)
- `MCQuestion` extends Question -- answer_order
- `Choice` -- question FK, choice text, is_correct
- `EssayQuestion` extends Question
- `TrueFalseQuestion` extends Question -- correct_answer (boolean)

## Known Issues

- `MCQuestionCreate.form_valid` uses non-namespaced redirect `"mc_create"` instead of `"frontend:quiz:mc_create"`

## Dependencies

- `course` (Course model)
- `model_utils` (InheritanceManager)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:quiz:<view_name>`
- API: `api:v1:quiz:<resource-name>`
