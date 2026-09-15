"""`aggregate_stream`, provider-agnostic.  ADR-0009, ADR-0027 layer 1.

Turning a `StreamEvent` sequence into a `ProviderResponse` is arithmetic over a
discriminated union, not provider behaviour — every adapter needs the identical logic, so
it exists once here rather than once per adapter. Every case below is checked against the
real frozen contracts in `contracts/events/v1/` (not a copy of their shape), the same
`jsonschema` + offline `$ref` registry `test_brain_contract.py` already built.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "contract"))

from lionel.brain.streaming import AggregationError, aggregate_stream  # noqa: E402

try:
    from test_brain_contract import EVENTS, load, valid  # noqa: E402
    _HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover - jsonschema is CI tooling
    _HAVE_JSONSCHEMA = False

TURN = "01JQ4X8ZK9P2M7VN3RTYB6WCDE"
REQUEST = "01JQ4X8ZK9P2M7VN3RTYB6WCDA"


def ev(etype: str, **fields) -> dict:
    return {"type": etype, "turn_id": TURN, "seq": 0, "provider": "ollama", **fields}


class TestTextAndThinkingAccumulate(unittest.TestCase):
    def test_text_deltas_concatenate_in_order(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
            ev("text_delta", text="Hello "), ev("text_delta", text="world"),
            ev("done", stop_reason="end_turn"),
        ])
        self.assertEqual("Hello world", r["text"])

    def test_thinking_deltas_are_separate_from_text(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="anthropic",
                             model="m", events=[
            ev("thinking_delta", text="reasoning..."), ev("text_delta", text="answer"),
            ev("done", stop_reason="end_turn"),
        ])
        self.assertEqual("answer", r["text"])
        self.assertEqual("reasoning...", r["thinking"])

    def test_no_thinking_deltas_leaves_thinking_null(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[ev("done", stop_reason="end_turn")])
        self.assertIsNone(r["thinking"])


class TestToolCallAssembly(unittest.TestCase):
    """The classic streaming tool-call bug, pinned: arguments are parsed only after
    `complete: true`, never from a partial fragment."""

    def test_a_single_delta_call_assembles(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
            ev("tool_call_delta", tool_call={
                "call_id": "c1", "index": 0, "name": "fs.read",
                "arguments_delta": '{"path": "x"}', "complete": True}),
            ev("done", stop_reason="tool_use"),
        ])
        self.assertEqual([{"call_id": "c1", "index": 0, "name": "fs.read",
                          "arguments": {"path": "x"}}], r["tool_calls"])

    def test_fragments_accumulate_before_parsing(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="anthropic",
                             model="m", events=[
            ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0, "name": "fs.read"}),
            ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0,
                                             "arguments_delta": '{"pa'}),
            ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0,
                                             "arguments_delta": 'th": "x"}',
                                             "complete": True}),
            ev("done", stop_reason="tool_use"),
        ])
        self.assertEqual({"path": "x"}, r["tool_calls"][0]["arguments"])

    def test_parallel_calls_stay_in_first_seen_order(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="anthropic",
                             model="m", events=[
            ev("tool_call_delta", tool_call={"call_id": "c2", "index": 1, "name": "b",
                                             "arguments_delta": "{}", "complete": True}),
            ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0, "name": "a",
                                             "arguments_delta": "{}", "complete": True}),
            ev("done", stop_reason="tool_use"),
        ])
        self.assertEqual(["c2", "c1"], [c["call_id"] for c in r["tool_calls"]])

    def test_a_call_with_no_arguments_defaults_to_an_empty_object(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
            ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0, "name": "ping",
                                             "complete": True}),
            ev("done", stop_reason="tool_use"),
        ])
        self.assertEqual({}, r["tool_calls"][0]["arguments"])

    def test_a_call_never_marked_complete_raises(self):
        with self.assertRaises(AggregationError) as cm:
            aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
                ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0, "name": "a"}),
                ev("done", stop_reason="tool_use"),
            ])
        self.assertIn("c1", str(cm.exception))

    def test_invalid_json_once_complete_raises(self):
        with self.assertRaises(AggregationError) as cm:
            aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
                ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0, "name": "a",
                                                 "arguments_delta": "{not json",
                                                 "complete": True}),
                ev("done", stop_reason="tool_use"),
            ])
        self.assertIn("not valid JSON", str(cm.exception))


class TestUsageAndStopReason(unittest.TestCase):
    def test_usage_is_carried_through(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
            ev("usage", usage={"input_tokens": 10, "output_tokens": 5}),
            ev("done", stop_reason="max_tokens"),
        ])
        self.assertEqual(10, r["usage"]["input_tokens"])
        self.assertEqual("max_tokens", r["stop_reason"])

    def test_no_usage_event_defaults_to_zero_counts_rather_than_a_missing_field(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[ev("done", stop_reason="end_turn")])
        self.assertEqual({"input_tokens": 0, "output_tokens": 0}, r["usage"])


class TestTerminalEventIsRequired(unittest.TestCase):
    def test_no_done_or_error_event_raises(self):
        with self.assertRaises(AggregationError) as cm:
            aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[ev("text_delta", text="hi")])
        self.assertIn("done", str(cm.exception))

    def test_an_error_event_is_carried_onto_the_response(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
            ev("error", error={"code": "unavailable", "message": "boom",
                               "retryable": True}),
        ])
        self.assertEqual("boom", r["error"]["message"])
        self.assertEqual("provider_error", r["stop_reason"])


class TestUnknownEventTypesAreSkipped(unittest.TestCase):
    """`stream-event.schema.json`'s discriminator: consumers MUST skip unknown `type`
    values, so a newer adapter can run against an older aggregator mid-rollout."""

    def test_an_unrecognised_type_does_not_raise_and_is_ignored(self):
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="m", events=[
            {"type": "a_future_event_type", "turn_id": TURN, "seq": 0, "surprise": True},
            ev("text_delta", text="hi"),
            ev("done", stop_reason="end_turn"),
        ])
        self.assertEqual("hi", r["text"])


@unittest.skipUnless(_HAVE_JSONSCHEMA, "jsonschema not installed (pyproject `ci` extra)")
class TestOutputValidatesAgainstTheRealContract(unittest.TestCase):
    """Not a copy of the schema's shape — the schema itself, through the same offline
    `$ref` registry `test_brain_contract.py` uses."""

    def test_a_full_turn_with_text_and_a_tool_call_validates(self):
        schema = load(EVENTS / "provider-response.schema.json")
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="ollama",
                             model="qwen2.5:14b", events=[
            ev("text_delta", text="Checking that for you."),
            ev("tool_call_delta", tool_call={"call_id": "c1", "index": 0, "name": "fs.read",
                                             "arguments_delta": '{"path": "x"}',
                                             "complete": True}),
            ev("usage", usage={"input_tokens": 40, "output_tokens": 12,
                               "estimated_cost_usd": None, "token_counts_estimated": False}),
            ev("done", stop_reason="tool_use"),
        ])
        self.assertTrue(valid(schema, r), json.dumps(r))

    def test_an_error_terminated_turn_validates(self):
        schema = load(EVENTS / "provider-response.schema.json")
        r = aggregate_stream(request_id=REQUEST, turn_id=TURN, provider="anthropic",
                             model="claude-sonnet-5", events=[
            ev("error", error={"code": "rate_limited", "message": "rate limited",
                               "retryable": True, "retry_after_ms": 2000}),
        ])
        self.assertTrue(valid(schema, r), json.dumps(r))


if __name__ == "__main__":
    unittest.main()
