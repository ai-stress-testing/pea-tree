"""Runtime configuration for Takt-Harness.

All paths and the agent endpoint come from the environment so the same image
runs locally and in Docker. Nothing here decides policy — the write-scope
policy lives in guard.py, which is the only module allowed to touch the
filesystem.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TAKT_", env_file=".env", extra="ignore")

    # The Takt-Harness tree — the ONLY place writes are permitted.
    root: Path = Path(__file__).resolve().parents[2]
    # Writable data (SQLite db, exports). Always under `root`.
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"

    # Ges-Talt roster + context — READ ONLY. Never written or deleted.
    gestalt_root: Path = Path("/home/user/Ges-Talt")

    # OpenAI-compatible endpoint for the local 30B model (LM Studio default
    # port 1234). Reached via host.docker.internal from inside the container.
    agent_base_url: str = "http://host.docker.internal:1234/v1"
    agent_model: str = "local-model"
    agent_api_key: str = "not-needed"  # local server ignores it; kept configurable

    # Retry policy for the agent endpoint (PRD Agent-Queue rule).
    agent_retries: int = 3
    agent_backoff_base: float = 0.5

    @property
    def db_path(self) -> Path:
        return self.data_dir / "takt.db"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"


settings = Settings()
