# Assess-AI

[![Node.js](https://img.shields.io/badge/Node.js-%3E%3D20.6.0-339933?logo=node.js&logoColor=white)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.12.3-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Agent_Service-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](#license)

Assess-AI is an AI-assisted assessment platform for educators. It extracts questions, rubrics, teacher solutions, and student answers from uploaded documents, stores structured assessment data, and uses multi-agent grading workflows to produce scores, confidence signals, feedback, and remediation insights.

The repository currently contains two services:

- `backend/`: an Express + TypeScript REST API for authentication, assignments, students, uploads, grading, analytics, and OpenAPI documentation.
- `agent/`: a FastAPI + LangGraph service for OCR/document processing, AI extraction, GraphRAG syllabus ingestion, TA chat, and grading workflows.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Services](#running-the-services)
- [API Documentation](#api-documentation)
- [Core Workflows](#core-workflows)
- [Development Commands](#development-commands)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## Features

- Email/password authentication with local JWT access tokens.
- Teacher-scoped assignment, student, question, rubric, solution, and student answer APIs.
- Multipart upload endpoints for PDF, image, DOCX, and text-based assessment documents.
- LangGraph-powered extraction agents for:
  - assignment questions
  - rubrics
  - teacher solutions
  - student answers
- AI grading workflow that compares student answers against rubrics and teacher solutions.
- Score storage with confidence metadata and teacher comments.
- Syllabus GraphRAG ingestion for prerequisite graphs, topic lookup, and contextual TA support.
- TA chat endpoints that can use syllabus/context data to answer teacher questions.
- OpenAPI documentation served by the backend at `/api-docs`.
- Jest test suite for backend controllers and health checks.

## Architecture

```text
Client / Frontend
       |
       v
Express + TypeScript API (backend/)
       |
       |-- PostgreSQL / Supabase-compatible database
       |-- Upstash Redis client
       |
       v
FastAPI + LangGraph Agent Service (agent/)
       |
       |-- OpenAI / LangChain model calls
       |-- document parsing and OCR helpers
       |-- GraphRAG syllabus pipeline
       |-- PostgreSQL writes through agent tools
```

The backend exposes the public API. For AI-assisted document processing it forwards internal requests to the agent service running at `http://localhost:8000`. The agent service performs extraction, grading, syllabus ingestion, and TA chat responses, then returns structured results to the backend.

## Project Structure

```text
.
|-- backend/
|   |-- src/
|   |   |-- common/          # middleware, errors, request handling
|   |   |-- config/          # env and OpenAPI configuration
|   |   |-- controllers/     # route handlers
|   |   |-- docs/            # OpenAPI path definitions
|   |   |-- lib/             # database, JWT, logger, Redis clients
|   |   |-- routes/          # Express routers
|   |   |-- schemas/         # validation schemas
|   |   |-- services/        # auth/user business logic
|   |   `-- types/           # shared TypeScript types
|   |-- supabase/migrations/ # database migrations
|   `-- test/                # Jest tests
|-- agent/
|   |-- api/service/         # Textract and file parsing service helpers
|   |-- config/              # database connection helpers
|   |-- utils/               # LangGraph agents and GraphRAG pipeline
|   |-- main.py              # FastAPI app and internal agent endpoints
|   |-- pyproject.toml       # Python package metadata
|   `-- seed_data.sql        # local schema/seed helper
|-- AGENT_ARCHITECTURE.md    # agent redesign notes
|-- FRONTEND_API_GUIDE.md    # frontend integration reference
|-- PRODUCTION_ROADMAP.md    # production hardening roadmap
`-- api.md                   # additional API notes
```

## Tech Stack

**Backend**

- Node.js 20.6+
- Express 4
- TypeScript 5
- PostgreSQL via `pg`
- JWT authentication with `jsonwebtoken`
- Swagger UI / OpenAPI
- Jest, Supertest, ESLint, Prettier

**Agent service**

- Python 3.12.3+
- FastAPI
- LangGraph
- LangChain
- OpenAI Python SDK
- PostgreSQL via `psycopg2`
- Supabase client
- PDF/DOCX/image parsing utilities
- Optional AWS Textract integration

## Prerequisites

Install the following before running the project locally:

- Node.js `>=20.6.0`
- npm
- Python `>=3.12.3`
- PostgreSQL database, or a Supabase project with a PostgreSQL connection string
- OpenAI API key for the agent workflows
- Upstash Redis credentials if you use Redis-backed features
- AWS credentials if you enable Textract-backed OCR paths

## Quick Start

Clone the repository:

```bash
git clone https://github.com/HeyMahdy/Assess-AI.git
cd Assess-AI
```

Install backend dependencies:

```bash
cd backend
npm install
```

Create `backend/.env`:

```bash
NODE_ENV=development
PORT=8080
DATABASE_URL=postgresql://postgres:password@localhost:5432/assess_ai
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=assess_ai
DATABASE_USER=postgres
DATABASE_PASSWORD=password
UPSTASH_REDIS_REST_URL=https://example.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-upstash-token
JWT_SECRET=replace-with-a-long-random-secret
JWT_EXPIRES_IN=7d
```

Install agent dependencies:

```bash
cd ../agent
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Create `agent/.env`:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/assess_ai
OPENAI_API_KEY=your-openai-api-key
TA_AGENT_MODEL=gpt-5.1
GRAPHRAG_ENTITY_CONCURRENCY=4
AWS_ACCESS_KEY_ID=optional-aws-access-key
AWS_SECRET_ACCESS_KEY=optional-aws-secret-key
```

Start both services in separate terminals:

```bash
# Terminal 1
cd backend
npm run dev
```

```bash
# Terminal 2
cd agent
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- Backend API: `http://localhost:8080`
- API docs: `http://localhost:8080/api-docs`
- Health check: `http://localhost:8080/health`
- Agent service: `http://localhost:8000`

## Environment Variables

### Backend

| Name | Required | Description |
| --- | --- | --- |
| `NODE_ENV` | No | `development`, `test`, or `production`. Defaults to `development`. |
| `PORT` | No | Configured API port. The current server binds to `8080`. |
| `DATABASE_URL` | Yes | PostgreSQL connection string used by the backend pool. |
| `DATABASE_HOST` | No | Database host, kept for tooling compatibility. |
| `DATABASE_PORT` | No | Database port, kept for tooling compatibility. |
| `DATABASE_NAME` | No | Database name, kept for tooling compatibility. |
| `DATABASE_USER` | No | Database user, kept for tooling compatibility. |
| `DATABASE_PASSWORD` | No | Database password, kept for tooling compatibility. |
| `UPSTASH_REDIS_REST_URL` | Yes | Upstash Redis REST URL. |
| `UPSTASH_REDIS_REST_TOKEN` | Yes | Upstash Redis REST token. |
| `JWT_SECRET` | Yes | Secret used to sign and verify API JWTs. |
| `JWT_EXPIRES_IN` | No | JWT lifetime. Defaults to `7d`. |

### Agent

| Name | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL connection string used by the agent tools. |
| `OPENAI_API_KEY` | Yes | OpenAI API key used by LangChain/OpenAI model calls. |
| `TA_AGENT_MODEL` | No | Model name for the TA chat agent. Defaults to `gpt-5.1` in code. |
| `GRAPHRAG_ENTITY_CONCURRENCY` | No | GraphRAG entity extraction concurrency. Defaults to `4`. |
| `AWS_ACCESS_KEY_ID` | No | AWS access key for Textract usage. |
| `AWS_SECRET_ACCESS_KEY` | No | AWS secret key for Textract usage. |

Do not commit real `.env` files. Keep secrets local or in your deployment platform's secret manager.

## Database Setup

Assess-AI expects a PostgreSQL-compatible database. The repository includes SQL helpers in two places:

- `backend/supabase/migrations/`: incremental Supabase/PostgreSQL migrations.
- `agent/seed_data.sql`: local reset/seed script for the agent-oriented schema.

For local development, create a database and apply the schema that matches your workflow. If you use Supabase, apply the migrations in `backend/supabase/migrations/` through the Supabase CLI or dashboard SQL editor.

Core tables include:

- users/profiles/roles
- students
- assignments
- questions
- rubrics
- teacher solutions
- student answers
- grading jobs and scores
- syllabus and GraphRAG knowledge tables
- remediation and weak concept tables

## Running the Services

### Backend API

```bash
cd backend
npm run dev
```

The backend uses `node --env-file=.env --import tsx --watch src/server.ts` in development and currently listens on `8080`.

Build and start compiled JavaScript:

```bash
cd backend
npm run build
npm start
```

### Agent Service

```bash
cd agent
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend controllers currently call the agent service at `http://localhost:8000`.

## API Documentation

When the backend is running, Swagger UI is available at:

```text
http://localhost:8080/api-docs
```

The frontend integration guide in `FRONTEND_API_GUIDE.md` contains endpoint examples and response shapes.

Common public API areas:

| Area | Example endpoints |
| --- | --- |
| Auth | `POST /auth/signup`, `POST /auth/login` |
| Users | `GET /users/me`, `PATCH /users/me` |
| Students | `GET /students`, `POST /students`, `PATCH /students/:studentId` |
| Assignments | `POST /assignments`, `GET /assignments/:assignmentId` |
| Questions | `POST /assignments/:assignmentId/questions/upload`, `GET /assignments/:assignmentId/questions` |
| Rubrics | `POST /assignments/:assignmentId/rubrics/upload`, `GET /assignments/:assignmentId/rubrics` |
| Solutions | `POST /assignments/:assignmentId/solutions/upload`, `GET /assignments/:assignmentId/solutions` |
| Student answers | `POST /assignments/:assignmentId/students/:studentId/answers/upload` |
| Grading | `POST /assignments/:assignmentId/students/:studentId/grade` |
| Syllabus | `POST /syllabus/upload`, `POST /syllabus/query` |
| TA chat | TA chat routes documented in the OpenAPI setup |

Protected routes require:

```text
Authorization: Bearer <access_token>
```

## Core Workflows

### 1. Assignment setup

1. A teacher signs up or logs in through the backend API.
2. The teacher creates an assignment.
3. The teacher uploads question documents, rubrics, and teacher solutions.
4. The backend forwards upload payloads to the FastAPI agent service.
5. The agent extracts structured data and saves it through database tools.

### 2. Student answer processing

1. A teacher creates or imports students.
2. Student answer sheets are uploaded for an assignment.
3. The backend forwards the files to `/internal/agent/student-answers/process`.
4. The agent extracts answers by question label and stores them in the database.

### 3. AI grading

1. The backend calls `/internal/agent/grade/process` with `teacher_id`, `student_id`, and `assignment_id`.
2. The grading agent loads rubrics, teacher solutions, and student answers.
3. The workflow produces per-question scores, confidence values, and feedback.
4. The backend exposes results through score endpoints.

### 4. Syllabus GraphRAG

1. A teacher uploads a syllabus.
2. The agent extracts text and runs a background ingestion pipeline.
3. Concepts and relationships are stored as a graph.
4. Teachers can query prerequisites, related topics, and learning context.

### 5. TA chat

The TA chat workflow uses teacher context and syllabus data to respond to study-plan or prerequisite questions. Backend controllers forward messages to the agent service.

## Development Commands

### Backend

| Command | Description |
| --- | --- |
| `npm run dev` | Run the API in watch mode with `.env` loaded. |
| `npm run build` | Compile TypeScript to `dist/`. |
| `npm start` | Run the compiled server. |
| `npm test` | Run Jest tests. |
| `npm run test:watch` | Run Jest in watch mode. |
| `npm run lint` | Run ESLint. |
| `npm run lint:fix` | Fix lint issues where possible. |
| `npm run format` | Format files with Prettier. |
| `npm run format:check` | Check formatting. |
| `npm run seed:roles` | Seed default role records. |

### Agent

The agent currently does not define package scripts. Use standard Python tooling:

```bash
cd agent
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

## Testing

Run backend tests:

```bash
cd backend
npm test
```

The Jest setup injects test environment variables from `backend/test/setupEnv.cjs`. Tests are located in `backend/test/`.

Recommended checks before opening a pull request:

```bash
cd backend
npm run lint
npm run format:check
npm test
npm run build
```

## Troubleshooting

### Backend starts but upload routes fail

Make sure the agent service is running on `http://localhost:8000`. Several backend controllers call that URL directly.

### `JWT secret is not configured`

Set `JWT_SECRET` in `backend/.env` to a long random value.

### Database connection errors

Verify `DATABASE_URL` in both `backend/.env` and `agent/.env`. Both services need access to the same PostgreSQL database.

### Agent import errors

Run the agent from the `agent/` directory so imports like `api.service.Textract_service` and `utils.*` resolve correctly.

### OCR or LLM calls fail

Confirm `OPENAI_API_KEY` is present in `agent/.env`. If you use AWS Textract features, also configure AWS credentials.

### Swagger docs are missing a route

Route behavior lives in `backend/src/routes/` and `backend/src/controllers/`; OpenAPI path definitions live separately in `backend/src/docs/`. Update both when adding new public endpoints.

## Contributing

Contributions are welcome. To keep changes easy to review:

1. Fork the repository and create a focused feature branch.
2. Install dependencies for the service you are changing.
3. Add or update tests for behavior changes.
4. Run linting, formatting checks, tests, and builds.
5. Update documentation when endpoints, environment variables, or workflows change.
6. Open a pull request with a clear description of the problem and solution.

Suggested branch names:

```text
feature/add-assignment-analytics
fix/student-answer-upload-validation
docs/update-agent-setup
```

## Security

- Never commit `.env` files, API keys, database credentials, JWT secrets, or service-role tokens.
- Treat uploaded assessment files as sensitive student data.
- Use HTTPS, secure secret storage, request size limits, and strict CORS settings in production.
- Review `PRODUCTION_ROADMAP.md` before deploying publicly.

If you discover a security issue, please avoid opening a public issue with exploit details. Contact the maintainers privately or open a minimal advisory request.

## Roadmap

See `PRODUCTION_ROADMAP.md` and `AGENT_ARCHITECTURE.md` for planned production hardening and agent-layer refactoring notes.

Likely next improvements include:

- centralizing agent configuration
- replacing hard-coded internal service URLs with environment variables
- adding `.env.example` files
- expanding integration tests across backend-agent boundaries
- adding a root `LICENSE` file
- containerizing local development with Docker Compose

## License

This project currently declares the ISC license in `backend/package.json`. If you publish or redistribute the repository, add a root `LICENSE` file containing the complete license text.
