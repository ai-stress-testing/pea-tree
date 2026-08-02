"""Pure helpers for the summon flow (Feature 1), isolated for unit testing
without the model endpoint."""
from __future__ import annotations

import json
import re

GATE_MESSAGE = (
    "A summon is already active in this chat. Please wait for it to complete "
    "before starting another."
)
NO_AGENTS_MESSAGE = "The model determined no agents are needed for this request."


def parse_agent_ids(model_text: str, known_ids: set[str]) -> list[str]:
    """Extract the agent ids the model chose from its response, keeping only
    ids that exist in the roster and de-duplicating while preserving order.

    Accepts a bare JSON array (`["a/b", ...]`) or objects with an `id` field
    (`[{"id":"a/b", ...}]`) so per-agent config can ride along."""
    m = re.search(r"\[.*\]", model_text, re.S)
    if not m:
        return []
    try:
        raw = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        aid = item.get("id") if isinstance(item, dict) else item
        if isinstance(aid, str) and aid in known_ids and aid not in out:
            out.append(aid)
    return out


def selection_prompt(prompt: str, roster: list[tuple[str, str]]) -> list[dict]:
    """System+user messages asking the model which agents to summon."""
    listing = "\n".join(f"- {aid}: {desc}" for aid, desc in roster)
    return [
        {
            "role": "system",
            "content": (
                "You are the summon router for a planning chat. Given the user's "
                "request and the agent roster, choose the agents whose expertise the "
                "request needs (0 to 6). Reply with ONLY a JSON array of agent id "
                "strings, nothing else. An empty array means no agents are needed."
            ),
        },
        {"role": "user", "content": f"REQUEST:\n{prompt}\n\nROSTER:\n{listing}"},
    ]
