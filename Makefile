.PHONY: help install seed backend frontend test lint build db-up db-down reset discover

help:
	@echo "Zenkai"
	@echo "  make install    Install backend and frontend dependencies"
	@echo "  make seed       Create tables and load the seed catalogue"
	@echo "  make backend    Run the FastAPI server on :8000"
	@echo "  make frontend   Run the Next.js server on :3000"
	@echo "  make test       Run the backend test suite"
	@echo "  make lint       Type-check and lint the frontend"
	@echo "  make build      Production build of the frontend"
	@echo "  make db-up      Start PostgreSQL in Docker"
	@echo "  make reset      Drop and re-seed the database"
	@echo "  make discover   Run live discovery against due, enabled sources"

install:
	cd backend && python3.11 -m venv .venv && .venv/bin/pip install -q -r requirements.txt
	cd frontend && npm install

seed:
	cd backend && .venv/bin/python -m app.seed.run

reset:
	cd backend && .venv/bin/python -m app.seed.run --reset

discover:
	cd backend && .venv/bin/python run_discovery.py

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/python -m pytest -q

lint:
	cd frontend && npx tsc --noEmit && npm run lint

build:
	cd frontend && npm run build

db-up:
	docker compose up -d

db-down:
	docker compose down
