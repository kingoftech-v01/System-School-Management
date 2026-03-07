# Library App Architecture

## Overview

The `library` app manages the school's book inventory, borrowing lifecycle, and overdue
tracking. It is tenant-scoped (every `Book` and `BorrowRecord` belongs to a `core.School`),
uses hierarchical categories via `django-mptt`, and integrates with Celery for automated
overdue email reminders.

The app exposes two interfaces: a set of template-based frontend views (9 views in
`views_frontend.py`) and a REST API via Django REST Framework (2 ViewSets in `views_api.py`).
Both share the same models and database tables but have different permission models --
notably, the API lacks tenant scoping and role restrictions.

---

## Directory Structure

```text
library/
    __init__.py
    admin.py                 # Admin registration for Book and BorrowRecord with tenant-scoped querysets
    apps.py                  # LibraryConfig (verbose_name='Library Management')
    forms.py                 # 2 ModelForms: BookForm (7 fields), BorrowForm (3 fields)
    models.py                # 4 models + 1 validator function (validate_isbn)
    serializers.py           # 2 DRF serializers using fields='__all__'
    tasks.py                 # 1 Celery task: send_overdue_reminders
    urls.py                  # Frontend (9 routes) + API (2 ViewSets via DefaultRouter)
    views_api.py             # 2 DRF ModelViewSets (BookViewSet, BorrowRecordViewSet)
    views_frontend.py        # 9 template-based views (list, detail, CRUD, borrow/return, overdue)
    migrations/
        __init__.py
        0001_initial.py
    tests/
        __init__.py
        test_admin.py        # Admin registration and configuration tests
        test_forms.py        # BookForm and BorrowForm validation tests
        test_models.py       # Model creation, methods, and ISBN validation tests
        test_serializers.py  # Serializer output tests
        test_tasks.py        # Celery task tests (with bug workarounds)
        test_views_api.py    # API ViewSet tests
        test_views_frontend.py  # Frontend view tests (role access, CRUD, borrow/return)
```

---

## Data Model

### Entity Relationship Diagram

```text
                          core.School (tenant)
                                |
               +----------------+----------------+
               |  FK (tenant)                    |  FK (tenant)
               v                                 v
           +--------+                     +--------------+
           |  Book  |--FK (book,CASCADE)->| BorrowRecord |
           +--------+                     +--------------+
           | tenant |                     | tenant       |
           | title  |                     | book --------+
           | author |                     | student -----+--> accounts.User
           | isbn   |                     | borrowed_at  |     (AUTH_USER_MODEL)
           | filiere+--FK (SET_NULL)----->| due_date     |
           | category                     | returned_at  |
           | publisher                    | status       |
           | publication_year             | fine_amount  |
           | edition |                    | notes        |
           | language|                    +--------------+
           | pages   |
           | barcode |
           | quantity|               filieres.Filiere (external)
           | available                     ^
           | shelf_location                |
           | cover_image           FK (filiere, SET_NULL)
           | description                   |
           | tags    |              -------+
           +----+----+
                |
    +-----------+-----------+
    |                       |
    | TreeFK                | FK
    | (SET_NULL)            | (SET_NULL)
    v                       v
+--------------+      +-----------+
| BookCategory |      | Publisher  |
| (MPTTModel)  |      +-----------+
+--------------+      | name      |
| name         |      | country   |
| parent (self)|      | website   |
| description  |      | email     |
| is_active    |      | phone     |
+--------------+      | created_at|
      |               +-----------+
      | TreeForeignKey
      | (self-referential,
      |  related_name='subcategories')
      +---> (parent categories)
```

### Detailed Relationships

```text
BookCategory (MPTTModel)
    |
    | self-referential TreeForeignKey (parent -> self, CASCADE)
    | related_name='subcategories'
    |
    +---> Book.category (TreeForeignKey, SET_NULL, related_name='books')

Publisher
    |
    +---> Book.publisher (FK, SET_NULL, related_name='books')

core.School
    |
    +---> Book.tenant (FK, CASCADE)
    +---> BorrowRecord.tenant (FK, CASCADE)

filieres.Filiere
    |
    +---> Book.filiere (FK, SET_NULL)

accounts.User (AUTH_USER_MODEL)
    |
    +---> BorrowRecord.student (FK, CASCADE)

Book
    |
    +---> BorrowRecord.book (FK, CASCADE)
```

### Model Details

#### BookCategory (MPTTModel)

Hierarchical categorization using django-mptt. Self-referential `parent` TreeForeignKey enables unlimited nesting depth. Not tenant-scoped. Categories are shared across all tenants.

| Field         | Type             | Constraints              |
|---------------|------------------|--------------------------|
| `name`        | CharField(100)   | unique=True              |
| `parent`      | TreeForeignKey   | self, CASCADE, null/blank|
| `description` | TextField        | blank=True               |
| `is_active`   | BooleanField     | default=True             |

- MPTT ordering: `order_insertion_by = ['name']`.
- Key method: `get_book_count()` -- recursively counts books in this category and all subcategories.

#### Publisher

Simple publisher directory. Not tenant-scoped (shared across all tenants). Ordered by `name`.

| Field        | Type            | Constraints     |
|--------------|-----------------|-----------------|
| `name`       | CharField(200)  | unique=True     |
| `country`    | CharField(100)  | blank=True      |
| `website`    | URLField        | blank=True      |
| `email`      | EmailField      | blank=True      |
| `phone`      | CharField(20)   | blank=True      |
| `created_at` | DateTimeField   | auto_now_add    |

#### Book

Core inventory model. Tenant-scoped via `tenant` FK to `core.School`. Database indexes: `isbn`, `barcode`, `(category, title)`. Ordered by `title`.

| Field              | Type              | Constraints                               |
|--------------------|-------------------|-------------------------------------------|
| `tenant`           | FK(core.School)   | CASCADE                                   |
| `title`            | CharField(300)    |                                           |
| `author`           | CharField(200)    |                                           |
| `isbn`             | CharField(20)     | unique, validated by `validate_isbn`       |
| `filiere`          | FK(Filiere)       | SET_NULL, null/blank                       |
| `category`         | TreeFK(BookCat.)  | SET_NULL, null/blank, related='books'      |
| `publisher`        | FK(Publisher)     | SET_NULL, null/blank, related='books'      |
| `publication_year` | IntegerField      | null/blank                                 |
| `edition`          | CharField(50)     | blank                                      |
| `language`         | CharField(50)     | default='English'                          |
| `pages`            | IntegerField      | null/blank                                 |
| `barcode`          | CharField(50)     | unique, null/blank (RFID/barcode support)  |
| `quantity`         | IntegerField      | default=1 (total copies owned)             |
| `available`        | IntegerField      | default=1 (copies currently available)     |
| `shelf_location`   | CharField(50)     | blank                                      |
| `cover_image`      | ImageField        | upload_to='library/covers/%Y/%m/'          |
| `description`      | TextField         | blank                                      |
| `tags`             | CharField(200)    | blank, comma-separated                     |
| `created_at`       | DateTimeField     | auto_now_add                               |
| `updated_at`       | DateTimeField     | auto_now                                   |

Key methods:

- `is_available()` -- returns `True` if `available > 0`.
- `borrow()` -- decrements `available` by 1 with `save(update_fields=['available'])`. Returns `True` on success, `False` if none available.
- `return_book()` -- increments `available` by 1 (capped at `quantity`) with `save(update_fields=['available'])`. Returns `True` on success, `False` if already at full quantity.

#### BorrowRecord

Lending transaction record. Tenant-scoped via `tenant` FK. Ordered by `-borrowed_at`. No unique constraint on `(book, student, status)` -- a student can have multiple active borrow records for the same book.

| Field         | Type                  | Constraints                                |
|---------------|-----------------------|--------------------------------------------|
| `tenant`      | FK(core.School)       | CASCADE                                    |
| `book`        | FK(Book)              | CASCADE                                    |
| `student`     | FK(AUTH_USER_MODEL)   | CASCADE                                    |
| `borrowed_at` | DateTimeField         | auto_now_add                               |
| `due_date`    | DateField             |                                            |
| `returned_at` | DateTimeField         | null/blank                                 |
| `status`      | CharField(20)         | choices: borrowed/returned/overdue/lost    |
| `fine_amount` | DecimalField(6,2)     | default=0                                  |
| `notes`       | TextField             | blank                                      |

Key method: `is_overdue()` -- returns `True` if status is `'borrowed'` and `due_date < today`.

Status state transitions:

```text
borrowed  --> returned  (via return_book view)
borrowed  --> overdue   (via Celery task or overdue_books view detection)
overdue   --> returned  (via return_book view)
borrowed  --> lost      (manual/admin only)
overdue   --> lost      (manual/admin only)
```

### ISBN Validation (`validate_isbn`)

- Standalone validator function applied on `Book.isbn`.
- Strips hyphens and spaces from input, then validates:
  - **ISBN-10**: 9 digits + check digit (0-9 or X). Uses weighted sum modulo 11.
  - **ISBN-13**: 13 digits. Uses alternating 1/3 weighted sum modulo 10.
- Raises `ValidationError` for invalid format, length, or check digit.

---

## URL Structure

All library URLs are mounted under `/library/` (frontend) and `/api/v1/library/` (API).

Namespacing: `frontend:library:<view_name>` and `api:library:<resource>`.

### Frontend URLs

| URL Pattern                    | View Function       | Name                | Method    |
|--------------------------------|---------------------|---------------------|-----------|
| `/library/`                    | `book_list`         | `book_list`         | GET       |
| `/library/create/`             | `book_create`       | `book_create`       | GET/POST  |
| `/library/overdue/`            | `overdue_books`     | `overdue_books`     | GET       |
| `/library/<pk>/`               | `book_detail`       | `book_detail`       | GET       |
| `/library/<pk>/edit/`          | `book_edit`         | `book_edit`         | GET/POST  |
| `/library/<pk>/delete/`        | `book_delete`       | `book_delete`       | GET/POST  |
| `/library/my-borrowed/`        | `my_borrowed_books` | `my_borrowed_books` | GET       |
| `/library/borrow/<book_id>/`   | `borrow_book`       | `borrow_book`       | POST      |
| `/library/return/<record_id>/` | `return_book`       | `return_book`       | POST      |

### API URLs (DRF DefaultRouter)

| URL Pattern                       | ViewSet                | Basename        |
|-----------------------------------|------------------------|-----------------|
| `/api/v1/library/books/`          | `BookViewSet`          | `book`          |
| `/api/v1/library/borrow-records/` | `BorrowRecordViewSet`  | `borrow-record` |

Both API viewsets are `ModelViewSet` with `IsAuthenticated` permission, exposing all
CRUD operations. The API viewsets do not filter by tenant -- they return
`Book.objects.all()` and `BorrowRecord.objects.all()`.

---

## Authentication and Authorization

### Decorator Stack

The frontend views use a layered decorator pattern from the `accounts` app:

| Decorator                       | Purpose                              | Used By                                                  |
|---------------------------------|--------------------------------------|----------------------------------------------------------|
| `@login_required`               | Ensures user is authenticated        | All 9 views                                              |
| `@role_required('student')`     | Restricts to student role only       | `borrow_book`, `return_book`, `my_borrowed_books`        |
| `@librarian_only`               | librarian, secretary, direction, admin | `book_create`, `book_edit`, `book_delete`, `overdue_books` |
| `@tenant_required`              | Ensures valid tenant context         | All 9 views                                              |
| `@ratelimit`                    | Rate limiting via django-ratelimit   | All 9 views (20-100/h)                                   |

Note: `@librarian_only` is a shortcut defined in `accounts/decorators.py` as `role_required('librarian', 'secretary', 'direction', 'admin')`. Superusers bypass all role checks.

### Role Access Matrix (Frontend)

| View                 | student | professor | direction | parent | admin | prefet | accountant | secretary | librarian | registrar |
|----------------------|---------|-----------|-----------|--------|-------|--------|------------|-----------|-----------|-----------|
| `book_list`          | R       | R         | R         | R      | R     | R      | R          | R         | R         | R         |
| `book_detail`        | R       | R         | R+H       | R      | R+H   | R      | R          | R+H       | R+H       | R         |
| `book_create`        | -       | -         | W         | -      | W     | -      | -          | W         | W         | -         |
| `book_edit`          | -       | -         | W         | -      | W     | -      | -          | W         | W         | -         |
| `book_delete`        | -       | -         | W         | -      | W     | -      | -          | W         | W         | -         |
| `overdue_books`      | -       | -         | R         | -      | R     | -      | -          | R         | R         | -         |
| `borrow_book`        | W       | -         | -         | -      | -     | -      | -          | -         | -         | -         |
| `return_book`        | W       | -         | -         | -      | -     | -      | -          | -         | -         | -         |
| `my_borrowed_books`  | R       | -         | -         | -      | -     | -      | -          | -         | -         | -         |

Legend:

- `R` = Read access
- `W` = Write access (create/update/delete/action)
- `R+H` = Read access with borrow history visible (last 20 BorrowRecords for that book)
- `-` = No access (redirected to dashboard)
- Superuser bypasses all role checks and has full access to everything

The `book_detail` view conditionally shows borrow history when `request.user.role` is one of `librarian`, `secretary`, `direction`, or `admin`, or when `request.user.is_superuser` is `True`. For students, it shows a `user_has_borrowed` flag indicating whether the student currently has an active borrow of that book.

### Rate Limiting

| View               | Rate Limit     | Method |
|--------------------|----------------|--------|
| `book_list`        | 100/h per user | ALL    |
| `book_detail`      | 100/h per user | ALL    |
| `borrow_book`      | 20/h per user  | POST   |
| `return_book`      | 20/h per user  | POST   |
| `book_create`      | 50/h per user  | POST   |
| `book_edit`        | 50/h per user  | POST   |
| `book_delete`      | 50/h per user  | POST   |
| `overdue_books`    | 100/h per user | ALL    |

### API Permission Model

| ViewSet                | Permission Class  | HTTP Methods                | Tenant Scoped |
|------------------------|-------------------|-----------------------------|---------------|
| `BookViewSet`          | `IsAuthenticated` | GET, POST, PUT, PATCH, DELETE | No            |
| `BorrowRecordViewSet`  | `IsAuthenticated` | GET, POST, PUT, PATCH, DELETE | No            |

Both API ViewSets use `ModelViewSet` which exposes full CRUD to any authenticated user.
There are no role-based restrictions and no tenant filtering in `get_queryset()`.

---

## Business Logic Workflows

### 1. Book Borrowing Lifecycle

```text
Student browses         Student clicks        BorrowRecord created      14-day
  book_list  ---------> borrow_book --------> status='borrowed'  -----> countdown
    (GET)                 (POST)              due_date = today+14        begins
                                              book.available -= 1

                    +------------------------+
                    |    While Borrowed       |
                    +------------------------+
                    |                        |
           Student returns            Celery task runs
           via return_book           (Mon/Wed/Fri 10AM)
              (POST)              send_overdue_reminders
                |                        |
                v                        v
        record.status =         Is due_date < today?
          'returned'             Yes: status='overdue'
        record.returned_at =          + send email
          today                  No:  skip
        book.available += 1
                |
                v
            COMPLETED
```

### 2. Borrow Book (Frontend) -- Step by Step

```text
Student clicks "Borrow" on book_list or book_detail
    |
    v
POST /library/borrow/<book_id>/
    |
    v
@role_required('student') -- only students can borrow
@tenant_required -- ensures tenant context
@ratelimit(20/h POST) -- prevents abuse
    |
    v
get_object_or_404(Book, id=book_id, tenant=request.tenant)
    |
    +-- Book not found? --> 404
    |
    v
Check: book.available > 0?
    |
    +-- No  --> messages.error('Book not available')
    |          redirect to book_list
    |
    +-- Yes --> Create BorrowRecord:
                    tenant = request.tenant
                    book = book
                    student = request.user
                    due_date = today + 14 days
                    status = 'borrowed' (default)
                |
                v
                book.available -= 1
                book.save()
                |
                v
                messages.success('Successfully borrowed {title}')
                redirect to book_list
```

### 3. Return Book (Frontend) -- Step by Step

```text
Student clicks "Return" on my_borrowed_books page
    |
    v
POST /library/return/<record_id>/
    |
    v
@role_required('student')
@tenant_required
@ratelimit(20/h POST)
    |
    v
get_object_or_404(BorrowRecord,
    id=record_id,
    student=request.user,       <-- ensures student owns the record
    tenant=request.tenant,
    status__in=['borrowed', 'overdue']  <-- only active borrows
)
    |
    +-- Not found? --> 404
    |
    v
record.status = 'returned'
record.returned_at = date.today()
record.save()
    |
    v
record.book.available += 1
record.book.save()
    |
    v
messages.success('Successfully returned {title}')
redirect to my_borrowed_books
```

### 4. Book Delete (Frontend) -- Step by Step

```text
Librarian clicks "Delete" on book_detail page
    |
    v
GET /library/<pk>/delete/
    |
    v
@librarian_only (librarian, secretary, direction, admin)
@tenant_required
    |
    v
get_object_or_404(Book, pk=pk, tenant=request.tenant)
    |
    v
Count active borrows:
    BorrowRecord.objects.filter(
        book=book,
        status__in=['borrowed', 'overdue']
    ).count()
    |
    v
Render book_confirm_delete.html
    (shows active borrow count as warning)
    |
    v
Librarian confirms (POST)
    |
    v
active_borrows > 0?
    |
    +-- Yes --> messages.error('Cannot delete with active borrows')
    |          redirect to book_detail
    |
    +-- No  --> book.delete()
                messages.success('Book deleted')
                redirect to book_list
```

### 5. Send Overdue Reminders (Celery Task)

```text
Celery beat triggers send_overdue_reminders()
    Schedule: Mon, Wed, Fri at 10:00 AM
    (crontab: hour=10, minute=0, day_of_week='1,3,5')
    |
    v
Query: BorrowRecord.objects.filter(
    status='borrowed',
    due_date__lt=date.today()
)
    |
    +-- NOTE: No tenant scoping -- processes ALL tenants at once
    |
    v
For each overdue record:
    |
    v
    record.status = 'overdue'
    record.save()
    |
    v
    send_mail(
        subject='[{tenant.name}] Overdue Book Reminder',
        message='Dear {student.get_full_name}, ...',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[student.email],
        fail_silently=True
    )
    |
    v
Return count of overdue records processed
```

### 6. Overdue Books Dashboard

Accessible only to librarian, secretary, direction, and admin roles.

```text
GET /library/overdue/
    |
    v
Query BorrowRecord where:
    status='overdue'  OR  (status='borrowed' AND due_date < now)
    |
    v
select_related('book', 'student')
order_by('due_date') -- most overdue first
    |
    v
Paginate: 20 per page
    |
    v
Render overdue_books.html with total_overdue count
```

### 7. Book Management (Librarian Workflow)

```text
CREATE:  book_create (GET form, POST submit)
         --> BookForm fields: title, isbn, author, publisher, category, quantity, available
         --> Sets book.tenant = request.tenant on save (commit=False pattern)
         --> Supports file upload (cover_image via request.FILES)

EDIT:    book_edit (GET pre-filled form, POST submit)
         --> Same BookForm, instance=book
         --> Supports file upload replacement

DELETE:  book_delete (GET confirmation page, POST delete)
         --> BLOCKED if active borrows exist (status in ['borrowed', 'overdue'])
         --> Shows count of active borrows on confirmation page
         --> Redirects to book_list after deletion
```

---

## Dependencies

### Outgoing Dependencies (What library depends on)

```text
library
    |
    +---> core.models.School        FK: Book.tenant, BorrowRecord.tenant
    |
    +---> accounts.models.User      FK: BorrowRecord.student (AUTH_USER_MODEL)
    |     accounts.decorators       @login_required, @role_required,
    |                               @tenant_required, @librarian_only,
    |                               @direction_only
    |
    +---> filieres.models.Filiere   FK: Book.filiere (optional, SET_NULL)
    |
    +---> django-mptt               MPTTModel, TreeForeignKey for BookCategory
    |
    +---> django-ratelimit          @ratelimit decorator on all frontend views
    |
    +---> djangorestframework       ViewSets, serializers, permissions (API)
    |
    +---> celery                    @shared_task for send_overdue_reminders
    |
    +---> Pillow                    ImageField for Book.cover_image
    |
    +---> django.core.mail          send_mail in tasks.py
```

### Incoming Dependencies (Other apps that import from library)

```text
+---------------------------------+    imports    +---------------------------+
| accounts/views_frontend.py      | <----------- | library.models.BorrowRecord|
| accounts/views.py               |              |                           |
|   Student dashboard shows       |              | Queries:                  |
|   borrowed_books (status=       |              |   .filter(student=user,   |
|   'borrowed', limit 5)          |              |    status='borrowed')     |
+---------------------------------+              |    .select_related('book')|
                                                 |    [:5]                   |
+---------------------------------+              |                           |
| accounts/views_frontend.py      | <----------- | library.models.BorrowRecord|
| accounts/views.py               |              |                           |
|   Direction dashboard shows     |              | Queries:                  |
|   library_stats {borrowed,      |              |   .filter(tenant, status) |
|   overdue counts}               |              |    .count()               |
+---------------------------------+              +---------------------------+

+---------------------------------+    imports    +---------------------------+
| core/views_frontend.py          | <----------- | library.models.Book       |
|   render_librarian_dashboard()  |              | library.models.BorrowRecord|
|                                 |              |                           |
|   Shows:                        |              | Queries:                  |
|   - total_books                 |              |   Book.objects.count()    |
|   - total_available             |              |   .filter(available__gt=0)|
|   - currently_borrowed          |              |   BorrowRecord            |
|   - overdue_count               |              |    .filter(status=...)    |
|   - recent_borrows (last 10)    |              |    .count()               |
|   - low_stock_books (avail < 3) |              |    .order_by(...)[:10]    |
|   - out_of_stock count          |              |   .filter(available__lt=3)|
+---------------------------------+              +---------------------------+

+---------------------------------+    imports    +---------------------------+
| monitoring/views_frontend.py    | <----------- | library.models.Book       |
|   dashboard_overview()          |              | library.models.BorrowRecord|
|   library_statistics()          |              |                           |
|   export_dashboard_csv()        |              | Queries:                  |
|                                 |              |   .filter(tenant)         |
|   Shows:                        |              |    .values('category')    |
|   - books_by_category           |              |    .annotate(count)       |
|   - borrow_stats by status      |              |    .values('status')      |
|   - CSV export with totals      |              |    .annotate(count)       |
+---------------------------------+              +---------------------------+

+---------------------------------+    imports    +---------------------------+
| monitoring/views_api.py         | <----------- | library.models.Book       |
|   DashboardStatsAPIView         |              | library.models.BorrowRecord|
|   LibraryStatsAPIView           |              |                           |
|                                 |              | Returns JSON:             |
|   Returns:                      |              |   books_by_category,      |
|   - library.total_books         |              |   borrow_status counts    |
|   - library.borrowed            |              |                           |
|   - library.overdue             |              |                           |
+---------------------------------+              +---------------------------+

+---------------------------------+    references +---------------------------+
| School_System/celery.py         | <----------- | library.tasks             |
|   CELERY_BEAT_SCHEDULE           |              |  .send_overdue_reminders  |
|   'send-overdue-book-reminders' |              |                           |
|   Mon/Wed/Fri at 10:00 AM      |              |                           |
+---------------------------------+              +---------------------------+

+---------------------------------+    imports    +---------------------------+
| core/management/commands/       | <----------- | library.models.Book       |
|   generate_beta_data.py         |              | library.models.BorrowRecord|
|   (seeds test/demo data)        |              |                           |
+---------------------------------+              +---------------------------+
```

### Dependency Summary Table

| Direction | App/Module                      | What Is Used                                                     |
|-----------|---------------------------------|------------------------------------------------------------------|
| OUT       | `core.models.School`            | FK `tenant` on Book, BorrowRecord                                |
| OUT       | `filieres.models.Filiere`       | FK `filiere` on Book                                             |
| OUT       | `accounts.models.User`          | FK `student` on BorrowRecord (AUTH_USER_MODEL)                   |
| OUT       | `accounts.decorators`           | `direction_only`, `librarian_only`, `tenant_required`, `role_required` |
| OUT       | `django-mptt`                   | `MPTTModel`, `TreeForeignKey` for BookCategory                   |
| OUT       | `django_ratelimit`              | `@ratelimit` on all frontend views                               |
| OUT       | `djangorestframework`           | `ModelViewSet`, `ModelSerializer`, `IsAuthenticated`              |
| OUT       | `celery`                        | `@shared_task` for `send_overdue_reminders`                      |
| OUT       | `django.core.mail`              | `send_mail` in overdue reminder task                             |
| OUT       | `Pillow`                        | `ImageField` for `Book.cover_image`                              |
| IN        | `accounts.views_frontend`       | Reads `BorrowRecord` for student dashboard (borrowed books)      |
| IN        | `accounts.views`                | Reads `BorrowRecord` for student dashboard (borrowed books)      |
| IN        | `accounts.views_frontend`       | Reads `BorrowRecord` for direction dashboard (library stats)     |
| IN        | `accounts.views`                | Reads `BorrowRecord` for direction dashboard (library stats)     |
| IN        | `core.views_frontend`           | Reads `Book`, `BorrowRecord` for librarian dashboard             |
| IN        | `monitoring.views_frontend`     | Reads `Book`, `BorrowRecord` for statistics, CSV export          |
| IN        | `monitoring.views_api`          | Reads `Book`, `BorrowRecord` for dashboard/library stats API     |
| IN        | `School_System.celery`          | Schedules `send_overdue_reminders` via Celery Beat               |
| IN        | `core.management.generate_beta_data` | Seeds demo Book and BorrowRecord data                       |

---

## Data Flow Diagrams

### 1. Student Borrow Flow

```text
 Browser                   Django View                  Database
 =======                   ===========                  ========

 GET /library/
   |
   +----> book_list -----------> Book.objects.filter(tenant=T)
   |        |                       .select_related('category','publisher')
   |        |                     + BookCategory.objects.filter(is_active=True)
   |        |                     + Book.objects.filter(tenant=T).count()
   |        |                     + Book.objects.filter(tenant=T, available__gt=0).count()
   |        |<--- render book_list.html (paginated 20/page, search, category filter)
   |
 GET /library/<pk>/
   |
   +----> book_detail ----------> Book.objects.get(pk, tenant=T)
   |        |                       .select_related('category','publisher','filiere')
   |        |                     + BorrowRecord.objects.filter(
   |        |                         book=book, student=user, status='borrowed').exists()
   |        |<--- render book_detail.html (with user_has_borrowed flag)
   |
 POST /library/borrow/<id>/
   |
   +----> borrow_book ----------> Book.objects.get(id, tenant=T)
   |        |                       if book.available > 0:
   |        |                         BorrowRecord.objects.create(
   |        |                           tenant=T, book=book, student=user,
   |        |                           due_date=today+14)
   |        |                         book.available -= 1; book.save()
   |        |<--- redirect to book_list + success message
   |
 GET /library/my-borrowed/
   |
   +----> my_borrowed_books ----> BorrowRecord.objects.filter(
   |        |                       student=user, tenant=T).order_by('-borrowed_at')
   |        |<--- render my_books.html
   |
 POST /library/return/<id>/
   |
   +----> return_book ----------> BorrowRecord.objects.get(
            |                       id, student=user, tenant=T,
            |                       status__in=['borrowed','overdue'])
            |                     record.status = 'returned'
            |                     record.returned_at = today; record.save()
            |                     record.book.available += 1; record.book.save()
            |<--- redirect to my_borrowed_books + success message
```

### 2. Librarian Management Flow

```text
 Browser                   Django View                  Database
 =======                   ===========                  ========

 GET /library/create/
   |
   +----> book_create ----------> render BookForm (empty)
   |
 POST /library/create/
   |
   +----> book_create ----------> BookForm.is_valid()?
   |        |                       book = form.save(commit=False)
   |        |                       book.tenant = request.tenant
   |        |                       book.save()
   |        |<--- redirect to book_detail/<pk>/ + success msg
   |
 GET /library/<pk>/edit/
   |
   +----> book_edit -------------> Book.objects.get(pk, tenant=T)
   |        |                       render BookForm(instance=book)
   |
 POST /library/<pk>/edit/
   |
   +----> book_edit -------------> BookForm(data, files, instance=book)
   |        |                       form.save()
   |        |<--- redirect to book_detail/<pk>/ + success msg
   |
 GET /library/<pk>/delete/
   |
   +----> book_delete -----------> Book.objects.get(pk, tenant=T)
   |        |                       BorrowRecord.objects.filter(
   |        |                         book=book, status__in=[...]).count()
   |        |<--- render confirmation page (shows active borrow count)
   |
 POST /library/<pk>/delete/
   |
   +----> book_delete -----------> if active_borrows > 0: BLOCK, redirect
            |                       else: book.delete()
            |<--- redirect to book_list + success msg
```

### 3. Celery Overdue Processing Flow

```text
 Celery Beat                  Celery Worker              Database          Email
 ===========                  =============              ========          =====

 Mon/Wed/Fri 10:00 AM
       |
       +--- triggers --------> send_overdue_reminders()
                                  |
                                  +-----> BorrowRecord.objects.filter(
                                  |         status='borrowed',
                                  |         due_date__lt=date.today())
                                  |
                                  |<----- [list of overdue records]
                                  |
                                  +-- for each record:
                                  |     record.status = 'overdue'
                                  |     record.save() ------> UPDATE BorrowRecord
                                  |                            SET status='overdue'
                                  |
                                  |     send_mail() --------> SMTP --> Student inbox
                                  |       subject: "[{tenant.name}] Overdue Book Reminder"
                                  |       to: record.student.email
                                  |       body: "Dear {name}, book '{title}' is overdue..."
                                  |       fail_silently=True
                                  |
                                  +--- return count
```

### 4. Cross-App Dashboard Data Flow

```text
                                      library.models
                                     +---------------+
                                     | Book          |
                                     | BorrowRecord  |
                                     +-------+-------+
                                             |
                     +-----------+-----------+-----------+-----------+
                     |           |                       |           |
                     v           v                       v           v
           Student Dash   Librarian Dash         Direction Dash  Monitoring
           (accounts/     (core/views_           (accounts/      (monitoring/
            views_         frontend.py)           views_          views_
            frontend.py)                          frontend.py)    frontend.py &
                |               |                     |           views_api.py)
                v               v                     v              |
         borrowed_books   total_books           library_stats        v
         (status=         total_available       {borrowed,      library_stats
          'borrowed',     currently_borrowed     overdue         books_by_category
          limit 5)        overdue_count          counts}         borrow_stats
                          recent_borrows                         CSV export
                          low_stock_books                        JSON API
                          out_of_stock
```

### 5. API Data Flow

```text
 API Client (JSON)            DRF ViewSet              Database
 =================            ===========              ========

 GET /api/v1/library/books/
   |
   +----> BookViewSet.list ------> Book.objects.all()
   |        |                       (no tenant filter)
   |        |<--- JSON: BookSerializer(queryset, many=True)
   |
 POST /api/v1/library/books/
   |
   +----> BookViewSet.create ----> BookSerializer.is_valid()
   |        |                       serializer.save()
   |        |<--- JSON: created book data
   |
 GET /api/v1/library/borrow-records/
   |
   +----> BorrowRecordViewSet.list -> BorrowRecord.objects.all()
   |        |                          (no tenant filter)
   |        |<--- JSON: BorrowRecordSerializer(queryset, many=True)
   |
 (PUT/PATCH/DELETE also available on detail endpoints)
```

---

## Forms

### BookForm (ModelForm)

- **Model**: `Book`
- **Fields**: `title`, `isbn`, `author`, `publisher`, `category`, `quantity`, `available`
- **Widgets**: All use Bootstrap `form-control`/`form-select` classes.
- Note: `publisher` uses `TextInput` widget but the model field is a ForeignKey. The
  `category` field uses a `Select` widget (rendered from `TreeForeignKey` choices).
  Many Book fields are not included (edition, language, pages, barcode, cover_image,
  description, tags, shelf_location, etc.).

### BorrowForm (ModelForm)

- **Model**: `BorrowRecord`
- **Fields**: `book`, `student`, `due_date`
- **Widgets**: Bootstrap-styled Select and DateInput.
- Defined but not used by any current view. Borrowing is handled programmatically in
  `borrow_book` (the student is inferred from `request.user`, and `due_date` is always
  `today + 14 days`).

---

## Serializers

### BookSerializer

- `ModelSerializer` with `fields = '__all__'` on the `Book` model.
- Exposes all fields including `tenant`, `isbn`, `barcode`, `created_at`, `updated_at`.
- No read-only fields defined.

### BorrowRecordSerializer

- `ModelSerializer` with `fields = '__all__'` on the `BorrowRecord` model.
- Exposes all fields including `tenant`, `student`, `fine_amount`.
- Returns `book` and `student` as integer IDs only (no nested representation).
- No read-only fields defined.

---

## Admin Configuration

### BookAdmin

- **list_display**: `title`, `author`, `isbn`, `quantity`, `available`, `tenant`
- **list_filter**: `filiere`, `category`, `tenant`
- **search_fields**: `title`, `author`, `isbn`
- **get_queryset**: Filters by `request.tenant` for non-superusers

### BorrowRecordAdmin

- **list_display**: `book`, `student`, `borrowed_at`, `due_date`, `status`, `tenant`
- **list_filter**: `status`, `tenant`
- **get_queryset**: Filters by `request.tenant` for non-superusers

Note: `BookCategory` and `Publisher` are NOT registered in admin.py. They can only be
managed through the Django shell or by registering them separately.

---

## Background Tasks (Celery)

| Task                                   | Schedule                        | Action                                   |
|----------------------------------------|---------------------------------|------------------------------------------|
| `library.tasks.send_overdue_reminders` | Mon, Wed, Fri at 10:00 AM       | Marks overdue records, sends email alerts |

The task is registered in `School_System/celery.py` under the beat schedule key
`'send-overdue-book-reminders'`. It processes all tenants in a single pass (no tenant
scoping in the query).

---

## Key Design Decisions

### Tenant Scoping

Both `Book` and `BorrowRecord` are tenant-scoped via a FK to `core.School`. All frontend
views filter by `request.tenant` (provided by the `@tenant_required` decorator). Admin
querysets also filter by tenant for non-superusers. However, `BookCategory` and `Publisher`
are NOT tenant-scoped -- they are shared across all tenants. This means all tenants see
the same categories and publishers.

### Role-Based Access Split

The library has a clear two-tier access model:

- **Students**: Can only borrow, return, and view their own records (`@role_required('student')`).
- **Librarians+**: Can manage books (create/edit/delete) and view overdue records (`@librarian_only` = librarian, secretary, direction, admin).
- **Everyone else**: Can browse the book list and view book details but cannot borrow or manage.

### Model-Level Borrow/Return Methods

The `Book` model provides `borrow()` and `return_book()` methods that atomically update
the `available` count using `save(update_fields=['available'])`. However, the frontend
views do NOT use these methods -- they manually increment/decrement `available` and call
`save()` without `update_fields`. This is an inconsistency between the model API and
view-level logic.

### Fixed Borrow Period

All borrows have a 14-day loan period (`due_date = today + 14 days`). There is no
configurable per-book or per-tenant loan duration.

### Delete Protection

Books with active borrows (status `'borrowed'` or `'overdue'`) cannot be deleted. The
`book_delete` view checks and blocks deletion with a user-facing error message.

### Overdue Detection (Dual Path)

Overdue detection happens in two places:

1. The `overdue_books` view detects overdue records on-the-fly using `Q(status='borrowed', due_date__lt=now)` (does not update the database).
2. The Celery task permanently updates the status field to `'overdue'` in the database and sends email notifications.

### View File Separation

Views are split into `views_frontend.py` (template-based, 9 views) and `views_api.py`
(DRF ViewSets, 2 ViewSets). Both operate on the same models but with different permission
models (frontend is more restrictive than API).

### ISBN Validation

ISBN validation is implemented as a standalone function (`validate_isbn`) applied as a
Django validator on the `isbn` field. It supports both ISBN-10 and ISBN-13 with full
checksum verification. Hyphens and spaces are stripped before validation.

### No Signals

The library app does not define any Django signals. All stock updates (available count
changes) are handled inline within views.

---

## Known Issues

1. **API has no tenant scoping** -- Both `BookViewSet` and `BorrowRecordViewSet` return `Model.objects.all()` without filtering by tenant.
2. **API has no role-based write restrictions** -- Both ViewSets use `ModelViewSet` with only `IsAuthenticated`. Any authenticated user can create, update, and delete books and borrow records via the API.
3. **`tasks.py` calls `get_full_name()` with parentheses** -- `send_overdue_reminders` calls `record.student.get_full_name()` but `get_full_name` is a `@property` on the User model, which would cause a `TypeError` at runtime.
4. **`borrow_book` has no duplicate borrow check** -- A student can borrow the same book multiple times without returning it first.
5. **`borrow_book` and `return_book` bypass model methods** -- Both views manually adjust `book.available` instead of calling `book.borrow()` / `book.return_book()`, bypassing the model's boundary checks and atomic saves.
6. **`return_book` sets `returned_at` to `date` instead of `datetime`** -- Assigns `date.today()` to a `DateTimeField`, losing time precision.
7. **`BorrowRecord.is_overdue()` uses naive datetime** -- Calls `datetime.now()` instead of `timezone.now()`, which can produce incorrect results in timezone-aware Django projects.
8. **`BookCategory` and `Publisher` not in admin** -- These models have no admin registration and no frontend CRUD views.
