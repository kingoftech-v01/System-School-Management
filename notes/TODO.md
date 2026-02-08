# Notes - TODO

## Backend

- [ ] Add NoteComment views: allow professors and direction to add comments to notes -- model exists but no views
- [ ] Add pagination to `note_list` view -- currently returns all notes unpaginated
- [ ] Add filtering by status and student to `note_list` view
- [ ] Add a view for direction to see all notes (not just pending) with filter options

## Frontend

- [ ] Add comment section to note detail template (showing NoteComments and a form to add new comments)
- [ ] Add status filter dropdown and student search to note list page
- [ ] Add pagination controls to note list template
- [ ] Add visual status badges (draft=gray, pending=yellow, approved=green, rejected=red) to note list items

## Sidebar

- [ ] Expand Notes from single link to expandable menu with sub-links: "My Notes" (professors), "Pending Approval" (direction)

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] None identified

## Documentation

- [ ] Add module docstring to models.py
