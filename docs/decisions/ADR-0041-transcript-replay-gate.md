# ADR-0041: The golden-transcript replay gate, and the phase plan's contradiction about where it lives

| | |
|---|---|
| Status | **Accepted** — Efe, 2026-09-10. In force. See the Erratum |
| Date | 2026-09-10 |
| Phase | 3 |
| Related | [ADR-0001](ADR-0001-swappable-brain-provider.md), [ADR-0021](ADR-0021-eval-harness-gates.md), [ADR-0013](ADR-0013-artifact-pinning.md), [ADR-0007](ADR-0007-degradation-ladder.md), [ADR-0040](ADR-0040-brain-provider-clients.md) |

## Context

[ADR-0001](ADR-0001-swappable-brain-provider.md)'s Verification clause, unchanged since
Phase 0 and still in force:

> Gate **G3**. The same golden transcript produces equivalent tool calls under `anthropic`
> and `ollama`; the comparison runs in CI as a regression gate. A static check asserts no
> caller branches on provider name.

`MASTER_PLAN_v2.md` §10 Phase 3's own DoD repeats it, in more emphatic terms than most of
that section carries:

> the same golden transcript replays correctly on `anthropic` and `ollama`, results recorded
> in ADR-0001 (v1.0's G3 requirement, **now automated as a regression gate** rather than a
> one-time measurement)

**And the same document's directory sketch, four hundred lines later, labels the directory
this needs as arriving five phases later:**

```
├── evals/                              ← NEW  Phase 8
```

This is not a close reading finding a subtlety. It is `MASTER_PLAN_v2.md` disagreeing with
itself about which phase its own §10 Phase 3 DoD belongs to — the same shape as the
tombstone `memory-record.schema.json` described and forbade in one document ([ADR-0037](ADR-0037-tombstone-record-shape.md)),
one level up, in the plan rather than a contract. `Phase3_Entry_Checklist.md` item 3 named
this as a decision needing an ADR rather than resolving it by picking a side unilaterally,
which is what a decision reserved to Efe by `Architecture_Freeze.md` §4 (*"the phase plan"*)
means in practice.

**[ADR-0021](ADR-0021-eval-harness-gates.md) already designed the harness this needs, at
Phase 8, Gate G8.** Its Golden set suite — *"Utterance → expected tool-call set. Correct
tool, correct arguments"* — is exactly the equivalence ADR-0001 asks for, and its own
Decision names the very thing this ADR is about: *"ADR-0001's Anthropic-vs-Ollama comparison
stops being a one-time measurement and becomes a standing regression gate."* ADR-0021 is not
wrong. It is scoped to the FULL harness — golden set, STT WER, wake FAR/FRR, TTS
intelligibility, a persisted leaderboard — which genuinely needs G8's STT/TTS/wake models to
exist. What it does not need to wait for is the narrow slice ADR-0001 asks for at G3: two
text-in, tool-calls-out providers, no audio.

Three decisions remain even once the phase is settled:

- **What "replays correctly" means.** Two models legitimately produce different prose for
  the same prompt. A comparison over exact text is a flake generator; ADR-0021's own Golden
  set framing already answers this — *"correct tool, correct arguments"* — not correct
  words.
- **Where the transcript lives, and what pins it.** `ADR-0013` governs every artifact in
  this repository that can be replaced quietly; a golden transcript recorded once and never
  re-verified against the providers it claims to represent is exactly that risk.
- **What CI does when neither provider is reachable.** `ADR-0007` is the constraint: a gate
  that needs the network is a gate that is red on a plane, and `Anthropic` needs the network
  unconditionally. `scripts/check_env.sh` and `scripts/verify_memory.sh` both settled on a
  recorded-fixture default plus an opt-in `--live` witness on the host; whether this gate
  follows that precedent or invents its own is a decision, not a default.

## Decision

**A narrow slice of `evals/` is pulled forward to G3 — `evals/golden/` and
`evals/harness/`, scoped to tool-call equivalence across text providers only. Everything
else ADR-0021 designed — STT WER, wake FAR/FRR, TTS intelligibility, the persisted
leaderboard — stays at G8 exactly as planned. `MASTER_PLAN_v2.md`'s directory sketch is
corrected to say so.**

1. **Equivalence is over tool calls and their arguments, never text.** A case in
   `evals/golden/` is `{prompt, expected_tool_calls: [{name, arguments}, ...]}` — no
   expected prose field exists to tempt a text comparison into the harness later.
   `arguments` compares as parsed JSON, not string equality, so key ordering and float
   formatting are not the assertion.
2. **A golden case is a pinned artifact, `ADR-0013`'s way.** `evals/golden/*.json` cases are
   added to `artifacts.lock.yaml`'s existing scheme; each entry names the model/version pair
   it was recorded against. A case that has silently stopped representing what the live
   providers actually do is worse than no case, which is exactly `ADR-0021`'s Negative
   Consequences naming a stale golden set as *"worse than none because it grants false
   confidence"* — recorded there for the full harness, true here for the slice.
3. **CI replays against recorded provider responses; a `--live` mode replays against the
   real providers, on the host, opt-in.** The recorded fixtures are what `evals/harness/`
   feeds `anthropic` and `ollama` provider adapters through in CI — no network reachable, no
   flake from an upstream outage, and `ADR-0007`'s guarantee holds for this gate the way it
   holds for every other one. `--live` is announced before it acts and needs
   `secret://env/ANTHROPIC_API_KEY` resolved and Ollama reachable, the same shape
   `check_env.sh`'s `--live` checks already have. **`--live` is not run in CI.** It is a host
   witness, run before a release the way the GitHub and filesystem `--live` checks were
   witnessed on 2026-08-25.
4. **This is a CI *job*, not one of the 23 policy gates `ci/run_gates.sh` enforces.** It
   asserts model *behaviour*, not repository *conformance* — the same distinction that keeps
   `unit-tests` and `windows-policy-gates` outside `ORDER` rather than inside it. A failure
   here blocks merge exactly as a policy gate failure does; it is simply not counted in "23
   gates, N rules."
5. **A regression blocks merge. Not a warning** — `ADR-0021`'s own operating rule, adopted
   unchanged for this slice.

**What this does not do.** It does not implement `llamacpp` into the comparison. ADR-0001's
Verification names `anthropic` and `ollama` specifically; `llamacpp`'s tool-calling
reliability was v1.0's largest named unknown (`ADR-0001`'s own Alternatives Rejected: *"the
project's largest unknown, and we would discover it late"*), and a golden set built against
a model whose reliability is the question under study would be measuring the fixture, not
the model. `llamacpp` joins the comparison once ADR-0021's leaderboard exists to track it
properly, at G8.

## Consequences

**What gets better.** `ADR-0001`'s six-year-old — for this repository's timescale — G3
Verification clause stops being an unfulfillable promise the moment `ADR-0040`'s providers
exist. `MASTER_PLAN_v2.md` stops contradicting its own Phase 3 DoD four hundred lines later.
`ADR-0021`'s eventual G8 harness inherits a working `evals/golden/` format and
`evals/harness/` runner rather than building both from nothing.

**What this costs.**

- **`evals/` now has two arrival dates in the same repository's history** — this ADR's
  narrow slice at G3, ADR-0021's full harness at G8 — and a reader who only reads one of the
  two ADRs gets a partial picture. Both now cross-reference the other by name, which is the
  mitigation, not a fix.
- **A golden case recorded against `claude-sonnet-5` and a specific Ollama model tag is a
  second lock entry to keep current**, on top of the embedding model ADR-0036 already added.
  `artifacts.lock.yaml`'s existing staleness story — a pin that fails loudly on substitution
  — is the same protection, applied to a third kind of artifact.
- **The `--live` witness needs a real Anthropic API key and a running Ollama on the host to
  mean anything**, which is more preflight surface `check_env.sh` has to track — but it is
  the same surface `ADR-0040` already requires for the providers to exist at all, not new
  exposure.
- **No `llamacpp` in the comparison for two more phases.** ADR-0001's original DoD did not
  name it either — this is not a narrowing of what was promised, but it is a gap a casual
  reading of "three providers ship" would not expect.

## Alternatives Rejected

| Alternative | Why rejected |
|---|---|
| **Build the full ADR-0021 harness now, at G3** | Needs STT/wake/TTS models that do not exist until G6, and a persisted leaderboard that needs more than two data points to mean anything. Building it early does not make G6's models exist sooner; it makes an empty harness that looks finished |
| **Amend ADR-0001 to defer its G3 Verification clause to G8, matching `evals/ ← NEW Phase 8`** | Resolves the contradiction by picking the OTHER side of it. Rejected because ADR-0001's clause is specific and load-bearing — *"the local-vs-API gap becomes measurable rather than assumed"* is that ADR's own stated Positive consequence, and deferring the measurement five phases past the decision it is meant to inform (which local model to actually run) makes the decision unmeasured for the phases that most need it |
| **A text-similarity comparison (embedding distance, ROUGE) instead of tool-call equivalence** | Measures whether two responses sound alike, not whether they did the same thing. ADR-0021's Golden set already rejected this shape by specifying *"correct tool, correct arguments"* rather than a similarity score, and this ADR does not get to re-litigate it for a narrower slice |
| **CI-only, no `--live` witness** | Nothing then proves the recorded fixtures still match what the real providers currently do. A fixture that has drifted from reality is the eval-harness version of the tombstone contract ADR-0037 found: described once, never checked against the thing it claims to describe |
| **Host-only, never in CI** | Loses exactly the property `MASTER_PLAN_v2` asked for when it upgraded this from "a one-time measurement" to "a regression gate" — that it runs on every relevant push, not when someone remembers |
| **A new top-level policy gate under `ci/run_gates.sh`'s `ORDER`** | This checks model behaviour against a fixture, not repository conformance against a rule with a `why` and a `fix`. Forcing it into the `Finding`/`Gate` shape the 23 policy gates share would be describing "the tool call didn't match" as if it were "a dependency has no version bound" — a different kind of failure wearing the wrong costume |

## Verification

**Withheld until this ADR is Accepted.** `evals/golden/` and `evals/harness/` stay empty
while this is `Proposed` — they are two of the four directories G2's contract test found
inside `src/lionel/brain/` in exactly this state, and the same discipline applies: nothing
gets written ahead of the decision that shapes it. `MASTER_PLAN_v2.md`'s directory sketch is
in the architecture checksum set, so correcting the `evals/` line is itself a checksummed
change withheld until acceptance, the same as every dependency addition in this repository's
history has been.

On acceptance:

| | |
|---|---|
| `MASTER_PLAN_v2.md` | the `evals/` directory-sketch line gains `(golden/harness slice: Phase 3 — ADR-0041; full suite: Phase 8 — ADR-0021)` |
| `evals/golden/` | golden case fixtures, `{prompt, expected_tool_calls}`, each entered in `artifacts.lock.yaml` |
| `evals/harness/` | the replay runner: feeds each case through both provider adapters, compares tool name and parsed arguments, fails on any mismatch |
| a new CI job | replays every golden case against recorded provider responses; wired the way `unit-tests` is wired, outside `ci/run_gates.sh`'s `ORDER` |
| `scripts/check_env.sh` | a `--live` row for the replay harness, following the shape its GitHub and filesystem `--live` checks already have |
| `docs/decisions/README.md` | a paragraph on ADR-0021 noting the G3 slice this ADR carved out of its scope |

Gate **G3**: the same golden transcript produces equivalent tool calls under `anthropic` and
`ollama`, exactly as `ADR-0001` specified, five phases after `MASTER_PLAN_v2`'s directory
sketch said the machinery for it would exist.

## Erratum — 2026-09-10: Accepted; the withholding is discharged

This ADR was written while `Proposed`, and its Verification section describes that pending
state as ongoing. Efe accepted it on 2026-09-10, the same day it was drafted. The decision is
unchanged — what follows corrects text that has stopped being true, per ADR-0029 rule 2.

The Verification section opened:

> **Withheld until this ADR is Accepted.** `evals/golden/` and `evals/harness/` stay empty
> while this is `Proposed` — they are two of the four directories G2's contract test found
> inside `src/lionel/brain/` in exactly this state, and the same discipline applies: nothing
> gets written ahead of the decision that shapes it. `MASTER_PLAN_v2.md`'s directory sketch
> is in the architecture checksum set, so correcting the `evals/` line is itself a
> checksummed change withheld until acceptance, the same as every dependency addition in
> this repository's history has been.

Discharged for the plan-document half. `MASTER_PLAN_v2.md`'s directory sketch now reads
`evals/ ← NEW  golden/harness slice: Phase 3 (ADR-0041); full suite: Phase 8 (ADR-0021)`,
with an `harness/` line added beside `golden/`.

**Not yet discharged: the harness itself.** `evals/golden/`, `evals/harness/`, the new CI
job, and `scripts/check_env.sh`'s `--live` row are all still empty or unwritten. They
cannot be built honestly yet in the order this Erratum would need to claim them in: a golden
case is a recorded transcript from a real `anthropic` and `ollama` call
(`Decision` item 2 — *"a golden case is a pinned artifact"*), and neither provider adapter
this gate replays against exists — `ADR-0040`'s Erratum records the same gap for
`src/lionel/brain/providers/`. Building the harness before the adapters it calls would be
building a comparison with nothing on either side of it, which is not what "regression gate"
means. `Phase3_Entry_Checklist.md` item 3 tracks this as continuing, not done, and it
follows `ADR-0040`'s item 2 rather than running in parallel with it.
