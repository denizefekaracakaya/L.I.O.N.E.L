"""`evals/harness`.  ADR-0041, ADR-0027 layer 1.

`evals/golden/` is empty — no case here is offered as a real provider's recorded output.
Every fixture below is produced by running a REAL `BrainProvider` adapter's `stream()`
against a controlled fake transport (the same `httpx.MockTransport` / fake-client pattern
`test_ollama_provider.py` and `test_anthropic_provider.py` already use) and capturing its
actual `StreamEvent` output — so what this harness replays is a genuine adapter translation
of a synthetic input, not a hand-typed guess at what a `StreamEvent` sequence looks like.
None of it lives in `evals/golden/` itself, and none of it is claimed as a recording.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from evals.harness import (  # noqa: E402
    CaseResult, GoldenCase, load_case, load_recorded_response, record_response,
    replay_case, run_suite, tool_calls_equivalent,
)
from lionel.brain.providers.ollama_provider import OllamaProvider  # noqa: E402

TURN = "01JQ4X8ZK9P2M7VN3RTYB6WCDE"
REQUEST_ID = "01JQ4X8ZK9P2M7VN3RTYB6WCDA"
TOKEN = "01JQ4XB2M5N8P1QRST2VWX3YZA"


def record_a_real_ollama_transcript(content: str, tool_call: dict) -> list[dict]:
    """Runs the REAL `OllamaProvider.stream()` against a fake transport carrying a
    plausible response, and returns its actual `StreamEvent` output — what `--live`
    would produce, minus the live network."""
    def ndjson(*objects):
        return b"\n".join(json.dumps(o).encode("utf-8") for o in objects) + b"\n"

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=ndjson(
            {"message": {"role": "assistant", "content": content}, "done": False},
            {"message": {"role": "assistant", "content": "",
                        "tool_calls": [{"function": tool_call}]}, "done": False},
            {"message": {"role": "assistant", "content": ""}, "done": True,
             "done_reason": "stop", "prompt_eval_count": 20, "eval_count": 8},
        ))

    provider = OllamaProvider("http://x", "m", 8192,
                              client=httpx.Client(transport=httpx.MockTransport(handler)))
    request = {
        "request_id": REQUEST_ID, "turn_id": TURN,
        "messages": [{"role": "user", "content": "read the file"}],
        "cancellation_token_id": TOKEN,
    }
    return list(provider.stream(request))


class TestToolCallsEquivalent(unittest.TestCase):
    def test_identical_calls_are_equivalent(self):
        calls = [{"call_id": "c1", "index": 0, "name": "fs.read",
                 "arguments": {"path": "x"}}]
        self.assertTrue(tool_calls_equivalent(calls, calls))

    def test_call_id_and_index_do_not_matter(self):
        """Ollama synthesizes ids; a live recording would not reproduce them
        identically between runs, and `Anthropic`'s real ids are provider-specific by
        construction. Neither can be part of what a golden case pins."""
        expected = [{"call_id": "c1", "index": 0, "name": "fs.read",
                    "arguments": {"path": "x"}}]
        actual = [{"call_id": "toolu_xyz", "index": 3, "name": "fs.read",
                  "arguments": {"path": "x"}}]
        self.assertTrue(tool_calls_equivalent(expected, actual))

    def test_key_order_within_arguments_does_not_matter(self):
        expected = [{"name": "a", "arguments": {"x": 1, "y": 2}}]
        actual = [{"name": "a", "arguments": {"y": 2, "x": 1}}]
        self.assertTrue(tool_calls_equivalent(expected, actual))

    def test_call_order_does_not_matter(self):
        expected = [{"name": "a", "arguments": {}}, {"name": "b", "arguments": {}}]
        actual = [{"name": "b", "arguments": {}}, {"name": "a", "arguments": {}}]
        self.assertTrue(tool_calls_equivalent(expected, actual))

    def test_a_different_tool_is_not_equivalent(self):
        expected = [{"name": "fs.read", "arguments": {"path": "x"}}]
        actual = [{"name": "fs.write", "arguments": {"path": "x"}}]
        self.assertFalse(tool_calls_equivalent(expected, actual))

    def test_different_arguments_are_not_equivalent(self):
        expected = [{"name": "fs.read", "arguments": {"path": "x"}}]
        actual = [{"name": "fs.read", "arguments": {"path": "y"}}]
        self.assertFalse(tool_calls_equivalent(expected, actual))

    def test_a_missing_call_is_not_equivalent(self):
        expected = [{"name": "a", "arguments": {}}, {"name": "b", "arguments": {}}]
        actual = [{"name": "a", "arguments": {}}]
        self.assertFalse(tool_calls_equivalent(expected, actual))

    def test_an_extra_call_is_not_equivalent(self):
        expected = [{"name": "a", "arguments": {}}]
        actual = [{"name": "a", "arguments": {}}, {"name": "b", "arguments": {}}]
        self.assertFalse(tool_calls_equivalent(expected, actual))


class TestCaseLoading(unittest.TestCase):
    def test_a_case_round_trips_through_json(self):
        with tempfile.TemporaryDirectory() as d:
            case_dir = Path(d) / "read_a_file"
            case_dir.mkdir()
            case = GoldenCase(
                case_id="read_a_file",
                messages=[{"role": "user", "content": "read x"}],
                tools=[{"name": "fs.read", "description": "d", "input_schema": {},
                       "side_effect": "read", "trust_required": "any"}],
                expected_tool_calls=[{"name": "fs.read", "arguments": {"path": "x"}}],
                notes="a fixture, not a recording")
            (case_dir / "case.json").write_text(
                json.dumps(case.to_dict()), encoding="utf-8")
            loaded = load_case(case_dir)
            self.assertEqual(case.messages, loaded.messages)
            self.assertEqual(case.expected_tool_calls, loaded.expected_tool_calls)
            self.assertEqual("read_a_file", loaded.case_id)


class TestRecordAndReplay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.case_dir = Path(self.tmp.name) / "read_a_file"
        self.case_dir.mkdir()
        case = GoldenCase(
            case_id="read_a_file",
            messages=[{"role": "user", "content": "read the file"}],
            tools=[{"name": "fs.read", "description": "d", "input_schema": {},
                   "side_effect": "read", "trust_required": "any"}],
            expected_tool_calls=[{"name": "fs.read", "arguments": {"path": "x"}}])
        (self.case_dir / "case.json").write_text(
            json.dumps(case.to_dict()), encoding="utf-8")
        self.case = case

    def tearDown(self):
        self.tmp.cleanup()

    def test_an_unrecorded_case_reports_not_recorded_not_a_failure(self):
        result = replay_case(self.case, "ollama", self.case_dir)
        self.assertEqual("not_recorded", result.status)
        self.assertIn("--live", result.detail)

    def test_record_then_replay_a_matching_transcript_passes(self):
        events = record_a_real_ollama_transcript(
            "Checking the file for you.",
            {"name": "fs.read", "arguments": {"path": "x"}})
        record_response(self.case_dir, "ollama", events)

        loaded_back = load_recorded_response(self.case_dir, "ollama")
        self.assertEqual(events, loaded_back)

        result = replay_case(self.case, "ollama", self.case_dir)
        self.assertEqual("pass", result.status)
        self.assertTrue(tool_calls_equivalent(self.case.expected_tool_calls, result.actual))

    def test_a_transcript_calling_the_wrong_tool_fails(self):
        events = record_a_real_ollama_transcript(
            "Checking.", {"name": "fs.write", "arguments": {"path": "x", "data": "y"}})
        record_response(self.case_dir, "ollama", events)

        result = replay_case(self.case, "ollama", self.case_dir)
        self.assertEqual("fail", result.status)
        self.assertEqual("fs.write", result.actual[0]["name"])

    def test_a_transcript_with_different_arguments_fails(self):
        events = record_a_real_ollama_transcript(
            "Checking.", {"name": "fs.read", "arguments": {"path": "y"}})
        record_response(self.case_dir, "ollama", events)

        result = replay_case(self.case, "ollama", self.case_dir)
        self.assertEqual("fail", result.status)

    def test_a_malformed_recording_reports_fail_not_a_crash(self):
        """An event sequence with no terminal `done`/`error` — the aggregator's own
        AggregationError, surfaced as a case failure rather than propagating out of the
        suite and stopping every other case from running."""
        record_response(self.case_dir, "ollama", [
            {"type": "text_delta", "turn_id": TURN, "seq": 1, "provider": "ollama",
             "text": "incomplete"},
        ])
        result = replay_case(self.case, "ollama", self.case_dir)
        self.assertEqual("fail", result.status)
        self.assertIn("aggregate", result.detail.lower())


class TestRunSuite(unittest.TestCase):
    def test_an_empty_golden_directory_returns_no_results(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual([], run_suite(Path(d)))

    def test_a_missing_golden_directory_returns_no_results_not_an_error(self):
        self.assertEqual([], run_suite(Path("/no/such/directory/anywhere")))

    def test_the_suite_covers_every_case_against_every_default_provider(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            for case_id in ("case_a", "case_b"):
                case_dir = base / case_id
                case_dir.mkdir()
                (case_dir / "case.json").write_text(json.dumps({
                    "messages": [{"role": "user", "content": "x"}],
                    "tools": [], "expected_tool_calls": [],
                }), encoding="utf-8")
            results = run_suite(base)
            pairs = {(r.case_id, r.provider) for r in results}
            self.assertEqual(
                {("case_a", "anthropic"), ("case_a", "ollama"),
                 ("case_b", "anthropic"), ("case_b", "ollama")},
                pairs)
            # Neither case was recorded, so every result is honestly "not_recorded" --
            # not silently absent from the suite.
            self.assertTrue(all(r.status == "not_recorded" for r in results))

    def test_llamacpp_is_not_a_default_provider(self):
        """ADR-0041's own scope: llamacpp's tool-calling reliability is the thing under
        study, not a fixture to measure against."""
        with tempfile.TemporaryDirectory() as d:
            base = Path(d)
            case_dir = base / "case_a"
            case_dir.mkdir()
            (case_dir / "case.json").write_text(json.dumps({
                "messages": [{"role": "user", "content": "x"}],
                "tools": [], "expected_tool_calls": [],
            }), encoding="utf-8")
            results = run_suite(base)
            self.assertNotIn("llamacpp", {r.provider for r in results})


if __name__ == "__main__":
    unittest.main()
