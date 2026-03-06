# VOLTRON — BBA Command OS
### Entrepreneur Command OS · Powered by Noble Savage

A full-stack business intelligence and document management platform for entrepreneurs and advisors.

| Layer | Stack |
|-------|-------|
| Frontend | Next.js 15 · TypeScript · Tailwind CSS · React Query |
| Backend | FastAPI · SQLAlchemy · Pydantic v2 · JWT auth |
| Database | SQLite (dev, zero setup) · PostgreSQL (prod) |
| AI | OpenAI GPT-4o (document analysis — optional) |
| Storage | Local filesystem (dev) · AWS S3 (prod) |

---

## 🚀 Quick Start

### Option 1 — VS Code (recommended)

1. **Open in VS Code:**  
   `File → Open Folder` → select the cloned project folder  
   Or from the terminal inside the folder: `code .`

2. **Install recommended extensions** when prompted (Python, Pylance, ESLint, Tailwind)

3. **Run the app** — press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> (or <kbd>⌘</kbd>+<kbd>Shift</kbd>+<kbd>B</kbd> on Mac)  
   This starts both the backend and frontend automatically.

4. **Open** http://localhost:3000 in your browser, register an account, and you're in.

> **First time only** — set up dependencies first:
> ```bash
> make install
> ```

### Option 2 — Terminal (one command)

```bash
# First time: install everything
make install

# Every time after: start the full stack
make dev
```

### Option 3 — Manual (step by step)

```bash
# 1. Backend (SQLite — no Postgres needed)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# 2. Frontend (in a new terminal)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000

---

## ✨ Features

| Page | What it does |
|------|-------------|
| **Dashboard** | Live stats: documents, tasks, readiness score, critical items |
| **Clients** | Manage your client portfolio with industry & revenue tracking |
| **Documents** | Drag-and-drop upload with AI classification (bank statements, contracts, tax returns, etc.) |
| **Tasks** | Priority-based action items with status tracking |
| **Knowledge Vault** | Full-text search across all processed documents |
| **Automations** | Rule-based workflow engine |
| **Audit Log** | Complete system activity history |
| **Settings** | User profile and organization management |

---

## 🧪 Tests

```bash
make test
# or: cd backend && pytest tests/ -v
# 24 tests — auth, clients, documents, organizations, tasks
```

---

## 🐳 Docker (production-like, with Postgres + Redis)

```bash
make docker         # Build and start full stack
make docker-down    # Stop
make docker-clean   # Stop and wipe all data
```

---

## 📁 Project Layout

```
├── .vscode/              VS Code workspace (tasks, debugger, extensions)
├── backend/              FastAPI API (11 routers, services, models)
├── frontend/             Next.js 15 app (App Router, React Query)
├── docker-compose.yml
├── Makefile              make install / make dev / make test
├── DEVELOPMENT.md        Full developer guide
└── README.md
```

→ See **[DEVELOPMENT.md](DEVELOPMENT.md)** for the complete reference guide.
