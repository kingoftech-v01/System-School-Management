# Library App

Book inventory and lending management with hierarchical categories, ISBN validation, barcode support, and borrow/return tracking.

## Description

The library app manages the school's book inventory and lending operations. It provides book listing for all users, borrow/return workflows for students with automatic due dates, and personal borrow history. The app supports hierarchical book categories via django-mptt, ISBN-10/ISBN-13 validation, and barcode/RFID fields.

## Main Features

- **Book Listing**: Browse all books in the library
- **Borrow Books**: Students borrow available books with automatic 14-day due date
- **Return Books**: Students return borrowed books, availability auto-updated
- **My Borrowed Books**: Students view their personal borrow history
- **ISBN Validation**: ISBN-10 and ISBN-13 format validation
- **Hierarchical Categories**: MPTT-based category tree

## User Roles

| Role | Permissions |
|------|------------|
| direction | View book list (no management views yet) |
| student | View books, borrow, view own borrowed books, return |
| professor | View book list |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Book | No | Yes (list only) | No | No |
| BorrowRecord | Yes (borrow) | Yes (my books) | Yes (return) | No |
| BookCategory | No | No | No | No |
| Publisher | No | No | No | No |

## Models

- `BookCategory` (MPTTModel) -- name, parent FK, description, is_active
- `Publisher` -- name, country, website, email, phone
- `Book` -- tenant FK, title, author, isbn (validated), category FK, publisher FK, quantity, available, shelf_location, cover_image, barcode
- `BorrowRecord` -- tenant FK, book FK, student FK, borrowed_at, due_date, returned_at, status (borrowed/returned/overdue/lost), fine_amount

## Dependencies

- `core` (School model for tenant)
- `filieres` (optional Filiere association on Book)
- `django-mptt` (hierarchical categories)
- `django-ratelimit`

## URL Namespace

- Frontend: `frontend:library:<view_name>`
- API: `api:v1:library:<resource-name>`
