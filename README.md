# Takt-Harness

A locally-hosted planning harness that drives a **30B-parameter model** (over an
OpenAI-compatible `/v1` endpoint on port **1234**) through the **Ges-Talt agent
roster**. Five interfaces: **Docs** (priority 1), Kanban, Agent-Queue,
Zettlebucket, Chats.

Built to the uploaded PRD/SRS/Implementation-Plan, decomposed by the Ges-Talt
`pm/project-manager` (see `docs/prd.md`, `docs/issue-specs/`, `docs/backlog.md`).

## Hard invariant (PRD acceptance #1/#2)

The app **never writes to or deletes under `ges-talt/`** — it is read-only
source (roster + context). **All writes are scoped under `takt-harness/`.**
This is enforced centrally in `backend/app/guard.py` (the only module that
touches the filesystem) and proven by `backend/tests/test_guard.py`.

## Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite (named Docker volume).
- **Frontend**: Vue 3 + TypeScript (Vite). Docs split editor renders markdown +
  Mermaid, sanitized with DOMPurify (XSS defense).
- **Agent**: OpenAI-compatible `/v1` client with exponential-backoff retries.
- **Deploy**: `docker-compose up --build`.

## Run

### Docker (prod-like)
```
docker-compose up --build          # web on :8000; Ges-Talt mounted read-only
```
Run your local model server (LM Studio / llama.cpp / vLLM) exposing
`http://localhost:1234/v1`. The container reaches it via `host.docker.internal`.

### Dev
```
# backend
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# frontend
cd web && npm install && npm run dev      # :5173, proxies /api → :8000
```

## Test
```
cd backend && pytest            # guard invariant + API
cd web && npm run typecheck
```

## Status

- ✅ Foundation: compose, SQLite, **write-scope guard (+tests)**, agent `/v1`
  client, read-only roster loader.
- ✅ Docs (priority 1): projects → sprints → document library (25 types),
  draggable split editor, live sanitized markdown + Mermaid preview, auto-save
  (30s + blur), agent-assist on a highlighted selection.
- ⏳ Kanban, Agent-Queue, Zettlebucket, Chats — specced in `docs/issue-specs/`,
  built in priority order.
