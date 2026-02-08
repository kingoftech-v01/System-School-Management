# Search App

Global search across multiple models with combined results and pagination.

## Description

The search app provides a cross-model search that queries NewsAndEvents, Programs, Courses, and Quizzes using each model's `.search()` manager method. Results are combined, sorted by primary key (descending), and displayed with pagination (20 items per page). The search is also accessible via the header search bar.

## Main Features

- **Cross-Model Search**: Searches across NewsAndEvents, Program, Course, Quiz
- **Combined Results**: Merged queryset from all models
- **Pagination**: 20 results per page
- **Header Integration**: Search bar in the site header posts to this app

## User Roles

| Role | Permissions |
|------|------------|
| all users | Search (no login required) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Search Results | N/A | Yes (search + paginate) | N/A | N/A |

## Models

- No models of its own (searches across core, course, quiz models)

## Dependencies

- `core` (NewsAndEvents model)
- `course` (Program, Course models)
- `quiz` (Quiz model)

## URL Namespace

- Frontend: `frontend:search:<view_name>`
