# Equity Intelligence Platform

A production-minded AI research platform for U.S. equity intelligence. This project is focused on research and decision support, not investment advice.

## Phase 0 — Repository Foundation

This phase establishes a clean development foundation with:

- FastAPI backend
- React + TypeScript frontend with Vite
- PostgreSQL in Docker Compose
- Backend tests with pytest
- GitHub Actions CI for backend tests

## Local development

1. Copy `.env.example` to `.env`
2. Start services:
   ```bash
   docker compose up --build
   ```
3. Backend API: `http://localhost:8000/api/v1/health`
4. Frontend: run from `frontend/` with `npm install` and `npm run dev`

## Research-first positioning

This platform is designed as a research and decision-support tool. It is not intended to provide investment advice.
