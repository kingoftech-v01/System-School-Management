# Forums App Architecture

## Overview

The forums app provides a thread-based discussion platform with moderation, voting,
tagging, subscriptions, and content reporting. It exposes both HTML frontend views
(template-rendered) and a REST API (DRF ViewSets). All forum content is scoped
per-tenant via the `@tenant_required` decorator on frontend views and
`CanAccessCategory` permission on the API.

---

## Model Relationships

```
+------------------+        +---------------------+
|  ForumCategory   |        |    auth.Group       |
|------------------|        +---------------------+
| name             |               ^
| slug             |               | M2M
| description      |               | allowed_groups
| icon             |        +------+-------------+
| order            |<-------| ForumCategory      |
| is_active        |  1   * | (self)             |
| requires_approval|        +--------------------+
| created_at       |
| updated_at       |
+--------+---------+
         |
         | FK (category)
         | 1:N
         v
+------------------+        +------------------+
|     Thread       |------->|      User        |
|------------------|  FK    |  (author)        |
| category    (FK) |  author+------------------+
| title            |
| slug             |  FK moderated_by
| author      (FK) |------->User (nullable)
| content (Rich)   |
| status           |        +------------------+
| is_published     |        |       Tag        |
| is_pinned        |        |------------------|
| is_locked        |<------>| name             |
| is_featured      |  M2M   | slug             |
| moderated_by(FK) |  tags   | description      |
| moderated_at     |        | color            |
| moderation_notes |        | use_count        |
| view_count       |        | created_at       |
| reply_count      |        +------------------+
| tags        (M2M)|
| created_at       |
| updated_at       |
| last_activity_at |
+--------+---------+
         |
         | FK (thread) 1:N
         v
+------------------+             +-------------------+
|      Post        |             | ThreadSubscription|
|------------------|             |-------------------|
| thread      (FK) |             | thread   (FK)     |
| author      (FK) |----> User  | user     (FK)     |
| parent      (FK) |  (self)    | email_on_reply    |
| content (Rich)   |  nullable  | last_read_at      |
| is_deleted       |            | subscribed_at     |
| is_edited        |            +-------------------+
| edited_at        |                 ^
| moderated_by(FK) |----> User      | FK thread
| moderation_reason|                | FK user
| upvotes          |            Thread ---+--- User
| downvotes        |
| created_at       |
| updated_at       |
+--------+---------+
         |
         | FK (post) 1:N
         v
+------------------+
|      Vote        |
|------------------|
| post        (FK) |
| user        (FK) |----> User
| vote_type        |  (+1 upvote / -1 downvote)
| created_at       |
+------------------+
  unique_together: [post, user]


+------------------+
|     Report       |  (GenericForeignKey - can reference Thread or Post)
|------------------|
| content_type(FK) |----> ContentType
| object_id        |
| content_object   |  (GFK)
| reported_by (FK) |----> User
| report_type      |  (spam|offensive|harassment|misinformation|other)
| description      |
| status           |  (pending|reviewing|resolved|dismissed)
| reviewed_by (FK) |----> User (nullable)
| reviewed_at      |
| resolution_notes |
| created_at       |
+------------------+
```

### Entity-Relationship Summary

```
ForumCategory  1 ---< *  Thread           (category FK, CASCADE)
Thread         1 ---< *  Post             (thread FK, CASCADE)
Post           1 ---< *  Post             (parent FK, self-ref, SET_NULL)
Post           1 ---< *  Vote             (post FK, CASCADE)
Thread         * >--< *  Tag              (M2M through thread.tags)
Thread         1 ---< *  ThreadSubscription (thread FK, CASCADE)
User           1 ---< *  ThreadSubscription (user FK, CASCADE)
User           1 ---< *  Thread           (author FK, SET_NULL)
User           1 ---< *  Post             (author FK, SET_NULL)
User           1 ---< *  Vote             (user FK, CASCADE)
User           1 ---< *  Report           (reported_by FK, CASCADE)
User           1 ---< *  Report           (reviewed_by FK, SET_NULL)
ForumCategory  * >--< *  auth.Group       (M2M allowed_groups)
ContentType    1 ---< *  Report           (GFK)
```

---

## Thread Status State Machine

```
              +-------+
              | draft |  (default on creation)
              +---+---+
                  |
       requires_approval?
          /           \
        yes            no
         |              |
         v              v
    +---------+    +-----------+
    | pending |    | published |<---------+
    +----+----+    +-----+-----+          |
         |              |                 |
    moderator           |            unlock action
    approves            |                 |
         |         +----+---+        +----+----+
         +-------->| active |------->| locked  |
                   +----+---+  lock  +---------+
                        |
                   archive (365d idle)
                        |
                        v
                  +-----------+
                  | archived  |
                  +-----------+
```

Status field values: `draft`, `pending`, `published`, `archived`, `locked`.

The `is_published` boolean is auto-computed from `status == 'published'` inside
`Thread.save()`. The `is_pinned`, `is_locked`, and `is_featured` booleans are
independent flags managed by moderators.

---

## View Access Patterns per Role

### Roles Reference (from `accounts.models.ROLE_CHOICES`)

| Role Key     | Display Name       |
|--------------|--------------------|
| `student`    | Student            |
| `professor`  | Professor          |
| `direction`  | Direction          |
| `parent`     | Parent             |
| `admin`      | Administrator      |
| `prefet`     | Discipline Officer |
| `accountant` | Accountant         |
| `secretary`  | Secretary          |
| `librarian`  | Librarian          |
| `registrar`  | Registrar          |

### Frontend Views Access Matrix

All frontend views require `@login_required` + `@tenant_required`. Superusers
bypass all role checks.

| View                  | URL Pattern                                      | student | professor | direction | parent | admin | prefet | accountant | secretary | librarian | registrar | Gate                        |
|-----------------------|--------------------------------------------------|---------|-----------|-----------|--------|-------|--------|------------|-----------|-----------|-----------|-----------------------------|
| `forum_home`          | `/`                                              | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `category_list`       | `/categories/`                                   | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `category_detail`     | `/categories/<slug>/`                            | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `category_create`     | `/categories/create/`                            | --      | --        | Y         | --     | Y     | --     | --         | Y         | --        | --        | `@direction_only`           |
| `category_edit`       | `/categories/<pk>/edit/`                         | --      | --        | Y         | --     | Y     | --     | --         | Y         | --        | --        | `@direction_only`           |
| `category_delete`     | `/categories/<pk>/delete/`                       | --      | --        | Y         | --     | Y     | --     | --         | Y         | --        | --        | `@direction_only`           |
| `thread_list`         | `/threads/`                                      | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `thread_detail`       | `/threads/<slug>/`                               | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `thread_create`       | `/threads/create/`                               | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `thread_update`       | `/threads/<slug>/edit/`                          | own     | own       | own+mod   | own    | mod   | own    | own        | own       | own       | own       | author OR `can_moderate`    |
| `thread_delete`       | `/threads/<slug>/delete/`                        | own     | own       | own+mod   | own    | mod   | own    | own        | own       | own       | own       | author OR `can_moderate`    |
| `post_create`         | `/threads/<slug>/reply/`                         | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required` + !locked  |
| `post_update`         | `/posts/<pk>/edit/`                              | own     | own       | own       | own    | own   | own    | own        | own       | own       | own       | author only                 |
| `post_delete`         | `/posts/<pk>/delete/`                            | own     | own       | own+mod   | own    | mod   | own    | own        | own       | own       | own       | author OR `can_moderate`    |
| `post_vote`           | `/posts/<pk>/vote/`                              | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required` (POST)     |
| `thread_subscribe`    | `/threads/<slug>/subscribe/`                     | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required` (POST)     |
| `thread_unsubscribe`  | `/threads/<slug>/unsubscribe/`                   | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required` (POST)     |
| `my_subscriptions`    | `/my-subscriptions/`                             | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `my_threads`          | `/my-threads/`                                   | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `my_posts`            | `/my-posts/`                                     | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `report_content`      | `/report/<ct_id>/<obj_id>/`                      | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `moderation_queue`    | `/moderation/`                                   | --      | --        | Y         | --     | Y     | --     | --         | Y         | --        | --        | `@direction_only`           |
| `search`              | `/search/`                                       | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `tag_list`            | `/tags/`                                         | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |
| `tag_threads`         | `/tags/<slug>/`                                  | Y       | Y         | Y         | Y      | Y     | Y      | Y          | Y         | Y         | Y         | `login_required`            |

Legend: `Y` = full access, `own` = own content only, `mod` = via `can_moderate_threads` perm,
`own+mod` = own content plus moderation perm, `--` = no access.

**Note on `@direction_only`**: Defined in `accounts/decorators.py` as
`role_required('secretary', 'direction', 'admin')`. This means **secretary**,
**direction**, and **admin** roles can access category management and the
moderation queue. All other roles are denied.

### API Endpoints Access Matrix

API ViewSets use DRF permissions. `IsAuthenticatedOrReadOnly` allows
unauthenticated GET but requires login for mutations. Custom permissions
layer on top.

| ViewSet                     | Base Permission                                         | Create/Update/Delete Gate                            |
|-----------------------------|---------------------------------------------------------|------------------------------------------------------|
| `ForumCategoryViewSet`      | `IsAuthenticatedOrReadOnly`                             | `CanModerateThreads` (requires `can_moderate_threads` perm) |
| `ThreadViewSet`             | `IsAuthenticatedOrReadOnly`, `CanAccessCategory`, `IsAuthorOrModeratorOrReadOnly` | Author or moderator for update/delete                |
| `PostViewSet`               | `IsAuthenticatedOrReadOnly`, `IsNotLocked`, `IsAuthorOrModeratorOrReadOnly` | Author or moderator; thread must not be locked       |
| `TagViewSet`                | ReadOnly (no mutations)                                 | N/A                                                  |
| `ThreadSubscriptionViewSet` | `IsAuthenticated`                                       | Scoped to `request.user` only                        |
| `ReportViewSet`             | `IsAuthenticated`                                       | Moderators see all; users see own reports; resolve/dismiss requires `CanModerateThreads` |

### API Custom Actions

| ViewSet   | Action       | Method | Permission Required          |
|-----------|--------------|--------|------------------------------|
| Thread    | `subscribe`  | POST   | `IsAuthenticated`            |
| Thread    | `unsubscribe`| POST   | `IsAuthenticated`            |
| Thread    | `pin`        | POST   | `CanPinThreads`              |
| Thread    | `unpin`      | POST   | `CanPinThreads`              |
| Thread    | `lock`       | POST   | `CanLockThreads`             |
| Thread    | `unlock`     | POST   | `CanLockThreads`             |
| Thread    | `feature`    | POST   | `CanModerateThreads`         |
| Thread    | `unfeature`  | POST   | `CanModerateThreads`         |
| Thread    | `posts`      | GET    | Default (read)               |
| Post      | `vote`       | POST   | `IsAuthenticated`            |
| Post      | `remove_vote`| POST   | `IsAuthenticated`            |
| Post      | `replies`    | GET    | Default (read)               |
| Subscription | `mark_read` | POST | `IsAuthenticated`           |
| Report    | `resolve`    | POST   | `CanModerateThreads`         |
| Report    | `dismiss`    | POST   | `CanModerateThreads`         |
| Category  | `threads`    | GET    | Default (read)               |
| Tag       | `threads`    | GET    | Default (read)               |

### Django Model-Level Permissions (Thread Meta)

```python
permissions = [
    ('can_moderate_threads', 'Can moderate threads'),
    ('can_pin_threads', 'Can pin threads'),
    ('can_lock_threads', 'Can lock threads'),
]
```

These are assigned to users/groups through Django's permission system. They are
**not** tied to any specific role by default -- an admin must assign them to
the appropriate groups or users via the Django admin.

---

## Business Logic Workflows

### 1. Thread Creation

```
User submits ThreadForm (category, title, content, tags)
         |
         v
   Is category.requires_approval == True?
        /                  \
      yes                   no
       |                     |
       v                     v
  status = 'pending'    status = 'published'
  is_published = False   is_published = True
       |                     |
       +----------+----------+
                  |
                  v
         thread.save()
         form.save_m2m()  (tags)
                  |
                  v
   ThreadSubscription.create(
     thread=thread, user=author,
     email_on_reply=True
   )
                  |
                  v
   Redirect to thread_detail
```

### 2. Post Creation (Reply)

```
User submits PostForm (content) on thread_slug
         |
         v
   Is thread.is_locked?
       /          \
     yes           no
      |             |
      v             v
  Error msg    post = form.save(commit=False)
  Redirect     post.thread = thread
               post.author = request.user
               post.parent = parent (if nested reply)
               post.save()
                    |
                    v
              Post.save() triggers:
                - thread.update_activity()
                  (sets last_activity_at = now)
                - Thread reply_count += 1
                  (atomic F() update)
                    |
                    v
              thread.update_activity()
              (called again from view -- double call)
                    |
                    v
              Redirect to thread_detail
```

### 3. Voting

```
User POSTs vote_type (+1 or -1) on post pk
         |
         v
   Vote.objects.get_or_create(post, user)
         |
    created?
    /       \
  yes        no
   |          |
   v          |
  Done   same vote_type?
          /         \
        yes          no
         |            |
         v            v
    vote.delete()   vote.vote_type = new
    "Vote removed"  vote.save()
                    "Vote updated"
         |
         v
   Vote.save() triggers atomic update on Post:
     - upvotes / downvotes adjusted via F() expressions
```

### 4. Content Reporting

```
User submits ReportForm (report_type, description)
  with content_type_id and object_id from URL
         |
         v
   Report.create(
     reported_by = user,
     content_type = ContentType(pk=content_type_id),
     object_id = object_id,
     status = 'pending'       (default)
   )
         |
         v
   Flash "Content reported. Moderators will review it."
         |
         v
   [Async] process_flagged_content task
   emails moderators a summary of pending reports
```

### 5. Moderation Queue (Direction/Admin/Secretary only)

```
Moderator visits /moderation/
         |
         v
   Loads three datasets:
     1. pending_threads  (status='pending')
     2. pending_reports  (status in ['pending', 'reviewing'])
     3. flagged_posts    (is_deleted=True, last 50)
         |
         v
   Moderator actions (via API):
     - Approve thread   -> status='published', is_published=True
     - Pin/Unpin        -> is_pinned toggle  (CanPinThreads)
     - Lock/Unlock      -> is_locked toggle  (CanLockThreads)
     - Feature/Unfeature-> is_featured toggle (CanModerateThreads)
     - Resolve report   -> status='resolved', reviewed_by=user
     - Dismiss report   -> status='dismissed', reviewed_by=user
```

### 6. Subscription and Notification

```
User subscribes to thread (POST)
         |
         v
   ThreadSubscription.get_or_create(
     thread, user, email_on_reply=True
   )
         |
         v
   [On new post] Celery task: send_new_post_notifications
     - Queries subscriptions where email_on_reply=True
     - Excludes the post author
     - Sends email to each subscriber
         |
         v
   User can mark_read (API action):
     subscription.last_read_at = now
   User can check has_unread_posts():
     thread.posts.filter(created_at > last_read_at).exists()
```

### 7. Category Group Restrictions

```
User accesses thread in a category
         |
         v
   category.allowed_groups.exists()?
      /            \
    no              yes
     |               |
     v               v
  Access OK     user.groups intersects allowed_groups?
                   /            \
                 yes             no
                  |               |
                  v               v
              Access OK      Access Denied
```

This logic lives in `CanAccessCategory` (API) and `ForumCategory.allowed_groups`
(M2M to `auth.Group`). The frontend views do **not** enforce group-level
restrictions -- only the API does via `CanAccessCategory`.

---

## Data Flow Diagrams

### Frontend Request Flow

```
Browser
  |
  v
Django URL Router
  |
  +--> /forums/           --> frontend_urlpatterns (namespace: frontend:forums)
  |      |
  |      +--> @login_required
  |      +--> @tenant_required  (or @direction_only for admin views)
  |      +--> @ratelimit(key='user', rate='50-200/h')
  |      |
  |      +--> views_frontend.py function
  |             |
  |             +--> Query models (ForumCategory, Thread, Post, etc.)
  |             +--> Paginate results (Paginator, 20-30 per page)
  |             +--> render() -> templates/forums/*.html
  |
  +--> /forums/api/       --> api_urlpatterns (DRF router)
         |
         +--> DRF ViewSet (permission_classes checked)
         +--> Serializer validates / transforms data
         +--> Response (JSON)
```

### Write Operation Flow (Thread Create Example)

```
POST /forums/threads/create/
  |
  v
@login_required --> @tenant_required --> @ratelimit(50/h)
  |
  v
thread_create(request)
  |
  v
ThreadForm(request.POST)  -->  validates title (>=5 chars)
  |                             validates content (>=10 chars)
  |                             filters active categories
  v
form.save(commit=False)
  |
  v
thread.author = request.user
  |
  v
category.requires_approval?
  |     |
  yes   no --> status='published', is_published=True
  |
  v
status='pending', is_published=False
  |
  v
thread.save()  -->  Thread.save() auto-generates slug
  |                  Thread.save() sets is_published from status
  v
form.save_m2m()  -->  saves Tag M2M
  |
  v
ThreadSubscription.objects.create(thread, user, email_on_reply=True)
  |
  v
messages.success("Thread created successfully.")
  |
  v
redirect('frontend:forums:thread_detail', slug=thread.slug)
```

### API Vote Flow

```
POST /forums/api/posts/{pk}/vote/
  |
  v
PostViewSet.vote(request, pk)
  |
  v
Permission check: IsAuthenticated
  |
  v
post = self.get_object()
  |
  v
vote_type in [1, -1]?  --> no: 400 Bad Request
  |
  yes
  v
Vote.objects.get_or_create(post=post, user=request.user)
  |
  v
created?
  |      |
  yes    no --> vote_type changed? --> vote.save()
  |                                     |
  v                                     v
Vote.save() triggers:           Vote.save() triggers:
  Post.upvotes += 1               old upvotes -= 1
  (atomic F() update)             new downvotes += 1
  |                               (atomic F() update)
  v
Response(VoteSerializer(vote).data)
```

---

## Dependencies

### Inbound Dependencies (other apps importing from forums)

The forums app is largely self-contained. No other app in the codebase imports
from `forums.models`, `forums.views_*`, or `forums.serializers`. The app is a
leaf node in the dependency graph.

### Outbound Dependencies (forums importing from other apps/packages)

| Dependency                          | Import Location                    | What Is Used                                              |
|-------------------------------------|------------------------------------|-----------------------------------------------------------|
| `accounts.decorators`               | `views_frontend.py`                | `tenant_required`, `direction_only`                       |
| `accounts.models.User`              | `models.py`, `serializers.py`, `tasks.py` | `get_user_model()`, FK author/user references             |
| `django.contrib.auth.models.Group`  | `models.py`                        | M2M `ForumCategory.allowed_groups`                        |
| `django.contrib.contenttypes`       | `models.py`, `views_frontend.py`   | `ContentType`, `GenericForeignKey` (for Report)           |
| `ckeditor`                          | `models.py`, `forms.py`            | `RichTextField`, `CKEditorWidget`                         |
| `rest_framework`                    | `views_api.py`, `serializers.py`, `permissions.py` | ViewSets, serializers, permissions, filters               |
| `django_filters`                    | `views_api.py`                     | `DjangoFilterBackend`                                     |
| `django_ratelimit`                  | `views_frontend.py`                | `@ratelimit` decorator                                    |
| `celery`                            | `tasks.py`                         | `@shared_task`                                            |
| `django.core.mail`                  | `tasks.py`                         | `send_mail` for notifications                             |
| `django.core.cache`                 | `tasks.py`                         | Cache-based view count batch updates                      |

### Dependency Diagram

```
                  +----------------+
                  | django.contrib |
                  |   .auth        |
                  |   .contenttypes|
                  +-------+--------+
                          |
                          v
+-------------+    +-------------+    +------------------+
|  accounts   |--->|   forums    |<---|  rest_framework  |
| (decorators,|    |             |    |  django_filters  |
|  User model)|    +------+------+    +------------------+
+-------------+           |
                          |
              +-----------+-----------+
              |           |           |
              v           v           v
         +--------+  +--------+  +--------+
         |ckeditor|  | celery |  |ratelimit|
         +--------+  +--------+  +--------+
```

---

## Celery Tasks

| Task Name                              | Trigger / Schedule     | Description                                              |
|----------------------------------------|------------------------|----------------------------------------------------------|
| `forums.send_new_thread_notifications` | Called manually        | Emails category subscribers about a new thread           |
| `forums.send_new_post_notifications`   | Called manually        | Emails thread subscribers (email_on_reply=True) about new posts, excluding the post author |
| `forums.process_flagged_content`       | Periodic / manual      | Queries pending reports, emails a summary to moderators (staff or users with `can_moderate_threads`) |
| `forums.cleanup_old_threads`           | Periodic / manual      | Identifies threads inactive >365 days (not pinned/locked) for archival |
| `forums.update_thread_view_counts`     | Periodic / manual      | Syncs cached view counts back to the database            |

**Note**: The tasks reference `thread.body` and `post.body` in email messages,
but the actual model field is `content`. These tasks also call
`author.get_full_name()` with parentheses, but `get_full_name` is a `@property`
on the User model. Both are latent bugs in `tasks.py`.

---

## Rate Limiting

All frontend views are rate-limited via `@ratelimit(key='user', rate='N/h')`:

| View Group                    | Rate Limit  |
|-------------------------------|-------------|
| Browse (home, list, detail)   | 100/h       |
| Create/Update/Delete thread   | 50/h        |
| Post create/update/delete     | 100/h       |
| Voting                        | 200/h       |
| Subscribe/Unsubscribe         | 100/h       |
| Search                        | 100/h       |
| Category management (POST)    | 50/h POST   |
| Moderation queue              | 100/h       |

---

## URL Namespace Structure

```
forums/
  +-- api/                          (namespace: api)
  |     +-- categories/             (DRF router: category-list, category-detail, category-threads)
  |     +-- threads/                (DRF router: thread-list, thread-detail, thread-subscribe, ...)
  |     +-- posts/                  (DRF router: post-list, post-detail, post-vote, ...)
  |     +-- tags/                   (DRF router: tag-list, tag-detail, tag-threads)
  |     +-- subscriptions/          (DRF router: subscription-list, subscription-detail, subscription-mark_read)
  |     +-- reports/                (DRF router: report-list, report-detail, report-resolve, report-dismiss)
  |
  +-- (frontend)                    (namespace: frontend)
        +-- /                       forum_home
        +-- categories/             category_list, category_create, category_edit, category_delete, category_detail
        +-- threads/                thread_list, thread_create, thread_detail, thread_update, thread_delete
        +-- threads/<slug>/subscribe|unsubscribe
        +-- threads/<slug>/reply/   post_create, post_reply
        +-- posts/<pk>/             post_update, post_delete, post_vote
        +-- tags/                   tag_list, tag_threads
        +-- my-threads/             my_threads
        +-- my-posts/               my_posts
        +-- my-subscriptions/       my_subscriptions
        +-- moderation/             moderation_queue
        +-- report/<ct>/<id>/       report_content
        +-- search/                 search
```

---

## Forms

| Form           | Model          | Fields                                              | Validation Rules                         |
|----------------|----------------|------------------------------------------------------|------------------------------------------|
| `ThreadForm`   | `Thread`       | `category`, `title`, `content`, `tags`               | title >= 5 chars, content >= 10 chars    |
| `PostForm`     | `Post`         | `content`                                            | content >= 10 chars                      |
| `ReportForm`   | `Report`       | `report_type`, `description`                         | description >= 10 chars                  |
| `CategoryForm` | `ForumCategory`| `name`, `description`, `icon`, `order`, `is_active`, `requires_approval` | name >= 2 chars                          |
| `SearchForm`   | (plain Form)   | `query`                                              | query >= 3 chars                         |

---

## Admin Configuration

All seven models are registered with customized `ModelAdmin` classes:

| Model               | Key Admin Features                                                                  |
|----------------------|-------------------------------------------------------------------------------------|
| `ForumCategory`      | Activate/deactivate bulk actions, thread/post count display, slug prepopulated      |
| `Thread`             | Publish/pin/lock/feature/archive bulk actions, date hierarchy, search by author     |
| `Post`               | Soft-delete/restore bulk actions, score display with color coding                   |
| `Vote`               | Color-coded vote type display, date hierarchy                                       |
| `Tag`                | Color badge preview, slug prepopulated, use_count readonly                          |
| `ThreadSubscription` | Unread indicator (boolean), date hierarchy on subscribed_at                         |
| `Report`             | Mark reviewing/resolved/dismissed bulk actions, content type display                |

---

## Key Design Decisions

1. **Soft delete for posts**: Posts use `is_deleted` flag rather than hard delete.
   The `PostViewSet.destroy()` method and `post_delete` frontend view both set
   `is_deleted=True` instead of calling `.delete()`. Threads are hard-deleted.

2. **GenericForeignKey for reports**: Reports can target any content type (Thread
   or Post) via Django's contenttypes framework, making the reporting system
   extensible to other models.

3. **Atomic vote counting**: Vote counts (`upvotes`, `downvotes`) are maintained
   denormalized on `Post` and updated atomically using `F()` expressions inside
   `Vote.save()`. This avoids race conditions.

4. **Atomic reply counting**: `Thread.reply_count` is incremented via `F()`
   expression in `Post.save()` when a new non-deleted post is created.

5. **Dual interface**: Every resource is available through both HTML templates
   (frontend) and JSON API (DRF). The frontend uses Django forms; the API uses
   DRF serializers. Authorization logic is implemented separately in each layer.

6. **Category-level group restrictions**: Categories can restrict posting to
   specific Django auth groups via the `allowed_groups` M2M field. An empty
   set means all authenticated users can participate.

7. **Auto-subscription**: Thread authors are automatically subscribed to their
   own thread upon creation, with `email_on_reply=True`.

8. **Slug-based URLs**: Threads and categories use slug fields for
   human-readable URLs. Slugs are auto-generated from `title`/`name` on first
   save.
