# Takt-Harness

A locally-hosted planning harness that drives a **30B-parameter model** (over an
OpenAI-compatible `/v1` endpoint on port **1234**) through its **own agent
roster** (SQLite). Five interfaces: **Docs** (priority 1), Kanban, Agent-Queue,
Zettlebucket, Chats.

Built to the uploaded PRD/SRS/Implementation-Plan, decomposed by the Ges-Talt
`pm/project-manager` (see `docs/prd.md`, `docs/issue-specs/`, `docs/backlog.md`).

## Agents live in SQLite (self-contained)

The harness owns its agents in the `agents` table — `id, team, title, actions,
skills, tools, model, system_prompt`. It is seeded once from the former
Ges-Talt roster into `backend/app/agents_seed.json` (regenerate with
`backend/scripts/gen_agents_seed.py`), then edited here. **No external repo is
read at runtime** — Ges-Talt targets frontier models; this harness drives a
smaller local one and keeps its own roster. An agent row is the unit passed to
the model: `POST /api/agents/{id}/invoke` renders the row's system prompt and
sends it to the local `/v1` endpoint.

## Write invariant (PRD acceptance #2)

**All writes are scoped under `takt-harness/`.** Enforced centrally in
`backend/app/guard.py` and proven by `backend/tests/test_guard.py` (traversal,
absolute, and symlink escapes all rejected).

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
