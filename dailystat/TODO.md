# Daily Stat - TODO

## Backend

- [ ] Add CSV/PDF export for daily stats -- no export functionality exists
- [ ] Add subject-level filtering on date stats view -- currently shows all subjects

## Frontend

- [ ] Add chart visualization on trends page -- currently text/table only, no graphs
- [ ] Add clickable student names on absent student lists linking to attendance reports
- [ ] Add subject filter dropdown on today_stats and date_stats pages

## Sidebar

- [ ] Add "Daily Stats" entry to sidebar under ANALYTICS section with sub-links: Dashboard, Trends

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] None identified

## Documentation

- [ ] `models.py:3` has DUPLICATE import: `from attendance.models import Satus, Subject` imported twice -- fix by keeping only one import line
- [ ] `views_frontend.py:259` placeholder comment about present count -- implement the actual logic
- [ ] Replace bare `except:` clauses (views_frontend.py:57-58, 98-99) with specific exception types
