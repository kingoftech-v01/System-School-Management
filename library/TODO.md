# Library - TODO

## Backend

- [ ] Add `book_detail` view to show full book information (description, category, publisher, availability, cover image)
- [ ] Add `book_create` view (direction only) for adding new books to the library
- [ ] Add `book_edit` view (direction only) for updating book information
- [ ] Add `book_delete` view (direction only) with confirmation
- [ ] Add URL patterns for book detail, create, edit, delete
- [ ] Add search/filter to `book_list` (by title, author, category, ISBN)
- [ ] Add pagination to `book_list` -- currently returns all books unpaginated
- [ ] Add overdue books list view (direction only) to show overdue BorrowRecords
- [ ] Fix `BookForm` field mismatch: form uses `available_quantity` but model field is `available`

## Frontend

- [ ] Add "Add Book" button to book list page (direction only)
- [ ] Add search bar and category filter dropdown to book list page
- [ ] Add pagination controls to book list template
- [ ] Add "Borrow" button directly on book list items (where available > 0)
- [ ] Add overdue warning indicator on my_books page for overdue records

## Sidebar

- [ ] Expand Library from single link to expandable menu with sub-links: "Browse Books", "My Books" (students), "Overdue Books" (direction)

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] None identified

## Documentation

- [ ] Add module docstring to models.py
- [ ] `BookForm` field mismatch: form uses `available_quantity` but model field is `available` -- fix form to match model
