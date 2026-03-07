# Alumni - TODO

All frontend views are placeholders. These are the minimum items to make the app functional.

## Backend

- [ ] Implement `alumni_directory` view -- replace placeholder with paginated list of alumni with search/filter
- [ ] Implement `alumni_profile` view -- replace placeholder with detailed alumni profile page
- [ ] Implement `alumni_event_list` view -- replace placeholder with list of upcoming/past events
- [ ] Implement `alumni_event_detail` view -- replace placeholder with event details and attendee list
- [ ] Implement `donation_create` view -- replace placeholder with donation form
- [ ] Add alumni create/edit views -- no way to create or update alumni records from frontend
- [ ] Add alumni achievement list view -- no URL for browsing achievements

## Frontend

- [ ] Create `alumni/directory.html` template for alumni directory listing
- [ ] Create `alumni/profile.html` template for individual alumni profiles
- [ ] Create `alumni/event_list.html` template for events listing
- [ ] Create `alumni/event_detail.html` template for event details
- [ ] Create `alumni/donation_form.html` template for making donations
- [ ] Extend AlumniForm to include more fields (industry, job_title, city, country)

## Sidebar

- [ ] Add "Alumni" entry to sidebar under COMMUNITY section with sub-links: Directory, Events

## Security

- [ ] No security issues found (all views are currently placeholders)

## Unnecessary Files

- [ ] `tests.py` -- empty placeholder file (already scheduled for deletion in git)

## Documentation

- [ ] Add module docstring to models.py
- [ ] `tasks.py:29` has placeholder comment "For now, this is a placeholder" -- implement the actual logic
- [ ] `tasks.py:48,96,146` hardcoded email `"alumni@school.com"` -- should use settings or tenant config
