# Articles - TODO

All frontend views are placeholders. These are the minimum items to make the app functional.

## Backend

- [ ] Implement `article_list` view -- replace placeholder with paginated list of published articles
- [ ] Implement `article_detail` view -- replace placeholder with full article display, comments, likes
- [ ] Implement `category_articles` view -- replace placeholder with articles filtered by category
- [ ] Implement `newsletter_subscribe` view -- replace placeholder with subscription form
- [ ] Add article create/edit views for staff -- no URL for creating articles from frontend
- [ ] Add comment submission endpoint -- no frontend comment form
- [ ] Add like/unlike toggle endpoint -- no frontend like button
- [ ] Fix ArticleForm fields -- references `category` (singular) and `is_published` which do not match model fields (`categories`, `status`)

## Frontend

- [ ] Create `articles/article_list.html` template for article listing with pagination
- [ ] Create `articles/article_detail.html` template with comments section and like button
- [ ] Create `articles/category_list.html` template showing category tree
- [ ] Create `articles/article_form.html` template for creating/editing articles
- [ ] Create `articles/newsletter_subscribe.html` template for newsletter subscription

## Sidebar

- [ ] Add "Articles" entry to sidebar under COMMUNITY section

## Security

- [ ] `CategoryViewSet` (views_api.py:12) uses `AllowAny` permission -- exposes all article categories publicly without authentication
- [ ] Articles use `RichTextField()` with CKEditor `allowedContent: True` (base.py:730) -- stored XSS risk, must sanitize HTML content

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] `tasks.py:39` hardcoded email `'noreply@school.com'` -- should use `settings.EMAIL_FROM_ADDRESS` or tenant config
- [ ] Fix `ArticleForm` field mismatch: form references `category` (singular) and `is_published` but model has `categories` (M2M) and `status`
- [ ] Add module docstring to models.py
