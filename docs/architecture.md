# Architecture Overview

## Phase 0 Foundation

This repository foundation is intentionally small and evolutionary.

### Components

- `backend/`: FastAPI API service.
- `frontend/`: React + TypeScript + Vite starter app.
- `docker-compose.yml`: Local development orchestration with PostgreSQL.
- `.github/workflows/test.yml`: CI for backend tests.

### Principles

- Keep the initial architecture simple.
- Build a working vertical slice starting with a single backend health check and frontend starter page.
- Preserve clean boundaries so future features can be added later without major refactoring.
- Maintain the platform positioning as research and decision support, not investment advice.

### Local development

Use `docker compose up --build` to bring up the backend and database. The frontend can be started separately from `frontend/`.
