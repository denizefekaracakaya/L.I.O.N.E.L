"""The `llamacpp` BrainProvider adapter.  ADR-0001, ADR-0009, ADR-0040.

In-process bindings — `llama-cpp-python` — not the HTTP-server shape (ADR-0040's
Decision, item 3). No `httpx`, no SDK client, no network: `capabilities().requires_network`
is `False` here and only here among the three adapters, which is the whole reason this
provider is in `[brain] fallback_chain` at L0 (`config/tiers/l0.toml`).

THE MODEL LOADS LAZILY, ONCE, AND A FAILED LOAD IS REMEMBERED
    `llama_cpp.Llama(model_path=...)` loads the whole model into memory synchronously —
    there is no async "still loading" state the way a separate server process like Ollama
    has, so `health()` cannot observe one either (Phase3_Entry_Checklist.md item 7's
    "`health()` reports not ready while it loads" is written about Ollama specifically,
    the one provider MASTER_PLAN_v2's DoD names by name). What this adapter can and does
    do: load on first use rather than at construction, behind a lock so two turns racing
    the first call do not load the model twice, and remember a load failure rather than
    retrying a broken path on every turn after.

TOKEN COUNTS ARE REAL, THE SPLIT IS DERIVED
    Streaming chat completions carry no `usage` field — confirmed directly against the
    installed `llama_cpp.llama_types` definitions, not assumed. `Llama.n_tokens` is the
    model's own running count of tokens in context, exact before and after a call; the
    delta is the true combined prompt+completion total. The completion half is then
    re-tokenized from the accumulated text to split the total, which can be off by a token
    or two at a boundary — `token_counts_estimated` is `True` for exactly that reason, even
    though every number that goes into it came from the model's own tokenizer, not a
    guess.

TOOL CALLS: SAME SHAPE AS OLLAMA, BETTER LINKED
    `llama-cpp-python`'s chat-completion format is OpenAI-shaped, the same family
    Ollama's is drawn from — tool call arguments typically arrive as one chunk rather than
    incrementally, so `ToolCallDelta.complete` is set on the same delta that carries
    `name` and `arguments_delta`, as `OllamaProvider` already does. Unlike Ollama,
    `ChatCompletionMessageToolCallChunk` carries a real `id`, so — like Anthropic, unlike
    Ollama — `call_id` is the model's own, not synthesized.

`SUPPORTS_TOOLS` IS AN EXPLICIT CONSTRUCTOR FLAG
    Tool-calling support in `llama-cpp-python` depends on the GGUF's chat template and
    the `chat_format`/`chat_handler` the model was loaded with — something this adapter
    cannot detect from the file alone. The operator who chose the model already knows
    whether it was built for tool use, the same reasoning `OllamaProvider.max_context_tokens`
    and `AnthropicProvider`'s pricing already use: explicit over guessed.

VISION IS UNSUPPORTED, SAME REASONING AS THE OTHER TWO
    No ref-fetching capability exists anywhere in this codebase yet; `capabilities().vision`
    is `False` and `stream()` refuses an `image_ref` content block rather than dropping it
    silently.

NOT WITNESSED AGAINST A REAL GGUF MODEL
    No model file was available while this was written — constructing a real `Llama`
    instance downloads or requires gigabytes this environment does not have. Every
    request/chunk shape below is checked directly against the installed
    `llama_cpp.llama_types` TypedDict definitions, and every translated request/response
    against the frozen contracts in `contracts/events/v1/`. `ADR-0041`'s `--live` witness —
    or here, more precisely a `--live-local` one, since nothing about this provider needs
    the network — is what closes the remaining gap.
"""
from __future__ import annotations

import json
import threading
from typing import Any, Iterator, Mapping, Optional

__all__ = ["LlamaCppProvider", "LlamaCppError"]

# `llama_cpp` is imported LAZILY, inside `_default_factory`, and nowhere else in this
# module. Two reasons, the same ones `lionel.memory`'s fastembed import gives:
#
#   1. `python3 -m unittest` must run with it absent. Unlike `anthropic` and `httpx`,
#      PyPI ships NO prebuilt wheel for `llama-cpp-python` — only a source tarball — so
#      installing it in CI means compiling llama.cpp on every run, which is slow on
#      Linux and needs a C++ toolchain configured for pip's build isolation on Windows.
#      Confirmed against the package index directly before writing this line, the same
#      way ADR-0036 checked before blaming the wrong library for a transitive pull.
#   2. A missing package must produce a NAMED error at the point of use, not an
#      ImportError three frames down at construction. Every test in this file injects
#      `llama_factory` directly and never touches this import at all.

_FINISH_REASON_MAP = {
    "stop": "end_turn",
    "length": "max_tokens",
    "tool_calls": "tool_use",
    "function_call": "tool_use",
}


class LlamaCppError(RuntimeError):
    """Raised only when the adapter itself is misused (an unsupported content block) or
    the model fails to load. Never for an ordinary generation failure, which is reported
    as an `error` `StreamEvent`, per the contract's own discriminated union."""


class LlamaCppProvider:
    """`model_path`, `n_ctx` and `supports_tools` are explicit constructor arguments —
    the same "explicit over guessed" reasoning `OllamaProvider.max_context_tokens` and
    `AnthropicProvider`'s per-1k costs already use. None of the three can be discovered
    reliably from the GGUF file alone without loading it, and loading it is exactly the
    expensive step this adapter defers until first use.
    """

    def __init__(self, model_path: str, n_ctx: int, default_max_output_tokens: int, *,
                supports_tools: bool = True, n_gpu_layers: int = 0,
                n_threads: Optional[int] = None,
                llama_factory: Optional[Any] = None):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.default_max_output_tokens = default_max_output_tokens
        self.supports_tools = supports_tools
        self._n_gpu_layers = n_gpu_layers
        self._n_threads = n_threads
        self._factory = llama_factory or self._default_factory
        self._llama: Optional[Any] = None
        self._load_error: Optional[Exception] = None
        self._lock = threading.Lock()

    def _default_factory(self) -> Any:
        try:
            import llama_cpp
        except ImportError as exc:
            raise LlamaCppError(
                f"llama-cpp-python is not installed, so no local model can be loaded "
                f"({exc}). It is declared in pyproject.toml under ADR-0040; run "
                f"`uv sync`. PyPI ships no prebuilt wheel for it, so this needs a C++ "
                f"toolchain — scripts/check_env.sh's `cl` row covers exactly this."
            ) from None
        return llama_cpp.Llama(
            model_path=self.model_path, n_ctx=self.n_ctx,
            n_gpu_layers=self._n_gpu_layers, n_threads=self._n_threads, verbose=False)

    def _ensure_loaded(self) -> Any:
        if self._llama is not None:
            return self._llama
        with self._lock:
            if self._llama is not None:
                return self._llama
            if self._load_error is not None:
                raise self._load_error
            try:
                self._llama = self._factory()
            except Exception as exc:
                self._load_error = exc
                raise
            return self._llama

    # -- BrainProvider -------------------------------------------------------------------

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "llamacpp",
            "model": self.model_path,
            "model_digest": None,
            "native_tools": self.supports_tools,
            "parallel_tool_calls": False,
            "structured_output": True,
            "streaming": True,
            "vision": False,
            "token_counting": True,
            "extended_thinking": False,
            "cancellation": True,
            "max_context_tokens": self.n_ctx,
            "max_output_tokens": self.default_max_output_tokens,
            # tool_call_reliability deliberately absent: its own schema description says
            # "Set from the eval harness (ADR-0021), not self-asserted."
            "requires_network": False,
            "cost_per_1k_input_usd": None,
            "cost_per_1k_output_usd": None,
            "languages": ["en", "tr"],
        }

    def health(self) -> dict[str, Any]:
        from datetime import datetime, timezone
        checked_at = datetime.now(timezone.utc).isoformat()
        try:
            self._ensure_loaded()
        except Exception as exc:
            return {"service": "brain_gateway.llamacpp", "live": True, "ready": False,
                    "state": "error", "checked_at": checked_at,
                    "degraded_reason": f"{type(exc).__name__}: {exc}"}
        return {"service": "brain_gateway.llamacpp", "live": True, "ready": True,
                "state": "ready", "checked_at": checked_at}

    def stream(self, request: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
        turn_id = request["turn_id"]
        seq = [0]

        def emit(**fields) -> dict[str, Any]:
            seq[0] += 1
            return {"turn_id": turn_id, "seq": seq[0], "provider": "llamacpp", **fields}

        try:
            llama = self._ensure_loaded()
        except Exception as exc:
            yield emit(type="error", error={
                "code": "unavailable", "message": f"model failed to load: {exc}",
                "retryable": False})
            return

        kwargs = self._build_kwargs(request)
        n_before = llama.n_tokens
        try:
            chunks = llama.create_chat_completion(**kwargs)
            yield from self._consume(llama, chunks, n_before, emit)
        except (ValueError, RuntimeError) as exc:
            yield emit(type="error", error={
                "code": "invalid_arguments" if isinstance(exc, ValueError) else "internal",
                "message": str(exc), "retryable": isinstance(exc, RuntimeError)})
        except MemoryError as exc:
            yield emit(type="error", error={
                "code": "internal", "message": f"out of memory: {exc}", "retryable": False})

    def _consume(self, llama: Any, chunks: Iterator[dict], n_before: int,
                emit) -> Iterator[dict[str, Any]]:
        text_parts: list[str] = []
        call_index = [0]
        open_call: Optional[dict] = None
        finish_reason: Optional[str] = None

        for chunk in chunks:
            choice = chunk["choices"][0]
            delta = choice.get("delta", {})

            content = delta.get("content")
            if content:
                text_parts.append(content)
                yield emit(type="text_delta", text=content)

            for tc in delta.get("tool_calls") or []:
                fn = tc.get("function", {})
                if tc.get("id") or open_call is None:
                    open_call = {"call_id": tc.get("id") or f"llamacpp-{call_index[0]}",
                                "index": call_index[0], "name_sent": False}
                    call_index[0] += 1
                fields: dict[str, Any] = {"call_id": open_call["call_id"],
                                          "index": open_call["index"]}
                if fn.get("name") and not open_call["name_sent"]:
                    fields["name"] = fn["name"]
                    open_call["name_sent"] = True
                if fn.get("arguments"):
                    fields["arguments_delta"] = fn["arguments"]
                yield emit(type="tool_call_delta", tool_call=fields)

            if choice.get("finish_reason"):
                finish_reason = choice["finish_reason"]
                if open_call is not None:
                    yield emit(type="tool_call_delta", tool_call={
                        "call_id": open_call["call_id"], "index": open_call["index"],
                        "complete": True})

        total_tokens = max(llama.n_tokens - n_before, 0)
        generated_text = "".join(text_parts)
        completion_tokens = len(llama.tokenize(generated_text.encode("utf-8"),
                                               add_bos=False)) if generated_text else 0
        prompt_tokens = max(total_tokens - completion_tokens, 0)
        yield emit(type="usage", usage={
            "input_tokens": prompt_tokens, "output_tokens": completion_tokens,
            "estimated_cost_usd": None, "token_counts_estimated": True})
        yield emit(type="done", stop_reason=_FINISH_REASON_MAP.get(
            finish_reason or "stop", "provider_error"))

    def _build_kwargs(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if request.get("response_schema") is not None:
            raise LlamaCppError(
                "response_schema is not supported by this adapter yet: mapping a "
                "ParameterSchema onto llama-cpp-python's grammar-backed response_format "
                "needs its own verification and is not wired.")

        messages = []
        system = request.get("system")
        if system:
            messages.append({"role": "system", "content": system})
        messages.extend(_translate_message(m) for m in request["messages"])

        kwargs: dict[str, Any] = {
            "messages": messages, "stream": True,
            "max_tokens": request.get("max_output_tokens") or self.default_max_output_tokens,
        }

        tools = request.get("tools") or []
        choice = request.get("tool_choice", "auto")
        if tools and choice != "none" and self.supports_tools:
            kwargs["tools"] = [_translate_tool(t) for t in tools]
            kwargs["tool_choice"] = choice

        if request.get("temperature") is not None:
            kwargs["temperature"] = request["temperature"]

        return kwargs


def _translate_message(message: Mapping[str, Any]) -> dict[str, Any]:
    role = message["role"]
    content = message["content"]

    if role == "tool_result":
        text = content if isinstance(content, str) else "".join(
            b.get("text", "") for b in content if b["type"] in ("text", "tool_result"))
        return {"role": "tool", "tool_call_id": message["call_id"], "content": text}

    if isinstance(content, str):
        return {"role": role, "content": content}

    text_parts = []
    tool_calls = []
    for block in content:
        btype = block["type"]
        if btype in ("text", "tool_result"):
            text_parts.append(block.get("text", ""))
        elif btype == "tool_use":
            tool_calls.append({
                "id": block["call_id"], "type": "function",
                "function": {"name": block["name"],
                            "arguments": json.dumps(block.get("input", {}))},
            })
        elif btype == "image_ref":
            raise LlamaCppError(
                "LlamaCppProvider.capabilities().vision is False; an image_ref content "
                "block was passed anyway. Fetching and inlining the referenced image is "
                "not something this adapter does.")
        else:
            raise LlamaCppError(f"unknown ContentBlock.type {btype!r}")

    result: dict[str, Any] = {"role": role, "content": "".join(text_parts)}
    if tool_calls:
        result["tool_calls"] = tool_calls
    return result


def _translate_tool(tool: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {"name": tool["name"], "description": tool["description"],
                    "parameters": tool["input_schema"]},
    }
