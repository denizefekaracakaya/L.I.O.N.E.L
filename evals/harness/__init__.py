"""The golden-transcript replay harness.  ADR-0041, ADR-0001, ADR-0027.

WHAT THIS IS THE G3 SLICE OF
    `ADR-0021` designed the full evaluation harness — golden set, STT WER, wake FAR/FRR,
    TTS intelligibility, a persisted leaderboard — for G8. `ADR-0041` pulled forward only
    what `ADR-0001`'s Verification asks for at G3: *"the same golden transcript produces
    equivalent tool calls under `anthropic` and `ollama`."* Two providers, text only,
    tool-call equivalence only. `llamacpp` is not in this comparison — `ADR-0041`'s own
    words: its tool-calling reliability *"is the thing under study, not a fixture to
    measure against."*

EQUIVALENCE IS TOOL CALLS AND PARSED ARGUMENTS, NEVER TEXT
    `ADR-0041` item 1, and `ADR-0021`'s Golden set framing before it: *"correct tool,
    correct arguments"*, not correct words. `tool_calls_equivalent()` below compares
    `(name, arguments)` pairs as a set — order-insensitive, because a provider emitting
    two independent tool calls in a different order than another provider is not the kind
    of disagreement this harness exists to catch; a provider calling a different tool, or
    the same tool with different arguments, is.

A RECORDED CASE IS A `STREAMEVENT` SEQUENCE, NOT A RAW WIRE CAPTURE
    Each provider's raw streaming wire format is different (Ollama's NDJSON,
    Anthropic's typed SSE events) and already has a translator: the `BrainProvider`
    adapter itself, tested directly by `tests/unit/test_{ollama,anthropic}_provider.py`.
    Recording the RAW wire format here would mean re-testing that translation on every
    CI run and building a second, harness-specific way to replay it. Recording the
    *output* of `stream()` — a `StreamEvent` sequence, already provider-agnostic — means
    replay is exactly `lionel.brain.streaming.aggregate_stream`, the same function every
    adapter already produces its `ProviderResponse` through. One aggregation path, not two.

`--LIVE` PRODUCES A RECORDING; THE DEFAULT MODE ONLY REPLAYS ONE
    Recording is `list(provider.stream(request))`, written to
    `evals/golden/<case_id>/<provider>.json`, run against a real credential and a real
    model — the same `--live` shape `scripts/check_env.sh` and `scripts/verify_memory.sh`
    already use, and named identically for the same reason: a default run must work with
    the cable pulled (ADR-0007), and recording new golden data never can.

`EVALS/GOLDEN/` IS EMPTY, ON PURPOSE, AS OF THIS WRITING
    No `anthropic` credential and no reachable `ollama` were available while this harness
    was built. Every piece here is exercised by `tests/unit/test_eval_harness.py` against
    synthetic, clearly-labelled fixtures that prove the MECHANISM — the comparison, the
    loader, the aggregation replay — works correctly. None of them are offered as a real
    provider's output, and none live in `evals/golden/` itself: a synthetic fixture
    sitting in the directory real golden cases belong in is exactly the *"looks real,
    isn't"* failure `ADR-0013`'s no-pending gate exists to catch one layer down, in
    artifacts rather than in eval data.

WHY THIS IS NOT WIRED AS A CI JOB YET
    `ADR-0041` calls for a CI job that replays every golden case and blocks merge on a
    regression. With zero recorded cases, that job would pass trivially on every push —
    green, and reporting nothing. `CI_Architecture.md`'s own history has a name for
    exactly this: `l0-conformance` was two `echo` statements for months, and the finding
    was that *"present, green, and hollow… is worse than absent, because an absent gate
    is visibly missing and a green stub is not."* Wiring the job is `evals/harness`'s next
    step, the same day the first case is recorded — not before.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_DIR = Path(__file__).resolve().parent.parent / "golden"

__all__ = [
    "GOLDEN_DIR",
    "GoldenCase",
    "CaseResult",
    "load_case",
    "load_recorded_response",
    "record_response",
    "replay_case",
    "run_suite",
    "tool_calls_equivalent",
]


@dataclass(frozen=True)
class GoldenCase:
    """One golden case: a prompt, the tools offered, and the tool calls any provider
    handling it correctly must produce. `case.json` under `evals/golden/<case_id>/`.
    """

    case_id: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]]
    expected_tool_calls: list[dict[str, Any]]
    notes: str = ""

    @classmethod
    def from_dict(cls, case_id: str, data: dict[str, Any]) -> "GoldenCase":
        return cls(
            case_id=case_id, messages=data["messages"], tools=data.get("tools", []),
            expected_tool_calls=data["expected_tool_calls"], notes=data.get("notes", ""))

    def to_dict(self) -> dict[str, Any]:
        return {"messages": self.messages, "tools": self.tools,
                "expected_tool_calls": self.expected_tool_calls, "notes": self.notes}


@dataclass(frozen=True)
class CaseResult:
    """One case, one provider, one verdict. `status` is `"pass"`, `"fail"`, or
    `"not_recorded"` — the third is not a failure, it is the honest state of a case
    `--live` has not produced data for yet, and `run_suite()` must be able to say so
    without either failing the whole suite or silently skipping it into a false pass.
    """

    case_id: str
    provider: str
    status: str
    expected: list[dict[str, Any]] = field(default_factory=list)
    actual: Optional[list[dict[str, Any]]] = None
    detail: str = ""


def _normalize(calls: list[dict[str, Any]]) -> frozenset:
    return frozenset(
        (c["name"], json.dumps(c.get("arguments", {}), sort_keys=True)) for c in calls)


def tool_calls_equivalent(expected: list[dict[str, Any]],
                          actual: list[dict[str, Any]]) -> bool:
    """`(name, arguments)` pairs as a set — order-insensitive. `call_id` and `index` are
    adapter-internal correlation fields (a `ToolCallDelta`/`AuditRecord` join key,
    per that field's own contract description); they are not part of what a golden case
    can meaningfully pin, since `ollama` synthesizes ids no live recording would repeat
    identically between runs, while `anthropic`'s real ids are stable but provider-specific
    by construction. Equivalence is: same tools, same arguments — the thing `ADR-0021`'s
    Golden set framing actually asks for.
    """
    return _normalize(expected) == _normalize(actual)


def load_case(case_dir: Path) -> GoldenCase:
    data = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    return GoldenCase.from_dict(case_dir.name, data)


def load_recorded_response(case_dir: Path, provider: str) -> Optional[list[dict[str, Any]]]:
    """The `StreamEvent` sequence `--live` recorded for `provider` against this case, or
    `None` if it has not been recorded — the ordinary state for a case nobody has run
    `--live` against yet, not an error."""
    path = case_dir / f"{provider}.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def record_response(case_dir: Path, provider: str, events: list[dict[str, Any]]) -> None:
    """Write what `--live` produced. Called by the recording step, never by the default
    replay path — `evals/golden/` only grows through this, deliberately, so a case
    directory's presence always means "recorded," never "fabricated to make CI green."
    """
    path = case_dir / f"{provider}.json"
    path.write_text(json.dumps(events, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def replay_case(case: GoldenCase, provider: str, case_dir: Path) -> CaseResult:
    from lionel.brain.streaming import aggregate_stream, AggregationError

    events = load_recorded_response(case_dir, provider)
    if events is None:
        return CaseResult(case.case_id, provider, "not_recorded",
                          expected=case.expected_tool_calls,
                          detail=f"no {provider}.json under {case_dir} — needs --live")

    try:
        response = aggregate_stream(
            request_id="00000000000000000000000000", turn_id="00000000000000000000000000",
            provider=provider, model="recorded", events=events)
    except AggregationError as exc:
        return CaseResult(case.case_id, provider, "fail", expected=case.expected_tool_calls,
                          detail=f"recorded events did not aggregate: {exc}")

    actual = response["tool_calls"]
    if tool_calls_equivalent(case.expected_tool_calls, actual):
        return CaseResult(case.case_id, provider, "pass",
                          expected=case.expected_tool_calls, actual=actual)
    return CaseResult(case.case_id, provider, "fail",
                      expected=case.expected_tool_calls, actual=actual,
                      detail="tool calls do not match the golden case")


def run_suite(golden_dir: Optional[Path] = None,
             providers: tuple[str, ...] = ("anthropic", "ollama")) -> list[CaseResult]:
    """Every case under `golden_dir`, against every provider in `providers`. `llamacpp`
    is not a default — `ADR-0041`'s own reasoning, not an oversight."""
    base = golden_dir or GOLDEN_DIR
    results: list[CaseResult] = []
    if not base.is_dir():
        return results
    for case_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if not (case_dir / "case.json").is_file():
            continue
        case = load_case(case_dir)
        for provider in providers:
            results.append(replay_case(case, provider, case_dir))
    return results
