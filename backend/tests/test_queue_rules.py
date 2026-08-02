"""The Agent-Queue retry state machine (PRD): retry 3×, skip, 6 more → user."""
from dataclasses import dataclass

from app.queue_rules import (
    next_candidate,
    on_failure,
    on_success,
    RETRY_BEFORE_SKIP,
    USER_THRESHOLD,
)


@dataclass
class _Item:
    state: str


def test_success_is_done_and_advances():
    t = on_success()
    assert t.state == "done" and t.skip_to_next


def test_first_retries_do_not_skip():
    for attempts in range(1, RETRY_BEFORE_SKIP):  # 1, 2
        t = on_failure(attempts)
        assert t.state == "error" and not t.skip_to_next


def test_third_failure_skips_to_next_but_keeps_item():
    t = on_failure(RETRY_BEFORE_SKIP)  # 3
    assert t.state == "error" and t.skip_to_next


def test_middle_failures_stay_error_and_skip():
    for attempts in range(RETRY_BEFORE_SKIP + 1, USER_THRESHOLD):  # 4..8
        t = on_failure(attempts)
        assert t.state == "error" and t.skip_to_next


def test_ninth_failure_escalates_to_user():
    t = on_failure(USER_THRESHOLD)  # 9
    assert t.state == "needs_user" and t.skip_to_next


def test_runner_skips_paused_and_terminal_items():
    # Runner passes over paused/needs_user/done/processing and picks the first
    # runnable (idle/error) item — realizing "skip to next".
    items = [_Item("paused"), _Item("needs_user"), _Item("done"), _Item("error"), _Item("idle")]
    assert next_candidate(items) is items[3]  # the first runnable


def test_runner_terminates_when_nothing_runnable():
    items = [_Item("paused"), _Item("needs_user"), _Item("done")]
    assert next_candidate(items) is None  # drained -> runner stops
