# Notices - TODO

## Backend

- [ ] Implement `notice_respond` view to actually create a `NoticeResponse` record -- currently just shows a success message without persisting anything
- [ ] Add acknowledgment tracking: show which users have acknowledged a notice on the detail page (direction only)
- [ ] Add file attachment upload support in `notice_create` and `notice_update` views for NoticeDocument -- form handles FILES but no document model save logic
- [ ] Add expiration filtering to `notice_list` -- hide expired notices by default, toggle to show

## Frontend

- [ ] Add "Acknowledge" button to notice detail page that triggers the notice_respond POST
- [ ] Add acknowledgment count/percentage display on notice detail page (direction only)
- [ ] Add expired notice visual indicator (grayed out or strikethrough)
- [ ] Add file attachment display on notice detail page

## Sidebar

- [ ] Expand Notices from single link to expandable menu with sub-links: "All Notices", "Create Notice" (direction only)

## Security

- [ ] `notice_respond` placeholder -- accepts POST but doesn't persist data (no actual NoticeResponse created) -- implement actual persistence

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Add module docstring to models.py
