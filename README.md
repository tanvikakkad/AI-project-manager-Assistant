# Mini AI Project Manager Assistant

Paste meeting notes or task descriptions → an LLM extracts structured tasks
(description, owner, due date, priority) → tasks are stored in Postgres →
manage them in a React UI (list, filter, edit, CSV export).

Full design rationale (architecture, schema, request lifecycles, design
patterns, SOLID/DRY, conventions): [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Stack

- **Backend**: FastAPI, async SQLAlchemy 2.x, PostgreSQL, Alembic, Pydantic v2
- **AI**: Gemini (default) with an automatic Groq fallback, behind a
  provider-agnostic `AIProvider` interface
- **Frontend**: React 19, TypeScript, Vite, TanStack Query, Axios, React Hook
  Form, Zod, CSS Modules

## Quick start

**1. Backend** — see [`backend/README.md`](backend/README.md) for full detail:

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, GEMINI_API_KEY
alembic upgrade head
uvicorn app.main:app --reload
```

**2. Frontend** — see [`frontend/README.md`](frontend/README.md):

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:5173.

## Repository layout

```
.
├── ARCHITECTURE.md   # full design document — read this first
├── backend/          # FastAPI service
├── frontend/          # React SPA
└── .gitignore
```
