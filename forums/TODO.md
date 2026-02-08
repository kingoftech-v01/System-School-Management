# Forums - TODO

## Backend

- [ ] Add category CRUD views (direction only): `category_create`, `category_edit`, `category_delete`
- [ ] Add moderation queue view for direction to review reported content and pending threads
- [ ] Extend forum search to also search post content -- currently only searches threads
- [ ] Add tag CRUD views (direction only) -- currently tags are read-only in the frontend

## Frontend

- [ ] Add "Manage Categories" link visible to direction on forum home page
- [ ] Add pagination controls to my_threads and my_posts templates
- [ ] Add unread indicator for subscribed threads with new posts

## Sidebar

- [ ] Expand Forums from single link to expandable menu with sub-links: "Forum Home", "My Threads", "My Subscriptions"

## Security

- [ ] Forum content uses `RichTextField()` with CKEditor `allowedContent: True` (models.py:87) -- stored XSS risk, must sanitize HTML content

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)
- [ ] `tasks.py:114` commented-out code `# old_threads.update(is_archived=True)` -- implement this archiving logic

## Documentation

- [ ] Add module docstring to models.py
