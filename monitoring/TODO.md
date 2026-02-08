# Monitoring - TODO

## Backend

- [ ] Wire `DashboardFilterForm` (date range) to `monitoring_dashboard` view to allow filtering statistics by date
- [ ] Wire `ExportFormatForm` to support XLSX, JSON, and PDF exports in addition to CSV
- [ ] Expand CSV export to include enrollment stats, gender stats, library stats, and discipline stats -- currently only 3 rows (students, professors, parents)
- [ ] Add attendance statistics to the dashboard (conditional import from attendance app)
- [ ] Add grade/result statistics to the dashboard (conditional import from result app)

## Frontend

- [ ] Add date range filter controls to dashboard template
- [ ] Add export format selector (CSV/XLSX/JSON/PDF) to dashboard template
- [ ] Add chart visualizations for enrollment stats and gender distribution

## Sidebar

- [ ] Expand Monitoring from single link to expandable menu with sub-links: "Dashboard", "Enrollment Stats", "Library Stats"

## Security

- [ ] No critical security issues found

## Unnecessary Files

- [ ] None identified

## Documentation

- [ ] Add module docstring to views_frontend.py
