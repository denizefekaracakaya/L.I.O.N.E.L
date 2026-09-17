"""A `CancellationToken` registry — the G3 slice of ADR-0025.  ADR-0009, ADR-0027.

WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT
    ADR-0025's Verification names two gates. **G6d** — barge-in aborting audio playback,
    TTS synthesis and in-flight tool calls in the specified fan-out order, "leaving zero
    orphaned work" — is `InterruptController.cancel()`'s job, and that method still
    correctly raises `NotYetImplemented("cancellation fan-out", "G7 (ADR-0025)")`: audio
    and TTS do not exist yet, and a fan-out with three of its four stages missing is not
    a fan-out. **G3** — *"a token aborts a streaming generation within 200 ms"* — is
    this file's entire scope: the one stage that exists once `Phase3_Entry_Checklist.md`
    item 2's adapters do. `cancellation.schema.json`'s `fan_out` array, which records
    per-stage status for the full G7 fan-out, is left empty here on purpose — populating
    it now would be inventing G7's tracking ahead of G7's own decision.

WHY A REGISTRY LOOKED UP BY ID, NOT A PASSED OBJECT
    ADR-0025 itself: *"gRPC stream cancellation carries the token to cluster services.
    MCP calls carry it as request metadata."* The token crosses process and network
    boundaries by id, not by reference — `ProviderRequest.cancellation_token_id` is
    already a plain string for exactly this reason. A registry that maps that id to a
    live `threading.Event` is the in-process side of the same design; nothing here
    changes once cancellation needs to cross a boundary this repository does not have
    yet (L2, ADR-0007).

THE 200 MS BUDGET IS CHECKED AT CHUNK BOUNDARIES, NOT PREEMPTED MID-CHUNK
    Every `BrainProvider.stream()` implementation checks `is_cancelled()` after each
    `StreamEvent` it is about to yield, and stops there — emitting one final `done` event
    with `stop_reason: "cancelled"`, which `StopReasonValues`' own description calls *"a
    normal outcome, not an error."* This is a real limitation, stated rather than hidden:
    a Python generator cannot preempt a blocking network read or a single llama.cpp token
    computation already in flight. For streaming text generation, successive chunks
    normally arrive well under 200 ms apart — the check adds microseconds, not the
    budget — but this is not a hard real-time guarantee against one anomalously slow
    chunk. `tests/unit/test_cancellation.py` measures the mechanism's own overhead, not a
    live model's chunk latency, and says so.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

# Reused rather than reimplemented: lionel.memory.service.new_ulid already produces the
# exact ULID shape cancellation.schema.json's `token_id` pins
# (`^[0-9A-HJKMNP-TV-Z]{26}$}`), sortable by creation time, checked by
# tests/contract/ulid_guard.py against the same alphabet. A second generator here would
# be a second thing to keep in step with that pattern.
from lionel.memory.service import new_ulid

__all__ = ["CancellationRegistry", "CancellationToken", "UnknownCancellationToken"]


class UnknownCancellationToken(KeyError):
    """`cancel()` was asked for a token nobody `issue()`d. Distinct from `is_cancelled()`
    returning `False` for an unknown id — a stream that checks a token that was never
    issued is a bug worth finding; a stream that finishes before anyone cancels it is the
    ordinary case, and `is_cancelled()` must not raise for it."""


@dataclass(frozen=True)
class CancellationToken:
    """`contracts/events/v1/cancellation.schema.json`'s shape, as a dataclass with a
    `to_dict()` — the same "explicit typed object with a wire-format escape hatch"
    pattern `StoredRecord` uses in `lionel.memory`, for a schema small enough that a bare
    dict would lose the field names to typos.
    """

    token_id: str
    turn_id: str
    reason: str
    issued_at: str
    issued_by: str
    deadline_ms: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "token_id": self.token_id, "turn_id": self.turn_id, "reason": self.reason,
            "issued_at": self.issued_at, "issued_by": self.issued_by,
        }
        if self.deadline_ms is not None:
            d["deadline_ms"] = self.deadline_ms
        return d


class CancellationRegistry:
    """One per session, matching ADR-0025's own ownership rule — *"A `CancellationToken`
    created by `SessionCoordinator`"* — though nothing in this repository constructs a
    real turn yet to hand this to; it exists so `Phase3_Entry_Checklist.md` item 7 has
    something concrete to check adapters against.

    Thread-safe: `issue()` and `cancel()` may be called from different threads (a
    barge-in detector firing while a generation is mid-stream on another thread is
    exactly the scenario this exists for), guarded by one lock over the two dicts.
    """

    def __init__(self, *, now: Optional[Any] = None):
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._tokens: dict[str, CancellationToken] = {}
        self._events: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def issue(self, *, turn_id: str, reason: str, issued_by: str,
             deadline_ms: Optional[int] = None) -> CancellationToken:
        token_id = new_ulid(int(self._now().timestamp() * 1000))
        token = CancellationToken(
            token_id=token_id, turn_id=turn_id, reason=reason,
            issued_at=self._now().isoformat(), issued_by=issued_by,
            deadline_ms=deadline_ms)
        with self._lock:
            self._tokens[token_id] = token
            self._events[token_id] = threading.Event()
        return token

    def cancel(self, token_id: str) -> None:
        """Idempotent — cancelling an already-cancelled token is a no-op, not an error,
        because two fan-out stages racing to cancel the same turn is the expected case,
        not a bug to report."""
        with self._lock:
            event = self._events.get(token_id)
        if event is None:
            raise UnknownCancellationToken(
                f"no token {token_id!r} — issue() must be called before cancel().")
        event.set()

    def is_cancelled(self, token_id: str) -> bool:
        """`False` for an id this registry never issued. A `stream()` call made with no
        registry injected, or one made after the turn already completed and `release()`d
        its token, must read as 'not cancelled' rather than raise — silence here is the
        ordinary path, not a bug."""
        with self._lock:
            event = self._events.get(token_id)
        return event.is_set() if event is not None else False

    def release(self, token_id: str) -> None:
        """Called once a turn ends, cancelled or not, so a long session's registry does
        not grow by one entry per turn forever."""
        with self._lock:
            self._tokens.pop(token_id, None)
            self._events.pop(token_id, None)
