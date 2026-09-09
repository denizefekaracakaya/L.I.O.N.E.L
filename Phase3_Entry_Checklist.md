# Phase 3 Entry Checklist

**Decisions and prerequisites only.** No implementation. Phase 3 is `MASTER_PLAN_v2.md` §10
Phase 3 — Brain Gateway & Provider Abstraction, gate **G3**.

| | |
|---|---|
| Gate | G2 → G3 |
| Status | **OPEN** — G2 signed 2026-09-02; item 1 cleared, the rest are Phase 3 work |
| Items | 8 |
| Done | **2 of 8** |
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

## NEEDS EFE — decisions, not work. Each is `Architecture_Freeze.md` §4

These are the reason this document exists. Phase 3 is the first phase whose implementation
cannot begin with implementation: three of its six DoD clauses are blocked on a decision
that §4 reserves, and discovering that mid-phase is how a dependency gets added because it
was obviously needed.

### ☐ 2. An ADR for the provider clients

ADR-0001 ships three implementations — `anthropic`, `ollama`, `llamacpp` — and chooses none
of their Python clients. `pyproject.toml` says so in its own header: *"MASTER_PLAN_v2 names
technologies … whose PYTHON CLIENTS are not yet chosen. Those arrive with the phase that
builds against them."* This is that phase.

| Provider | What is already decided | What is not |
|---|---|---|
| `ollama` | `httpx>=0.27` is declared, and `DEP-002` names it *the* HTTP client. Ollama's API is HTTP | whether the gateway calls it directly or takes the `ollama` package. A second client for one provider is `DEP-002`'s drift |
| `anthropic` | nothing | the `anthropic` SDK is a **new dependency**. §4 applies in full |
| `llamacpp` | nothing | in-process bindings (`llama-cpp-python`, which compiles, and `check_env.sh` already tracks VS Build Tools for exactly this class of package) or its HTTP server. These are different decisions with different offline stories |

**ADR-0036 is the shape to copy.** It arrived with the phase that needed it, declared both
packages directly rather than through an extra, and its Verification withheld the
`pyproject.toml` edit until acceptance.

### ☐ 3. An ADR for the transcript-replay gate

v1.0 required the cross-provider comparison as a one-time measurement. **v2 requires it as a
regression gate**, and `CI_Architecture.md` §7 step 1 is *ADR first*. The decisions it needs
are not implementation details:

- what "the same golden transcript replays correctly" means when two models legitimately
  emit different prose — the comparison has to be over *tool calls and their arguments*,
  not over text, or the gate is a flake generator
- where the transcript lives, and what pins it (ADR-0013 is about artifacts that get
  replaced quietly)
- **what CI does when neither provider is reachable.** ADR-0007 is the constraint: a gate
  that needs the network is a gate that is red on a plane. The honest answer is probably a
  recorded-response fixture in CI plus a `--live` witness on the host, which is what
  `check_env.sh` and `verify_memory.sh` both settled on — but it is a decision, and the
  fixture/live split is precisely where a proof quietly stops proving anything

### ☐ 4. Decide whether `anthropic` may hold a credential at L0

`lionel.secrets` resolves `secret://` and redacts in logs (ADR-0015), so the mechanism
exists. The question is the degradation ladder: `[brain] fallback_chain` is
`["ollama", "llamacpp"]` and the comment beside it reads *"no network deps at L0"*. Phase 3
is the first time a provider that needs egress becomes reachable from the turn path, and
`l0-conformance` is the gate that will have an opinion.

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

### ☐ 6. The static check that no caller branches on provider name

ADR-0001: *"No module outside `brain/providers/` may import a concrete provider or branch on
a provider name."* A gate enforcing an **existing** decision more completely needs no ADR —
that is §4's third permitted item, and it is the same standing `ARCH-001` has.

Seven steps, `CI_Architecture.md` §7, and step 6 is the one that gets skipped: a planted
violation in `ci/self_test.sh`. `gate-coverage` now fails if it is missing.

### ☐ 7. Cancellation within 200 ms, and `health()` reporting *not ready*

ADR-0025 sets the budget and names G3 as its gate. Both clauses are timing facts about a
running model on a host — `health()` must report not-ready *while Ollama loads a model*,
which cannot be observed on a CI runner that has no Ollama.

**Unblocked 2026-09-02.** ADR-0039 item 1 made `HealthStatus` one definition —
`provider-capabilities.$defs.HealthStatus` now refs `core/v1/health-status.schema.json` —
so `health()` has a shape to return.

This is the third instance of the same shape, so it should look like the first two rather
than being invented again: `scripts/verify_memory.sh` and `scripts/check_env.sh` are host
scripts, opt-in, announced before they act, exit `0/1/2`, and neither is a gate. **R-A20's
residual applies unchanged** — nothing forces them to run, and nothing can.

### ☐ 8. The cost ceiling

`[brain.quota]` already exists in `config/lionel.toml` — `max_tokens_per_turn`,
`max_spend_per_day_usd`, `on_exceeded = "halt"` — chosen by ADR-0009 and read rather than
defaulted, the way `MemoryConfig` reads `[memory]`. Enforcement is implementation.

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
