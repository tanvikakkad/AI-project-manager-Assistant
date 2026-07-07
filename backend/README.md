# Backend — Mini AI Project Manager Assistant

FastAPI + async SQLAlchemy 2.x + PostgreSQL + Alembic + Pydantic v2.
See [`../ARCHITECTURE.md`](../ARCHITECTURE.md) for the full design.

## Setup

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — set DATABASE_URL to your local Postgres credentials,
# and GEMINI_API_KEY (required) / GROQ_API_KEY (optional automatic fallback)
```

## Running the API

```bash
uvicorn app.main:app --reload
```

Health check: `curl http://localhost:8000/health` → `{"status": "ok"}`

## Migrations

The first migration (`meetings` + `tasks` tables, native enums, FK cascade,
indexes) is already written. Once `DATABASE_URL` in `.env` points at your
Postgres instance:

```bash
alembic upgrade head
```

To preview the exact SQL without touching a database (useful for review):

```bash
alembic upgrade head --sql
```

`alembic.ini` has no hardcoded database URL — `alembic/env.py` reads it from
`Settings` (i.e. from `.env`), so the connection string has exactly one
source of truth across the app and its migrations.

## Project layout

See the "Folder Structure" section of `../ARCHITECTURE.md` for the full,
maintained layout and the responsibility of every module.
