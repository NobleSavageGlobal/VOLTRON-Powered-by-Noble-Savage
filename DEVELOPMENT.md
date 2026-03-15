# VOLTRON / BBA Command OS — Developer Guide

> **Entrepreneur Command OS** — a full-stack platform for BBA Services, powered by Noble Savage.  
> FastAPI backend · Next.js 15 frontend · SQLite (dev) / PostgreSQL (prod)

---

## Table of Contents

- [Quick Start (Local — no Docker)](#quick-start-local--no-docker)
- [Docker Compose Setup](#docker-compose-setup)
- [Project Structure](#project-structure)
- [Backend Reference](#backend-reference)
- [Frontend Reference](#frontend-reference)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Environment Variables](#environment-variables)
- [Useful Commands Cheatsheet](#useful-commands-cheatsheet)
- [Troubleshooting](#troubleshooting)

---

## Quick Start (Local — no Docker)

The fastest way to run everything locally uses **SQLite** (no Postgres required).

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| npm | 9+ |

### 1 — Clone and enter the repo

```bash
git clone https://github.com/noblesavage561/VOLTRON-Powered-by-Noble-Savage.git
cd VOLTRON-Powered-by-Noble-Savage
```

### 2 — Set up the backend

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Create your local .env (SQLite — no Postgres needed)
cp .env.example .env
```

Edit `backend/.env` — the defaults work out of the box for local dev:

```env
DATABASE_URL=sqlite+aiosqlite:///./dev.db
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
CORS_ORIGINS=["http://localhost:3000"]
ENVIRONMENT=development
DEBUG=true
STORAGE_BACKEND=local
LOCAL_STORAGE_PATH=./storage
OPENAI_API_KEY=            # optional — leave blank to skip AI analysis
```

Start the backend:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The database tables are created automatically on first startup (SQLite file: `backend/dev.db`).

✅ Health check: http://localhost:8000/health  
✅ Interactive API docs: http://localhost:8000/api/docs

### 3 — Set up the frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Create your local .env
cp .env.local.example .env.local
# .env.local contains: NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the dev server (hot-reload)
npm run dev
```

✅ App: http://localhost:3000

### 4 — Create your account

Open http://localhost:3000/register and fill in:
- **Full name** — your name
- **Email** — any valid email (no verification in dev)
- **Password** — minimum 8 characters
- **Organization name** — your firm name (optional)

You'll be redirected straight to the Command Center dashboard.

---

## Docker Compose Setup

For a production-like environment with PostgreSQL and Redis:

```bash
# Copy root env
cp .env.example .env
# Edit .env — set a strong SECRET_KEY at minimum

# Build and start all services
docker compose up --build

# Stop
docker compose down

# Wipe volumes (start fresh)
docker compose down -v
```

Services started:

| Service | Port | Description |
|---------|------|-------------|
| postgres | 5432 | PostgreSQL 15 database |
| redis | 6379 | Redis 7 cache/queue |
| backend | 8000 | FastAPI API server |
| frontend | 3000 | Next.js production build |

---

## Project Structure

```
VOLTRON-Powered-by-Noble-Savage/
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/v1/              # Route handlers (11 routers)
│   │   │   ├── auth.py          # Register, login, refresh, logout
│   │   │   ├── clients.py       # Client CRUD
│   │   │   ├── documents.py     # Upload, list, reprocess
│   │   │   ├── tasks.py         # Task management
│   │   │   ├── financial.py     # Connections, transactions, rollups
│   │   │   ├── credit.py        # Credit reports, disputes, letters
│   │   │   ├── plans.py         # Decision plans & scoring
│   │   │   ├── automations.py   # Workflow engine
│   │   │   ├── knowledge.py     # Document search & chunks
│   │   │   ├── organizations.py # Org settings & members
│   │   │   └── audit.py         # Audit log
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # Business logic layer
│   │   │   ├── ai_service.py    # OpenAI document analysis
│   │   │   ├── document_service.py
│   │   │   ├── financial_service.py
│   │   │   ├── credit_service.py
│   │   │   ├── decision_service.py
│   │   │   ├── automation_service.py
│   │   │   └── knowledge_service.py
│   │   ├── core/                # Auth, security, exceptions, logging
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   └── main.py              # FastAPI app entry point
│   ├── tests/                   # Pytest test suite
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── .env.example
│
├── frontend/                    # Next.js 15 application
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   │   ├── (auth)/          # login, register
│   │   │   └── (dashboard)/     # All protected pages
│   │   │       ├── dashboard/
│   │   │       ├── clients/
│   │   │       ├── documents/
│   │   │       ├── tasks/
│   │   │       ├── knowledge/
│   │   │       ├── automations/
│   │   │       ├── audit/
│   │   │       └── settings/
│   │   ├── components/
│   │   │   ├── layout/          # Sidebar, Header
│   │   │   ├── dashboard/       # StatsCard, QuickActions
│   │   │   └── ui/              # Button, Card, Badge, Input, Modal, Spinner
│   │   ├── hooks/               # React Query hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useClients.ts
│   │   │   ├── useDocuments.ts
│   │   │   └── useTasks.ts
│   │   └── lib/
│   │       ├── api.ts           # Axios client + all API calls
│   │       └── types.ts         # TypeScript interfaces
│   ├── .env.local.example
│   └── package.json
│
├── docker-compose.yml           # Full stack with Postgres + Redis
├── .env.example                 # Root env for docker-compose
└── DEVELOPMENT.md               # This file
```

---

## Backend Reference

### Key commands

```bash
cd backend
source .venv/bin/activate

# Start with auto-reload
uvicorn app.main:app --reload --port 8000

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_clients.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

### Database

- **Development**: SQLite (`backend/dev.db`) — auto-created on startup, no setup needed
- **Production**: PostgreSQL via `DATABASE_URL=postgresql+asyncpg://...`
- **Test**: File-based SQLite via `DATABASE_URL=sqlite+aiosqlite:///./test.db` (created fresh for each test run)

Tables are created via `init_db()` in `app.database` — called automatically when `ENVIRONMENT=development`. For production, use Alembic migrations.

### Authentication flow

```
POST /api/v1/auth/register  →  creates User + Organization, returns user data
POST /api/v1/auth/login     →  returns { access_token, refresh_token }
POST /api/v1/auth/refresh   →  rotates tokens
GET  /api/v1/auth/me        →  returns current user (requires Bearer token)
```

All protected endpoints require `Authorization: Bearer <access_token>` header.

### Document processing

When a file is uploaded (`POST /api/v1/documents/upload`):
1. File is saved to `LOCAL_STORAGE_PATH` (or S3 if configured)
2. Document type is guessed from the filename
3. If `OPENAI_API_KEY` is set → full AI analysis (summary, risks, key dates, extracted data)
4. If no API key → document is marked processed with placeholder values (50% confidence)

---

## Frontend Reference

### Key commands

```bash
cd frontend

npm run dev      # Dev server with hot-reload (port 3000)
npm run build    # Production build
npm run start    # Serve the production build
npm run lint     # ESLint check
```

### Adding a new page

1. Create `src/app/(dashboard)/your-page/page.tsx`
2. Add a nav link in `src/components/layout/Sidebar.tsx`
3. Add the API call in `src/lib/api.ts`
4. Create a React Query hook in `src/hooks/useYourPage.ts`

### UI component reference

| Component | Usage |
|-----------|-------|
| `<Button variant="primary\|secondary\|danger\|ghost" size="sm\|md\|lg">` | All buttons |
| `<Card className="p-5">` | Card containers |
| `<Badge label="active" colorClass="bg-emerald-500/20 text-emerald-400">` | Status badges |
| `<Input label="Name" error={errors.name?.message}>` | Form inputs |
| `<Modal isOpen={bool} onClose={fn} title="Title">` | All modals/dialogs |
| `<Spinner>` | Loading states |

> ⚠️ **Badge** uses `label` prop (not `children`). See `src/components/ui/Badge.tsx`.

---

## Running Tests

```bash
cd backend

# Full test suite (24 tests)
pytest tests/ -v --tb=short

# Individual suites
pytest tests/test_auth.py -v          # 6 tests — register, login, tokens
pytest tests/test_clients.py -v       # 7 tests — CRUD, auth guard, status filter
pytest tests/test_documents.py -v     # 4 tests — upload, list, get, auth guard
pytest tests/test_organizations.py -v # 4 tests — get, update (admin), members
pytest tests/test_tasks.py -v         # 3 tests — create, list, update
```

All tests run against a fresh SQLite database — no Postgres or Redis needed.

---

## API Documentation

With the backend running, visit:

- **Swagger UI** (interactive): http://localhost:8000/api/docs
- **ReDoc** (readable): http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

All 11 route groups appear in the sidebar. You can authorize with a Bearer token directly in Swagger UI.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./dev.db` | Database connection string |
| `SECRET_KEY` | *(required)* | JWT signing secret — minimum 32 chars |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token TTL |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins (JSON array) |
| `OPENAI_API_KEY` | *(empty)* | OpenAI key — leave blank to skip AI |
| `OPENAI_MODEL` | `gpt-4o` | Model for document analysis |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |
| `LOCAL_STORAGE_PATH` | `./storage` | Directory for uploaded files |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file upload size |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DEBUG` | `true` | Enables SQL echo logging |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

---

## Useful Commands Cheatsheet

```bash
# ── BACKEND ──────────────────────────────────────────────
cd backend && source .venv/bin/activate

uvicorn app.main:app --reload            # Start API (dev)
pytest tests/ -v                         # Run all tests
curl http://localhost:8000/health        # Health check

# ── FRONTEND ─────────────────────────────────────────────
cd frontend

npm run dev                              # Start UI (dev, port 3000)
npm run build && npm run start           # Build + serve production
npm run lint                             # Check for ESLint errors

# ── DOCKER ───────────────────────────────────────────────
docker compose up --build                # Full stack (Postgres + Redis)
docker compose down -v                   # Stop and wipe volumes

# ── API QUICK TEST ────────────────────────────────────────
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Test1234!","full_name":"Your Name","org_name":"My Company"}'

# Login (save the token)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"Test1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create a client
curl -X POST http://localhost:8000/api/v1/clients/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Acme Corp","entity_type":"business","industry":"Technology"}'

# List documents
curl http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### `CORS_ORIGINS` parse error on startup

The value must be a **JSON array**, not a comma-separated string:

```env
# ✅ Correct
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# ❌ Wrong
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### `pool_size` error with SQLite

SQLite doesn't support connection pooling. The `database.py` automatically detects SQLite and omits pool parameters — no action needed as long as your `DATABASE_URL` starts with `sqlite`.

### Port 8000 or 3000 already in use

```bash
# Find and kill the process on a port (Linux/macOS)
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Frontend can't reach backend (`Network Error`)

1. Confirm backend is running: `curl http://localhost:8000/health`
2. Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. Restart the frontend dev server after changing `.env.local`

### `ModuleNotFoundError` in backend

Make sure your virtual environment is activated:

```bash
source backend/.venv/bin/activate
```

### AI analysis shows "no API key configured"

This is normal without an OpenAI key. Documents will still upload, classify by filename, and be marked as processed — just without AI-powered summaries and risk extraction. Add your key to `.env` when ready:

```env
OPENAI_API_KEY=sk-...
```
