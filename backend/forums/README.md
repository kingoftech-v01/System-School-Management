# Forums App

Full-featured discussion forums with categories, threads, posts, voting, subscriptions, tags, reporting, and moderation support.

## Description

The forums app provides a complete discussion platform. It includes category browsing, thread CRUD with tag support, nested post replies with soft delete, upvote/downvote voting, thread subscriptions with email notifications, content reporting, forum search, tag browsing, and user activity pages.

## Main Features

- **Forum Home**: Featured threads and recent activity
- **Categories**: Browse categories with thread counts
- **Threads**: Full CRUD with tag support, pinning, locking, featuring
- **Posts**: Nested replies with soft delete and editing
- **Voting**: Upvote/downvote system on posts
- **Subscriptions**: Thread subscriptions with email notifications
- **Reporting**: Content reporting via GenericFK
- **Search**: Search threads by title/content (minimum 3 characters)
- **Tags**: Tag browsing and filtering
- **User Activity**: My threads, my posts, my subscriptions pages

## User Roles

| Role | Permissions |
|------|------------|
| all authenticated | Create threads, post replies, vote, subscribe, report |
| thread author | Edit/delete own threads and posts |
| moderators | Edit/delete any thread or post (via `can_moderate_threads` permission) |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| ForumCategory | No | Yes (list + detail) | No | No |
| Thread | Yes | Yes (list + detail) | Yes | Yes |
| Post | Yes | Yes (via thread) | Yes | Yes (soft delete) |
| Vote | Yes (toggle) | N/A | N/A | N/A |
| ThreadSubscription | Yes | Yes (list) | N/A | Yes (unsubscribe) |
| Report | Yes | N/A | N/A | N/A |

## Models

- `ForumCategory` -- name, slug, description, is_active, requires_approval, ordering
- `Thread` -- category FK, author FK, title, content, slug, status, is_pinned/locked/featured, view_count, tags M2M
- `Post` -- thread FK, author FK, content, parent FK (nested), is_edited, is_deleted (soft delete), score
- `Vote` -- post FK, user FK, vote_type (+1/-1)
- `Tag` -- name, slug, use_count
- `ThreadSubscription` -- thread FK, user FK, email_on_reply
- `Report` -- GenericFK, reported_by FK, reason, status

## Dependencies

- `django.contrib.contenttypes` (GenericFK for reports)
- `django-ckeditor` (rich text in thread/post forms)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:forums:<view_name>`
- API: `api:v1:forums:<resource-name>`
