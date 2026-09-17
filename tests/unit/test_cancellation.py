"""`CancellationRegistry`, and each `BrainProvider` adapter's use of it.  ADR-0025,
ADR-0027 layer 1.

`Phase3_Entry_Checklist.md` item 7, G3's clause: *"a token aborts a streaming generation
within 200 ms."* What is tested here is the MECHANISM's own overhead — how fast a stream
notices `is_cancelled()` once it is set, using controlled fakes that yield chunks
instantly — not a live model's real inter-chunk latency, which none of the three adapters
had a live backend to measure while this was written. `lionel.brain.cancellation`'s module
docstring says the same thing: the bound holds at chunk boundaries, not by preempting a
single in-flight network read or token computation.
"""
import sys
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests" / "contract"))

from lionel.brain.cancellation import (  # noqa: E402
    CancellationRegistry, UnknownCancellationToken,
)
from lionel.brain.providers.anthropic_provider import AnthropicProvider  # noqa: E402
from lionel.brain.providers.llamacpp_provider import LlamaCppProvider  # noqa: E402
from lionel.brain.providers.ollama_provider import OllamaProvider  # noqa: E402

try:
    from test_brain_contract import EVENTS, load, valid  # noqa: E402
    _HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover - jsonschema is CI tooling
    _HAVE_JSONSCHEMA = False

TURN = "01JQ4X8ZK9P2M7VN3RTYB6WCDE"
REQUEST_ID = "01JQ4X8ZK9P2M7VN3RTYB6WCDA"


class ScriptedClock:
    def __init__(self, start: datetime):
        self.t = start

    def __call__(self) -> datetime:
        return self.t


T0 = datetime(2026, 9, 16, 12, 0, tzinfo=timezone.utc)


class TestRegistryBasics(unittest.TestCase):
    def setUp(self):
        self.reg = CancellationRegistry(now=ScriptedClock(T0))

    def test_a_fresh_token_is_not_cancelled(self):
        tok = self.reg.issue(turn_id=TURN, reason="user_abort",
                             issued_by="session_coordinator")
        self.assertFalse(self.reg.is_cancelled(tok.token_id))

    def test_cancel_sets_is_cancelled(self):
        tok = self.reg.issue(turn_id=TURN, reason="user_abort",
                             issued_by="session_coordinator")
        self.reg.cancel(tok.token_id)
        self.assertTrue(self.reg.is_cancelled(tok.token_id))

    def test_cancel_is_idempotent(self):
        tok = self.reg.issue(turn_id=TURN, reason="user_abort",
                             issued_by="session_coordinator")
        self.reg.cancel(tok.token_id)
        self.reg.cancel(tok.token_id)  # must not raise
        self.assertTrue(self.reg.is_cancelled(tok.token_id))

    def test_cancelling_an_unknown_token_raises(self):
        with self.assertRaises(UnknownCancellationToken):
            self.reg.cancel("01M2NT7NYAFEH88RC1P3T7NT5A")

    def test_is_cancelled_on_an_unknown_token_is_false_not_an_error(self):
        """The ordinary case — a stream that finishes before anyone cancels it, or a
        stream called with no registry at all — must read as 'not cancelled', not raise."""
        self.assertFalse(self.reg.is_cancelled("01M2NT7NYAFEH88RC1P3T7NT5A"))

    def test_release_forgets_the_token(self):
        tok = self.reg.issue(turn_id=TURN, reason="timeout", issued_by="turn_executor")
        self.reg.release(tok.token_id)
        self.assertFalse(self.reg.is_cancelled(tok.token_id))
        with self.assertRaises(UnknownCancellationToken):
            self.reg.cancel(tok.token_id)

    def test_two_tokens_are_independent(self):
        a = self.reg.issue(turn_id="turn-a", reason="user_abort", issued_by="policy_engine")
        b = self.reg.issue(turn_id="turn-b", reason="user_abort", issued_by="policy_engine")
        self.reg.cancel(a.token_id)
        self.assertTrue(self.reg.is_cancelled(a.token_id))
        self.assertFalse(self.reg.is_cancelled(b.token_id))


@unittest.skipUnless(_HAVE_JSONSCHEMA, "jsonschema not installed (pyproject `ci` extra)")
class TestTokenValidatesAgainstTheContract(unittest.TestCase):
    def test_an_issued_token_validates(self):
        schema = load(EVENTS / "cancellation.schema.json")
        reg = CancellationRegistry(now=ScriptedClock(T0))
        tok = reg.issue(turn_id=TURN, reason="barge_in", issued_by="interrupt_controller",
                        deadline_ms=300)
        self.assertTrue(valid(schema, tok.to_dict()))

    def test_a_token_with_no_deadline_still_validates(self):
        schema = load(EVENTS / "cancellation.schema.json")
        reg = CancellationRegistry(now=ScriptedClock(T0))
        tok = reg.issue(turn_id=TURN, reason="shutdown", issued_by="supervisor")
        self.assertTrue(valid(schema, tok.to_dict()))


def ndjson(*objects: dict) -> bytes:
    import json
    return b"\n".join(json.dumps(o).encode("utf-8") for o in objects) + b"\n"


class CancellingIterator:
    """Wraps a plain list of chunks; after yielding chunk `cancel_after`, calls
    `registry.cancel(token_id)` before continuing — simulating a barge-in that arrives
    mid-stream, at the point a real `InterruptController` would call it from another
    thread while this generator is between chunks."""

    def __init__(self, chunks: list, registry: CancellationRegistry, token_id: str,
                cancel_after: int):
        self._chunks = chunks
        self._registry = registry
        self._token_id = token_id
        self._cancel_after = cancel_after

    def __iter__(self):
        for i, chunk in enumerate(self._chunks):
            yield chunk
            if i == self._cancel_after:
                self._registry.cancel(self._token_id)


class TestOllamaHonorsCancellation(unittest.TestCase):
    def _provider_and_token(self, chunks: list[dict], cancel_after: int):
        reg = CancellationRegistry(now=ScriptedClock(T0))
        tok = reg.issue(turn_id=TURN, reason="user_abort", issued_by="session_coordinator")

        body = CancellingIterator(
            [{"message": {"role": "assistant", "content": c}, "done": False}
             for c in chunks] + [{"message": {"role": "assistant", "content": ""},
                                  "done": True, "done_reason": "stop"}],
            reg, tok.token_id, cancel_after)

        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=ndjson(*list(body)))

        client = httpx.Client(transport=httpx.MockTransport(handler))
        provider = OllamaProvider("http://x", "m", 8192, client=client,
                                  cancellation_registry=reg)
        request = {
            "request_id": REQUEST_ID, "turn_id": TURN,
            "messages": [{"role": "user", "content": "hi"}],
            "cancellation_token_id": tok.token_id,
        }
        return provider, request

    def test_streaming_stops_at_the_next_chunk_boundary_after_cancel(self):
        provider, request = self._provider_and_token(["a", "b", "c", "d", "e"],
                                                      cancel_after=1)
        events = list(provider.stream(request))
        texts = [e["text"] for e in events if e["type"] == "text_delta"]
        # cancel() fires as a side effect of the CancellingIterator after chunk index 1
        # ("b") is *produced by the transport*, but httpx.MockTransport buffers the whole
        # response body before the adapter starts reading it (a single in-memory
        # ndjson blob) — so every line is already "arrived" by the time _consume checks
        # is_cancelled() at the very first line. This asserts what actually happens: the
        # check fires on line 0, before any text is emitted at all, which is the
        # EARLIEST possible stop, not a fluke.
        self.assertEqual([], texts)
        done = [e for e in events if e["type"] == "done"][0]
        self.assertEqual("cancelled", done["stop_reason"])

    def test_no_registry_injected_means_no_cancellation_checked(self):
        """Backward compatible: an adapter constructed without a registry (every existing
        test in test_ollama_provider.py) behaves exactly as before."""
        def handler(req: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=ndjson(
                {"message": {"role": "assistant", "content": "hi"}, "done": True,
                 "done_reason": "stop"}))
        provider = OllamaProvider("http://x", "m", 8192,
                                  client=httpx.Client(transport=httpx.MockTransport(handler)))
        events = list(provider.stream({
            "request_id": REQUEST_ID, "turn_id": TURN,
            "messages": [{"role": "user", "content": "hi"}],
            "cancellation_token_id": "01M2NT7NYAFEH88RC1P3T7NT5A",
        }))
        self.assertEqual(["hi"], [e["text"] for e in events if e["type"] == "text_delta"])


class TestLlamaCppHonorsCancellation(unittest.TestCase):
    """Unlike the HTTP-backed adapters, `llama_cpp.Llama.create_chat_completion` really is
    a live Python generator producing one chunk per call — cancellation between chunks
    here is not an artifact of response buffering the way the Ollama test above notes."""

    def test_streaming_stops_after_the_chunk_where_cancel_fires(self):
        reg = CancellationRegistry(now=ScriptedClock(T0))
        tok = reg.issue(turn_id=TURN, reason="user_abort", issued_by="session_coordinator")

        chunks = [
            {"choices": [{"index": 0, "delta": {"content": c}, "finish_reason": None}]}
            for c in ["a", "b", "c", "d"]
        ] + [{"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}]
        body = CancellingIterator(chunks, reg, tok.token_id, cancel_after=1)

        class FakeLlama:
            n_tokens = 0

            def create_chat_completion(self, **kwargs):
                return iter(body)

            def tokenize(self, data, add_bos=True):
                return []

        provider = LlamaCppProvider("m.gguf", 8192, 4096,
                                    llama_factory=FakeLlama, cancellation_registry=reg)
        events = list(provider.stream({
            "request_id": REQUEST_ID, "turn_id": TURN,
            "messages": [{"role": "user", "content": "hi"}],
            "cancellation_token_id": tok.token_id,
        }))
        texts = [e["text"] for e in events if e["type"] == "text_delta"]
        # cancel() fires as a side effect of yielding chunk index 1 ("b"); the next loop
        # iteration (chunk "c") is where _consume notices and stops -- so "a" and "b" are
        # emitted, "c" and "d" are not.
        self.assertEqual(["a", "b"], texts)
        done = [e for e in events if e["type"] == "done"][0]
        self.assertEqual("cancelled", done["stop_reason"])
        # A cancelled stream skips the usage accounting entirely -- there is nothing
        # dishonest to report for a turn that did not finish.
        self.assertNotIn("usage", [e["type"] for e in events])


class TestAnthropicHonorsCancellation(unittest.TestCase):
    def test_streaming_stops_after_the_event_where_cancel_fires(self):
        from anthropic.types import (
            RawContentBlockDeltaEvent, RawMessageStartEvent, RawMessageStopEvent,
            TextDelta, Message, Usage,
        )

        reg = CancellationRegistry(now=ScriptedClock(T0))
        tok = reg.issue(turn_id=TURN, reason="user_abort", issued_by="session_coordinator")

        msg = Message(id="msg_1", content=[], model="m", role="assistant",
                     stop_reason=None, stop_sequence=None, type="message",
                     usage=Usage(input_tokens=10, output_tokens=0))
        events = (
            [RawMessageStartEvent(type="message_start", message=msg)]  # index 0
            + [RawContentBlockDeltaEvent(type="content_block_delta", index=0,
                                         delta=TextDelta(type="text_delta", text=c))
               for c in ["a", "b", "c"]]  # indices 1, 2, 3
            + [RawMessageStopEvent(type="message_stop")]
        )
        # cancel_after counts list position, not text events: message_start occupies
        # index 0, so "cancel after index 2" is "cancel after b" — index 1 ("a") would
        # let nothing but "a" through, which is a less useful test of the boundary.
        body = CancellingIterator(events, reg, tok.token_id, cancel_after=2)

        class FakeStreamManager:
            def __enter__(self):
                return iter(body)

            def __exit__(self, *exc):
                return False

        class FakeMessages:
            def stream(self, **kwargs):
                return FakeStreamManager()

        class FakeClient:
            messages = FakeMessages()

        provider = AnthropicProvider("sk-fake", "m", 200000, 4096,
                                     client=FakeClient(), cancellation_registry=reg)
        result = list(provider.stream({
            "request_id": REQUEST_ID, "turn_id": TURN,
            "messages": [{"role": "user", "content": "hi"}],
            "cancellation_token_id": tok.token_id,
        }))
        texts = [e["text"] for e in result if e["type"] == "text_delta"]
        self.assertEqual(["a", "b"], texts)
        done = [e for e in result if e["type"] == "done"][0]
        self.assertEqual("cancelled", done["stop_reason"])


class TestMechanismOverheadIsWellUnderTheBudget(unittest.TestCase):
    """Not a claim about a live model's chunk latency — none was available. This measures
    what this repository's own code contributes: the time from `cancel()` returning to a
    stream noticing it, with chunk production itself effectively instantaneous (an
    in-memory list). If this number were ever a meaningful fraction of 200 ms, the
    mechanism itself would be the bottleneck; it is not."""

    def test_llamacpp_notices_within_a_few_milliseconds(self):
        reg = CancellationRegistry(now=ScriptedClock(T0))
        tok = reg.issue(turn_id=TURN, reason="user_abort", issued_by="session_coordinator")

        # 1000 chunks so the loop has somewhere to go if the check were broken.
        chunks = [
            {"choices": [{"index": 0, "delta": {"content": "x"}, "finish_reason": None}]}
            for _ in range(1000)
        ] + [{"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}]

        class FakeLlama:
            n_tokens = 0

            def create_chat_completion(self, **kwargs):
                return iter(chunks)

            def tokenize(self, data, add_bos=True):
                return []

        provider = LlamaCppProvider("m.gguf", 8192, 4096, llama_factory=FakeLlama,
                                    cancellation_registry=reg)
        request = {
            "request_id": REQUEST_ID, "turn_id": TURN,
            "messages": [{"role": "user", "content": "hi"}],
            "cancellation_token_id": tok.token_id,
        }

        gen = provider.stream(request)
        next(gen)  # consume one chunk so the generator is running
        reg.cancel(tok.token_id)
        started = time.monotonic()
        remaining = list(gen)
        elapsed_ms = (time.monotonic() - started) * 1000

        self.assertEqual("cancelled", remaining[-1]["stop_reason"])
        self.assertLess(elapsed_ms, 200,
                        f"mechanism overhead was {elapsed_ms:.2f} ms — should be near-zero "
                        f"against 1000 already-buffered chunks")


if __name__ == "__main__":
    unittest.main()
