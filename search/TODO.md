# Search - TODO

## Backend

- [ ] Add `@login_required` decorator to SearchView for consistent access control
- [ ] Add tenant filtering to search results -- currently searches all tenants
- [ ] Expand search to include additional models: Student profiles, Forum threads, Library books, Notices
- [ ] Add minimum query length validation (e.g., 2+ characters) to prevent empty/single-char searches

## Frontend

- [ ] Add search result type indicators (icon or label showing whether result is a Course, Quiz, News, etc.)
- [ ] Add "No results found" message when search returns empty
- [ ] Add search suggestions or autocomplete

## Sidebar

- [ ] No sidebar changes needed -- search is accessed via the header search bar

## Security

- [ ] `SearchAPIView` (views_api.py:50) uses `AllowAny` -- exposes data to unauthenticated users
- [ ] No limit validation on `limit` parameter (views_api.py:55) -- DoS risk with large values, add maximum cap
- [ ] Missing tenant filtering -- searches across all tenants in multi-tenant setup

## Unnecessary Files

- [ ] `models.py` is empty (just `from django.db import models` comment) -- implement a SearchIndex model for caching search results
- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Add module docstring to views_api.py
