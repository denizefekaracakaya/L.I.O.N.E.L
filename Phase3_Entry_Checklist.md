# Phase 3 Entry Checklist

**Decisions and prerequisites.** Phase 3 is `MASTER_PLAN_v2.md` §10 Phase 3 — Brain Gateway
& Provider Abstraction, gate **G3**. What started as decisions-only now tracks the
implementation each accepted decision commits to as well.

| | |
|---|---|
| Gate | G2 → G3 |
| Status | **OPEN** — all three Efe decisions made (ADR-0040, ADR-0041, item 4); items 2, 3, 5 still have implementation behind their decisions |
| Items | 8 |
| Done | **4 of 8 fully done (☑), 3 partial (◐)** |
| Blocking | 0 |

**This document states no counts about the pipeline.** `Phase1_Entry_Checklist.md` is out of
`doc-claims` scope because its per-item records and its current-state claims are interleaved
and cannot be separated without restructuring it — the entry says so, with an owner. Rather
than register a second document with the same problem, this one simply does not make claims
of that shape. Where a number matters it is in `Architecture_Freeze.md` or in
`Phase2_Final_Signoff.md` §8, both of which are measured.

---

## BLOCKING — had to complete before any Phase 3 work

### ☑ 1. Sign G2 — **DONE 2026-09-02**

```
Phase2_Final_Signoff.md §7   Signed | Efe · 2026-09-02
                             Verdict | PASS — G2 closed, Phase 3 may begin
                             Architecture at signing | 1.19.0 · sha256:0585d19fc64d…
```

`Phase2_Final_Signoff.md` §7 is Efe's and nobody else's. Phase 3 could not open while G2 was
unsigned; that is what a gated phase plan means, and G1's sign-off was blocking in exactly
the same way.

Both live clauses were re-witnessed on the host on the day of signing, with the real
embedder rather than the fixture — `ok persistence survived`, `ok semantic retrieved`, and
no `skip` on the embedder row — and `memory_backup.sh selftest` the same day.

Two things happened on signing, both written into the document rather than into a gate's
configuration:

| | |
|---|---|
| §7 | replaced with the signature block, the verdict, and the architecture version at signing |
| `doc_claims.documents` → `doc_claims.out_of_scope` | §8 stops tracking the present. A signed sign-off is a dated record; refreshing one is editing the archive |

Worth re-running on the host before signing, because clauses 6 and 7 are the only ones no
machine re-checks on its own — and, since 2026-09-01, one more:

```bash
docker compose up -d qdrant
bash scripts/verify_memory.sh
bash scripts/memory_backup.sh selftest
```

---

## DECIDED — Efe's calls, recorded in ADRs. Two of three still have work behind them

These were the reason this document existed. Phase 3 was the first phase whose
implementation could not begin with implementation: three of its six DoD clauses were
blocked on a decision `Architecture_Freeze.md` §4 reserves. All three are decided; two
still have real engineering behind the decision.

### ☑ 2. An ADR for the provider clients — **DONE 2026-09-16, all 3 adapters written**

ADR-0001 ships three implementations — `anthropic`, `ollama`, `llamacpp` — and chose none
of their Python clients. `pyproject.toml` said so in its own header: *"MASTER_PLAN_v2 names
technologies … whose PYTHON CLIENTS are not yet chosen. Those arrive with the phase that
builds against them."* This was that phase.

**Decided:** `anthropic>=1.4` and `llama-cpp-python>=0.3.35` (in-process bindings, not the
HTTP-server shape) as new dependencies, each in `pyproject.toml` naming `ADR-0040`.
`ollama` is called over the already-declared `httpx` — no second HTTP client, no `ollama`
package. `ci/policy/policy.yaml`'s `cl` preflight row moved `required_at: G6` → `G3`, since
`llama-cpp-python` needs the same toolchain `whisper.cpp` does, now three phases earlier.

**Found on acceptance:** `uv lock` pulled `httpx2` — a real, separate package (`httpx`'s own
in-progress v2, published under its own name), not a duplicate of the `httpx` already
declared. `anthropic` depends on it directly, and `dependencies.forbid_packages` being
name-based meant nothing caught it — the `requests`-via-`fastembed` finding ADR-0036
recorded, one dependency later. Now named in `forbid_packages` with a
`transitive_exemptions` entry, `bash ci/run_gates.sh dependencies` sees it and passes on
purpose rather than by omission.

**Not done:** `src/lionel/brain/providers/` — three adapters, each translating one SDK's
shape into `ProviderRequest`/`StreamEvent`/`ProviderResponse`/`ProviderCapabilities`. ADR-0040's
own Erratum says so plainly rather than claiming delivery: this is real engineering, not a
configuration change, and it did not happen in the same pass as the dependency additions.

**`ollama` is the one done.** `lionel.brain.providers.OllamaProvider` (`stream`,
`capabilities`, `health` against `/api/chat`, `/api/version`, `/api/ps`) and the
provider-agnostic `lionel.brain.streaming.aggregate_stream` it shares with the other two
adapters once they exist. `lionel.coordinators.BrainProvider` — the G1 stub, `generate(*,
messages, tools)`, untyped and unexercised by any test in the repository — is replaced by
the real streaming Protocol; declared in `coordinators/__init__.py` rather than
`lionel.brain`, because that module IS `core/turn_executor` and ADR-0001 says exactly that
is where the name belongs. 48 assertions, every shape checked against the real contracts
through `test_brain_contract.py`'s offline `$ref` registry. **Not witnessed against a live
Ollama** — none was reachable while writing this; `ADR-0041`'s `--live` mode is what
closes that gap.

**One gate-config gap found writing the test.** `ARCH-018`'s `provider_branch_allowed_dirs`
had never included `tests/` — a unit test for one adapter must import it directly to test
it, which is not the ADR-0001 hazard (a runtime caller forking per provider). Added,
architecture 1.24.0.

**One CI-config gap found the same day, the hard way.** `httpx` (a main dependency, not
the `ci` extra) was never installed by the `unit-tests` workflow job, which only names the
three `ci`-extra packages. `main` went red on both OS matrix entries within minutes of the
push — `ModuleNotFoundError` at test collection, not a real test failure. Fixed the same
day by adding `httpx` to that job's install line, with a comment naming the reason so the
next adapter's test dependency does not rediscover it.

**`anthropic` is the second adapter done.** `lionel.brain.providers.AnthropicProvider`
(`stream`, `capabilities`, `health` via the SDK's `messages.stream` and
`models.retrieve`). Genuinely different translation shape from `ollama`: tool-call
arguments arrive as real incremental JSON fragments (`input_json_delta`) rather than one
atomic chunk — the actual case `ToolCallDelta`'s `complete` flag and
`aggregate_stream`'s fragment-accumulation exist for — and call ids are the SDK's own
(`toolu_...`), not synthesized. `ProviderRequest.trust_level`'s documented purpose —
*"the adapter can annotate untrusted spans in the prompt"* — is implemented: a text block
whose `trust` is `tool_result` or `external_content` is wrapped with an explicit
`UNTRUSTED CONTENT` marker before it reaches the model, defence in depth only, per that
field's own description. `response_schema` and `image_ref` are both refused loudly
(`AnthropicError`) rather than silently dropped — the SDK's structured-output parameter
takes a Python type, not the raw JSON Schema this contract carries, and no ref-fetching
capability exists to turn an `image_ref` into bytes. 40 assertions, every fixture a real
`anthropic` SDK type constructed from the installed package's own definitions (verified
directly, not guessed), every request/response checked against the frozen contracts.
**Not witnessed against a live account** — no credential was available while writing
this; `ADR-0041`'s `--live` witness is what closes that gap. Anthropic's own cost is
never guessed: `cost_per_1k_input_usd`/`output_usd` are explicit constructor arguments,
and `estimated_cost_usd` stays `null` — honestly, not wrong — until an operator supplies
current pricing.

**A real cross-adapter inconsistency, caught and fixed in all three at once.**
`ProviderCapabilities.tool_call_reliability`'s own schema description says *"Set from the
eval harness (ADR-0021), not self-asserted."* Both `ollama` and `anthropic` had
self-asserted it anyway (`"degraded"`, `"native"`) — nothing caught this until writing
`llamacpp` made the pattern visible by comparison. All three now omit the field, and
`test_brain_contract.py` gained a check across all three that would catch a fourth
adapter reintroducing it.

**`llamacpp` is the third and final adapter.** `lionel.brain.providers.LlamaCppProvider`
— in-process bindings, no network, no HTTP client at all, the only one of the three
usable at L0 (`config/tiers/l0.toml`'s `fallback_chain`). The model loads lazily on
first use, behind a lock, with a failed load remembered rather than retried on every
subsequent turn. Tool call ids are the model's own, like `anthropic` and unlike the
synthesized ones `ollama` needed. Token usage is genuinely derived rather than guessed:
`Llama.n_tokens`'s delta before/after a call is the model's own exact running count
(prompt + completion combined), split by re-tokenizing the generated text —
`token_counts_estimated: True` because the split is inferred even though every number
feeding it came from the real tokenizer. 31 assertions.

**`llama_cpp` is imported lazily — module-level, unlike the other two adapters — and
that was the right call, checked rather than assumed.** PyPI ships llama-cpp-python as
a source tarball only, no prebuilt wheel for any platform; adding it to the `unit-tests`
CI job's install line, the fix the previous two adapters needed, would mean compiling
llama.cpp on every push. Confirmed by building a venv with every OTHER dependency the
job needs and `llama_cpp` deliberately absent, then running the full 376-test suite
against it — clean, because the test file never imports the package at all; every test
injects a fake model factory. `lionel.brain.providers.llamacpp_provider` imports it
inside `_default_factory` only, the same shape `lionel.memory`'s `fastembed` import
already uses, for the same reason: a missing package should be a named error at the
point of use, not an `ImportError` from CI's test collector.

### ◐ 3. An ADR for the transcript-replay gate — **ADR-0041 accepted 2026-09-10; harness not yet written**

v1.0 required the cross-provider comparison as a one-time measurement. v2's DoD requires it
as a regression gate — and, it turned out, contradicts itself about which phase it belongs
to: `MASTER_PLAN_v2.md` §10 Phase 3 requires it at G3, while the same document's directory
sketch, four hundred lines later, had labelled `evals/` `NEW Phase 8`.

**Decided:** a narrow slice of `ADR-0021`'s already-designed harness — `evals/golden/` +
`evals/harness/`, tool-call equivalence between `anthropic` and `ollama` only — pulled
forward to G3. Equivalence is over tool calls and parsed arguments, never text. A golden
case is a pinned artifact (`ADR-0013`'s way), entered in `artifacts.lock.yaml`. CI replays
against recorded provider responses; a `--live` mode replays against the real providers, on
the host, opt-in, never in CI — the same shape `check_env.sh` and `verify_memory.sh`
already have. `ADR-0021`'s full harness (STT WER, wake FAR/FRR, TTS, the leaderboard) stays
at G8, unchanged. `llamacpp` stays out of the comparison — ADR-0001 never named it, and its
tool-calling reliability is the thing under study, not a fixture to measure against.
`MASTER_PLAN_v2.md`'s `evals/` line now names both arrival dates.

**Not done:** `evals/golden/` and `evals/harness/` are still empty, no CI job exists, and
`check_env.sh` has no `--live` row for it yet. `ADR-0041`'s Erratum is explicit about why it
comes after item 2's adapters rather than beside them: a golden case is a recorded
transcript from a real `anthropic`/`ollama` call, and neither adapter exists to record one
from yet. Building the harness first would be a comparison with nothing on either side.

### ☑ 4. Whether `anthropic` may hold a credential at L0 — **DONE 2026-09-10, no new mechanism**

`lionel.secrets` resolves `secret://` and redacts in logs (ADR-0015), so the mechanism
already existed. `ADR-0040` decided that provider-selection enforcement is sufficient:
`l0-conformance` already asserts `network_allowed: "false"` and rejects
`provider = "anthropic"` at L0 (`l0_forbidden_providers`), and a credential sitting unread
behind `secret://` resolution while unused at L0 is inert configuration — the same shape the
L0 `fallback_chain` already is. A stronger assertion (checking that `secrets.resolve()` is
never called for an `anthropic`-scoped URI while `tier == l0`) was considered and rejected:
it would duplicate what selection already guarantees, checking one fact from two places that
can drift apart. Nothing changed; nothing needs to.

---

## PERMITTED WITHOUT AN ADR — work, and item 1 has cleared

### ◐ 5. `src/lionel/brain/` against the frozen contracts — **contract test done 2026-09-02, four defects found and fixed**

The contracts Phase 3 builds to are already frozen and inside the checksum set:
`tool-spec`, `stream-event`, `provider-request`, `provider-response`,
`provider-capabilities` in `contracts/events/v1/`. Implementation under `src/lionel/`
conforming to frozen contracts is explicitly permitted (§4).

**The G2 lesson applies here before a line is written.** All four of G2's defects were in
something reviewed, frozen, and never executed — and `memory-record.schema.json` had
described a state it forbade for twenty-six days. These five schemas have had no consumer
either. The first thing to write is the contract test, not the provider.

`tests/contract/test_brain_contract.py` was written first and ran before any provider code
existed. **Twelve assertions, four of them pinning a defect:**

| | |
|---|---|
| HealthStatus is defined twice | and no object satisfies both — `core/v1` requires `service`, `provider-capabilities` forbids it. **This blocks item 7's `health()` clause outright** |
| `Usage` is defined twice | `token_counts_estimated` exists only on the terminal one, and the quota ceiling is enforced off the streamed one |
| `cancellation_token_id` | a ULID where it is defined, any string where it is required. `""` validates |
| a reported tool name | unconstrained in both places it comes back, while `ToolSpec.name` pins it and cites ADR-0023 for why |

**ADR-0039 recorded all four and Efe accepted it 2026-09-02**, the day it was drafted — every
one of them was a `stability: stable` schema inside the checksum set, so §4 reserved the edit
to him. All five contracts are now 1.1.0: `HealthStatus` is one definition, a cancellation
token and a reported tool name are each constrained by `$ref` to the schema that defines
them, and the two `StopReason` copies became one. The four tests inverted into four
coherence-pinning classes. **Item 5 is unblocked; `src/lionel/brain/` may be written against
contracts that no longer contradict each other.**

### ☑ 6. The static check that no caller branches on provider name — **DONE 2026-09-10**

ADR-0001: *"No module outside `brain/providers/` may import a concrete provider or branch on
a provider name."* A gate enforcing an **existing** decision more completely needs no ADR —
that is §4's third permitted item, and it is the same standing `ARCH-001` has.

**The branching half (`ARCH-002`) already existed and had never been exercised.** Its own
gate — `architecture` — was already marked covered via `ARCH-001` and `ARCH-017`, so
`gate-coverage` (which tracks gates, not rules) would not have noticed `ARCH-002` silently
stop firing. That is exactly "step 6 is the one that gets skipped," one rule over from the
gate it was supposed to protect.

**The import half had no check at all.** New rule `ARCH-018`: no module outside
`src/lionel/brain/providers/` may `import lionel.brain.providers*`. Both `ARCH-002` and
`ARCH-018` now have a planted violation in `ci/self_test.sh` (33 → 35, both added together),
and both are cited against `ADR-0001`, which the gate's own ADR list had never named.

Verified: 23/23 gates · self-test 35/35 · checksum unchanged (`ci/gates/*.py` and
`ci/self_test.sh` are not in the checksum set) · 151 rules, regenerated docs current.

### ☐ 7. Cancellation within 200 ms, and `health()` reporting *not ready*

ADR-0025 sets the budget and names G3 as its gate. Both clauses are timing facts about a
running model on a host — `health()` must report not-ready *while Ollama loads a model*,
which cannot be observed on a CI runner that has no Ollama.

**Unblocked in two stages.** ADR-0039 item 1 (2026-09-02) made `HealthStatus` one
definition — `provider-capabilities.$defs.HealthStatus` now refs
`core/v1/health-status.schema.json` — so `health()` has a shape to return. ADR-0040
(2026-09-10) chose `llama-cpp-python`/`anthropic`/`httpx` as the clients, so there is now a
decision to build against. **Still blocked on item 2's adapters actually being written** —
`health()` reporting not-ready *while Ollama loads a model* needs the `ollama` adapter to
exist, and cancellation needs at least one streaming adapter to cancel.

This is the third instance of the same shape, so it should look like the first two rather
than being invented again: `scripts/verify_memory.sh` and `scripts/check_env.sh` are host
scripts, opt-in, announced before they act, exit `0/1/2`, and neither is a gate. **R-A20's
residual applies unchanged** — nothing forces them to run, and nothing can.

### ☑ 8. The cost ceiling — **DONE 2026-09-10**

`[brain.quota]` already exists in `config/lionel.toml` — `max_tokens_per_turn`,
`max_spend_per_day_usd`, `on_exceeded = "halt"` — chosen by ADR-0009 and read rather than
defaulted, the way `MemoryConfig` reads `[memory]`. Enforcement is implementation.

`src/lionel/brain/accounting/`: `BrainQuotaConfig.from_toml()` reads the section with the
same refusals `MemoryConfig` uses for `[memory]` — missing file, missing section, missing
key, an `on_exceeded` value that isn't `halt`/`warn`, a non-positive token ceiling, negative
spend. `QuotaGuard` tracks per-turn output tokens and per-calendar-day estimated spend
against it and returns a verdict; it does not call a provider or issue a
`CancellationToken`, because neither exists yet — it is the decision, not the action, for
whichever of `turn_executor` or the brain gateway calls it once items 2–4 are decided.

**Reads `StreamEvent.Usage`, not only `ProviderResponse.usage`**, which is the reason
ADR-0039 made the two shapes identical: the ceiling has to *halt generation*, so the guard
has to act on the mid-stream object, not the one that arrives after generation is already
over. `token_counts_estimated` gets a 20% safety margin (`ESTIMATED_TOKEN_SAFETY_MARGIN`,
a code constant rather than a fourth config key — `[brain.quota]` is ADR-0009's contract),
per that field's own description: *"the quota guard then applies a safety margin rather
than trusting the number."*

`tests/unit/test_brain_accounting.py`: 24 assertions — config refusals, per-turn
accumulation and the exact-at-the-ceiling boundary, the estimation margin (including the
case where it turns a pass into a halt), `warn` continuing to accumulate rather than
resetting, the daily boundary under a scripted clock, and a null `estimated_cost_usd`
(a local provider) contributing nothing. `tests/contract/test_brain_contract.py` gained one
more: `QuotaVerdict.stop_reason` is checked against the live `StopReasonValues` enum, so the
guard cannot drift from the contract it hands its verdict to.

Verified: 23/23 gates · self-test 35/35 · checksum unchanged (`src/lionel/` is not in the
checksum set) · 256 tests, 1 skipped.

---

## Ready — no action required

| | |
|---|---|
| The five brain contracts | frozen in `contracts/events/v1/`, in the checksum set, versioned |
| `lionel.secrets` | `secret://` resolution and log redaction (ADR-0015), exercised by G1 |
| `lionel.policy` | denies an unregistered tool by default (ADR-0012) |
| `lionel.coordinators` | five coordinators, four of them frozen dataclasses (ADR-0008) |
| `httpx` | declared, and `DEP-002` makes it the HTTP client rather than a choice to re-make |
| `[brain]` config | provider, fallback chain and quota all present and read from one file |
| the host preflight | `check_env.sh` already tracks VS Build Tools, which item 2 may need |

---

## What remains after G3

Not this document's scope, recorded so the sequence is visible: Phase 4 is the capability
services and the Policy Engine's enforcement path (G4), and `MASTER_PLAN_v2.md` §10 carries
both. The two open items that outlive Phase 3 are the Turkish TTS licence (R-A15, blocks
distribution at G6c) and R-A21's residual — that nothing schedules a memory backup.
