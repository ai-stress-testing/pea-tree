"""The Agent-Queue retry rule, isolated so it is unit-testable without the
model endpoint (PRD Agent-Queue): on error retry up to 3 times, then skip to
the next item; after 6 further failures, escalate to user intervention.
"""
from dataclasses import dataclass

RETRY_BEFORE_SKIP = 3       # attempts 1..3 are ordinary retries
EXTRA_BEFORE_USER = 6       # 6 more failures after that -> needs_user
USER_THRESHOLD = RETRY_BEFORE_SKIP + EXTRA_BEFORE_USER  # 9


@dataclass
class Transition:
    state: str          # new state
    skip_to_next: bool  # runner should advance to the next queue item


def on_success() -> Transition:
    return Transition(state="done", skip_to_next=True)


def on_failure(attempts_after: int) -> Transition:
    """`attempts_after` is the attempt count AFTER incrementing for this
    failure. Returns the new state and whether the runner should move on."""
    if attempts_after >= USER_THRESHOLD:
        return Transition(state="needs_user", skip_to_next=True)
    if attempts_after >= RETRY_BEFORE_SKIP:
        # exhausted the 3 quick retries — skip to the next item, keep this one
        # in 'error' so it can be picked up again later.
        return Transition(state="error", skip_to_next=True)
    return Transition(state="error", skip_to_next=False)  # will retry shortly


# States the runner may still act on. `needs_user`, `done`, `processing`, and
# `paused` are all terminal-for-the-runner.
RUNNABLE = {"idle", "error"}


def next_candidate(items):
    """The next item a runner should process from an ordered list: the first
    runnable, non-paused item. Returns None when the queue has nothing to do
    (so the runner terminates instead of looping)."""
    for it in items:
        if it.state in RUNNABLE:
            return it
    return None
