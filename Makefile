# ─────────────────────────────────────────────────────────────────────────────
# BBA Command OS — Developer Makefile
#
# Usage:
#   make install     Install all dependencies (first-time setup)
#   make dev         Start backend + frontend in parallel
#   make backend     Start only the FastAPI backend
#   make frontend    Start only the Next.js frontend
#   make test        Run backend test suite
#   make lint        Lint frontend (ESLint)
#   make docker      Start full stack via Docker Compose
#
# Requirements: Python 3.11+, Node.js 20+, npm
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: install install-backend install-frontend \
        dev backend frontend \
        test lint \
        docker docker-down \
        env-setup help

# ─── Paths ───────────────────────────────────────────────────────────────────
BACKEND_DIR  := backend
FRONTEND_DIR := frontend
VENV         := $(BACKEND_DIR)/.venv
PYTHON       := $(VENV)/bin/python
PIP          := $(VENV)/bin/pip
UVICORN      := $(VENV)/bin/uvicorn

# ─── Default goal ────────────────────────────────────────────────────────────
.DEFAULT_GOAL := help

# ─────────────────────────────────────────────────────────────────────────────
# Installation
# ─────────────────────────────────────────────────────────────────────────────

## install: Install all dependencies and copy env files
install: env-setup install-backend install-frontend
	@echo ""
	@echo "✅  Setup complete! Run 'make dev' to start the app."
	@echo "    Frontend → http://localhost:3000"
	@echo "    Backend  → http://localhost:8000"
	@echo "    API docs → http://localhost:8000/api/docs"

## install-backend: Create venv and install Python dependencies
install-backend:
	@echo "→ Installing backend dependencies..."
	python3 -m venv $(VENV)
	$(PIP) install --quiet -r $(BACKEND_DIR)/requirements.txt
	@[ -f $(BACKEND_DIR)/requirements-dev.txt ] && $(PIP) install --quiet -r $(BACKEND_DIR)/requirements-dev.txt || true
	@echo "✓ Backend dependencies installed"

## install-frontend: Install Node.js dependencies
install-frontend:
	@echo "→ Installing frontend dependencies..."
	# --legacy-peer-deps: react-dropzone 14 declares a peer on React 16/17/18; Next.js 15 uses React 19 RC.
	# The libraries are fully compatible at runtime — this flag suppresses the false-positive peer conflict.
	cd $(FRONTEND_DIR) && npm install --legacy-peer-deps
	@echo "✓ Frontend dependencies installed"

## env-setup: Copy .env.example files if .env files don't exist yet
env-setup:
	@[ -f $(BACKEND_DIR)/.env ] || (cp $(BACKEND_DIR)/.env.example $(BACKEND_DIR)/.env && echo "✓ Created backend/.env from .env.example")
	@[ -f $(FRONTEND_DIR)/.env.local ] || (cp $(FRONTEND_DIR)/.env.local.example $(FRONTEND_DIR)/.env.local && echo "✓ Created frontend/.env.local from .env.local.example")

# ─────────────────────────────────────────────────────────────────────────────
# Development servers
# ─────────────────────────────────────────────────────────────────────────────

## dev: Start backend and frontend together (Ctrl+C stops both)
dev: env-setup
	@echo "🚀 Starting BBA Command OS..."
	@echo "   Frontend → http://localhost:3000"
	@echo "   Backend  → http://localhost:8000/api/docs"
	@echo ""
	@trap 'kill 0' INT; \
	  (cd $(BACKEND_DIR) && $(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | sed 's/^/[backend] /') & \
	  (cd $(FRONTEND_DIR) && npm run dev 2>&1 | sed 's/^/[frontend] /') & \
	  wait

## backend: Start only the FastAPI backend (with auto-reload)
backend: env-setup
	@echo "🐍 Starting FastAPI backend on http://localhost:8000"
	cd $(BACKEND_DIR) && $(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload

## frontend: Start only the Next.js frontend
frontend: env-setup
	@echo "🌐 Starting Next.js frontend on http://localhost:3000"
	cd $(FRONTEND_DIR) && npm run dev

# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

## test: Run the full backend test suite (24 tests)
test:
	@echo "🧪 Running backend tests..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v --tb=short

## test-coverage: Run tests with coverage report
test-coverage:
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ --cov=app --cov-report=term-missing

## lint: Run ESLint on the frontend
lint:
	cd $(FRONTEND_DIR) && npm run lint

# ─────────────────────────────────────────────────────────────────────────────
# Docker
# ─────────────────────────────────────────────────────────────────────────────

## docker: Build and start full stack with Docker Compose (Postgres + Redis)
docker:
	@[ -f .env ] || cp .env.example .env
	docker compose up --build

## docker-down: Stop and remove Docker containers
docker-down:
	docker compose down

## docker-clean: Stop containers and wipe all data volumes
docker-clean:
	docker compose down -v

# ─────────────────────────────────────────────────────────────────────────────
# Help
# ─────────────────────────────────────────────────────────────────────────────

## help: Show this help
help:
	@echo ""
	@echo "BBA Command OS — available commands:"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  make /' | column -t -s ':'
	@echo ""
