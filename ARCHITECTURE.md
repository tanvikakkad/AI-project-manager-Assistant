# Mini AI Project Manager Assistant — Software Architecture Document

Status: Phase 1 (no code). This document is the single source of truth for
Phases 2–9. Two tables only — `meetings` and `tasks` — one meeting has many
tasks.

---

## Part I — System Overview

### 1. High-Level Architecture

A layered monolith: one React SPA, one FastAPI service, one Postgres database,
one external LLM (Gemini, swappable). No queue, no cache, no microservices —
the problem has one write path (notes → meeting → tasks) and one read/edit
path (task management), and a single well-layered service handles both
correctly. Complexity is spent on internal separation of concerns, not on
distributed infrastructure the problem doesn't require.

```
┌────────────────────┐   HTTPS/JSON    ┌───────────────────────────────────────────────┐
│   React SPA (Vite)  │ ──────────────▶ │              FastAPI Application               │
│                      │ ◀────────────── │                                                 │
│ - Notes input        │                 │  Router layer        (HTTP only)               │
│ - Task list/filters  │                 │       │                                         │
│ - Edit dialog        │                 │       ▼                                         │
│ - CSV export         │                 │  Service layer       (business rules, orchestration) │
└────────────────────┘                 │       │                                         │
                                         │       ▼                                         │
                                         │  Repository layer    (SQLAlchemy async ORM)     │
                                         │       │                                         │
                                         │       ▼                                         │
                                         │   AsyncPG  ───────────▶  PostgreSQL              │
                                         │                              │                   │
                                         │                    meetings (1) ──▶ (N) tasks     │
                                         │                                                 │
                                         │  AI layer (Gemini) ◀── MeetingService/Extraction  │
                                         └───────────────────────────────────────────────┘
```

### 2. Complete Workflow

```
1. User pastes raw meeting notes (+ optional title/date/time) in the SPA.
2. SPA calls POST /api/v1/meetings/extract.
3. Backend resolves defaults (title/date/time), validates business rules
   (notes non-blank after trim, date/time not in the future), builds a
   prompt, and calls the configured AIProvider (Gemini by default, Groq
   fallback). NOTHING is persisted at this step.
4. LLM returns JSON — a list of {description, due_date, owner, priority,
   source_text} — parsed, normalized, and validated into ExtractedTaskDTO[].
5. Response returns a MeetingExtractionPreview (resolved metadata + proposed
   tasks) to the SPA. No Meeting or Task row exists in the database yet.
6. SPA shows the AI Extraction Review panel: every proposed task is editable
   (description/owner/due date/priority) and removable, entirely in local
   component state — still nothing persisted.
7. User clicks "Save All" → SPA calls POST /api/v1/meetings with the
   (possibly edited/filtered) task list plus the unchanged meeting metadata.
   Clicking "Cancel" instead discards everything client-side; no request is
   made.
8. Backend persists the Meeting row (status = COMPLETED immediately — the
   extraction already succeeded and was reviewed) and bulk-inserts exactly
   the confirmed Task rows. No AI call happens at this step.
9. Response returns the saved Meeting + its Tasks; SPA invalidates the tasks
   query → table refreshes.
10. User lists/filters (owner, status, priority)/edits tasks; edits go through
    PATCH /api/v1/tasks/{id}.
11. User optionally exports the current filtered view as CSV.
```

This is a deliberate **human-in-the-loop** design: extraction (AI) and
persistence (database) are two separate operations, not one pipeline — see
§15 for why, and §4 lists the two-column consequence for `ExtractedTaskDTO`
being reused as-is for both the preview response and the confirm request.

### 3. Request Lifecycle

Every request follows the same shape, regardless of feature:

```
HTTP request
  → FastAPI routing + Pydantic request validation (schema layer, including
    business-rule field/model validators — see §16)
  → Router function (thin — extracts params, calls exactly one service method)
  → Service method (business rules, orchestrates 1+ repositories and/or the AI layer)
  → Repository method(s) (translate to SQLAlchemy statements, execute against
    the async session)
  → Service maps ORM rows → Pydantic response schema
  → Router returns it wrapped in the shared response envelope
  → Global exception handlers intercept any AppException raised at any layer
    (and FastAPI's own RequestValidationError) and convert it to the same
    structured error response — routers never contain try/except business
    logic themselves.
```

Concretely for the three mutating/read endpoints on `meetings`:

- **`POST /api/v1/meetings/extract`** (preview, no persistence):
  `router → MeetingService.preview_extraction(payload)` → resolves
  title/date/time defaults → `ExtractionService.extract(raw_notes, reference_date)`
  (prompt build → AIProvider call → parse → normalize → validate) → returns
  `MeetingExtractionPreview`. No repository is touched.

- **`POST /api/v1/meetings`** (confirm, no AI call):
  `router → MeetingService.save_reviewed_meeting(payload)` →
  `MeetingRepository.create(status=COMPLETED)` → `TaskRepository.bulk_create`
  (from the client's, possibly-edited, `ExtractedTaskDTO[]`) → returns
  `MeetingWithTasksRead`. Nothing here ever calls `ExtractionService`.

- **`PATCH /api/v1/tasks/{id}`** (edit):
  `router → TaskService.update_task(id, payload) → TaskRepository.get_by_id`
  (404 → `TaskNotFoundError`) `→ TaskRepository.update` → `TaskRead`.

### 4. AI Workflow

This is the *application-level* pipeline that surrounds the model call —
owned by `ExtractionService`, not by any LLM SDK. `AIProvider` is deliberately
the thinnest possible contract (`generate(prompt: str) -> str` — see §5): every
concern that isn't "send text, get text back" lives outside the provider, so
none of it is duplicated when a new provider is added.

```
raw_notes, reference_date
  → prompts.build_extraction_prompt(raw_notes, reference_date)
      (in features/extraction/prompts.py — injects today's date so "by
       Friday"/"next week" resolve to real dates; embeds the exact JSON
       shape the model must return)
  → AIProvider.generate(prompt)                 # interface, not a concrete SDK
      (factory-provided instance is retry-wrapped, and falls back from the
       primary provider to Groq on failure — see §5)
  → raw text response
  → parser.parse_json_array(raw_text)            # in features/extraction/parser.py
      (guarded JSON extraction/parsing only → AIExtractionError on malformed
       JSON, InvalidLLMOutputError if the JSON isn't an array — no cleaning,
       no DTO validation here)
  → normalizer.normalize(raw_items)               # in features/extraction/normalizer.py
      (trims/collapses whitespace, title-cases owner names, folds varied
       date strings into one ISO format, defaults a missing/empty priority to
       MEDIUM, removes duplicate tasks by normalized description+owner+
       due_date, THEN validates each cleaned item against ExtractedTaskDTO —
       Pydantic, unknown/malformed fields rejected, not silently coerced)
  → valid, clean, deduplicated DTOs handed to TaskRepository.bulk_create
  → invalid/partial responses raise InvalidLLMOutputError, caught by the
    global handler, meeting flipped to FAILED
```

The LLM's output is treated as **untrusted external input** — identical
posture to validating a client HTTP body — never passed directly to the
database or the frontend unvalidated. Note that *parsing, normalization, and
validation are provider-agnostic*: they run identically regardless of which
`AIProvider` is configured (or whether the Groq fallback fired), because they
operate only on the raw text every provider returns, not on any
provider-specific response object — and `normalizer.py` imports nothing from
`app.ai`, FastAPI, or SQLAlchemy, so it has zero dependency on how that text
was produced.

### 5. LLM Workflow

This is the narrower concern *inside* and *around* a concrete provider,
entirely isolated in `app/ai/`:

- **`AIProvider` (`ai/base.py`)** — an ABC with exactly one method,
  `async def generate(self, prompt: str) -> str`. It knows nothing about
  tasks, JSON shape, or meetings — "prompt in, text out," full stop. This is
  what makes it swappable: OpenAI/Claude/Groq/Ollama all reduce to the same
  shape.
- **`GeminiProvider` (`ai/gemini_provider.py`)** — the only module that
  imports the Gemini SDK; the default primary provider. Uses the SDK's native
  async client (`client.aio.models.generate_content`) so no thread-pool
  wrapping is needed, and `response_mime_type="application/json"` to steer
  the model toward valid JSON — a first line of defense; Pydantic validation
  in the AI workflow above is the non-negotiable second line. If a future
  provider's SDK is sync-only, its implementation wraps calls in
  `asyncio.to_thread` to keep the event loop unblocked — an implementation
  detail local to that one provider, never leaking into `AIProvider`,
  `ExtractionService`, or `retry.py`.
- **`GroqProvider` (`ai/groq_provider.py`)** — the only module that imports
  the Groq SDK; usable standalone (`AI_PROVIDER=groq`) or as the automatic
  fallback (see below). Deliberately does *not* force JSON-object response
  mode — Groq's OpenAI-compatible strict JSON mode expects a top-level
  object, but the shared prompt asks for a top-level array; correctness
  instead relies on the shared prompt plus the parser's tolerant extraction.
- **`RetryingAIProvider` (`ai/retry.py`)** — a Decorator that wraps *any*
  `AIProvider` and adds bounded retry-with-backoff around `generate()`, on any
  exception the underlying call raises (including a provider-level timeout).
  Retry policy (attempt count, backoff) is defined exactly once here and
  applies uniformly to every current and future provider — a new provider
  never reimplements retry or timeout handling. Exhausting all attempts
  raises `ExternalServiceError`, caught by the global handler like any other
  `AppException`.
- **`FallbackAIProvider` (`ai/fallback.py`)** — a Decorator/Composite that
  tries a primary `AIProvider` and, on any failure, switches to a secondary
  one. Composes with `RetryingAIProvider`: the factory wires
  `Fallback(Retrying(Gemini), Retrying(Groq))`, so Gemini is retried first,
  and only after *its* retries are exhausted does Groq get tried (also with
  its own retries). If the fallback also fails, its exception propagates
  unchanged.
- **`get_ai_provider()` (`ai/factory.py`)** — reads `AI_PROVIDER` from
  `Settings`, constructs the matching concrete provider, wraps it in
  `RetryingAIProvider`, and attaches a retry-wrapped `GroqProvider` as an
  automatic `FallbackAIProvider` — unless Groq *is* the primary (no
  self-fallback) or `GROQ_API_KEY` isn't configured (fallback silently
  omitted; the primary provider is never broken by a missing optional
  secret). This is the *only* place that maps a config string to a class —
  adding a new primary provider means one new class plus one new
  `_PROVIDERS` entry here.
- Reference date is passed as explicit prompt context (built in
  `features/extraction/prompts.py`), never inferred by the model from "today"
  (models have no reliable clock).

### 6. Backend Workflow

Startup: `main.py` builds the FastAPI app → loads `Settings` once → configures
logging → registers exception handlers → registers routers → wires the async
engine's lifespan (dispose on shutdown). Per request: dependency-injected async
DB session (one per request, closed automatically) → router → service →
repository → response. No global mutable state; every dependency is resolved
per-request via `Depends`.

### 7. Frontend Workflow

`App` mounts a `QueryClientProvider` (TanStack Query) and the layout shell.
Two feature areas share one page: notes input (top) and task management
(below). Submitting notes calls the extraction mutation → on success, invalidates
the tasks query key → the task table refetches automatically. All server state
(tasks, meetings) lives in TanStack Query's cache; all local/UI state (dialog
open, form fields) lives in component state / React Hook Form. No global
client-state store.

### 8. Database Workflow

Single Postgres database, two tables, one relationship. Writes: `meetings`
row created first and independently committed (durability before the LLM
call), `tasks` rows created in a second step once extraction succeeds, always
carrying `meeting_id`. Reads: task list/filter queries never join `meetings`
unless a caller explicitly wants meeting context (e.g., a future "view source
meeting" affordance) — the task table alone satisfies every required frontend
filter (owner, status, priority). Migrations are the only way the schema
changes (Alembic), never manual DDL.

---

## Part II — Structure

### 9. Folder Structure

**Backend (`backend/`)**

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   ├── enums.py             # TaskStatus, TaskPriority, ProcessingStatus
│   │   ├── responses.py         # generic APIResponse[T] / APIErrorResponse
│   │   └── constants/
│   │       ├── api.py           # API_V1_PREFIX
│   │       ├── limits.py        # MAX_* field length limits
│   │       ├── defaults.py      # DEFAULT_MEETING_TITLE
│   │       └── messages.py      # user-facing message strings
│   ├── db/
│   │   ├── base.py
│   │   ├── session.py
│   │   └── repository.py       # BaseRepository[ModelType] — generic get_by_id/delete shared by every repo
│   ├── features/
│   │   ├── meetings/
│   │   │   ├── models.py        # Meeting ORM
│   │   │   ├── schemas.py       # MeetingCreate / MeetingRead / MeetingWithTasksRead
│   │   │   ├── repository.py    # MeetingRepository
│   │   │   ├── service.py       # MeetingService (orchestrates extraction)
│   │   │   └── router.py        # /api/v1/meetings
│   │   ├── tasks/
│   │   │   ├── models.py        # Task ORM
│   │   │   ├── schemas.py       # TaskCreate / TaskUpdate / TaskRead / TaskFilterParams
│   │   │   ├── repository.py    # TaskRepository
│   │   │   ├── service.py       # TaskService
│   │   │   └── router.py        # /api/v1/tasks
│   │   └── extraction/
│   │       ├── schemas.py       # ExtractedTaskDTO
│   │       ├── exceptions.py    # AIExtractionError, InvalidLLMOutputError (shared by parser + normalizer)
│   │       ├── prompts.py       # prompt template — the only module that builds prompt strings
│   │       ├── parser.py        # raw LLM text -> raw list[dict] (JSON-only, provider-agnostic)
│   │       ├── normalizer.py    # raw list[dict] -> clean, deduped, validated ExtractedTaskDTO[]
│   │       └── service.py       # ExtractionService (thin orchestration: prompt -> provider -> parser -> normalizer)
│   └── ai/
│       ├── base.py              # AIProvider ABC — generate(prompt: str) -> str, nothing else
│       ├── constants.py         # EXTRACTION_TEMPERATURE shared by every provider
│       ├── gemini_provider.py   # only module that imports the Gemini SDK
│       ├── groq_provider.py     # only module that imports the Groq SDK
│       ├── retry.py             # RetryingAIProvider — Decorator adding retry/backoff to any AIProvider
│       ├── fallback.py          # FallbackAIProvider — Decorator/Composite: primary provider, fall back to a secondary
│       └── factory.py           # get_ai_provider() — config -> retry-wrapped primary + Groq fallback
├── alembic/
├── alembic.ini
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

**Frontend (`frontend/`)**

```
frontend/
├── src/
│   ├── api/                     # axiosClient, apiTypes, getApiErrorMessage, meetings.api.ts, tasks.api.ts
│   ├── features/
│   │   ├── tasks/
│   │   │   ├── types.ts, schemas.ts (Zod)
│   │   │   ├── hooks/            # useTasksQuery, useUpdateTaskMutation, useDeleteTaskMutation
│   │   │   └── components/       # TasksSection, TaskTable, TaskFilters, TaskEditDialog,
│   │   │                         # StatusBadge, PriorityBadge, ExportCsvButton
│   │   └── notes-input/
│   │       ├── types.ts, schemas.ts (Zod)
│   │       ├── hooks/            # useCreateMeetingMutation
│   │       └── components/       # NotesInputSection, NotesInputForm, ExtractionResultPreview
│   ├── components/               # shared: Button, Select, TextInput, TextArea, Badge,
│   │                             # Toast (context+provider), EmptyState, Spinner, ConfirmDialog, Layout
│   ├── constants/                 # apiRoutes.ts, taskLabels.ts (labels + color tokens)
│   ├── theme/                     # tokens.css (CSS variables, light/dark via prefers-color-scheme)
│   ├── types/                     # enums.ts — TS mirrors of backend core/enums.py
│   ├── App.tsx
│   └── main.tsx                   # QueryClientProvider + ToastProvider wiring
├── .env.example
├── package.json
└── README.md
```

Note: `ExtractionService` lives under `features/extraction/` and is
*stateless with respect to persistence* — it only talks to the AI layer and
returns validated DTOs. `MeetingService` is what calls both
`ExtractionService` and the repositories, and owns the transactional sequence
described in §3. This keeps "talk to the LLM" and "coordinate the save"
as two distinct responsibilities, each independently testable/mockable.

### 10. Responsibilities of Every Folder

| Folder | Responsibility |
|---|---|
| `core/` | Cross-cutting infrastructure *and* shared vocabulary: settings, logging, exception types, enums, response envelope, constants — nothing feature-specific |
| `core/constants/` | One file per domain of constant (`api`, `limits`, `defaults`, `messages`) — no monolithic constants dumping ground |
| `db/` | Owns the async engine/session lifecycle, the declarative base, and the generic repository base — no feature queries |
| `features/meetings/` | Everything about the `meetings` entity and its persistence + orchestration |
| `features/tasks/` | Everything about the `tasks` entity: persistence, filtering/update rules, HTTP surface |
| `features/extraction/` | Everything about turning raw text into validated task DTOs (prompt, parser, orchestration) — no DB, no HTTP, no vendor SDK |
| `ai/` | Everything about talking to *some* LLM vendor SDK, behind one minimal interface — no knowledge of tasks/meetings/JSON shape |
| `alembic/` | Schema version history — the only sanctioned path to change the DB shape |
| `frontend/src/api/` | HTTP calls only — no React, no business logic |
| `frontend/src/features/*` | One folder per user-facing concern: components + hooks + types colocated |
| `frontend/src/components/` | Presentation-only primitives reused across features |
| `frontend/src/constants/`, `theme/` | The only places literal strings/colors are allowed to live |

### 11. Responsibilities of Every Module

| Module | Does | Never does |
|---|---|---|
| `meetings/models.py`, `tasks/models.py` | ORM column/relationship mapping | Validation, HTTP, business rules |
| `meetings/repository.py`, `tasks/repository.py` | Translate service intent → SQLAlchemy statements | Decide *what* a valid filter/update is |
| `meetings/service.py` | Orchestrate meeting creation → extraction → task persistence → status transitions | Raw SQL, direct LLM SDK calls |
| `tasks/service.py` | Filtering rules, update rules, CSV row assembly | SQL, HTTP |
| `extraction/prompts.py` | Build the exact prompt string | Anything about persistence, HTTP, or the vendor SDK |
| `extraction/exceptions.py` | Define `AIExtractionError`/`InvalidLLMOutputError` | Parsing or normalization logic itself |
| `extraction/parser.py` | Turn a provider's raw text into a raw `list[dict]` (JSON-only) | Cleaning, deduplication, defaults, DTO validation |
| `extraction/normalizer.py` | Clean, dedupe, default, and validate raw dicts into `ExtractedTaskDTO[]` | Calling the provider, persistence, FastAPI/SQLAlchemy/vendor SDK imports |
| `extraction/service.py` | Orchestrate: prompt → `AIProvider.generate()` → parser → normalizer → return DTOs | DB writes, parsing/cleaning logic itself |
| `ai/base.py` | Define the one-method `AIProvider` contract | Prompt text, JSON shape, retry policy |
| `ai/constants.py` | Hold tuning shared by every provider (e.g. extraction temperature) | Provider-specific request building |
| `ai/gemini_provider.py` | Speak the Gemini SDK dialect, return raw text | Prompt text, DTO validation, retry policy |
| `ai/groq_provider.py` | Speak the Groq SDK dialect, return raw text | Prompt text, DTO validation, retry policy |
| `ai/retry.py` | Wrap any `AIProvider` with retry/backoff | Provider-specific SDK calls |
| `ai/fallback.py` | Wrap a primary + secondary `AIProvider`, switching over on failure | Retry policy (composes with, doesn't replace, `retry.py`) |
| `ai/factory.py` | Choose + retry-wrap the primary `AIProvider`, attach a Groq fallback from config | Business logic |
| `core/exceptions.py` | Define `AppException` subclasses + FastAPI handlers | Feature-specific messages beyond the error shape |
| routers (`*/router.py`) | Parse request → call exactly one service method → return | Queries, LLM calls, conditionals beyond simple dispatch |

---

## Part III — Patterns & Principles

### 12–13. Design Patterns Used, and Why

| Pattern | Where | Why chosen |
|---|---|---|
| **Repository** | `MeetingRepository`, `TaskRepository` | Isolates SQLAlchemy from business logic; lets services be unit-tested against an in-memory fake repository |
| **Service Layer** | `MeetingService`, `TaskService`, `ExtractionService` | Single place for business rules and orchestration, keeping routers as thin coordinators (mandated by the brief) |
| **Strategy** | `AIProvider` implementations (`GeminiProvider`, `GroqProvider`, future `OpenAIProvider`/`ClaudeProvider`/`OllamaProvider`) | "Send a prompt, get text back" is interchangeable without touching `ExtractionService` |
| **Decorator** | `RetryingAIProvider` (`ai/retry.py`) | Adds retry/backoff around *any* `AIProvider` without either the concrete provider or the caller knowing it's there |
| **Decorator/Composite** | `FallbackAIProvider` (`ai/fallback.py`) | Composes a primary + secondary `AIProvider` behind the same interface; stacks with `RetryingAIProvider` without either decorator knowing about the other |
| **Factory** | `ai/factory.py` | Centralizes *which* strategy is constructed (and that it's retry-wrapped, with a fallback attached), driven by config (`AI_PROVIDER`, `GROQ_API_KEY`) |
| **DTO / Schema separation** | Pydantic schemas vs. ORM models | API contracts and DB shape evolve independently; prevents leaking ORM internals (e.g., lazy-loaded fields) into responses |
| **Dependency Injection** | FastAPI `Depends()` chains | Testable, swappable dependencies (real DB session in prod, test session in tests, fake `AIProvider` in tests) without touching call sites |
| **Adapter** | `GeminiProvider`/`GroqProvider` wrapping their vendor SDKs | Vendor SDK shapes/quirks never leak past `ai/gemini_provider.py` / `ai/groq_provider.py` |

These are exactly the patterns the brief's layering rules imply — nothing
extra was added (no CQRS, no event sourcing, no generic plugin system) because
the problem's scale doesn't justify them.

### 14. Repository Pattern (detail)

`TaskRepository` and `MeetingRepository` each expose intention-revealing async
methods (`get_by_id`, `find_all(filters)`, `bulk_create`, `update`,
`update_status`) that internally build `select()`/`insert()`/`update()`
statements against the injected `AsyncSession`. A small generic
`BaseRepository[ModelType]` supplies the identical `get_by_id`/`delete`
implementation shared by both, avoiding duplication (see DRY, §39) while each
concrete repository adds its entity-specific query methods (e.g.
`TaskRepository.find_all` builds the dynamic owner/status/priority `WHERE`).

### 15. Service Layer (detail)

Services are the only callers of repositories and the only callers of the AI
layer. `MeetingService.create_from_notes` is the one place that knows the
*sequence* (persist meeting → extract → persist tasks → flip status) —
routers and repositories individually have no idea this sequence exists.
`TaskService` owns what "a valid filter combination" or "a valid status
transition" means, so that rule lives in exactly one place if it ever needs to
change (e.g., disallowing `DONE → TODO` in the future).

### 16. Validation Layer

Two independent validation boundaries, both Pydantic v2:
1. **Client input** — request schemas (`MeetingCreate`, `MeetingConfirmRequest`,
   `TaskUpdate`, `TaskFilterParams`) validate everything arriving over HTTP
   before a router even calls a service. Beyond types/lengths, `MeetingCreate`
   and `MeetingConfirmRequest` both enforce business rules via
   `field_validator`/`model_validator`, delegating the actual rule logic to
   shared plain functions in `features/meetings/validators.py` (not a
   duplicated Pydantic mixin, since the two schemas have different field
   optionality): notes are trimmed and rejected if blank, `meeting_date`
   cannot be in the future, and `meeting_time` cannot be in the future for
   today's (effective) date. `MeetingConfirmRequest` re-validates these even
   though the client echoes them back from the preview step — a request body
   is never trusted just because it matches a shape the server itself
   returned earlier.
2. **AI output** — `ExtractedTaskDTO` validates everything the LLM returns
   before it reaches the repository, treating the model exactly like an
   untrusted upstream API.
3. **Frontend (UX only)** — a mirrored Zod schema (`notesInputSchema`)
   enforces the identical rules client-side via `superRefine` for immediate
   inline feedback. The backend remains the source of truth: every one of
   these rules is re-checked server-side regardless of what the client sent.

Every validation failure — whether raised inside a router's own schema
validation or deep inside a custom validator — is caught by one exception
handler (`_handle_request_validation_error`) and returned in the same
`APIErrorResponse` envelope as every other error, never FastAPI's default
`{"detail": [...]}` shape. No hand-rolled `if`-based validation anywhere;
schema classes are the single source of truth for "what does valid data look
like" at each boundary.

### 17. Dependency Injection

FastAPI's `Depends()` forms a chain: `get_db` (session) → `get_task_repository(db)`
→ `get_task_service(repo)` → used by `router.py`. Same shape for meetings and
for `get_ai_provider()` (reads `Settings.AI_PROVIDER`, constructs the matching
provider). Nothing is instantiated with a bare constructor call inside a
router; everything arrives via injection, which is what makes each layer
mockable in isolation.

### 18. Async Flow

`async def` end-to-end: FastAPI route handlers, service methods, repository
methods, the SQLAlchemy `AsyncSession`/`asyncpg` driver, and the AI provider
call (natively async, or `asyncio.to_thread`-wrapped if the SDK is sync-only,
per §5). One session per request, opened by the `get_db` dependency and closed
automatically at request end — no long-lived or shared sessions across
requests.

### 37. Reusability Strategy

- `BaseRepository[ModelType]` (generic CRUD) shared by both repositories.
- `core/responses.py` generic envelope (`APIResponse[T]`) shared by every
  endpoint.
- `core/enums.py` is the single definition of `TaskStatus`/`TaskPriority`/
  `ProcessingStatus`, consumed by ORM models, Pydantic schemas, and the
  extraction validator alike — never redefined per-layer.
- `RetryingAIProvider` (`ai/retry.py`) — one retry implementation reused by
  every current and future `AIProvider`, instead of each provider
  reimplementing its own backoff loop.
- `ai/constants.py` (`EXTRACTION_TEMPERATURE`) — one tuning value shared by
  `GeminiProvider` and `GroqProvider` instead of two independently-drifting
  magic numbers.
- Frontend: a small `useApiQuery`/`useApiMutation` convention over TanStack
  Query so each feature hook is a thin, consistent wrapper; shared `Button`,
  `Select`, `Badge`, `EmptyState`, `Toast` components used by both features.

### 38. SOLID Implementation

- **S**ingle Responsibility — router/service/repository/provider each change
  for exactly one reason (HTTP contract, business rule, query shape, vendor
  SDK, respectively).
- **O**pen/Closed — `AIProvider` is open for extension (new providers) and
  closed for modification (interface never changes to accommodate a new vendor).
- **L**iskov Substitution — any `AIProvider` implementation is a drop-in
  replacement for another; `ExtractionService` never checks *which* provider
  it has.
- **I**nterface Segregation — `AIProvider` exposes exactly one method
  (`generate`), not the vendor SDK's full surface.
- **D**ependency Inversion — `ExtractionService` depends only on the
  `AIProvider` abstraction (injected via `get_ai_provider()`), never on a
  concrete SDK; services generally depend on repository/provider
  *abstractions*, never constructing concrete infrastructure classes
  themselves.

### 39. DRY Implementation

Enums defined once (`core/enums.py`) and imported everywhere they're needed;
generic `BaseRepository` avoids duplicating `get_by_id`/`delete` per entity;
one response envelope; one prompt-building function (not copy-pasted per call
site); frontend constants/theme tokens defined once and imported, never
inlined per component.

---

## Part IV — Cross-Cutting Concerns

### 19. Error Handling

`AppException` base class (already defined in `core/exceptions.py`) with typed
subclasses: `NotFoundError`-derived `MeetingNotFoundError`/`TaskNotFoundError`,
`ValidationError`-derived `AIExtractionError`/`InvalidLLMOutputError` (parsing/
validation failures), and `ExternalServiceError` (provider failure after
`RetryingAIProvider` exhausts its attempts). Each maps to an HTTP status in one place
(`core/exceptions.py`'s handler registration) — routers never write
`try/except`. Every error response uses the same `APIErrorResponse` shape
(`code`, `message`, optional `details`), so the frontend has exactly one error
shape to handle, ever.

### 20. Logging

Configured once in `core/logging.py`, level driven by `LOG_LEVEL` env var.
Logs request method/path/status/duration, LLM call latency and outcome
(success/failure/timeout), and DB errors. Raw meeting notes and extracted task
content are **not** logged at INFO level (privacy — meeting notes may contain
sensitive business information); available at DEBUG only, for local
troubleshooting.

### 21. Configuration Management

One `Settings(BaseSettings)` class (`core/config.py`) is the *only* place
`os.environ`/`.env` is read. Every other module receives configuration values
already parsed and typed, via `Settings` injected/imported — never a second
`os.getenv` scattered elsewhere.

### 22. Environment Variables

`DATABASE_URL`, `AI_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL`,
`GROQ_API_KEY`, `GROQ_MODEL`, `CORS_ORIGINS`, `LOG_LEVEL`, `ENVIRONMENT` on
the backend; `VITE_API_BASE_URL` on the frontend. `AI_PROVIDER` is validated
against the `AIProviderName` enum at startup (fails fast on a typo'd value,
not on first request). `GROQ_API_KEY` is the one genuinely optional secret —
its absence only disables the automatic Groq fallback, it doesn't break the
primary provider. All documented in `.env.example` with safe placeholder
values.

### 23. Constants Management

`core/constants/` is split by domain rather than one monolithic file:
`api.py` (route prefixes), `limits.py` (field length limits), `defaults.py`
(fallback values like `DEFAULT_MEETING_TITLE`), `messages.py` (user-facing
strings). `core/enums.py` (status/priority/processing vocab) rounds out the
backend's "magic value" sources. Frontend mirrors this with `constants/`
(labels, colors, route strings) and `theme/` (spacing/color/type tokens) — no
literal hex codes or status strings inline in components.

### 24. Prompt Management

`features/extraction/prompts.py` owns the one template used for extraction.
The template: states the task (extract action items), embeds the reference
date, embeds the exact JSON schema the model must emit (mirroring
`ExtractedTaskDTO`), and instructs "JSON only, no prose." Kept as a single
named function (`build_extraction_prompt`) so future prompt changes touch one
file, and are trivially diffable/reviewable — never string-built inline
inside the service.

---

## Part V — Quality Attributes

### 25. Scalability

The FastAPI process is stateless — horizontally scalable behind a load
balancer with no sticky sessions. Fully async I/O maximizes throughput per
instance under concurrent requests. SQLAlchemy's async engine pools
connections. Indexes on `tasks(owner)`, `tasks(status)`, `tasks(priority)`,
`tasks(meeting_id)`, and `meetings(meeting_date)` keep filtered list queries
fast as data grows — already in place in the first migration, not deferred.
`TaskFilterParams` is already a structured dependency object, so adding
`limit`/`offset` pagination later is additive, not a breaking change.

### 26. Future Extensibility

- `GroqProvider` and the Gemini→Groq automatic fallback are already built
  (`ai/fallback.py`, `ai/factory.py`) — adding a *third* provider (OpenAI,
  Claude, Ollama) is one new class + one `_PROVIDERS` entry, no other code
  changes.
- Move extraction to a background worker (Celery/RQ/arq) — `processing_status`
  already models `PENDING → PROCESSING → COMPLETED/FAILED`, so the state
  machine doesn't change, only *what* drives the transition.
- Add authentication/authorization as an additional FastAPI dependency layered
  in front of existing routers, without touching services/repositories.
- Add a "retry extraction" endpoint for `FAILED` meetings — `raw_notes` is
  already durably stored, which is precisely why it's a separate table.
- Add a meetings list/detail UI later (backend already models meetings as a
  first-class entity, not just a transient input).
- Promote `owner` from a plain string to a `people`/`assignees` table if
  multi-owner tasks are ever needed — additive, doesn't change today's schema.

### 27. Security Considerations

- Server computes "today" for the prompt itself — never trusts a
  client-supplied date.
- `raw_notes` has a max-length constraint enforced at the schema layer
  (prevents unbounded LLM cost/abuse from a single request).
- All queries go through SQLAlchemy's parameterized query building — no
  string-concatenated SQL anywhere, so there is no injection surface.
- CORS restricted to configured origins only (`CORS_ORIGINS` env var), not `*`.
- Secrets (`GEMINI_API_KEY`, `DATABASE_URL`) only ever live in `.env`
  (git-ignored); `.env.example` ships placeholders only.
- LLM output is validated (schema + length caps on `description`/`owner`)
  before storage, so a model returning unexpected/oversized content can't
  corrupt data or blow up storage.
- Rate limiting is *not* built in v1 (no auth/multi-tenant concept yet in
  scope) — flagged under Future Extensibility rather than built speculatively.

### 28. Production Considerations

`GET /health` liveness endpoint for container orchestration. Alembic
migrations are a required deploy step (`alembic upgrade head`), never manual
DDL. Config is fully 12-factor (env-driven, no hardcoded environment
branches). The async engine is disposed on FastAPI's shutdown event for clean
connection teardown. Logs are structured enough to ship to any aggregator
without reformatting.

---

## Part VI — Data & API

### 29. Database Schema

Two tables, one relationship (`meetings 1 ──▶ N tasks`), enforced by a foreign
key with `ON DELETE CASCADE` (deleting a meeting removes its extracted tasks —
they have no independent meaning without their source).

**`meetings`**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID`, PK, `server_default gen_random_uuid()` | Client-side `uuid4()` fires through the ORM; server default is a defense-in-depth fallback for any raw-SQL insert |
| `title` | `VARCHAR(255)`, not null, default `'Untitled Meeting'` | Optional on input; MeetingService/column default fills it in — never left null |
| `meeting_date` | `DATE`, not null, default today, **indexed** | Optional on input; defaulted if omitted |
| `meeting_time` | `TIME`, not null, default current time | Optional on input; defaulted if omitted |
| `raw_notes` | `TEXT`, not null | The pasted input — source of truth, kept even if extraction fails |
| `processing_status` | `ENUM('PENDING','PROCESSING','COMPLETED','FAILED')`, not null, default `PENDING` | Tracks the extraction lifecycle; see §3, §26 |
| `created_at` | `TIMESTAMPTZ`, server default `now()` | |
| `updated_at` | `TIMESTAMPTZ`, server default `now()`, updated on write | |

**`tasks`**

| Column | Type | Notes |
|---|---|---|
| `id` | `UUID`, PK, `server_default gen_random_uuid()` | Same defense-in-depth pattern as `meetings.id` |
| `meeting_id` | `UUID`, FK → `meetings.id`, not null, `ON DELETE CASCADE`, **indexed** | Enforces the one-to-many relationship; indexed for the join/filter path |
| `description` | `TEXT`, not null | The task itself |
| `owner` | `VARCHAR(255)`, nullable, **indexed** | LLM may not find one; indexed — required frontend filter |
| `priority` | `ENUM('LOW','MEDIUM','HIGH','URGENT')`, not null, default `MEDIUM`, **indexed** | Required frontend filter |
| `status` | `ENUM('TODO','IN_PROGRESS','DONE')`, not null, default `TODO`, **indexed** | Always app-assigned, never LLM-inferred; required frontend filter |
| `due_date` | `DATE`, nullable | LLM may not find one |
| `source_text` | `TEXT`, nullable | The exact notes snippet the task was derived from — explainability for AI-generated data |
| `created_at` | `TIMESTAMPTZ`, server default `now()` | |
| `updated_at` | `TIMESTAMPTZ`, server default `now()`, updated on write | |

No additional tables. `owner` stays a plain string (no `people` table) — the
spec doesn't call for user/identity management, and adding one would be
unrequested scope (see §26 for how it could be added later if ever needed).

**Confirmed:** `title`/`meeting_date`/`meeting_time` are optional frontend
fields, user-provided only — the LLM's responsibility is strictly limited to
the raw notes → task extraction and never touches meeting metadata. If
omitted, `Meeting` applies defensive column-level defaults
(`title` → `"Untitled Meeting"`, `meeting_date` → today, `meeting_time` →
current time) as a data-integrity safety net; the actual "what counts as a
sensible default" decision is made once, in `MeetingService`, when Phase 5
builds the row from the request payload.

### 30. API Endpoints

| Method | Path | Request | Response | Purpose |
|---|---|---|---|---|
| `POST` | `/api/v1/meetings/extract` | `{ title?, meeting_date?, meeting_time?, raw_notes }` | `{ data: MeetingExtractionPreview }` | Run AI extraction only — **nothing persisted** |
| `POST` | `/api/v1/meetings` | `{ title, meeting_date, meeting_time, raw_notes, tasks: ExtractedTaskDTO[] }` | `{ data: MeetingWithTasksRead }` | Persist the meeting + human-reviewed tasks — **no AI call** |
| `GET` | `/api/v1/meetings/{id}` | — | `{ data: MeetingWithTasksRead }` | Fetch a meeting and its tasks (supports future "view source" UI) |
| `GET` | `/api/v1/tasks` | query: `owner?`, `status?`, `priority?` | `{ data: TaskRead[] }` | List/filter tasks — the required frontend feature |
| `GET` | `/api/v1/tasks/{id}` | — | `{ data: TaskRead }` | Fetch one task |
| `PATCH` | `/api/v1/tasks/{id}` | partial `TaskUpdate` | `{ data: TaskRead }` | Edit a task |
| `DELETE` | `/api/v1/tasks/{id}` | — | `204 No Content` | Remove a task |
| `GET` | `/api/v1/tasks/export/csv` | query: same filters as list | `text/csv` stream | CSV export, respects active filters |
| `GET` | `/health` | — | `{ status: "ok" }` | Liveness check |

`TaskRead` includes `meeting_id` (and, if joined, `source_text`) so the
frontend can — optionally, not required by the spec — surface "why was this
created" context next to a task.

---

## Part VII — Frontend Design

### 31. Component Hierarchy

```
App
└── Layout (header + page shell)
    ├── NotesInputSection                 (holds preview state: form XOR review)
    │   ├── NotesInputForm                (title?/date?/time?/raw_notes, RHF + Zod; calls /extract)
    │   └── ExtractionReviewPanel         (human-in-the-loop review; local state only until "Save All")
    └── TasksSection
        ├── TaskFilters                    (owner/status/priority selects)
        ├── ExportCsvButton                (respects active filters)
        ├── TaskTable                      (rows inline: StatusBadge, PriorityBadge, Edit/Delete actions)
        ├── TaskEditDialog                 (opened per-row; RHF + Zod)
        └── ConfirmDialog                  (delete confirmation)
```

`NotesInputSection` renders exactly one of `NotesInputForm` or
`ExtractionReviewPanel` at a time, based on whether an unsaved
`MeetingExtractionPreview` exists in its state — the workflow's two phases
(extract, then confirm) map directly onto which component is mounted.

Shared, feature-agnostic primitives (`Button`, `Select`, `TextInput`,
`TextArea`, `Badge`, `Toast`, `EmptyState`, `Spinner`, `ConfirmDialog`) live in
`components/` and are consumed by both sections — each is a thin styled
wrapper around its native HTML element, so React Hook Form's `register()`
spreads onto them exactly as it would onto a raw `<input>`/`<select>`/
`<textarea>` (React 19 forwards `ref` as a normal prop, no `forwardRef`
boilerplate needed).

### 32. State Management

**Server state** (tasks, meetings) lives entirely in TanStack Query's cache —
`useTasksQuery`, `useCreateMeetingMutation`, `useUpdateTaskMutation`, etc.
Mutations invalidate the `['tasks']` query key on success so the table
reflects reality without manual state syncing. **Local/UI state** (dialog
open/closed, current form values, current filter selections before they're
applied) lives in ordinary component state and React Hook Form. No
Redux/Zustand/Context-based global store — there is no client-only state
complex enough to justify one, and introducing it would violate the brief's
"do not introduce unnecessary libraries."

---

## Part VIII — Conventions

### 33–34. Naming Conventions & Coding Standards

**Python**: `snake_case` for modules, functions, variables; `PascalCase` for
classes (`TaskRepository`, `MeetingService`, `AIProvider`); `UPPER_SNAKE_CASE`
for module-level constants and enum members. Ruff + Black enforced, full type
hints on every function signature, docstrings only where the *why* isn't
obvious from the signature/name.

**TypeScript/React**: `PascalCase` for component files and their default
export (`TaskTable.tsx`); `camelCase` for functions/variables/hooks (hooks
always prefixed `use...`); `UPPER_SNAKE_CASE` for exported constants;
interfaces/types `PascalCase` (`TaskRead`, `TaskFilterParams`).

### 35–36. Folder & File Naming Conventions

Backend feature folders are singular domain nouns matching the entity
(`meetings/`, `tasks/`) except `extraction/`, which names a *capability*
rather than an entity (it has no table of its own). Every feature folder uses
the same fixed file set (`models.py`, `schemas.py`, `repository.py`,
`service.py`, `router.py`) so any engineer can navigate a new feature by
convention alone. Frontend feature folders are kebab-case nouns
(`notes-input/`), each with `components/`/`hooks/` subfolders; component files
are `PascalCase.tsx` with a colocated `PascalCase.module.css`.

---

## Part IX — Rationale

### 40. Why This Architecture Is Better Than a Beginner Implementation

| Beginner approach | This architecture |
|---|---|
| SQL/business logic inline in route handlers | Routes only coordinate; logic lives in services, queries live in repositories |
| Trusts the LLM's JSON blindly, crashes on malformed output | LLM output validated as untrusted input (`ExtractedTaskDTO`) before it ever reaches the DB |
| Notes are lost if the LLM call fails | Meeting persisted *before* the LLM call; `processing_status` preserves raw notes on failure |
| Hardcoded API keys/DB URLs in source | Everything env-driven through one typed `Settings` object |
| String literals for status/priority (typo-prone, no DB-level guarantee) | Native Postgres enums, single Python enum definition shared across every layer |
| One giant `App.tsx` with inline `fetch` and no caching | TanStack Query-managed server state, feature-based component structure |
| Manual/ad-hoc schema changes | Alembic migrations are the only sanctioned schema change path |
| Tightly coupled to one LLM vendor | `AIProvider` abstraction — vendor swap is a config change, not a rewrite |
| No separation → testing requires the full stack (real DB, real LLM) | Each layer (repository/service/AI provider) is independently mockable and unit-testable |
| Ad-hoc error responses per endpoint | One `AppException` hierarchy → one consistent error envelope everywhere |

---

This document supersedes the single-table draft from the previous iteration.
Nothing here should need to change once Phases 2–9 begin unless a phase
surfaces a concrete reason to revise it — flag the meeting-metadata assumption
in §29 now if it needs to change before Phase 2 starts.
