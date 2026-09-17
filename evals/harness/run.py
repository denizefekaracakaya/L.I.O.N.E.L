#!/usr/bin/env python3
"""`evals/harness/run.py` — replay every golden case against `anthropic` and `ollama`.

    python3 evals/harness/run.py

Reads `evals/golden/<case_id>/case.json` plus any `<provider>.json` recorded transcript
sitting beside it (`evals/harness`'s own module docstring explains the recording format
and why replay works on `StreamEvent` sequences rather than raw provider wire bytes).
A case with no recording for a provider reports `not_recorded` — the honest state for a
case `--live` has not produced data for, not a failure and not silently skipped.

NOT A CI JOB YET, AND SAYS SO EVERY TIME IT RUNS
    `evals/harness`'s module docstring: wiring this into `.github/workflows/ci.yml` with
    zero recorded cases would be a hollow gate, exactly the `l0-conformance` failure shape
    this repository's own history already found once. This script is runnable by hand
    today; it becomes a CI job the day the first case is recorded, not before.

EXIT CODES ARE THE SAME CONTRACT AS EVERYWHERE ELSE
    0  every recorded case passed (unrecorded cases do not fail the run — ADR-0041's
       regression gate is about cases that WERE checked and disagreed, not about data
       that does not exist yet)
    1  at least one recorded case's tool calls did not match its golden expectation
    2  this script is broken (a case directory it could not even parse)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from evals.harness import CaseResult, GOLDEN_DIR, run_suite  # noqa: E402


def _print_report(results: list[CaseResult]) -> None:
    if not results:
        print(f"  no golden cases found under {GOLDEN_DIR}")
        print("  (evals/golden/ is empty until a case is added and `--live` records it "
              "against at least one provider)")
        return

    by_status = {"pass": 0, "fail": 0, "not_recorded": 0}
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        marker = {"pass": "ok", "fail": "FAIL", "not_recorded": "skip"}[r.status]
        print(f"  {marker:5s} {r.case_id:30s} {r.provider:10s} {r.detail}")

    print()
    print(f"  {by_status['pass']} passed, {by_status['fail']} failed, "
         f"{by_status['not_recorded']} not recorded")


def main() -> int:
    print()
    print("== golden-transcript replay — ADR-0041's G3 slice (anthropic, ollama)")
    print(f"   golden cases: {GOLDEN_DIR}")
    print()

    try:
        results = run_suite()
    except Exception as exc:  # noqa: BLE001 — a run that cannot even start is broken
        print(f"  BROKEN  {type(exc).__name__}: {exc}")
        return 2

    _print_report(results)

    failed = sum(1 for r in results if r.status == "fail")
    print()
    if failed:
        print(f"  FAIL  {failed} case(s) did not match their golden expectation.")
        return 1
    print("  PASS  no recorded case disagreed with its golden expectation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
