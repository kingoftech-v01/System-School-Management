# API Documentation

Complete API reference for the School Management System REST API.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Pagination](#pagination)
- [Filtering & Search](#filtering--search)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [Users](#users)
  - [Students](#students)
  - [Courses](#courses)
  - [Attendance](#attendance)
  - [Results](#results)
  - [Payments](#payments)
  - [Programs](#programs)
- [Webhooks](#webhooks)
- [Code Examples](#code-examples)

## Overview

### Base URL

```
Production: https://api.example.com/api/v1/
Development: http://localhost:8000/api/v1/
```

### API Version

Current version: `v1`

### Content Type

All requests and responses use JSON:

```
Content-Type: application/json
Accept: application/json
```

### HTTP Methods

- `GET` - Retrieve resources
- `POST` - Create resources
- `PUT` - Update resources (full update)
- `PATCH` - Update resources (partial update)
- `DELETE` - Delete resources

## Authentication

### JWT Token Authentication

The API uses JWT (JSON Web Tokens) for authentication.

#### Obtain Token Pair

**Endpoint:** `POST /api/token/`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Access Token:** Valid for 50 minutes
**Refresh Token:** Valid for 10 days

#### Refresh Access Token

**Endpoint:** `POST /api/token/refresh/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Using Token

Include the access token in the Authorization header:

```http
GET /api/students/ HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Verify Token

**Endpoint:** `POST /api/token/verify/`

**Request:**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "valid": true
}
```

## Rate Limiting

API requests are rate-limited to prevent abuse:

### Limits

- **Anonymous users:** 100 requests/hour
- **Authenticated users:** 1,000 requests/hour
- **Admin users:** 10,000 requests/hour
- **Login endpoint:** 5 requests/minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded

**Response:** `429 Too Many Requests`

```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input data",
    "details": {
      "email": ["This field is required."],
      "age": ["Ensure this value is greater than or equal to 5."]
    }
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Successful deletion |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

### Error Codes

| Code | Description |
|------|-------------|
| `authentication_failed` | Invalid or missing credentials |
| `permission_denied` | Insufficient permissions |
| `not_found` | Resource not found |
| `validation_error` | Input validation failed |
| `throttled` | Rate limit exceeded |
| `server_error` | Internal server error |

## Pagination

### Default Pagination

All list endpoints are paginated by default:

- **Default page size:** 20 items
- **Maximum page size:** 100 items

### Query Parameters

- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

### Example Request

```http
GET /api/students/?page=2&page_size=50
```

### Response Format

```json
{
  "count": 150,
  "next": "https://api.example.com/api/students/?page=3&page_size=50",
  "previous": "https://api.example.com/api/students/?page=1&page_size=50",
  "results": [
    {
      "id": 51,
      "first_name": "John",
      "last_name": "Doe",
      ...
    },
    ...
  ]
}
```

## Filtering & Search

### Filtering

Use query parameters to filter results:

```http
GET /api/students/?program=Science&level=Bachelor
```

### Search

Use the `search` parameter for text search:

```http
GET /api/students/?search=john
```

Searches across multiple fields (name, email, etc.)

### Ordering

Use `ordering` parameter:

```http
GET /api/students/?ordering=-created_at
```

- Ascending: `ordering=field_name`
- Descending: `ordering=-field_name`

## Endpoints

## Authentication Endpoints

### Register User

**POST** `/api/auth/register/`

**Request:**
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "SecurePassword123",
  "password_confirm": "SecurePassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response:** `201 Created`
```json
{
  "id": 123,
  "username": "newuser",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_student": false,
  "is_lecturer": false,
  "is_parent": false
}
```

### Login

**POST** `/api/auth/login/`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 123,
    "username": "user@example.com",
    "email": "user@example.com",
    "role": "Student"
  }
}
```

### Logout

**POST** `/api/auth/logout/`

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `204 No Content`

### Password Reset Request

**POST** `/api/auth/password/reset/`

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** `200 OK`
```json
{
  "detail": "Password reset email sent."
}
```

### Password Reset Confirm

**POST** `/api/auth/password/reset/confirm/`

**Request:**
```json
{
  "uid": "MTIz",
  "token": "5tk-ab1c2d3e4f5g6h7i8j9k",
  "new_password": "NewSecurePassword123"
}
```

**Response:** `200 OK`

## Users

### Get Current User

**GET** `/api/users/me/`

**Response:** `200 OK`
```json
{
  "id": 123,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_student": true,
  "is_lecturer": false,
  "is_parent": false,
  "is_dep_head": false,
  "gender": "M",
  "phone": "+1-555-0100",
  "address": "123 Main St",
  "picture": "https://example.com/media/profile.jpg",
  "date_joined": "2024-01-15T10:30:00Z"
}
```

### Update Profile

**PATCH** `/api/users/me/`

**Request:**
```json
{
  "first_name": "Jonathan",
  "phone": "+1-555-0199",
  "address": "456 Oak Avenue"
}
```

**Response:** `200 OK`

### Change Password

**POST** `/api/users/me/change-password/`

**Request:**
```json
{
  "old_password": "OldPassword123",
  "new_password": "NewSecurePassword456"
}
```

**Response:** `200 OK`

### Upload Profile Picture

**POST** `/api/users/me/upload-picture/`

**Request:** `multipart/form-data`
```
picture: [binary file data]
```

**Response:** `200 OK`
```json
{
  "picture": "https://example.com/media/profiles/user_123.jpg"
}
```

## Students

### List Students

**GET** `/api/students/`

**Query Parameters:**
- `program` - Filter by program ID
- `level` - Filter by level (Bachelor, Master)
- `search` - Search by name or email
- `ordering` - Sort by field

**Response:** `200 OK`
```json
{
  "count": 150,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "student": {
        "id": 123,
        "username": "student1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "picture": "https://..."
      },
      "level": "Bachelor",
      "program": {
        "id": 1,
        "title": "Science"
      }
    }
  ]
}
```

### Get Student Detail

**GET** `/api/students/{id}/`

**Response:** `200 OK`
```json
{
  "id": 1,
  "student": {
    "id": 123,
    "username": "student1",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "gender": "M",
    "phone": "+1-555-0100",
    "address": "123 Main St",
    "picture": "https://..."
  },
  "level": "Bachelor",
  "program": {
    "id": 1,
    "title": "Science",
    "summary": "Science and Mathematics program"
  },
  "enrolled_courses": [
    {
      "id": 10,
      "title": "Mathematics 101",
      "code": "MATH101"
    }
  ]
}
```

### Create Student

**POST** `/api/students/`

**Permission:** Direction or Admin only

**Request:**
```json
{
  "username": "newstudent",
  "email": "student@example.com",
  "password": "SecurePassword123",
  "first_name": "Jane",
  "last_name": "Smith",
  "gender": "F",
  "phone": "+1-555-0200",
  "level": "Bachelor",
  "program": 1
}
```

**Response:** `201 Created`

### Update Student

**PUT/PATCH** `/api/students/{id}/`

**Permission:** Direction or Admin only

**Request:**
```json
{
  "level": "Master",
  "program": 2
}
```

**Response:** `200 OK`

### Delete Student

**DELETE** `/api/students/{id}/`

**Permission:** Admin only

**Response:** `204 No Content`

## Courses

### List Courses

**GET** `/api/courses/`

**Query Parameters:**
- `program` - Filter by program ID
- `level` - Filter by level
- `semester` - Filter by semester
- `is_elective` - Filter elective courses
- `search` - Search by title or code

**Response:** `200 OK`
```json
{
  "count": 50,
  "results": [
    {
      "id": 10,
      "slug": "mathematics-101-science",
      "title": "Mathematics 101",
      "code": "MATH101",
      "credit": 3,
      "summary": "Introduction to Mathematics",
      "program": {
        "id": 1,
        "title": "Science"
      },
      "level": "Bachelor",
      "year": 1,
      "semester": "First",
      "is_elective": false
    }
  ]
}
```

### Get Course Detail

**GET** `/api/courses/{slug}/`

**Response:** `200 OK`
```json
{
  "id": 10,
  "slug": "mathematics-101-science",
  "title": "Mathematics 101",
  "code": "MATH101",
  "credit": 3,
  "summary": "Introduction to Mathematics",
  "program": {
    "id": 1,
    "title": "Science",
    "summary": "Science program"
  },
  "level": "Bachelor",
  "year": 1,
  "semester": "First",
  "is_elective": false,
  "allocated_lecturers": [
    {
      "id": 50,
      "name": "Dr. Smith",
      "email": "smith@example.com"
    }
  ],
  "materials": [
    {
      "id": 5,
      "title": "Lecture Notes - Week 1",
      "file": "https://...",
      "upload_time": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Create Course

**POST** `/api/courses/`

**Permission:** Direction or Admin only

**Request:**
```json
{
  "title": "Physics 101",
  "code": "PHYS101",
  "credit": 4,
  "summary": "Introduction to Physics",
  "program": 1,
  "level": "Bachelor",
  "year": 1,
  "semester": "First",
  "is_elective": false
}
```

**Response:** `201 Created`

### Update Course

**PUT/PATCH** `/api/courses/{slug}/`

**Permission:** Direction or Admin only

**Response:** `200 OK`

### Delete Course

**DELETE** `/api/courses/{slug}/`

**Permission:** Admin only

**Response:** `204 No Content`

### Upload Course Material

**POST** `/api/courses/{slug}/upload-material/`

**Permission:** Lecturer (allocated) or Direction

**Request:** `multipart/form-data`
```
title: "Lecture Notes - Week 2"
file: [binary file data]
```

**Response:** `201 Created`

## Attendance

### List Attendance Records

**GET** `/api/attendance/`

**Query Parameters:**
- `subject` - Filter by subject/course
- `student` - Filter by student ID
- `date` - Filter by date (YYYY-MM-DD)
- `date_from` - Start date
- `date_to` - End date

**Response:** `200 OK`
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "subject": {
        "id": 10,
        "name": "Mathematics 101"
      },
      "date": "2024-12-24",
      "reports": [
        {
          "student": {
            "id": 1,
            "name": "John Doe"
          },
          "status": "present"
        },
        {
          "student": {
            "id": 2,
            "name": "Jane Smith"
          },
          "status": "absent"
        }
      ]
    }
  ]
}
```

### Record Attendance

**POST** `/api/attendance/`

**Permission:** Lecturer or Direction

**Request:**
```json
{
  "subject": 10,
  "date": "2024-12-24",
  "reports": [
    {
      "student": 1,
      "status": "present"
    },
    {
      "student": 2,
      "status": "absent"
    },
    {
      "student": 3,
      "status": "late"
    }
  ]
}
```

**Response:** `201 Created`

### Get Student Attendance

**GET** `/api/attendance/student/{student_id}/`

**Response:** `200 OK`
```json
{
  "student": {
    "id": 1,
    "name": "John Doe"
  },
  "total_sessions": 50,
  "present": 45,
  "absent": 3,
  "late": 2,
  "attendance_percentage": 90.0,
  "records": [
    {
      "date": "2024-12-24",
      "subject": "Mathematics 101",
      "status": "present"
    }
  ]
}
```

## Results

### List Results

**GET** `/api/results/`

**Query Parameters:**
- `student` - Filter by student ID
- `semester` - Filter by semester
- `session` - Filter by academic session

**Response:** `200 OK`

### Get Student Results

**GET** `/api/results/student/{student_id}/`

**Response:** `200 OK`
```json
{
  "student": {
    "id": 1,
    "name": "John Doe"
  },
  "semester": "First",
  "session": "2024/2025",
  "level": "Bachelor",
  "gpa": 3.75,
  "cgpa": 3.68,
  "courses": [
    {
      "course": {
        "title": "Mathematics 101",
        "code": "MATH101",
        "credit": 3
      },
      "assignment": 8.5,
      "mid_exam": 18.0,
      "quiz": 9.0,
      "attendance": 9.5,
      "final_exam": 45.0,
      "total": 90.0,
      "grade": "A+",
      "point": 12.0,
      "comment": "PASS"
    }
  ]
}
```

### Record Grades

**POST** `/api/results/grades/`

**Permission:** Lecturer or Direction

**Request:**
```json
{
  "student": 1,
  "course": 10,
  "assignment": 8.5,
  "mid_exam": 18.0,
  "quiz": 9.0,
  "attendance": 9.5,
  "final_exam": 45.0
}
```

**Response:** `201 Created`

### Generate Report Card (PDF)

**GET** `/api/results/student/{student_id}/report-card/`

**Response:** `200 OK` (PDF file)
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="report_card_john_doe.pdf"
```

## Payments

### List Invoices

**GET** `/api/payments/invoices/`

**Query Parameters:**
- `student` - Filter by student (user ID)
- `payment_complete` - Filter by payment status (true/false)

**Response:** `200 OK`
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "user": {
        "id": 123,
        "name": "John Doe"
      },
      "invoice_code": "INV-20241224-001",
      "total": 1500.00,
      "amount": 1500.00,
      "payment_complete": true,
      "created_at": "2024-12-01T10:00:00Z"
    }
  ]
}
```

### Get Invoice Detail

**GET** `/api/payments/invoices/{id}/`

**Response:** `200 OK`

### Create Invoice

**POST** `/api/payments/invoices/`

**Permission:** Direction or Admin

**Request:**
```json
{
  "user": 123,
  "total": 2000.00,
  "invoice_code": "INV-20241224-002"
}
```

**Response:** `201 Created`

### Record Payment

**POST** `/api/payments/invoices/{id}/pay/`

**Request:**
```json
{
  "amount": 500.00,
  "payment_method": "stripe",
  "transaction_id": "txn_abc123"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "total": 2000.00,
  "amount": 500.00,
  "payment_complete": false,
  "remaining": 1500.00
}
```

## Programs

### List Programs

**GET** `/api/programs/`

**Response:** `200 OK`
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "title": "Science",
      "summary": "Science and Mathematics program",
      "student_count": 45,
      "course_count": 12
    }
  ]
}
```

### Create Program

**POST** `/api/programs/`

**Permission:** Direction or Admin

**Request:**
```json
{
  "title": "Engineering",
  "summary": "Engineering program"
}
```

**Response:** `201 Created`

## Webhooks

### Stripe Payment Webhook

**POST** `/api/webhooks/stripe/`

Receives Stripe payment events for processing.

## Code Examples

### Python (requests)

```python
import requests

# Login
response = requests.post(
    'https://api.example.com/api/token/',
    json={
        'username': 'user@example.com',
        'password': 'password'
    }
)
tokens = response.json()
access_token = tokens['access']

# Make authenticated request
headers = {
    'Authorization': f'Bearer {access_token}'
}

students = requests.get(
    'https://api.example.com/api/students/',
    headers=headers
).json()

print(students)
```

### JavaScript (fetch)

```javascript
// Login
const response = await fetch('https://api.example.com/api/token/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'user@example.com',
    password: 'password'
  })
});

const tokens = await response.json();
const accessToken = tokens.access;

// Make authenticated request
const students = await fetch('https://api.example.com/api/students/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
}).then(res => res.json());

console.log(students);
```

### cURL

```bash
# Login
curl -X POST https://api.example.com/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password"}'

# Use token
curl -X GET https://api.example.com/api/students/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

**API Version:** v1
**Last Updated:** December 24, 2025
**Support:** api-support@rhematek-solutions.com
