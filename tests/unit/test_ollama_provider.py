"""`OllamaProvider`.  ADR-0001, ADR-0009, ADR-0040, ADR-0027 layer 1.

No Ollama instance is reachable in CI or, currently, on the host this was written on —
`httpx.MockTransport` stands in for the network entirely, so every case here is a real
assertion about the translation logic and none of it needs a `--live` flag to run. What it
cannot check is whether these fixtures match what a real Ollama server actually sends;
that is `ADR-0041`'s `--live` witness, once one exists.

Every request this adapter builds and every event it yields is checked against the real
frozen contracts in `contracts/events/v1/`, through the same offline `$ref` registry
`test_brain_contract.py` built — not a hand-copied shape of them.
"""
import json
import sys
import unittest
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "contract"))

from lionel.brain.providers.ollama_provider import (  # noqa: E402
    OllamaError, OllamaProvider,
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


def ndjson(*objects: dict) -> bytes:
    return b"\n".join(json.dumps(o).encode("utf-8") for o in objects) + b"\n"


def mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def base_request(**overrides) -> dict:
    r = {
        "request_id": REQUEST_ID, "turn_id": TURN,
        "messages": [{"role": "user", "content": "hi"}],
        "cancellation_token_id": TOKEN,
    }
    r.update(overrides)
    return r


class TestRequestTranslation(unittest.TestCase):
    """What `/api/chat` actually receives."""

    def _sent_payload(self, request: dict) -> dict:
        captured = {}

        def handler(req: httpx.Request) -> httpx.Response:
            captured["payload"] = json.loads(req.content)
            return httpx.Response(200, content=ndjson(
                {"message": {"role": "assistant", "content": "ok"}, "done": True,
                 "done_reason": "stop"}))

        provider = OllamaProvider("http://x", "qwen2.5", 8192, client=mock_client(handler))
        list(provider.stream(request))
        return captured["payload"]

    def test_plain_text_messages_translate_directly(self):
        payload = self._sent_payload(base_request(
            messages=[{"role": "user", "content": "hello"}]))
        self.assertEqual([{"role": "user", "content": "hello"}], payload["messages"])

    def test_a_system_prompt_becomes_the_first_message(self):
        payload = self._sent_payload(base_request(system="be terse"))
        self.assertEqual("system", payload["messages"][0]["role"])
        self.assertEqual("be terse", payload["messages"][0]["content"])

    def test_tool_result_role_becomes_tool(self):
        payload = self._sent_payload(base_request(messages=[
            {"role": "user", "content": "hi"},
            {"role": "tool_result", "content": "42", "call_id": "c1"},
        ]))
        self.assertEqual("tool", payload["messages"][1]["role"])

    def test_content_blocks_with_a_tool_use_block_carry_tool_calls(self):
        payload = self._sent_payload(base_request(messages=[
            {"role": "assistant", "content": [
                {"type": "text", "text": "checking"},
                {"type": "tool_use", "call_id": "c1", "name": "fs.read",
                 "input": {"path": "x"}},
            ]},
        ]))
        msg = payload["messages"][0]
        self.assertEqual("checking", msg["content"])
        self.assertEqual([{"function": {"name": "fs.read", "arguments": {"path": "x"}}}],
                         msg["tool_calls"])

    def test_an_image_ref_block_is_refused(self):
        with self.assertRaises(OllamaError):
            self._sent_payload(base_request(messages=[
                {"role": "user", "content": [{"type": "image_ref", "ref": "handle://x"}]},
            ]))

    def test_tools_translate_to_ollamas_function_shape(self):
        payload = self._sent_payload(base_request(tools=[
            {"name": "fs.read", "description": "read a file",
             "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
             "side_effect": "read", "trust_required": "any"},
        ]))
        self.assertEqual([{
            "type": "function",
            "function": {"name": "fs.read", "description": "read a file",
                        "parameters": {"type": "object",
                                      "properties": {"path": {"type": "string"}}}},
        }], payload["tools"])

    def test_tool_choice_none_omits_tools_even_when_provided(self):
        payload = self._sent_payload(base_request(
            tools=[{"name": "fs.read", "description": "d", "input_schema": {},
                   "side_effect": "read", "trust_required": "any"}],
            tool_choice="none"))
        self.assertNotIn("tools", payload)

    def test_max_output_tokens_becomes_num_predict(self):
        payload = self._sent_payload(base_request(max_output_tokens=256))
        self.assertEqual(256, payload["options"]["num_predict"])

    def test_temperature_passes_through_options(self):
        payload = self._sent_payload(base_request(temperature=0.3))
        self.assertEqual(0.3, payload["options"]["temperature"])

    def test_response_schema_becomes_format(self):
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
        payload = self._sent_payload(base_request(response_schema=schema))
        self.assertEqual(schema, payload["format"])

    def test_stream_is_always_true(self):
        payload = self._sent_payload(base_request())
        self.assertTrue(payload["stream"])


class TestStreamEventTranslation(unittest.TestCase):
    def _events(self, chunks: list[dict], request: dict | None = None) -> list[dict]:
        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=ndjson(*chunks))

        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        return list(provider.stream(request or base_request()))

    def test_content_chunks_become_text_deltas(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "Hel"}, "done": False},
            {"message": {"role": "assistant", "content": "lo"}, "done": False},
            {"message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "stop"},
        ])
        texts = [e["text"] for e in events if e["type"] == "text_delta"]
        self.assertEqual(["Hel", "lo"], texts)

    def test_an_empty_content_chunk_yields_no_text_delta(self):
        events = self._events([
            {"message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "stop"},
        ])
        self.assertNotIn("text_delta", [e["type"] for e in events])

    def test_a_tool_call_becomes_one_complete_delta(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "",
                        "tool_calls": [{"function": {"name": "fs.read",
                                                     "arguments": {"path": "x"}}}]},
             "done": False},
            {"message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "stop"},
        ])
        deltas = [e for e in events if e["type"] == "tool_call_delta"]
        self.assertEqual(1, len(deltas))
        call = deltas[0]["tool_call"]
        self.assertTrue(call["complete"])
        self.assertEqual("fs.read", call["name"])
        self.assertEqual({"path": "x"}, json.loads(call["arguments_delta"]))

    def test_a_tool_call_forces_stop_reason_tool_use_even_when_ollama_says_stop(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "",
                        "tool_calls": [{"function": {"name": "a", "arguments": {}}}]},
             "done": False},
            {"message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "stop"},
        ])
        done = [e for e in events if e["type"] == "done"][0]
        self.assertEqual("tool_use", done["stop_reason"])

    def test_parallel_tool_calls_get_distinct_call_ids_and_indices(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "",
                        "tool_calls": [
                            {"function": {"name": "a", "arguments": {}}},
                            {"function": {"name": "b", "arguments": {}}},
                        ]},
             "done": False},
            {"message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "stop"},
        ])
        deltas = [e["tool_call"] for e in events if e["type"] == "tool_call_delta"]
        self.assertEqual(["ollama-0", "ollama-1"], [d["call_id"] for d in deltas])
        self.assertEqual([0, 1], [d["index"] for d in deltas])

    def test_length_done_reason_maps_to_max_tokens(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "x"}, "done": True,
             "done_reason": "length"},
        ])
        done = [e for e in events if e["type"] == "done"][0]
        self.assertEqual("max_tokens", done["stop_reason"])

    def test_a_load_event_reason_maps_to_provider_error(self):
        events = self._events([
            {"message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "unload"},
        ])
        done = [e for e in events if e["type"] == "done"][0]
        self.assertEqual("provider_error", done["stop_reason"])

    def test_prompt_and_eval_counts_become_a_usage_event(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "x"}, "done": True,
             "done_reason": "stop", "prompt_eval_count": 40, "eval_count": 12},
        ])
        usage = [e for e in events if e["type"] == "usage"][0]
        self.assertEqual(40, usage["usage"]["input_tokens"])
        self.assertEqual(12, usage["usage"]["output_tokens"])
        self.assertFalse(usage["usage"]["token_counts_estimated"])

    def test_no_counts_means_no_usage_event(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "x"}, "done": True,
             "done_reason": "stop"},
        ])
        self.assertNotIn("usage", [e["type"] for e in events])

    def test_blank_lines_in_the_stream_are_skipped(self):
        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=(
                ndjson({"message": {"role": "assistant", "content": "a"}, "done": False})
                + b"\n"
                + ndjson({"message": {"role": "assistant", "content": ""}, "done": True,
                         "done_reason": "stop"})
            ))
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        events = list(provider.stream(base_request()))
        self.assertEqual(["a"], [e["text"] for e in events if e["type"] == "text_delta"])

    def test_every_event_carries_provider_and_the_requests_turn_id(self):
        events = self._events([
            {"message": {"role": "assistant", "content": "x"}, "done": True,
             "done_reason": "stop"},
        ])
        for e in events:
            self.assertEqual("ollama", e["provider"])
            self.assertEqual(TURN, e["turn_id"])


class TestTransportErrorsBecomeErrorEvents(unittest.TestCase):
    """A provider-side failure is reported through the stream's own `error` variant, not
    as a raised exception — the discriminated union already has a slot for it."""

    def test_an_http_error_status_yields_an_error_event(self):
        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(500, content=b"boom")
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        events = list(provider.stream(base_request()))
        self.assertEqual(1, len(events))
        self.assertEqual("error", events[0]["type"])
        self.assertTrue(events[0]["error"]["retryable"])

    def test_a_connection_error_yields_an_error_event(self):
        def handler(req: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=req)
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        events = list(provider.stream(base_request()))
        self.assertEqual("error", events[0]["type"])
        self.assertEqual("unavailable", events[0]["error"]["code"])

    def test_a_404_maps_to_not_found(self):
        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(404, content=b"model not found")
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        events = list(provider.stream(base_request()))
        self.assertEqual("not_found", events[0]["error"]["code"])
        self.assertFalse(events[0]["error"]["retryable"])


class TestHealth(unittest.TestCase):
    def test_unreachable_server_reports_unreachable(self):
        def handler(req: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused", request=req)
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        h = provider.health()
        self.assertFalse(h["live"])
        self.assertFalse(h["ready"])
        self.assertEqual("unreachable", h["state"])

    def test_reachable_with_model_loaded_reports_ready(self):
        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/api/version":
                return httpx.Response(200, json={"version": "0.5.0"})
            return httpx.Response(200, json={"models": [{"model": "m"}]})
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        h = provider.health()
        self.assertTrue(h["live"])
        self.assertTrue(h["ready"])
        self.assertEqual("ready", h["state"])

    def test_reachable_with_a_different_model_loaded_reports_loading(self):
        def handler(req: httpx.Request) -> httpx.Response:
            if req.url.path == "/api/version":
                return httpx.Response(200, json={"version": "0.5.0"})
            return httpx.Response(200, json={"models": [{"model": "some-other-model"}]})
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        h = provider.health()
        self.assertTrue(h["live"])
        self.assertFalse(h["ready"])
        self.assertEqual("loading", h["state"])


@unittest.skipUnless(_HAVE_JSONSCHEMA, "jsonschema not installed (pyproject `ci` extra)")
class TestOutputsValidateAgainstTheRealContracts(unittest.TestCase):
    def test_capabilities_validates(self):
        schema = load(EVENTS / "provider-capabilities.schema.json")
        provider = OllamaProvider("http://x", "qwen2.5", 32768)
        self.assertTrue(valid(schema, provider.capabilities()))

    def test_health_validates_in_every_reachability_state(self):
        schema = load(CORE / "health-status.schema.json")

        def unreachable(req):
            raise httpx.ConnectError("refused", request=req)
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(unreachable))
        self.assertTrue(valid(schema, provider.health()))

        def reachable_and_loaded(req):
            if req.url.path == "/api/version":
                return httpx.Response(200, json={"version": "x"})
            return httpx.Response(200, json={"models": [{"model": "m"}]})
        provider = OllamaProvider("http://x", "m", 8192,
                                  client=mock_client(reachable_and_loaded))
        self.assertTrue(valid(schema, provider.health()))

    def test_every_emitted_event_individually_validates(self):
        stream_schema = load(EVENTS / "stream-event.schema.json")

        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=ndjson(
                {"message": {"role": "assistant", "content": "hi"}, "done": False},
                {"message": {"role": "assistant", "content": "",
                            "tool_calls": [{"function": {"name": "fs.read",
                                                         "arguments": {"path": "x"}}}]},
                 "done": False},
                {"message": {"role": "assistant", "content": ""}, "done": True,
                 "done_reason": "stop", "prompt_eval_count": 10, "eval_count": 5},
            ))
        provider = OllamaProvider("http://x", "m", 8192, client=mock_client(handler))
        for event in provider.stream(base_request()):
            with self.subTest(type=event["type"]):
                self.assertTrue(valid(stream_schema, event), json.dumps(event))

    def test_a_full_streamed_turn_aggregates_to_a_valid_provider_response(self):
        response_schema = load(EVENTS / "provider-response.schema.json")

        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=ndjson(
                {"message": {"role": "assistant", "content": "Sure, "}, "done": False},
                {"message": {"role": "assistant", "content": "one moment."}, "done": False},
                {"message": {"role": "assistant", "content": "",
                            "tool_calls": [{"function": {"name": "fs.read",
                                                         "arguments": {"path": "x"}}}]},
                 "done": False},
                {"message": {"role": "assistant", "content": ""}, "done": True,
                 "done_reason": "stop", "prompt_eval_count": 55, "eval_count": 20},
            ))
        provider = OllamaProvider("http://x", "qwen2.5", 8192, client=mock_client(handler))
        response = aggregate_stream(
            request_id=REQUEST_ID, turn_id=TURN, provider="ollama", model="qwen2.5",
            events=provider.stream(base_request()))
        self.assertTrue(valid(response_schema, response), json.dumps(response))
        self.assertEqual("Sure, one moment.", response["text"])
        self.assertEqual("tool_use", response["stop_reason"])


if __name__ == "__main__":
    unittest.main()
