"""The `ollama` BrainProvider adapter.  ADR-0001, ADR-0009, ADR-0040.

Called over `httpx` directly — ADR-0040's decision, item 2: Ollama's `/api/chat` is plain
HTTP/JSON with nothing a hand-rolled layer gets subtly wrong, and taking the `ollama`
package would be `DEP-002`'s drift, declared on purpose rather than discovered by a gate.

WHAT THIS ADAPTER DOES AND DOES NOT DO
    `stream()` is the only primitive: it translates one `ProviderRequest` into Ollama's
    `/api/chat` request, and translates Ollama's NDJSON stream into `StreamEvent` objects.
    Turning those events into a `ProviderResponse` is `lionel.brain.streaming.
    aggregate_stream` — provider-agnostic on purpose, so this file has no aggregation logic
    to keep in step with the other two adapters.

    `capabilities()` is pure — no network call — because ADR-0036's precedent for
    `FastEmbedEmbedder` already established the rule this repository holds construction
    and cheap getters to: a caller has to be able to tell "not configured" from "cannot
    reach the provider," and collapsing them removes the distinction before anyone can act
    on it. `health()` is where the network call lives.

VISION IS UNSUPPORTED, ON PURPOSE
    `ProviderCapabilities.vision` is `False` here. Translating an `image_ref` content block
    into Ollama's `images` field would mean fetching the bytes the `ref` points at and
    base64-encoding them — a capability (fetching a referenced image) this adapter does not
    have and ADR-0006 keeps off the wire anyway. `stream()` refuses an `image_ref` block
    rather than silently dropping it.

TOOL CALLS ARRIVE WHOLE, NOT INCREMENTALLY
    Ollama does not stream a tool call's arguments token by token the way some providers'
    native tool-use formats do — the whole `arguments` object appears in one response
    chunk. Each tool call still goes through the `ToolCallDelta` protocol properly: one
    delta, `complete: true`, `arguments_delta` holding the full JSON text. A single-delta
    call is a valid call under `contracts/events/v1/stream-event.schema.json`, not a
    shortcut around it.

CALL IDS: A --LIVE CORRECTION
    This module first shipped assuming Ollama's response never names a tool call, and
    synthesized `ollama-<n>` unconditionally. A `--live` run against Ollama 0.34.1
    (`qwen2.5:3b-instruct`) on 2026-09-17 showed that assumption was wrong: the real wire
    response carries `tool_calls[].id` (`"call_uukikxqs"`, observed directly, not a doc
    guess). The adapter now prefers that id and only synthesizes `ollama-<n>` when it is
    absent — an older server, or a model whose chat template omits it. `ADR-0041`'s own
    reasoning for `--live` existing at all: contract fixtures built from documentation
    reviewed once and never run are exactly the failure shape `Phase2_Final_Signoff.md`
    §1 found four times over.

NOT WITNESSED AGAINST A LIVE OLLAMA
    No Ollama instance was reachable in the environment this was written in. Every line of
    request/response translation is checked against `contracts/events/v1/*.schema.json`
    directly and against Ollama's documented `/api/chat` shape via `httpx.MockTransport` —
    real assertions against the real contracts, with no live model on the other end. A
    `--live` witness, the same shape `check_env.sh` and `verify_memory.sh` already use,
    belongs to `ADR-0041`'s harness once one exists to run it against.
"""
from __future__ import annotations

import json
from typing import Any, Iterator, Mapping, Optional

import httpx

from lionel.brain.cancellation import CancellationRegistry

__all__ = ["OllamaProvider", "OllamaError"]

_STOP_REASON_MAP = {
    "stop": "end_turn",
    "length": "max_tokens",
}
_LOAD_EVENT_REASONS = {"load", "unload"}


class OllamaError(RuntimeError):
    """Raised only when the adapter itself is misused (a caller passing an unsupported
    content block, for example) — never for a provider-side failure, which is reported as
    an `error` `StreamEvent` instead, per the contract's own discriminated union."""


class OllamaProvider:
    """`base_url`, `model` and `max_context_tokens` are all explicit constructor
    arguments — no config file is read here. `max_context_tokens` is genuinely
    model-specific and Ollama exposes it only through per-model-family keys in
    `/api/show`'s `model_info` (`"qwen2.context_length"`, `"llama.context_length"`, ...)
    that this adapter does not try to parse; the operator who chose the model already
    knows its context window, and a wrong guess here would silently mis-size every prompt
    this provider ever receives.
    """

    def __init__(self, base_url: str, model: str, max_context_tokens: int, *,
                client: httpx.Client | None = None, timeout_s: float = 120.0,
                cancellation_registry: Optional[CancellationRegistry] = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_context_tokens = max_context_tokens
        self._client = client or httpx.Client(timeout=timeout_s)
        self._owns_client = client is None
        self._cancellation = cancellation_registry

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    # -- BrainProvider -------------------------------------------------------------------

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "ollama",
            "model": self.model,
            "model_digest": None,
            "native_tools": True,
            "parallel_tool_calls": False,
            "structured_output": True,
            "streaming": True,
            "vision": False,
            "token_counting": True,
            "extended_thinking": False,
            "cancellation": True,
            "max_context_tokens": self.max_context_tokens,
            "max_output_tokens": None,
            # tool_call_reliability deliberately absent: its own schema description says
            # "Set from the eval harness (ADR-0021), not self-asserted." An adapter has no
            # eval results to report yet — that is ADR-0021's G8 leaderboard's job, once
            # ADR-0041's replay harness exists to feed it.
            "requires_network": False,
            "cost_per_1k_input_usd": None,
            "cost_per_1k_output_usd": None,
            "languages": ["en", "tr"],
        }

    def health(self) -> dict[str, Any]:
        from datetime import datetime, timezone
        checked_at = datetime.now(timezone.utc).isoformat()
        try:
            self._client.get(f"{self.base_url}/api/version", timeout=5.0).raise_for_status()
        except httpx.HTTPError as exc:
            return {
                "service": "brain_gateway.ollama", "live": False, "ready": False,
                "state": "unreachable", "checked_at": checked_at,
                "degraded_reason": f"{type(exc).__name__}: {exc}",
            }
        try:
            resp = self._client.get(f"{self.base_url}/api/ps", timeout=5.0)
            resp.raise_for_status()
            loaded = {m.get("model") or m.get("name") for m in resp.json().get("models", [])}
        except httpx.HTTPError as exc:
            return {
                "service": "brain_gateway.ollama", "live": True, "ready": False,
                "state": "degraded", "checked_at": checked_at,
                "degraded_reason": f"reachable but /api/ps failed: {exc}",
            }
        if self.model in loaded:
            return {"service": "brain_gateway.ollama", "live": True, "ready": True,
                    "state": "ready", "checked_at": checked_at}
        # Ollama has no "actively loading right now" signal distinct from "not loaded
        # yet" through a plain GET — a request for an unloaded model triggers a load on
        # demand. "loading" is the honest label for "alive, model not resident," even
        # though it is an approximation of a state Ollama does not expose directly.
        return {"service": "brain_gateway.ollama", "live": True, "ready": False,
                "state": "loading", "checked_at": checked_at,
                "degraded_reason": f"{self.model!r} is not currently loaded"}

    def stream(self, request: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
        turn_id = request["turn_id"]
        token_id = request.get("cancellation_token_id")
        payload = self._build_payload(request)
        seq = [0]

        def emit(**fields) -> dict[str, Any]:
            seq[0] += 1
            return {"turn_id": turn_id, "seq": seq[0], "provider": "ollama", **fields}

        timeout = (request.get("deadline_ms") or 0) / 1000 or None
        try:
            with self._client.stream("POST", f"{self.base_url}/api/chat", json=payload,
                                     timeout=timeout) as response:
                response.raise_for_status()
                yield from self._consume(response, emit, token_id)
        except httpx.HTTPStatusError as exc:
            yield emit(type="error", error=_http_status_error(exc))
        except httpx.TimeoutException as exc:
            yield emit(type="error", error={
                "code": "timeout", "message": str(exc) or "request timed out",
                "retryable": True})
        except httpx.HTTPError as exc:
            yield emit(type="error", error={
                "code": "unavailable", "message": f"{type(exc).__name__}: {exc}",
                "retryable": True})

    def _consume(self, response: httpx.Response, emit,
                token_id: Optional[str] = None) -> Iterator[dict[str, Any]]:
        tool_call_index = [0]
        for line in response.iter_lines():
            # Checked at every chunk boundary — the earliest point a generator can act
            # without preempting an in-flight network read. See the module docstring in
            # lionel.brain.cancellation for the honest limit of this bound.
            if (self._cancellation is not None and token_id is not None
                    and self._cancellation.is_cancelled(token_id)):
                yield emit(type="done", stop_reason="cancelled")
                return
            if not line:
                continue
            chunk = json.loads(line)
            message = chunk.get("message") or {}

            content = message.get("content")
            if content:
                yield emit(type="text_delta", text=content)

            for call in message.get("tool_calls", []):
                fn = call.get("function", {})
                cid = call.get("id") or f"ollama-{tool_call_index[0]}"
                tool_call_index[0] += 1
                yield emit(type="tool_call_delta", tool_call={
                    "call_id": cid, "index": tool_call_index[0] - 1,
                    "name": fn.get("name", ""),
                    "arguments_delta": json.dumps(fn.get("arguments", {})),
                    "complete": True,
                })

            if chunk.get("done"):
                prompt_n = chunk.get("prompt_eval_count")
                eval_n = chunk.get("eval_count")
                if prompt_n is not None or eval_n is not None:
                    yield emit(type="usage", usage={
                        "input_tokens": prompt_n or 0, "output_tokens": eval_n or 0,
                        "estimated_cost_usd": None, "token_counts_estimated": False,
                    })
                yield emit(type="done", stop_reason=self._stop_reason(
                    chunk.get("done_reason"), tool_call_index[0] > 0))
                return

    @staticmethod
    def _stop_reason(done_reason: str | None, made_tool_calls: bool) -> str:
        if done_reason in _LOAD_EVENT_REASONS:
            return "provider_error"
        if done_reason == "stop" and made_tool_calls:
            return "tool_use"
        return _STOP_REASON_MAP.get(done_reason or "stop", "provider_error")

    def _build_payload(self, request: Mapping[str, Any]) -> dict[str, Any]:
        messages = []
        system = request.get("system")
        if system:
            messages.append({"role": "system", "content": system})
        messages.extend(_translate_message(m) for m in request["messages"])

        payload: dict[str, Any] = {
            "model": self.model, "messages": messages, "stream": True,
        }

        tools = request.get("tools") or []
        if tools and request.get("tool_choice", "auto") != "none":
            payload["tools"] = [_translate_tool(t) for t in tools]

        response_schema = request.get("response_schema")
        if response_schema is not None:
            payload["format"] = response_schema

        options: dict[str, Any] = {}
        if request.get("max_output_tokens") is not None:
            options["num_predict"] = request["max_output_tokens"]
        if request.get("temperature") is not None:
            options["temperature"] = request["temperature"]
        if options:
            payload["options"] = options

        return payload


def _translate_message(message: Mapping[str, Any]) -> dict[str, Any]:
    role = message["role"]
    ollama_role = "tool" if role == "tool_result" else role
    content = message["content"]
    if isinstance(content, str):
        return {"role": ollama_role, "content": content}

    text_parts = []
    tool_calls = []
    for block in content:
        btype = block["type"]
        if btype == "text":
            text_parts.append(block["text"])
        elif btype == "tool_result":
            text_parts.append(block.get("text", ""))
        elif btype == "tool_use":
            tool_calls.append({"function": {"name": block["name"],
                                            "arguments": block.get("input", {})}})
        elif btype == "image_ref":
            raise OllamaError(
                "OllamaProvider.capabilities().vision is False; an image_ref content "
                "block was passed anyway. Fetching and inlining the referenced image is "
                "not something this adapter does.")
        else:
            raise OllamaError(f"unknown ContentBlock.type {btype!r}")

    result: dict[str, Any] = {"role": ollama_role, "content": "".join(text_parts)}
    if tool_calls:
        result["tool_calls"] = tool_calls
    return result


def _translate_tool(tool: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
        },
    }


def _http_status_error(exc: httpx.HTTPStatusError) -> dict[str, Any]:
    status = exc.response.status_code
    code = "not_found" if status == 404 else "internal"
    return {"code": code, "message": f"Ollama returned HTTP {status}",
            "retryable": status >= 500, "detail": exc.response.text[:500]}
