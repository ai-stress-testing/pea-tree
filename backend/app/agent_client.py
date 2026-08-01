"""Client for the local 30B model over an OpenAI-compatible `/v1` endpoint
(LM Studio / llama.cpp / vLLM style) at port 1234.

Model is a parameter, never hard-coded — the harness stays interchangeable.
Retry policy follows the PRD Agent-Queue rule: retry with exponential backoff;
the queue layer escalates to user intervention after the configured ceiling.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from .config import settings


@dataclass
class ChatResult:
    text: str
    model: str


class AgentUnavailable(RuntimeError):
    """The agent endpoint could not be reached within the retry budget."""


class AgentClient:
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.agent_base_url).rstrip("/")
        self.model = model or settings.agent_model

    async def available(self) -> bool:
        """Liveness check for the status indicators each feature shows."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as c:
                r = await c.get(f"{self.base_url}/models")
                return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{self.base_url}/models")
            r.raise_for_status()
            return [m["id"] for m in r.json().get("data", [])]

    async def chat(
        self, messages: list[dict], *, model: str | None = None, temperature: float = 0.4
    ) -> ChatResult:
        """One completion, with bounded exponential-backoff retries. Raises
        AgentUnavailable once the budget is spent — the caller (queue) decides
        whether to skip or escalate to user intervention."""
        use_model = model or self.model
        payload = {"model": use_model, "messages": messages, "temperature": temperature}
        headers = {"Authorization": f"Bearer {settings.agent_api_key}"}
        last: Exception | None = None
        for attempt in range(settings.agent_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as c:
                    r = await c.post(
                        f"{self.base_url}/chat/completions", json=payload, headers=headers
                    )
                    r.raise_for_status()
                    data = r.json()
                    return ChatResult(
                        text=data["choices"][0]["message"]["content"], model=use_model
                    )
            except httpx.HTTPError as e:
                last = e
                if attempt < settings.agent_retries - 1:
                    await asyncio.sleep(settings.agent_backoff_base * (2**attempt))
        raise AgentUnavailable(f"agent endpoint unreachable after retries: {last}")


agent_client = AgentClient()
