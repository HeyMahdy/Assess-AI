# Frontend Developer API Integration Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Authentication](#authentication)
4. [Complete API Reference](#complete-api-reference)
5. [Integration Examples](#integration-examples)
6. [Error Handling](#error-handling)

---

## Project Overview

**AI-Powered Automated Grading System** for teachers to:
- Manage students and assignments
- Upload exam questions (with AI OCR extraction)
- Upload grading rubrics (with AI extraction)
- Upload teacher solutions (with AI extraction)

### Tech Stack
- **Backend**: Node.js + TypeScript + Express (Port 3000)
- **Agent Service**: Python + FastAPI + LangGraph + GPT-4o (Port 8000)
- **Database**: PostgreSQL
- **Authentication**: JWT (Access Token)

---

## Architecture

```
Frontend (React/Vue/etc)
    ↓ HTTP/REST
Backend (Node.js:3000)
    ↓ Internal HTTP
Agent Service (Python:8000)
    ↓
Database (PostgreSQL)
```

**Important**: Frontend only calls Backend. Backend internally calls Agent Service.

---

## Authentication

### Base URL
```
Development: http://localhost:3000
Production: https://your-domain.com
```

### How Authentication Works
1. **Signup/Login** → Receive `access_token`
2. **Store token** securely
3. **Include token** in all protected API calls:
   ```
   Authorization: Bearer <access_token>
   ```


---

## Complete API Reference

### 🔐 1. Authentication APIs

#### POST `/auth/signup`
Create a new user account.

**Request:**
```json
{
  "email": "teacher@example.com",
  "password": "securePassword123",
  "display_name": "Dr. Smith"
}
```

**Field Requirements:**
- `email`: Required, valid email, max 320 characters
- `password`: Required, min 8 characters, max 128 characters
- `display_name`: Optional, max 200 characters

**Success Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "user": {
    "id": "uuid-here",
    "email": "teacher@example.com",
    "display_name": "Dr. Smith"
  }
}
```

**Error Responses:**
- `400`: Invalid email format or password too short
- `409`: Email already registered

---

#### POST `/auth/login`
Login with email and password.

**Request:**
```json
{
  "email": "teacher@example.com",
  "password": "securePassword123"
}
```

**Field Requirements:**
- `email`: Required, valid email
- `password`: Required, min 1 character, max 128 characters

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "user": {
    "id": "uuid-here",
    "email": "teacher@example.com",
    "display_name": "Dr. Smith"
  }
}
```

**Error Responses:**
- `400`: Missing email or password
- `401`: Invalid email or password


---

### 👤 2. User Profile APIs

**All endpoints require:** `Authorization: Bearer <access_token>`

#### GET `/users/me`
Get current user profile.

**Success Response (200):**
```json
{
  "id": "uuid-here",
  "email": "teacher@example.com",
  "display_name": "Dr. Smith",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### PATCH `/users/me`
Update current user profile.

**Request:**
```json
{
  "display_name": "Dr. John Smith"
}
```

**Success Response (200):**
```json
{
  "id": "uuid-here",
  "email": "teacher@example.com",
  "display_name": "Dr. John Smith",
  "created_at": "2024-01-15T10:30:00Z"
}
```


---

### 📝 3. Assignment APIs

**All endpoints require:** `Authorization: Bearer <access_token>`

#### POST `/assignments`
Create a new assignment.

**Request:**
```json
{
  "title": "Midterm Exam",
  "subject": "Computer Science",
  "total_marks": 50
}
```

**Field Requirements:**
- `title`: Required
- `subject`: Required
- `total_marks`: Required, integer

**Success Response (201):**
```json
{
  "assignment_id": 12,
  "message": "Assignment created successfully"
}
```

---

#### GET `/assignments/:assignmentId`
Get assignment details.

**Success Response (200):**
```json
{
  "assignment_id": 12,
  "title": "Midterm Exam",
  "subject": "Computer Science",
  "topic": "Recursion",
  "total_marks": 50
}
```

**Error Responses:**
- `404`: Assignment not found

---

#### PATCH `/assignments/:assignmentId`
Update assignment details.

**Request:**
```json
{
  "title": "Updated Midterm Exam",
  "topic": "Advanced Recursion"
}
```

**Success Response (200):**
```json
{
  "id": 12,
  "title": "Updated Midterm Exam",
  "subject": "Computer Science",
  "topic": "Advanced Recursion",
  "total_marks": 50,
  "teacher_id": "uuid-here",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

#### DELETE `/assignments/:assignmentId`
Delete an assignment.

**Success Response (200):**
```json
{
  "message": "Assignment deleted successfully"
}
```

**Error Responses:**
- `404`: Assignment not found


---

### 🎓 4. Student Management APIs

**All endpoints require:** `Authorization: Bearer <access_token>`

#### POST `/students`
Add a new student.

**Request:**
```json
{
  "id": "2021001",
  "name": "Alice Johnson"
}
```

**Field Requirements:**
- `id`: Required, student ID (string)
- `name`: Required, student name

**Success Response (201):**
```json
{
  "message": "Student added successfully",
  "data": {
    "teacher_id": "uuid-here",
    "id": "2021001",
    "name": "Alice Johnson",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**
- `400`: Missing id or name
- `401`: Unauthorized
- `409`: Student ID already exists for this teacher

---

#### GET `/students`
Get all students for the authenticated teacher.

**Success Response (200):**
```json
{
  "message": "Students retrieved successfully",
  "count": 25,
  "data": [
    {
      "teacher_id": "uuid-here",
      "id": "2021001",
      "name": "Alice Johnson",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "teacher_id": "uuid-here",
      "id": "2021002",
      "name": "Bob Smith",
      "created_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

#### GET `/students/:studentId`
Get a specific student.

**Success Response (200):**
```json
{
  "message": "Student retrieved successfully",
  "data": {
    "teacher_id": "uuid-here",
    "id": "2021001",
    "name": "Alice Johnson",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Error Responses:**
- `404`: Student not found or unauthorized

---

#### PATCH `/students/:studentId`
Update a student's name.

**Request:**
```json
{
  "name": "Alice Marie Johnson"
}
```

**Success Response (200):**
```json
{
  "message": "Student updated successfully",
  "data": {
    "teacher_id": "uuid-here",
    "id": "2021001",
    "name": "Alice Marie Johnson",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

---

#### DELETE `/students/:studentId`
Delete a student.

**Success Response (200):**
```json
{
  "message": "Student deleted successfully",
  "data": {
    "teacher_id": "uuid-here",
    "id": "2021001",
    "name": "Alice Johnson"
  }
}
```


---

### ❓ 5. Question APIs (AI-Powered OCR)

**All endpoints require:** `Authorization: Bearer <access_token>`

#### POST `/assignments/:assignmentId/questions/upload`
Upload exam question papers and extract questions using AI.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `files`: File[] (up to 10 images or PDFs)
- `is_handwritten`: string ("true" or "false")

**Example using JavaScript Fetch:**
```javascript
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);
formData.append('is_handwritten', 'false');

fetch('/assignments/12/questions/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`
  },
  body: formData
});
```

**Success Response (200):**
```json
{
  "message": "Questions processed successfully",
  "data": "{\"questions\": [{\"question_label\": \"1a\", \"question_description\": \"Explain recursion...\"}]}"
}
```

**Error Responses:**
- `400`: No files uploaded
- `401`: Unauthorized
- `500`: Failed to process question document

---

#### GET `/assignments/:assignmentId/questions`
Get all questions for an assignment.

**Success Response (200):**
```json
{
  "message": "Questions retrieved successfully",
  "count": 5,
  "data": [
    {
      "id": 1,
      "question_label": "1a",
      "question_description": "Explain the concept of recursion with an example.",
      "marks": 5,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "question_label": "1b",
      "question_description": "Write a recursive function for factorial.",
      "marks": 10,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### PATCH `/assignments/:questionId/questions`
Update a question.

**Request (all fields optional):**
```json
{
  "question_label": "1a (updated)",
  "question_description": "Explain recursion with TWO examples.",
  "marks": 7
}
```

**Success Response (200):**
```json
{
  "message": "Question updated successfully",
  "data": {
    "id": 1,
    "question_label": "1a (updated)",
    "question_description": "Explain recursion with TWO examples.",
    "marks": 7,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```


---

### 📋 6. Rubrics APIs (AI-Powered OCR)

**All endpoints require:** `Authorization: Bearer <access_token>`

#### POST `/assignments/:assignmentId/rubrics/upload`
Upload grading rubrics and extract criteria using AI.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `files`: File[] (up to 10 images or PDFs)
- `is_handwritten`: string ("true" or "false")

**Success Response (200):**
```json
{
  "message": "Rubrics processed successfully",
  "data": "{\"rubrics\": [{\"question_label\": \"1a\", \"rubric_description\": {...}}]}"
}
```

---

#### GET `/assignments/:assignmentId/rubrics`
Get all rubrics for an assignment.

**Success Response (200):**
```json
{
  "message": "Rubrics retrieved successfully",
  "count": 5,
  "data": [
    {
      "id": 1,
      "question_label": "1a",
      "rubric_description": {
        "criteria": [
          {"points": 2, "description": "Correct definition"},
          {"points": 2, "description": "Valid example"}
        ],
        "penalties": [
          {"deduction": -1, "condition": "Missing base case"}
        ],
        "fatal_flaw": "Completely incorrect concept"
      },
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### PATCH `/assignments/:rubricId/rubrics`
Update a rubric.

**Request (all fields optional):**
```json
{
  "question_label": "1a (updated)",
  "rubric_description": {
    "criteria": [
      {"points": 3, "description": "Excellent definition"}
    ],
    "penalties": [],
    "fatal_flaw": null
  }
}
```

**Success Response (200):**
```json
{
  "message": "Rubric updated successfully",
  "data": {
    "id": 1,
    "question_label": "1a (updated)",
    "rubric_description": {...},
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```


---

### ✅ 7. Teacher Solutions APIs (AI-Powered OCR)

**All endpoints require:** `Authorization: Bearer <access_token>`

#### POST `/assignments/:assignmentId/solutions/upload`
Upload teacher solution documents and extract solutions using AI.

**Headers:**
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Form Data:**
- `files`: File[] (up to 10 images or PDFs)
- `is_handwritten`: string ("true" or "false")

**Success Response (200):**
```json
{
  "message": "Solutions processed successfully",
  "data": "{\"solutions\": [{\"question_label\": \"1a\", \"solution_text\": \"Recursion is...\"}]}"
}
```

---

#### GET `/assignments/:assignmentId/solutions`
Get all teacher solutions for an assignment.

**Success Response (200):**
```json
{
  "message": "Solutions retrieved successfully",
  "count": 5,
  "data": [
    {
      "id": 1,
      "question_label": "1a",
      "solution_text": "Recursion is a programming technique where a function calls itself...",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

#### PATCH `/assignments/:solutionId/solutions`
Update a teacher solution.

**Request (all fields optional):**
```json
{
  "question_label": "1a (updated)",
  "solution_text": "Updated solution text..."
}
```

**Success Response (200):**
```json
{
  "message": "Solution updated successfully",
  "data": {
    "id": 1,
    "question_label": "1a (updated)",
    "solution_text": "Updated solution text...",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```


---

## Integration Examples

### Example 1: User Signup and Login

```javascript
// Signup
const signupResponse = await fetch('http://localhost:3000/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'teacher@example.com',
    password: 'securePassword123',
    display_name: 'Dr. Smith'
  })
});

const { access_token, user } = await signupResponse.json();
localStorage.setItem('access_token', access_token);

// Login
const loginResponse = await fetch('http://localhost:3000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'teacher@example.com',
    password: 'securePassword123'
  })
});

const { access_token, user } = await loginResponse.json();
localStorage.setItem('access_token', access_token);
```

---

### Example 2: Complete Assignment Setup

```javascript
const token = localStorage.getItem('access_token');

// 1. Create Assignment
const assignmentRes = await fetch('http://localhost:3000/assignments', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'Midterm Exam',
    subject: 'Computer Science',
    total_marks: 50
  })
});
const { assignment_id } = await assignmentRes.json();

// 2. Upload Questions
const questionFormData = new FormData();
questionFormData.append('files', questionFile);
questionFormData.append('is_handwritten', 'false');

await fetch(`http://localhost:3000/assignments/${assignment_id}/questions/upload`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: questionFormData
});

// 3. Upload Rubrics
const rubricFormData = new FormData();
rubricFormData.append('files', rubricFile);
rubricFormData.append('is_handwritten', 'false');

await fetch(`http://localhost:3000/assignments/${assignment_id}/rubrics/upload`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: rubricFormData
});

// 4. Upload Solutions
const solutionFormData = new FormData();
solutionFormData.append('files', solutionFile);
solutionFormData.append('is_handwritten', 'false');

await fetch(`http://localhost:3000/assignments/${assignment_id}/solutions/upload`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: solutionFormData
});
```

---

### Example 3: Student Management

```javascript
const token = localStorage.getItem('access_token');

// Add Student
await fetch('http://localhost:3000/students', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    id: '2021001',
    name: 'Alice Johnson'
  })
});

// Get All Students
const studentsRes = await fetch('http://localhost:3000/students', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { data: students } = await studentsRes.json();

// Update Student
await fetch('http://localhost:3000/students/2021001', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ name: 'Alice Marie Johnson' })
});

// Delete Student
await fetch('http://localhost:3000/students/2021001', {
  method: 'DELETE',
  headers: { 'Authorization': `Bearer ${token}` }
});
```


---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "Error message",
  "details": "Additional details (optional)"
}
```

### Common HTTP Status Codes

| Code | Meaning | When It Happens |
|------|---------|-----------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid data or missing required fields |
| 401 | Unauthorized | Missing or invalid access token |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., email/student ID exists) |
| 500 | Internal Server Error | Server or database error |

### Error Handling Example

```javascript
async function apiCall(url, options) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Token expired - redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
          break;
        case 409:
          // Conflict (duplicate)
          alert(`Error: ${error.error}`);
          break;
        case 400:
          // Validation error
          alert(`Validation Error: ${error.error}`);
          break;
        default:
          console.error('API Error:', error);
          alert('An error occurred. Please try again.');
      }
      return null;
    }
    
    return await response.json();
    
  } catch (err) {
    console.error('Network error:', err);
    alert('Network error. Please check your connection.');
    return null;
  }
}

// Usage
const result = await apiCall('http://localhost:3000/students', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ id: '2021001', name: 'Alice' })
});
```

---

## Quick Reference: All Endpoints

### Authentication
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login

### User Profile
- `GET /users/me` - Get profile
- `PATCH /users/me` - Update profile

### Students
- `POST /students` - Add student
- `GET /students` - Get all students
- `GET /students/:studentId` - Get student
- `PATCH /students/:studentId` - Update student
- `DELETE /students/:studentId` - Delete student

### Assignments
- `POST /assignments` - Create assignment
- `GET /assignments/:assignmentId` - Get assignment
- `PATCH /assignments/:assignmentId` - Update assignment
- `DELETE /assignments/:assignmentId` - Delete assignment

### Questions (AI OCR)
- `POST /assignments/:assignmentId/questions/upload` - Upload & extract
- `GET /assignments/:assignmentId/questions` - Get questions
- `PATCH /assignments/:questionId/questions` - Update question

### Rubrics (AI OCR)
- `POST /assignments/:assignmentId/rubrics/upload` - Upload & extract
- `GET /assignments/:assignmentId/rubrics` - Get rubrics
- `PATCH /assignments/:rubricId/rubrics` - Update rubric

### Teacher Solutions (AI OCR)
- `POST /assignments/:assignmentId/solutions/upload` - Upload & extract
- `GET /assignments/:assignmentId/solutions` - Get solutions
- `PATCH /assignments/:solutionId/solutions` - Update solution

---

## Important Notes

1. **Authentication**: All endpoints except `/auth/*` require `Authorization: Bearer <token>`
2. **File Uploads**: Use `multipart/form-data` with `FormData` object
3. **AI Processing**: Upload endpoints may take 5-30 seconds
4. **File Limits**: Maximum 10 files per upload
5. **Supported Formats**: Images (JPG, PNG) and PDFs
6. **Token Storage**: Store `access_token` securely (localStorage/sessionStorage)
7. **Base URL**: `http://localhost:3000` (development)

---

## Database Schema Reference

### Users Table
- `id`: UUID (primary key)
- `email`: String (unique)
- `display_name`: String (nullable)
- `password_hash`: String
- `created_at`: Timestamp

### Students Table
- `teacher_id`: UUID (foreign key to users)
- `id`: String (student ID)
- `name`: String
- `created_at`: Timestamp
- **Primary Key**: (teacher_id, id)

### Assignments Table
- `id`: Integer (primary key)
- `teacher_id`: UUID (foreign key)
- `title`: String
- `subject`: String
- `topic`: String (nullable)
- `total_marks`: Integer
- `created_at`: Timestamp

### Questions Table
- `id`: Integer (primary key)
- `teacher_id`: UUID (foreign key)
- `assignment_id`: Integer (foreign key)
- `question_label`: String
- `question_description`: Text
- `marks`: Integer (nullable)
- `created_at`: Timestamp

### Rubrics Table
- `id`: Integer (primary key)
- `teacher_id`: UUID (foreign key)
- `assignment_id`: Integer (foreign key)
- `question_label`: String
- `rubric_description`: JSONB
- `created_at`: Timestamp

### Teacher Solutions Table
- `id`: Integer (primary key)
- `teacher_id`: UUID (foreign key)
- `assignment_id`: Integer (foreign key)
- `question_label`: String
- `solution_text`: Text
- `created_at`: Timestamp

---

## Support

For issues:
- Check error messages in API responses
- Verify token is included in headers
- Ensure request body matches expected format
- Check browser DevTools Network tab

**Backend Port**: 3000 (default)
**Agent Service**: 8000 (internal only - don't call directly)
