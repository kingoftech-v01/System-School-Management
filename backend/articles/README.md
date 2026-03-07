# Articles App

News, blog articles, and announcements with hierarchical categories, comments, likes, and newsletter management.

## Description

The articles app provides a content management system for school news, blogs, and announcements. It features hierarchical categories using MPTT, rich text content via CKEditor, tagging via django-taggit, auto-slugs, a comment system with moderation, article likes, and newsletter subscription management.

**Status: All frontend views are currently placeholders returning "Coming soon in Phase 5" text responses.**

## Main Features (Planned)

- **Articles**: Rich text articles with featured images, SEO fields, reading time estimation
- **Categories**: Hierarchical MPTT-based category tree with article counts
- **Comments**: Threaded comments with moderation (pending, approved, rejected, spam)
- **Likes**: Article like/favorite system with unique constraint per user
- **Newsletter**: Subscription management with verification tokens and frequency preferences
- **Tags**: Article tagging via django-taggit

## User Roles

| Role | Permissions |
|------|------------|
| admin/direction | Publish, feature, and moderate articles and comments |
| professor | Create and submit articles for review |
| student | View published articles, comment, like |
| public | Subscribe to newsletter |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Article | API only | Placeholder | API only | API only |
| Category | API only | Placeholder | API only | API only |
| Comment | N/A | N/A | N/A | N/A |
| Newsletter | N/A | N/A | N/A | N/A |

## Models

- `Category` (MPTTModel) -- name, slug, parent FK, description
- `Article` -- title, slug, author, categories M2M, tags, content, featured_image, status, is_featured, views_count
- `Comment` -- article FK, user FK, content, parent FK, status (pending/approved/rejected/spam)
- `Like` -- article FK, user FK (unique together)
- `Newsletter` -- email, user FK, is_subscribed, frequency, verification_token
- `NewsletterSent` -- newsletter FK, article FK, sent_at

## Dependencies

- `accounts` (User model for authors)
- `django-mptt`, `django-ckeditor`, `django-taggit`, `django-autoslug`

## URL Namespace

- Frontend: `frontend:articles:<view_name>`
- API: `api:v1:articles:<resource-name>`
