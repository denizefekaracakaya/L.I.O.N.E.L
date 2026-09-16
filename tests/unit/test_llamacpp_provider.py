"""`LlamaCppProvider`.  ADR-0001, ADR-0009, ADR-0040, ADR-0027 layer 1.

No GGUF model file was available while this was written — constructing a real
`llama_cpp.Llama` needs gigabytes this environment does not have. A `FakeLlama` test
double stands in, implementing exactly the surface the adapter reads
(`n_tokens`, `create_chat_completion`, `tokenize`) — verified directly against the
installed `llama_cpp` package (`n_tokens` is a real instance attribute set in
`llama.py`'s `eval()`; streaming chunks carry no `usage` field, confirmed against
`llama_cpp.llama_types.CreateChatCompletionStreamResponse`'s own definition).

Every request this adapter builds and every event it yields is checked against the real
frozen contracts, through `test_brain_contract.py`'s offline `$ref` registry.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "contract"))

from lionel.brain.providers.llamacpp_provider import (  # noqa: E402
    LlamaCppError, LlamaCppProvider,
)
from lionel.brain.streaming import aggregate_stream  # noqa: E402

try:
    from test_brain_contract import CORE, EVENTS, load, valid  # noqa: E402
    _HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover - jsonschema is CI tooling
    _HAVE_JSONSCHEMA = False

TURN = "01JQ4X8ZK9P2M7VN3RTYB6WCDE"
REQUEST_ID = "01JQ4X8ZK9P2M7VN3RTYB6WCDA"
TOKEN = "01JQ4XB2M5N8P1QRST2VWX3YZA"


def base_request(**overrides) -> dict:
    r = {
        "request_id": REQUEST_ID, "turn_id": TURN,
        "messages": [{"role": "user", "content": "hi"}],
        "cancellation_token_id": TOKEN,
    }
    r.update(overrides)
    return r


def chunk(content: str = None, tool_calls=None, finish_reason=None) -> dict:
    delta = {}
    if content is not None:
        delta["content"] = content
    if tool_calls is not None:
        delta["tool_calls"] = tool_calls
    return {"id": "x", "model": "m", "object": "chat.completion.chunk", "created": 0,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}]}


class FakeLlama:
    """Implements exactly what `LlamaCppProvider` reads from a real `llama_cpp.Llama`:
    `.n_tokens` (the model's own running context-token count, exact before and after a
    call — verified against `llama.py`'s `self.n_tokens += n_tokens` in `eval()`),
    `.create_chat_completion(**kwargs)`, and `.tokenize(bytes, add_bos=...)`.
    """

    def __init__(self, chunks: list[dict], tokens_consumed: int = 20,
                tokenize_words: bool = True):
        self.n_tokens = 0
        self._chunks = chunks
        self._tokens_consumed = tokens_consumed
        self._tokenize_words = tokenize_words
        self.captured_kwargs = None

    def create_chat_completion(self, **kwargs):
        self.captured_kwargs = kwargs
        self.n_tokens += self._tokens_consumed
        return iter(self._chunks)

    def tokenize(self, data: bytes, add_bos: bool = True) -> list[int]:
        # A word-count stand-in for a real tokenizer — sufficient to test that the
        # completion/prompt SPLIT arithmetic is correct, not to test real token counts.
        text = data.decode("utf-8")
        n = len(text.split()) if self._tokenize_words else len(text)
        return list(range(n))


def make_provider(chunks=None, tokens_consumed: int = 20, load_error: Exception = None,
                  **kwargs) -> tuple[LlamaCppProvider, "_FactoryState"]:
    state = _FactoryState()

    def factory():
        if load_error is not None:
            raise load_error
        state.llama = FakeLlama(chunks or [], tokens_consumed=tokens_consumed)
        return state.llama

    provider = LlamaCppProvider("models/x.gguf", 8192, 4096, llama_factory=factory,
                                **kwargs)
    return provider, state


class _FactoryState:
    llama: FakeLlama = None


class TestLazyLoading(unittest.TestCase):
    def test_the_model_is_not_loaded_at_construction(self):
        loaded = []
        provider = LlamaCppProvider("x", 8192, 4096,
                                    llama_factory=lambda: loaded.append(1) or FakeLlama([]))
        self.assertEqual([], loaded)

    def test_the_model_loads_on_first_stream_call(self):
        provider, state = make_provider(chunks=[chunk(content="hi", finish_reason="stop")])
        list(provider.stream(base_request()))
        self.assertIsNotNone(state.llama)

    def test_a_second_call_does_not_reload(self):
        calls = []

        def factory():
            calls.append(1)
            return FakeLlama([chunk(content="hi", finish_reason="stop")])

        provider = LlamaCppProvider("x", 8192, 4096, llama_factory=factory)
        list(provider.stream(base_request()))
        list(provider.stream(base_request()))
        self.assertEqual(1, len(calls))

    def test_a_load_failure_is_remembered_rather_than_retried(self):
        calls = []

        def factory():
            calls.append(1)
            raise ValueError("bad model")

        provider = LlamaCppProvider("x", 8192, 4096, llama_factory=factory)
        list(provider.stream(base_request()))
        list(provider.stream(base_request()))
        self.assertEqual(1, len(calls))

    def test_a_load_failure_surfaces_as_an_error_event_not_an_exception(self):
        provider, _ = make_provider(load_error=ValueError("bad model"))
        events = list(provider.stream(base_request()))
        self.assertEqual(1, len(events))
        self.assertEqual("error", events[0]["type"])
        self.assertFalse(events[0]["error"]["retryable"])


class TestRequestTranslation(unittest.TestCase):
    def _sent_kwargs(self, request: dict, **provider_kwargs) -> dict:
        provider, state = make_provider(
            chunks=[chunk(content="ok", finish_reason="stop")], **provider_kwargs)
        list(provider.stream(request))
        return state.llama.captured_kwargs

    def test_plain_text_message_translates_directly(self):
        kwargs = self._sent_kwargs(base_request(
            messages=[{"role": "user", "content": "hello"}]))
        self.assertEqual([{"role": "user", "content": "hello"}], kwargs["messages"])

    def test_system_prepends_a_system_message(self):
        kwargs = self._sent_kwargs(base_request(system="be terse"))
        self.assertEqual("system", kwargs["messages"][0]["role"])
        self.assertEqual("be terse", kwargs["messages"][0]["content"])

    def test_tool_result_role_becomes_tool_with_a_linked_call_id(self):
        kwargs = self._sent_kwargs(base_request(messages=[
            {"role": "user", "content": "hi"},
            {"role": "tool_result", "content": "42", "call_id": "call_1"},
        ]))
        second = kwargs["messages"][1]
        self.assertEqual("tool", second["role"])
        self.assertEqual("call_1", second["tool_call_id"])
        self.assertEqual("42", second["content"])

    def test_tool_use_content_block_carries_real_call_id_and_json_string_arguments(self):
        kwargs = self._sent_kwargs(base_request(messages=[
            {"role": "assistant", "content": [
                {"type": "tool_use", "call_id": "call_1", "name": "fs.read",
                 "input": {"path": "x"}},
            ]},
        ]))
        tc = kwargs["messages"][0]["tool_calls"][0]
        self.assertEqual("call_1", tc["id"])
        self.assertEqual({"path": "x"}, json.loads(tc["function"]["arguments"]))

    def test_an_image_ref_block_is_refused(self):
        with self.assertRaises(LlamaCppError):
            self._sent_kwargs(base_request(messages=[
                {"role": "user", "content": [{"type": "image_ref", "ref": "handle://x"}]},
            ]))

    def test_response_schema_is_refused(self):
        with self.assertRaises(LlamaCppError):
            self._sent_kwargs(base_request(response_schema={"type": "object"}))

    def test_tools_translate_to_the_openai_compatible_shape(self):
        kwargs = self._sent_kwargs(base_request(tools=[
            {"name": "fs.read", "description": "read a file",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
             "side_effect": "read", "trust_required": "any"},
        ]))
        self.assertEqual([{"type": "function", "function": {
            "name": "fs.read", "description": "read a file",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}}],
                         kwargs["tools"])

    def test_tool_choice_passes_through_unchanged(self):
        kwargs = self._sent_kwargs(base_request(
            tools=[{"name": "a", "description": "d", "input_schema": {},
                   "side_effect": "read", "trust_required": "any"}],
            tool_choice="required"))
        self.assertEqual("required", kwargs["tool_choice"])

    def test_tool_choice_none_omits_tools(self):
        kwargs = self._sent_kwargs(base_request(
            tools=[{"name": "a", "description": "d", "input_schema": {},
                   "side_effect": "read", "trust_required": "any"}],
            tool_choice="none"))
        self.assertNotIn("tools", kwargs)

    def test_supports_tools_false_omits_tools_even_when_offered(self):
        kwargs = self._sent_kwargs(base_request(
            tools=[{"name": "a", "description": "d", "input_schema": {},
                   "side_effect": "read", "trust_required": "any"}]),
            supports_tools=False)
        self.assertNotIn("tools", kwargs)

    def test_max_output_tokens_overrides_the_default(self):
        kwargs = self._sent_kwargs(base_request(max_output_tokens=256))
        self.assertEqual(256, kwargs["max_tokens"])

    def test_stream_is_always_true(self):
        kwargs = self._sent_kwargs(base_request())
        self.assertTrue(kwargs["stream"])


class TestStreamEventTranslation(unittest.TestCase):
    def _events(self, chunks: list[dict], **kwargs) -> list[dict]:
        provider, _ = make_provider(chunks=chunks, **kwargs)
        return list(provider.stream(base_request()))

    def test_content_chunks_become_text_deltas(self):
        events = self._events([
            chunk(content="Hel"), chunk(content="lo"), chunk(finish_reason="stop"),
        ])
        texts = [e["text"] for e in events if e["type"] == "text_delta"]
        self.assertEqual(["Hel", "lo"], texts)

    def test_a_tool_call_carries_the_models_own_id(self):
        events = self._events([
            chunk(tool_calls=[{"index": 0, "id": "call_xyz",
                              "function": {"name": "fs.read", "arguments": "{}"}}]),
            chunk(finish_reason="tool_calls"),
        ])
        deltas = [e["tool_call"] for e in events if e["type"] == "tool_call_delta"]
        self.assertEqual("call_xyz", deltas[0]["call_id"])

    def test_a_tool_call_forces_stop_reason_tool_use(self):
        events = self._events([
            chunk(tool_calls=[{"index": 0, "id": "call_1",
                              "function": {"name": "a", "arguments": "{}"}}]),
            chunk(finish_reason="tool_calls"),
        ])
        done = [e for e in events if e["type"] == "done"][0]
        self.assertEqual("tool_use", done["stop_reason"])

    def test_the_final_delta_marks_complete(self):
        events = self._events([
            chunk(tool_calls=[{"index": 0, "id": "call_1",
                              "function": {"name": "a", "arguments": "{}"}}]),
            chunk(finish_reason="tool_calls"),
        ])
        deltas = [e["tool_call"] for e in events if e["type"] == "tool_call_delta"]
        self.assertTrue(deltas[-1]["complete"])

    def test_length_finish_reason_maps_to_max_tokens(self):
        events = self._events([chunk(content="x", finish_reason="length")])
        done = [e for e in events if e["type"] == "done"][0]
        self.assertEqual("max_tokens", done["stop_reason"])

    def test_usage_is_derived_from_the_real_context_token_delta(self):
        # 20 tokens consumed total (FakeLlama default); "one two three" tokenizes to 3
        # words with the FakeLlama tokenizer, so prompt = 20 - 3 = 17.
        events = self._events(
            [chunk(content="one two three", finish_reason="stop")], tokens_consumed=20)
        usage = [e["usage"] for e in events if e["type"] == "usage"][0]
        self.assertEqual(3, usage["output_tokens"])
        self.assertEqual(17, usage["input_tokens"])
        self.assertTrue(usage["token_counts_estimated"])

    def test_usage_never_goes_negative_when_the_split_overshoots(self):
        events = self._events(
            [chunk(content="one two three four five", finish_reason="stop")],
            tokens_consumed=2)
        usage = [e["usage"] for e in events if e["type"] == "usage"][0]
        self.assertGreaterEqual(usage["input_tokens"], 0)

    def test_every_event_carries_provider_and_the_requests_turn_id(self):
        events = self._events([chunk(content="x", finish_reason="stop")])
        for e in events:
            self.assertEqual("llamacpp", e["provider"])
            self.assertEqual(TURN, e["turn_id"])


class TestHealth(unittest.TestCase):
    def test_a_loadable_model_reports_ready(self):
        provider, _ = make_provider(chunks=[])
        h = provider.health()
        self.assertTrue(h["live"])
        self.assertTrue(h["ready"])
        self.assertEqual("ready", h["state"])

    def test_an_unloadable_model_reports_not_ready(self):
        provider, _ = make_provider(load_error=ValueError("bad model"))
        h = provider.health()
        self.assertTrue(h["live"])
        self.assertFalse(h["ready"])
        self.assertEqual("error", h["state"])


@unittest.skipUnless(_HAVE_JSONSCHEMA, "jsonschema not installed (pyproject `ci` extra)")
class TestOutputsValidateAgainstTheRealContracts(unittest.TestCase):
    def test_capabilities_validates(self):
        schema = load(EVENTS / "provider-capabilities.schema.json")
        provider = LlamaCppProvider("models/x.gguf", 8192, 4096)
        self.assertTrue(valid(schema, provider.capabilities()))

    def test_health_validates(self):
        schema = load(CORE / "health-status.schema.json")
        provider, _ = make_provider(chunks=[])
        self.assertTrue(valid(schema, provider.health()))

    def test_every_emitted_event_individually_validates(self):
        stream_schema = load(EVENTS / "stream-event.schema.json")
        provider, _ = make_provider(chunks=[
            chunk(content="Sure, "), chunk(content="one moment."),
            chunk(tool_calls=[{"index": 0, "id": "call_1",
                              "function": {"name": "fs.read",
                                          "arguments": '{"path": "x"}'}}]),
            chunk(finish_reason="tool_calls"),
        ])
        for event in provider.stream(base_request()):
            with self.subTest(type=event["type"]):
                self.assertTrue(valid(stream_schema, event), json.dumps(event))

    def test_a_full_streamed_turn_aggregates_to_a_valid_provider_response(self):
        response_schema = load(EVENTS / "provider-response.schema.json")
        provider, _ = make_provider(chunks=[
            chunk(content="Sure, "), chunk(content="one moment."),
            chunk(tool_calls=[{"index": 0, "id": "call_1",
                              "function": {"name": "fs.read",
                                          "arguments": '{"path": "x"}'}}]),
            chunk(finish_reason="tool_calls"),
        ])
        response = aggregate_stream(
            request_id=REQUEST_ID, turn_id=TURN, provider="llamacpp", model="local",
            events=provider.stream(base_request()))
        self.assertTrue(valid(response_schema, response), json.dumps(response))
        self.assertEqual("Sure, one moment.", response["text"])
        self.assertEqual("tool_use", response["stop_reason"])
        self.assertEqual("call_1", response["tool_calls"][0]["call_id"])


if __name__ == "__main__":
    unittest.main()
