# VOLTRON — BBA Command OS
### Entrepreneur Command OS · Powered by Noble Savage

A full-stack business intelligence and document management platform for entrepreneurs and advisors.

| Layer | Stack |
|-------|-------|
| Frontend | Next.js 15 · TypeScript · Tailwind CSS · React Query |
| Backend | FastAPI · SQLAlchemy · Pydantic v2 · JWT auth |
| Database | SQLite (dev) · PostgreSQL (prod) |
| AI | OpenAI GPT-4o (document analysis — optional) |
| Storage | Local filesystem (dev) · AWS S3 (prod) |

---

## ✨ Features

- **Dashboard** — live stats: documents, tasks, readiness score, critical items
- **Clients** — manage your client portfolio with industry & revenue tracking
- **Documents** — drag-and-drop upload with AI classification (bank statements, contracts, tax returns, etc.)
- **Tasks** — priority-based action items with status tracking
- **Knowledge Vault** — full-text search across all processed documents
- **Automations** — rule-based workflow engine
- **Audit Log** — complete activity history
- **Settings** — user profile and organization management

---

## �� Quick Start

```bash
# 1. Backend (Python — SQLite, no Postgres needed)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # defaults work out of the box
uvicorn app.main:app --reload --port 8000

# 2. Frontend (Node.js)
cd ../frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000**, register an account, and you're in.

→ See **[DEVELOPMENT.md](DEVELOPMENT.md)** for the full setup guide, Docker instructions, API reference, test commands, and troubleshooting.

---

## 🧪 Tests

```bash
cd backend && pytest tests/ -v
# 24 tests · auth · clients · documents · organizations · tasks
```

---

## 📁 Project Layout

```
├── backend/          FastAPI API (11 routers, services, models)
├── frontend/         Next.js 15 app (App Router, React Query)
├── docker-compose.yml
├── DEVELOPMENT.md    ← Full developer guide
└── README.md
```
