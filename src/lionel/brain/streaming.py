"""Aggregating a `StreamEvent` sequence into a `ProviderResponse`.  ADR-0009.

WHY THIS IS PROVIDER-AGNOSTIC AND LIVES OUTSIDE `providers/`
    `contracts/events/v1/provider-response.schema.json`'s own description: *"StreamEvent
    carries the incremental view; this is the terminal one, produced after the stream
    closes. Both exist because TurnExecutor needs incremental deltas for low-latency TTS
    chunking AND a settled object for the transcript, replay tests, and cost accounting."*
    Turning one into the other is arithmetic over a discriminated union, not provider
    behaviour — every adapter that emits valid `StreamEvent`s needs the identical
    aggregation, and writing it three times (once per adapter) is three chances for the
    copies to drift, the exact shape `ADR-0039` found four times over in the contracts
    themselves. One function, called by every adapter and by `ADR-0041`'s eventual replay
    harness alike.

WHY TOOL-CALL ARGUMENTS ARE PARSED HERE AND NOWHERE EARLIER
    `ToolCallDelta.arguments_delta` is "Partial JSON text. Accumulate across deltas; parse
    ONLY after `complete` is true." Parsing a partial fragment is, in that field's own
    words, "the classic streaming tool-call bug." This function is the one place a
    `tool_call_delta`'s accumulated text is finally handed to `json.loads` — after the
    matching delta's `complete: true`, never before.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

__all__ = ["aggregate_stream", "AggregationError"]


class AggregationError(ValueError):
    """The event sequence did not shape into a valid `ProviderResponse` — for example, a
    `tool_call_delta` marked `complete` whose accumulated text is not valid JSON, or a
    stream that produced no terminal `done`/`error` event at all."""


class _ToolCallBuilder:
    __slots__ = ("index", "name", "arguments_text", "complete")

    def __init__(self, index: int) -> None:
        self.index = index
        self.name: str | None = None
        self.arguments_text = ""
        self.complete = False


def aggregate_stream(*, request_id: str, turn_id: str, provider: str, model: str,
                     events: Iterable[Mapping[str, Any]],
                     model_digest: str | None = None) -> dict[str, Any]:
    """Consume every `StreamEvent` in `events` and return a `ProviderResponse` dict.

    `events` is exhausted eagerly — aggregation cannot start until the stream ends, which
    is the same constraint the contract's own description states. Pass a generator from
    `BrainProvider.stream()` directly; this function does the accumulating, `for` loop and
    all, so callers needing only the terminal object do not have to write it themselves.
    """
    started = datetime.now(timezone.utc)
    text_parts: list[str] = []
    thinking_parts: list[str] = []
    tool_calls_by_id: dict[str, _ToolCallBuilder] = {}
    order: list[str] = []
    usage: dict[str, Any] | None = None
    stop_reason: str | None = None
    error: dict[str, Any] | None = None
    first_token_at: datetime | None = None
    seen_terminal = False

    for event in events:
        etype = event.get("type")
        if etype in ("text_delta", "thinking_delta") and first_token_at is None:
            first_token_at = datetime.now(timezone.utc)

        if etype == "text_delta":
            text_parts.append(event["text"])
        elif etype == "thinking_delta":
            thinking_parts.append(event["text"])
        elif etype == "tool_call_delta":
            delta = event["tool_call"]
            call_id = delta["call_id"]
            if call_id not in tool_calls_by_id:
                tool_calls_by_id[call_id] = _ToolCallBuilder(delta["index"])
                order.append(call_id)
            builder = tool_calls_by_id[call_id]
            if "name" in delta:
                builder.name = delta["name"]
            if "arguments_delta" in delta:
                builder.arguments_text += delta["arguments_delta"]
            if delta.get("complete"):
                builder.complete = True
        elif etype == "usage":
            usage = dict(event["usage"])
        elif etype == "done":
            stop_reason = event["stop_reason"]
            seen_terminal = True
        elif etype == "error":
            error = dict(event["error"])
            seen_terminal = True
        # Unknown `type` values are skipped, not rejected — stream-event.schema.json's own
        # discriminator description: "CONSUMERS MUST SKIP UNKNOWN VALUES rather than
        # failing," so a newer adapter can run against an older aggregator during a
        # rolling upgrade.

    if not seen_terminal:
        raise AggregationError(
            "the event stream ended with no `done` or `error` event — a ProviderResponse "
            "needs a stop_reason, and there is none to report.")

    tool_calls: list[dict[str, Any]] = []
    for call_id in order:
        builder = tool_calls_by_id[call_id]
        if not builder.complete:
            raise AggregationError(
                f"tool call {call_id!r} never received a delta with complete: true — its "
                f"arguments cannot be parsed without one.")
        if builder.name is None:
            raise AggregationError(f"tool call {call_id!r} completed with no `name`.")
        try:
            arguments = json.loads(builder.arguments_text) if builder.arguments_text else {}
        except json.JSONDecodeError as exc:
            raise AggregationError(
                f"tool call {call_id!r}: accumulated arguments_delta is not valid JSON "
                f"once complete — {exc}") from None
        tool_calls.append({
            "call_id": call_id, "index": builder.index,
            "name": builder.name, "arguments": arguments,
        })

    completed = datetime.now(timezone.utc)
    response: dict[str, Any] = {
        "request_id": request_id,
        "turn_id": turn_id,
        "provider": provider,
        "model": model,
        "model_digest": model_digest,
        "text": "".join(text_parts),
        "thinking": "".join(thinking_parts) or None,
        "tool_calls": tool_calls,
        "structured_output": None,
        "stop_reason": stop_reason if stop_reason is not None else "provider_error",
        "usage": usage or {"input_tokens": 0, "output_tokens": 0},
        "completed_at": completed.isoformat(),
        "first_token_ms": (
            (first_token_at - started).total_seconds() * 1000
            if first_token_at is not None else None),
        "total_ms": (completed - started).total_seconds() * 1000,
    }
    if error is not None:
        response["error"] = error
    return response
