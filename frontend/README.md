# Frontend — Mini AI Project Manager Assistant

React 19 + TypeScript + Vite + TanStack Query + Axios + React Hook Form + Zod
+ CSS Modules. See [`../ARCHITECTURE.md`](../ARCHITECTURE.md) for the full
design (folder structure, component hierarchy, state management).

## Setup

```bash
cd frontend
npm install
cp .env.example .env
# edit .env if your backend isn't running on http://localhost:8000
```

## Running

```bash
npm run dev
```

Open http://localhost:5173. The backend (see `../backend/README.md`) must be
running for the app to load/extract/edit tasks.

## Scripts

- `npm run dev` — start the Vite dev server
- `npm run build` — type-check (`tsc -b`) then production build
- `npm run lint` — oxlint
- `npm run preview` — preview the production build locally

## Project layout

See the "Folder Structure" and "Component Hierarchy" sections of
`../ARCHITECTURE.md` for the maintained layout and the responsibility of
every module.
