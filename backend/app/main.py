"""Takt-Harness API entry. Serves the built Vue SPA and the JSON API; all
persistence is SQLite under the guard-scoped data tree.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import SessionLocal, init_db
from .roster import seed_agents
from .routers import agents, docs

app = FastAPI(title="Takt-Harness", version="0.1.0")

# Dev: Vite runs on 5173 and proxies /api; in prod the SPA is served from here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(docs.router)
app.include_router(agents.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed_agents(db)  # populate the agents table from the committed seed
    finally:
        db.close()


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "root": str(settings.root)}


# Serve the built SPA if present (prod image). Missing in dev — that's fine.
_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"
if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        return FileResponse(_DIST / "index.html")
