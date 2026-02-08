# Core - TODO

## Backend

- [ ] Add news/events detail view -- currently only list view, no individual detail page
- [ ] Add search functionality to news/events list -- NewsAndEventsManager has `search()` but it is not used in the view
- [ ] Add `post_add` view access control -- currently any logged-in user can create posts; should require lecturer or direction role

## Frontend

- [ ] Add "View Details" link on each news/event item in the list
- [ ] Add "Add Post" button on the news/events list page for authorized users
- [ ] Add confirmation dialog before deleting a session or semester
- [ ] Add visual indicator (badge/highlight) for current session and current semester in lists

## Sidebar

- [ ] Add "News & Events" link under MAIN section or within Settings submenu -- no direct sidebar link to news list
- [ ] Add "Add Post" link alongside "News & Events" for authorized roles

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] School model methods lack docstrings -- add docstrings to all public methods
- [ ] Complete partial docstrings that exist in models.py
