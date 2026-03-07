# Library - TODO

## Bugs

- [ ] **`tasks.py` `get_full_name()` called as method** (tasks.py:22) -- `record.student.get_full_name()` calls `get_full_name` with parentheses, but `get_full_name` is a `@property` on the User model (not a method). This raises `TypeError` at runtime when the task tries to send overdue reminder emails. Fix: change to `record.student.get_full_name` (no parentheses).
- [ ] **`BookForm` missing fields for full book editing** (forms.py:7) -- `BookForm.Meta.fields` only includes `['title', 'isbn', 'author', 'publisher', 'category', 'quantity', 'available']`. Missing fields that the `book_create`/`book_edit` views could benefit from: `filiere`, `publication_year`, `edition`, `language`, `pages`, `barcode`, `shelf_location`, `cover_image`, `description`, `tags`. The `publisher` widget is `TextInput` but the model field is a ForeignKey, so it should use `Select`.
- [ ] **`borrow_book` view duplicates `Book.borrow()` logic** (views_frontend.py:68-76) -- The view manually decrements `book.available` and saves, but the `Book` model already has a `borrow()` method that does the same thing atomically with `update_fields`. The view should call `book.borrow()` instead to avoid inconsistency and use the model's boundary check.
- [ ] **`return_book` view duplicates `Book.return_book()` logic** (views_frontend.py:114-120) -- Same issue as `borrow_book`: the view manually increments `book.available` and saves instead of calling `book.return_book()`. Also sets `returned_at = date.today()` (a `date` object) but the model field is `DateTimeField` -- should use `timezone.now()` for a proper datetime.
- [ ] **`return_book` view sets `returned_at` to date instead of datetime** (views_frontend.py:115) -- `record.returned_at = date.today()` assigns a `date` to a `DateTimeField`. Django may auto-convert this but it loses time precision. Should use `django.utils.timezone.now()`.
- [ ] **`send_overdue_reminders` task has no tenant scoping** (tasks.py:11) -- Queries `BorrowRecord.objects.filter(status='borrowed', due_date__lt=date.today())` without tenant filtering. In a multi-tenant system, this sends emails from all tenants in a single task run. Should iterate per-tenant or at minimum include tenant name correctly.
- [ ] **`BookCategory.get_book_count()` N+1 query problem** (models.py:70-72) -- Recursively calls `get_book_count()` on each subcategory, generating one query per node in the tree. Should use MPTT's `get_descendants()` with a single query: `Book.objects.filter(category__in=self.get_descendants(include_self=True)).count()`.
- [ ] **`BorrowRecord.is_overdue()` uses `datetime.now()` instead of `timezone.now()`** (models.py:250) -- `self.due_date < datetime.now().date()` uses naive datetime. Should use `django.utils.timezone.now().date()` for timezone-aware comparison.

## Backend

- [x] Add `book_detail` view to show full book information (description, category, publisher, availability, cover image)
- [x] Add `book_create` view (librarian only) for adding new books to the library
- [x] Add `book_edit` view (librarian only) for updating book information
- [x] Add `book_delete` view (librarian only) with confirmation
- [x] Add URL patterns for book detail, create, edit, delete
- [x] Add search/filter to `book_list` (by title, author, category, ISBN)
- [x] Add pagination to `book_list` -- now 20 per page via `django.core.paginator.Paginator`
- [x] Add overdue books list view (librarian only) to show overdue BorrowRecords
- [x] Fix `BookForm` field mismatch: form uses `available_quantity` but model field is `available` -- form now uses `available`
- [ ] Add tenant scoping to API ViewSets -- `BookViewSet.get_queryset()` returns `Book.objects.all()` without filtering by `request.tenant`; same for `BorrowRecordViewSet`
- [ ] Add role-based API permissions -- both ViewSets use only `IsAuthenticated`; any authenticated user can create/update/delete books and borrow records via the API
- [ ] Add custom DRF permission class for library (e.g., `IsLibrarian`) to restrict write operations to librarian/direction/admin roles
- [ ] Add `BorrowForm` usage -- `BorrowForm` is defined in forms.py but never used by any view; consider adding a librarian-initiated borrow view
- [ ] Add configurable borrow period -- currently hardcoded to 14 days in `borrow_book` view (line 73); should be a setting or per-tenant config
- [ ] Add fine calculation logic -- `BorrowRecord.fine_amount` field exists but is never set by any view or task
- [ ] Add book reservation/hold system -- students can only borrow immediately; no queuing for unavailable books
- [ ] Add borrow limit per student -- no limit on how many books a student can borrow simultaneously
- [ ] Add `BookCategory` and `Publisher` frontend CRUD views -- currently only manageable via Django admin

## Frontend

- [ ] Add "Add Book" button to book list page (librarian only)
- [ ] Add search bar and category filter dropdown to book list page
- [ ] Add pagination controls to book list template
- [ ] Add "Borrow" button directly on book list items (where available > 0)
- [ ] Add overdue warning indicator on my_books page for overdue records

## Sidebar

- [ ] Expand Library from single link to expandable menu with sub-links: "Browse Books", "My Books" (students), "Overdue Books" (librarian)

## Security

- [ ] **API ViewSets expose full CRUD without tenant scoping** -- `BookViewSet` and `BorrowRecordViewSet` return all records across all tenants. Any authenticated user can read/modify any tenant's data via the API.
- [ ] **API ViewSets use `ModelViewSet` with no write restrictions** -- Any authenticated user can POST/PUT/PATCH/DELETE books and borrow records via the API. Should restrict write methods to librarian/admin roles.
- [ ] **Serializers use `fields = '__all__'`** -- Exposes all model fields including `tenant` FK. A user could potentially set the `tenant` field to another tenant's ID when creating records via the API.
- [ ] **`borrow_book` view has no duplicate borrow check** -- A student can borrow the same book multiple times without returning it first. The `book_detail` view checks `user_has_borrowed` for display but `borrow_book` does not enforce it.
- [ ] **`book_delete` does not filter active borrows by tenant** (views_frontend.py:221) -- `BorrowRecord.objects.filter(book=book, status__in=['borrowed', 'overdue']).count()` does not include `tenant=request.tenant`, though the book itself is already tenant-scoped.

## API

- [ ] Add pagination to API ViewSets -- neither `BookViewSet` nor `BorrowRecordViewSet` defines pagination; relies on global `DEFAULT_PAGINATION_CLASS` if set
- [ ] Add search/filter to `BookViewSet` -- no `filter_backends`, `search_fields`, or `filterset_fields` defined
- [ ] Add nested book detail in `BorrowRecordSerializer` -- currently returns only the book FK ID; should include book title/author for client convenience
- [ ] Add `@action` for borrow/return operations on `BookViewSet` -- e.g., `POST /api/v1/library/books/<pk>/borrow/` and `POST /api/v1/library/books/<pk>/return/`
- [ ] Add `BookCategorySerializer` and `PublisherSerializer` -- these models have no API representation
- [ ] Add read-only fields to serializers -- `created_at`, `updated_at`, `borrowed_at` should be read-only

## Tests

- [ ] Add test for duplicate borrow prevention (same student borrowing same book twice)
- [ ] Add test for `BookCategory.get_book_count()` with deeply nested categories
- [ ] Add test for `validate_isbn` with ISBN-10 including 'X' check digit
- [ ] Add test for `book_create` POST with valid data (current tests only test GET and invalid POST)
- [ ] Add test for `book_edit` POST with valid data
- [ ] Add test for `book_delete` with no active borrows (verify book is actually deleted)
- [ ] Add test for `overdue_books` view with mixed status records
- [ ] Add API test for creating a book via POST
- [ ] Add API test for updating a book via PUT/PATCH
- [ ] Add API test for deleting a book via DELETE
- [ ] Add API test for creating a borrow record via POST
- [ ] Add test for `send_overdue_reminders` with multiple overdue records across tenants
- [ ] Strengthen test assertions -- many frontend tests use `assertIn(resp.status_code, [200, 302, 403, 404, 500])` which passes on any status code; should assert specific expected codes

## Documentation

- [x] Add module docstring to models.py
- [x] `BookForm` field mismatch: form uses `available_quantity` but model field is `available` -- fixed, form now uses `available`

## Unnecessary Files

- [ ] None identified
