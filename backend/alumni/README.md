# Alumni App

Alumni network management with directory, events, donations, and achievement tracking.

## Description

The alumni app manages graduated students' profiles, networking events, donations, and achievements. It provides models for alumni records linked to student profiles, alumni-specific events with registration, a donation system, and achievement tracking.

**Status: All frontend views are currently placeholders returning "Coming soon in Phase 5" text responses.**

## Main Features (Planned)

- **Alumni Directory**: Browse and search alumni by graduation year, industry, location
- **Alumni Profiles**: Career info, contact details, mentorship willingness
- **Events**: Reunions, networking, workshops with attendee management and registration limits
- **Donations**: Track donations by purpose (scholarship, infrastructure, etc.) with tax receipts
- **Achievements**: Track notable alumni accomplishments with featured highlights

## User Roles

| Role | Permissions |
|------|------------|
| admin/direction | Full management of alumni records, events, donations |
| alumni (authenticated) | View directory, update own profile, register for events, make donations |
| public | View featured achievements |

## CRUD Summary

| Entity | Create | Read | Update | Delete |
|--------|--------|------|--------|--------|
| Alumni | API only | Placeholder | API only | API only |
| AlumniEvent | API only | Placeholder | API only | API only |
| AlumniDonation | Placeholder | N/A | N/A | N/A |
| AlumniAchievement | API only | N/A | API only | API only |

## Models

- `Alumni` -- student FK, graduation_year, current_occupation, employer, industry, linkedin_url, willing_to_mentor
- `AlumniEvent` -- title, description, dates, location, max_attendees, registration_deadline
- `AlumniDonation` -- amount, currency, purpose, transaction_id, payment_method, is_anonymous, tax_receipt_sent
- `AlumniAchievement` -- achievement_type, title, description, achievement_date, is_featured

## Dependencies

- `accounts` (Student model via OneToOneField, User model for organizers)

## URL Namespace

- Frontend: `frontend:alumni:<view_name>`
- API: `api:v1:alumni:<resource-name>`
