# Core - TODO

## Backend

- [ ] Add news/events detail view -- currently only list view, no individual detail page
- [ ] Add search functionality to news/events list -- NewsAndEventsManager has `search()` but it is not used in the view
- [ ] Add `post_add` view access control -- currently any logged-in user can create posts; should require lecturer or direction role
- [ ] Add pagination to session and semester list views
- [ ] Add `is_subscription_valid()` check in dashboard views for tenant-aware deployment

## Frontend

- [ ] Add "View Details" link on each news/event item in the list
- [ ] Add "Add Post" button on the news/events list page for authorized users
- [ ] Add confirmation dialog before deleting a session or semester
- [ ] Add visual indicator (badge/highlight) for current session and current semester in lists
- [ ] Add responsive card layout for news/events on the home page

## Sidebar

- [ ] Add "News & Events" link under MAIN section or within Settings submenu -- no direct sidebar link to news list
- [ ] Add "Add Post" link alongside "News & Events" for authorized roles

## Security

- [ ] No critical security issues found

## API

- [ ] Add filtering by `posted_as` (News/Event) on NewsAndEventsViewSet
- [ ] Add search endpoint for news/events using existing `NewsAndEventsManager.search()`
- [ ] Add rate limiting to session/semester toggle endpoints (`set_current`)

## Testing

- [x] Models tests exist (test_models.py, test_models_extended.py)
- [x] Views tests exist (test_views.py, test_views_api.py)
- [x] Form tests exist (test_forms.py)
- [x] Serializer tests exist (test_serializers.py)
- [x] Template tag tests exist (test_templatetags.py)
- [x] Utility tests exist (test_utils.py)
- [x] Admin tests exist (test_admin.py)

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] School model methods lack docstrings -- add docstrings to all public methods
- [ ] Complete partial docstrings that exist in models.py
- [ ] Add docstrings to views_frontend.py dashboard renderer functions
