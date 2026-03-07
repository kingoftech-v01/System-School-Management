# Aurelius - School Management System

> **"Shaping Tomorrow's Leaders Today"** / *Fingere Duces Crastini Hodie*

A comprehensive, multi-tenant school management platform with a Django REST API backend, React web frontend, and React Native mobile app.

## Architecture

```
System-School-Management/
├── backend/      Django REST API (Python 3.11, Django 5.0.6)
├── frontend/     React Web App (Vite, TypeScript, Tailwind CSS, shadcn/ui)
└── mobile/       React Native Mobile App (Expo, TypeScript)
```

## Quick Start

### Backend (Django API)

```bash
cd backend
python -m venv ../venv
../venv/Scripts/activate       # Windows
pip install -r requirements.txt
python manage.py migrate --settings=School_System.settings.development
python manage.py seed_initial_data --settings=School_System.settings.development
python manage.py create_demo_data --settings=School_System.settings.development
python manage.py runserver 9000 --settings=School_System.settings.development
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev    # Starts on port 3000, proxies /api to backend:9000
```

### Mobile (Expo)

```bash
cd mobile
npm install
npx expo start
```

## API

All API endpoints are under `/api/v1/`. Authentication uses JWT tokens.

- Login: `POST /api/v1/accounts/auth/login/`
- Refresh: `POST /api/token/refresh/`
- User profile: `GET /api/v1/accounts/users/me/`

83+ ViewSets across 27 apps providing full CRUD for courses, students, attendance, payments, grading, and more.

## Demo Credentials

| Role | Username | Email | Password |
|------|----------|-------|----------|
| Professor | `prof1` | `professor1@school.edu` | `password123` |
| Student | `student1` | `student1@school.edu` | `password123` |
| Parent | `parent1` | `parent1@email.com` | `password123` |
| Direction | `direction1` | `direction1@school.edu` | `password123` |

## License

Proprietary
