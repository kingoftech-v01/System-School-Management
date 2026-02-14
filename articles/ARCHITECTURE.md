# Articles App - Architecture

## Overview

The articles app provides a content management system for news, blogs, and
announcements within the school platform. It supports hierarchical categories
(MPTT), rich-text articles with tagging, threaded comments with moderation,
like/unlike toggling, newsletter subscriptions with digest scheduling, and
background Celery tasks for email delivery and housekeeping.

---

## Model Relationships

```
+---------------------------+          +---------------------------+
|        Category           |          |       User (accounts)     |
|  (MPTTModel)              |          |                           |
|---------------------------|          |  id, username, role, ...  |
|  id                       |          +---------------------------+
|  name          (unique)   |                |          |       |
|  slug          (auto)     |                |          |       |
|  parent   FK -> self      |<------+       |          |       |
|  description              |       |       |          |       |
|  icon                     |       |       |          |       |
|  is_active                |       |       |          |       |
|  created_at               |       |       |          |       |
|  updated_at               |       |       |          |       |
+---------------------------+       |       |          |       |
        ^                           |       |          |       |
        | M2M (categories)          |       |          |       |
        |                           |       |          |       |
+---------------------------+       |       |          |       |
|        Article            |-------+       |          |       |
|---------------------------|               |          |       |
|  id                       |               |          |       |
|  title                    |  author       |          |       |
|  slug          (auto)     |  FK ----------+          |       |
|  author        FK -> User |                          |       |
|  categories    M2M -> Cat |                          |       |
|  tags          (taggit)   |                          |       |
|  summary                  |                          |       |
|  content       (CKEditor) |                          |       |
|  featured_image           |                          |       |
|  status        (4 states) |                          |       |
|  is_featured              |                          |       |
|  is_pinned                |                          |       |
|  views_count              |                          |       |
|  likes_count              |                          |       |
|  comments_count           |                          |       |
|  published_at             |                          |       |
|  created_at               |                          |       |
|  updated_at               |                          |       |
|  meta_description         |                          |       |
|  meta_keywords            |                          |       |
+---------------------------+                          |       |
        |          |                                   |       |
        |          |                                   |       |
        v          v                                   |       |
+---------------+ +----------------+                   |       |
|   Comment     | |    Like        |                   |       |
|---------------| |----------------|                   |       |
| id            | | id             |                   |       |
| article  FK --| | article  FK ---|---> Article       |       |
| author   FK --|----> User        | user     FK ------|       |
| parent   FK ->self               | created_at        |       |
| content       | | unique_together|                   |       |
| status (4st.) | |  (article,user)|                   |       |
| created_at    | +----------------+                   |       |
| updated_at    |                                      |       |
+---------------+                                      |       |
                                                       |       |
+---------------------------+                          |       |
|      Newsletter           |                          |       |
|---------------------------|                          |       |
|  id                       |                          |       |
|  email         (unique)   |                          |       |
|  user          O2O -> User|  (optional) -------------|       |
|  is_subscribed            |                                  |
|  is_verified              |                                  |
|  verification_token       |                                  |
|  frequency     (3 opts)   |                                  |
|  subscribed_at            |                                  |
|  unsubscribed_at          |                                  |
+---------------------------+                                  |
                                                               |
+---------------------------+                                  |
|    NewsletterSent         |                                  |
|---------------------------|                                  |
|  id                       |                                  |
|  subject                  |                                  |
|  articles      M2M -> Art.|                                  |
|  recipients_count         |                                  |
|  sent_at                  |                                  |
|  sent_by       FK -> User |  --------------------------------+
+---------------------------+
```

### Key Relationship Summary

| Relationship                    | Type           | on_delete   | Related Name             |
|---------------------------------|----------------|-------------|--------------------------|
| Category.parent -> Category     | TreeForeignKey  | CASCADE     | `children`              |
| Article.author -> User          | ForeignKey     | SET_NULL    | `articles`               |
| Article.categories -> Category  | ManyToMany     | --          | `articles`               |
| Comment.article -> Article      | ForeignKey     | CASCADE     | `comments`               |
| Comment.author -> User          | ForeignKey     | CASCADE     | `article_comments`       |
| Comment.parent -> Comment       | ForeignKey     | CASCADE     | `replies`                |
| Like.article -> Article         | ForeignKey     | CASCADE     | `likes`                  |
| Like.user -> User               | ForeignKey     | CASCADE     | `article_likes`          |
| Newsletter.user -> User         | OneToOne       | CASCADE     | `newsletter_subscription`|
| NewsletterSent.articles -> Art. | ManyToMany     | --          | `newsletters`            |
| NewsletterSent.sent_by -> User  | ForeignKey     | SET_NULL    | `sent_newsletters`       |

---

## Article Status State Machine

```
                 author creates
                       |
                       v
                  +---------+     author/admin publishes    +------------+
                  |  DRAFT  | ----------------------------> | PUBLISHED  |
                  +---------+                               +------------+
                       |                                       |      ^
                       | author submits                        |      |
                       v                                       |      |
                  +---------+    admin approves                |      |
                  | PENDING | ---------------------------------+      |
                  +---------+                                         |
                       |                                              |
                       +--- admin rejects ---> back to DRAFT ---------+
                                                                      |
                                               admin archives         |
                                                   |                  |
                                                   v                  |
                                              +----------+            |
                                              | ARCHIVED | ---------->+
                                              +----------+   re-publish
```

Status values defined in `Article.STATUS_CHOICES`:
- `draft` -- Work in progress, visible only to its author
- `pending` -- Submitted for review, awaiting moderation
- `published` -- Live, visible to all authenticated users; `published_at` auto-set on first publish
- `archived` -- Retired from public view

---

## Comment Status State Machine

```
    user submits
         |
         v
    +---------+
    | PENDING | --- auto-moderation task (5+ approved history) ---> APPROVED
    +---------+                                                         |
         |                                                              |
         +--- spam keyword match --------------------------> SPAM       |
         |                                                              |
         +--- admin manual action -----------------------> REJECTED     |
         |                                                              |
         +--- admin manual action -----------------------> APPROVED ----+
```

Status values defined in `Comment.STATUS_CHOICES`:
- `pending` -- Default; awaits moderation
- `approved` -- Visible on the article detail page; increments `article.comments_count`
- `rejected` -- Hidden from public view
- `spam` -- Flagged by auto-moderation or admin

---

## View Access Patterns per Role

### Frontend Views (`views_frontend.py`)

| View                  | URL Pattern                          | Decorator           | Allowed Roles                                                    |
|-----------------------|--------------------------------------|----------------------|------------------------------------------------------------------|
| `article_list`        | `/articles/`                         | `@login_required`    | ALL authenticated (student, professor, direction, parent, admin, prefet, accountant, secretary, librarian, registrar) |
| `article_detail`      | `/articles/<slug>/`                  | `@login_required`    | ALL authenticated                                                |
| `category_articles`   | `/articles/category/<slug>/`         | `@login_required`    | ALL authenticated                                                |
| `article_create`      | `/articles/create/`                  | `@lecturer_required` | **professor** only (maps to `role_required('professor')`)        |
| `article_edit`        | `/articles/<slug>/edit/`             | `@lecturer_required` | **professor** only; further restricted to article's own **author** or **superuser** |
| `comment_submit`      | `/articles/<int:pk>/comment/`        | `@login_required` + `@require_POST` | ALL authenticated          |
| `article_like_toggle` | `/articles/<int:pk>/like/`           | `@login_required` + `@require_POST` | ALL authenticated          |
| `newsletter_subscribe`| `/articles/newsletter/`              | *(none)*             | **Public** -- no authentication required                         |

### API Views (`views_api.py`)

| ViewSet             | URL Pattern (router)        | Permission                       | Operations                        |
|---------------------|-----------------------------|----------------------------------|-----------------------------------|
| `ArticleViewSet`    | `/api/v1/articles/articles/` | `IsAuthenticatedOrReadOnly`     | Full CRUD (list, create, retrieve, update, destroy) |
| `CategoryViewSet`   | `/api/v1/articles/categories/` | `AllowAny`                    | **Read-only** (list, retrieve)    |

### Role-by-Role Access Matrix (Frontend)

| Action               | student | professor | direction | parent | admin | prefet | accountant | secretary | librarian | registrar | anonymous |
|----------------------|---------|-----------|-----------|--------|-------|--------|------------|-----------|-----------|-----------|-----------|
| List articles        | Yes     | Yes       | Yes       | Yes    | Yes   | Yes    | Yes        | Yes       | Yes       | Yes       | No        |
| View article detail  | Yes     | Yes       | Yes       | Yes    | Yes   | Yes    | Yes        | Yes       | Yes       | Yes       | No        |
| Browse by category   | Yes     | Yes       | Yes       | Yes    | Yes   | Yes    | Yes        | Yes       | Yes       | Yes       | No        |
| Create article       | No      | **Yes**   | No*       | No     | No*   | No     | No         | No        | No        | No        | No        |
| Edit own article     | No      | **Yes**   | No*       | No     | No*   | No     | No         | No        | No        | No        | No        |
| Edit any article     | No      | No        | No        | No     | **Yes** (superuser) | No | No  | No        | No        | No        | No        |
| Post comment         | Yes     | Yes       | Yes       | Yes    | Yes   | Yes    | Yes        | Yes       | Yes       | Yes       | No        |
| Like/unlike article  | Yes     | Yes       | Yes       | Yes    | Yes   | Yes    | Yes        | Yes       | Yes       | Yes       | No        |
| Subscribe newsletter | Yes     | Yes       | Yes       | Yes    | Yes   | Yes    | Yes        | Yes       | Yes       | Yes       | **Yes**   |

> *Note: `@lecturer_required` maps to `role_required('professor')`. Users with
> `direction` or `admin` roles cannot create/edit articles through the frontend
> unless they are **superusers** (superusers bypass all role checks in
> `role_required`). The admin panel provides an alternative path for these roles.*

### Admin Panel Access

The Django admin (`admin.py`) registers all six models with full CRUD plus
batch actions. Admin panel access is governed by `is_staff` / `is_superuser`
flags, independent of the `role` field:

| Model            | Batch Actions Available                           |
|------------------|---------------------------------------------------|
| `Category`       | -- (standard CRUD only via MPTTModelAdmin)        |
| `Article`        | publish_articles, feature_articles, archive_articles |
| `Comment`        | approve_comments, reject_comments, mark_as_spam   |
| `Like`           | -- (standard CRUD only)                           |
| `Newsletter`     | verify_subscriptions, unsubscribe_users            |
| `NewsletterSent` | -- (read-only style, filter_horizontal on articles)|

---

## Business Logic Workflows

### 1. Article Publishing Workflow

```
Professor creates article (draft)
         |
         v
+--------------------+
| ArticleForm fields:|    POST /articles/create/
|  title, summary,   |    author = request.user (auto-set)
|  content, cats,    |    save() + save_m2m()
|  tags, image,      |
|  status            |
+--------------------+
         |
         | if status='published' and published_at is None
         v
  Article.save() auto-sets published_at = timezone.now()
         |
         v
  (optional) Celery: send_article_notification(article.id)
         |
         v
  Emails sent to Newsletter subscribers (is_subscribed=True, is_verified=True)
```

### 2. Article Viewing & Counter Increment

```
User visits /articles/<slug>/
         |
         v
  article_detail() view
         |
         +---> article.increment_views()
         |         uses F('views_count') + 1 (atomic DB update)
         |         article.refresh_from_db()
         |
         +---> Fetch approved comments (status='approved')
         |         .select_related('author')
         |
         +---> Check Like.exists(article=article, user=request.user)
         |         -> has_liked boolean for template
         |
         v
  Render article_detail.html with article, comments, comment_form, has_liked
```

### 3. Comment Moderation Workflow

```
User POSTs to /articles/<pk>/comment/
         |
         v
  CommentForm validates 'content' field
         |
         v
  Comment.save(status='pending')    <-- default status
         |
         | (if status='approved' on new save, comments_count increments)
         | (but default is 'pending', so no immediate increment)
         |
         v
  Celery: moderate_pending_comments() (periodic task)
         |
         +---> For each pending comment:
         |       |
         |       +--- author has 5+ approved comments? --> auto-approve
         |       |
         |       +--- content contains spam keywords? ----> mark as spam
         |       |
         |       +--- otherwise: stays pending for manual moderation
         |
         v
  Admin can also manually approve/reject/spam via admin panel batch actions
```

### 4. Like Toggle Workflow

```
User POSTs to /articles/<pk>/like/
         |
         v
  Like.objects.get_or_create(article=article, user=request.user)
         |
         +--> created=True:
         |       Like.save() increments article.likes_count via F() expression
         |       article.refresh_from_db()
         |       Message: "You liked this article."
         |
         +--> created=False (already liked):
                like.delete()
                article.likes_count = Like.objects.filter(article=article).count()
                article.save(update_fields=['likes_count'])
                Message: "You unliked this article."
         |
         v
  Redirect back to article_detail
```

### 5. Newsletter Subscription Workflow

```
Anyone visits /articles/newsletter/ (no login required)
         |
         v
  NewsletterForm: email + frequency (daily/weekly/monthly)
         |
         v
  Newsletter.objects.update_or_create(email=email, defaults={...})
         |
         +---> If user is authenticated: defaults['user'] = request.user
         |
         v
  Message: "You have been subscribed to the newsletter."
  Redirect to same page
```

### 6. Weekly Newsletter Dispatch (Celery)

```
Periodic task: send_weekly_newsletter()
         |
         v
  Query articles published in last 7 days (limit 10, ordered by -published_at)
         |
         v
  Query Newsletter subscribers: is_subscribed=True, is_verified=True, frequency='weekly'
         |
         v
  For each subscriber:
    render articles/email/weekly_newsletter.html
    send EmailMultiAlternatives
         |
         v
  Create NewsletterSent record:
    subject, recipients_count, articles.set(articles)
```

### 7. Draft Cleanup (Celery)

```
Periodic task: cleanup_draft_articles()
         |
         v
  Delete articles where status='draft' AND created_at < 90 days ago
```

### 8. Statistics Reconciliation (Celery)

```
Periodic task: update_article_statistics()
         |
         v
  For each published article:
    likes_count   = Like.objects.filter(article=article).count()
    comments_count = Comment.objects.filter(article=article, status='approved').count()
    save(update_fields=['likes_count', 'comments_count'])
```

---

## Data Flow Diagrams

### Read Path (Article Consumption)

```
Browser                 Django                        Database
  |                       |                              |
  |  GET /articles/       |                              |
  |---------------------->|                              |
  |                       |  Article.objects.published() |
  |                       |  .select_related('author')   |
  |                       |  .prefetch_related('cats')   |
  |                       |----------------------------->|
  |                       |<-----------------------------|
  |                       |  Paginator(articles, 10)     |
  |  article_list.html    |                              |
  |<----------------------|                              |
  |                       |                              |
  |  GET /articles/<slug>/|                              |
  |---------------------->|                              |
  |                       |  get_object_or_404(slug,     |
  |                       |    status='published')       |
  |                       |----------------------------->|
  |                       |  increment_views() F()+1     |
  |                       |----------------------------->|
  |                       |  refresh_from_db()           |
  |                       |----------------------------->|
  |                       |  comments.filter(approved)   |
  |                       |----------------------------->|
  |                       |  Like.exists(article, user)  |
  |                       |----------------------------->|
  |  article_detail.html  |                              |
  |<----------------------|                              |
```

### Write Path (Article Creation)

```
Professor               Django                        Database         Celery
  |                       |                              |                |
  |  GET /articles/create/|                              |                |
  |---------------------->|                              |                |
  |  article_form.html    |                              |                |
  |<----------------------|                              |                |
  |                       |                              |                |
  |  POST /articles/create/ (title, summary, content,   |                |
  |       categories, tags, featured_image, status)      |                |
  |---------------------->|                              |                |
  |                       |  ArticleForm.is_valid()      |                |
  |                       |  article.author = user       |                |
  |                       |  article.save()              |                |
  |                       |  (auto-sets published_at     |                |
  |                       |   if status='published')     |                |
  |                       |----------------------------->|                |
  |                       |  form.save_m2m()             |                |
  |                       |----------------------------->|                |
  |                       |                              |                |
  |                       |  send_article_notification   |                |
  |                       |  .delay(article.id)          |                |
  |                       |--------------------------------------------->|
  |                       |                              |                |
  |  302 -> article_detail|                              |   Newsletter   |
  |<----------------------|                              |   subscribers  |
  |                       |                              |<---------------|
```

### Interaction Path (Comments + Likes)

```
User                    Django                        Database
  |                       |                              |
  |  POST /<pk>/comment/  |                              |
  |  {content: "..."}     |                              |
  |---------------------->|                              |
  |                       |  CommentForm.is_valid()      |
  |                       |  comment.article = article   |
  |                       |  comment.author  = user      |
  |                       |  comment.save(status=pending)|
  |                       |----------------------------->|
  |  302 -> article_detail|                              |
  |<----------------------|                              |
  |                       |                              |
  |  POST /<pk>/like/     |                              |
  |---------------------->|                              |
  |                       |  Like.get_or_create          |
  |                       |----------------------------->|
  |                       |  (created? increment count)  |
  |                       |  (exists?  delete + recount) |
  |                       |----------------------------->|
  |  302 -> article_detail|                              |
  |<----------------------|                              |
```

### Newsletter Digest Path (Celery Periodic)

```
Celery Beat                 Celery Worker               Database           SMTP
  |                             |                          |                  |
  | schedule:                   |                          |                  |
  | send_weekly_newsletter()    |                          |                  |
  |--------------------------->|                          |                  |
  |                             | Article.objects.filter   |                  |
  |                             |  (published, last 7 days)|                  |
  |                             |------------------------->|                  |
  |                             |<-------------------------|                  |
  |                             | Newsletter.objects.filter|                  |
  |                             |  (subscribed, verified,  |                  |
  |                             |   frequency='weekly')    |                  |
  |                             |------------------------->|                  |
  |                             |<-------------------------|                  |
  |                             |                          |                  |
  |                             | render email templates   |                  |
  |                             | EmailMultiAlternatives   |                  |
  |                             |------------------------------------------>|
  |                             |                          |                  |
  |                             | NewsletterSent.create()  |                  |
  |                             |------------------------->|                  |
  |                             |<-------------------------|                  |
```

---

## Dependencies

### Inbound (who depends on articles)

| Consumer                    | What It Uses                                  | Purpose                                    |
|-----------------------------|-----------------------------------------------|--------------------------------------------|
| `tests/helpers.py`          | `Category`, `Article`                        | Test factory methods                       |
| `tests/test_tasks_deep.py`  | All 5 Celery tasks                           | Task integration tests                     |
| `tests/test_admin_registration.py` | All 6 models                          | Admin site registration tests              |
| `tests/test_views_deep.py`  | `Article`                                    | Frontend view integration tests            |
| `tests/test_forms_tasks_misc_deep.py` | Tasks + `Article`                  | Form and task coverage tests               |
| `School_System/urls.py`     | `articles.urls` (frontend + api_urlpatterns) | URL routing at project level               |

### Outbound (what articles depends on)

| Dependency                        | Import Location           | Purpose                                       |
|-----------------------------------|---------------------------|-----------------------------------------------|
| `django.contrib.auth` (User)     | `models.py`               | `get_user_model()` for FK/O2O relations       |
| `accounts.decorators`            | `views_frontend.py`       | `lecturer_required` for professor-only views  |
| `mptt` (django-mptt)             | `models.py`, `admin.py`   | `MPTTModel`, `TreeForeignKey`, `MPTTModelAdmin` for hierarchical categories |
| `taggit` (django-taggit)         | `models.py`               | `TaggableManager` for article tags            |
| `ckeditor` (django-ckeditor)     | `models.py`               | `RichTextField` for article content           |
| `autoslug` (django-autoslug)     | `models.py`               | `AutoSlugField` for auto-generated URL slugs  |
| `celery`                         | `tasks.py`                | `shared_task` for async email and maintenance |
| `rest_framework`                 | `views_api.py`, `serializers.py` | DRF viewsets, serializers, permissions  |

---

## URL Namespace Structure

```
/                                   (project root)
|
+-- /articles/                      namespace: "frontend:articles"
|   +-- /                           article_list
|   +-- /create/                    article_create
|   +-- /newsletter/                newsletter (subscribe)
|   +-- /category/<slug>/           category_articles
|   +-- /<slug>/                    article_detail
|   +-- /<slug>/edit/               article_edit
|   +-- /<pk>/comment/              comment_submit
|   +-- /<pk>/like/                 article_like
|
+-- /api/v1/articles/               namespace: "api-v1:articles"
    +-- /articles/                  ArticleViewSet  (list, create, retrieve, update, destroy)
    +-- /articles/<pk>/             ArticleViewSet  (detail)
    +-- /categories/                CategoryViewSet (list, retrieve)
    +-- /categories/<pk>/           CategoryViewSet (detail)
```

---

## Custom Managers and QuerySets

`ArticleQuerySet` provides chainable filters used throughout the codebase:

| Method         | Filter Logic                                                   |
|----------------|----------------------------------------------------------------|
| `.published()` | `status='published'` AND `published_at <= now()`              |
| `.draft()`     | `status='draft'`                                               |
| `.pending()`   | `status='pending'`                                             |
| `.featured()`  | `.published()` + `is_featured=True`                            |
| `.by_author()` | `author=<user>`                                                |
| `.by_category()` | `categories=<category>`                                      |

`ArticleManager` exposes `.published()` and `.featured()` as top-level manager
methods. Both `Article.objects` and `Article.published` use `ArticleManager`.

---

## Database Indexes

| Model      | Indexed Fields                                        |
|------------|-------------------------------------------------------|
| Category   | `slug`, `is_active`                                   |
| Article    | `(status, -published_at)`, `(author, status)`, `slug`, `(-is_featured, -published_at)` |
| Comment    | `(article, status, -created_at)`, `(author, -created_at)` |
| Like       | `(article, user)` + unique_together                   |
| Newsletter | `email`, `(is_subscribed, is_verified)`               |

---

## Custom Permissions

Defined in `Article.Meta.permissions`:

| Codename                | Description              |
|-------------------------|--------------------------|
| `can_publish_article`   | Can publish articles     |
| `can_feature_article`   | Can feature articles     |
| `can_moderate_comments` | Can moderate comments    |

These permissions are available for assignment via Django's auth system but are
**not currently enforced** in the view layer. They exist for future use with
Django's `permission_required` decorator or DRF permission classes.

---

## Celery Tasks Summary

| Task                          | Trigger     | Retry | Description                                      |
|-------------------------------|-------------|-------|--------------------------------------------------|
| `send_article_notification`   | On-demand   | 3x, 5min backoff | Email all verified subscribers about a new article |
| `send_weekly_newsletter`      | Periodic    | No    | Digest of articles from last 7 days to weekly subscribers |
| `cleanup_draft_articles`      | Periodic    | No    | Delete drafts older than 90 days                 |
| `moderate_pending_comments`   | Periodic    | No    | Auto-approve (5+ history) or flag spam keywords  |
| `update_article_statistics`   | Periodic    | No    | Recount likes_count and comments_count from DB   |

---

## File Inventory

```
articles/
  __init__.py             Empty init
  apps.py                 ArticlesConfig (default_auto_field = BigAutoField)
  models.py               Category, Article, Comment, Like, Newsletter, NewsletterSent
  forms.py                ArticleForm, CommentForm, NewsletterForm
  serializers.py          ArticleSerializer, CategorySerializer (ModelSerializer, fields='__all__')
  views_frontend.py       8 function-based views (list, detail, category, create, edit, comment, like, newsletter)
  views_api.py            ArticleViewSet (ModelViewSet), CategoryViewSet (ReadOnlyModelViewSet)
  urls.py                 api_router + api_urlpatterns + frontend_urlpatterns
  tasks.py                5 Celery shared_tasks
  admin.py                6 ModelAdmin registrations with batch actions
  migrations/
    0001_initial.py       Initial schema migration
  tests/
    test_models.py        Model unit tests
    test_forms.py         Form validation tests
    test_admin.py         Admin registration and action tests
    test_views_api.py     API endpoint tests
    test_views_frontend.py Frontend view tests
```
