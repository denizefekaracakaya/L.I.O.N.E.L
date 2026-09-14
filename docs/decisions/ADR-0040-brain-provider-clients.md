# ADR-0040: The three BrainProvider clients

| | |
|---|---|
| Status | **Accepted** — Efe, 2026-09-10. In force. See the Erratum |
| Date | 2026-09-10 |
| Phase | 3 |
| Related | [ADR-0001](ADR-0001-swappable-brain-provider.md), [ADR-0009](ADR-0009-extended-brain-provider-contract.md), [ADR-0013](ADR-0013-artifact-pinning.md), [ADR-0002](ADR-0002-project-root-path.md), [ADR-0036](ADR-0036-memory-client-and-embedding-runtime.md) |

## Context

[ADR-0001](ADR-0001-swappable-brain-provider.md) ships three `BrainProvider`
implementations — `anthropic`, `ollama`, `llamacpp` — and chooses none of their Python
clients. `pyproject.toml` says so in its own header:

> MASTER_PLAN_v2 names technologies (Qdrant, Kokoro, Piper, faster-whisper, openWakeWord,
> Ollama) whose PYTHON CLIENTS are not yet chosen. Those arrive with the phase that builds
> against them — G2 for memory, G6 for the sensory stack — each with its own ADR.

This is that ADR for G3. [ADR-0036](ADR-0036-memory-client-and-embedding-runtime.md) did the
same job for G2 and is the shape this one copies: arrive with the phase that needs it,
declare packages directly, withhold the `pyproject.toml` edit until acceptance.

Three providers, three different questions:

- **`ollama`** already has almost everything decided. `httpx>=0.27` is declared, and
  `dependencies.forbid_packages` (`DEP-002`) names it *the* HTTP client — *"httpx is already
  a dependency. Two HTTP clients is drift, not choice."* Ollama's API is plain HTTP/JSON.
  The only open question is whether the gateway calls it directly or takes the `ollama`
  package, which is itself a thin `httpx`-equivalent wrapper.
- **`anthropic`** has nothing decided. The SDK is a genuinely new dependency, and
  `Architecture_Freeze.md` §4 applies to it in full — it is also the one provider whose
  presence at L0 the tier model has an opinion about (`config/tiers/l0.toml`:
  `provider = "ollama"  # never "anthropic" at L0`; `ci/policy/policy.yaml`:
  `l0_forbidden_providers: [anthropic]`).
- **`llamacpp`** has nothing decided either, and its two candidate shapes carry genuinely
  different offline stories: in-process bindings (`llama-cpp-python`, a compiled extension —
  `scripts/check_env.sh` already tracks VS Build Tools for exactly this class of package,
  currently gated at `required_at: G6` for `whisper.cpp`) or `llama.cpp`'s own HTTP server as
  a second supervised process ([ADR-0014](ADR-0014-process-supervisor.md) already owns
  process lifetime).

## Decision

**All three providers ship this phase, as ADR-0001 already committed to.**

1. **`anthropic` (MIT, current 1.4.0)** is declared directly. It is the reference
   implementation ADR-0001's golden-transcript comparison needs on the other side of the
   comparison from a local model — without it there is nothing to compare `ollama` against,
   and [ADR-0041](ADR-0041-transcript-replay-gate.md) cannot be verified.
2. **`ollama` is called over `httpx` directly. No `ollama` package is declared.** Its API is
   HTTP/JSON with no binary protocol, no streaming framing `httpx` cannot already do, and no
   semantics a hand-rolled layer would silently get wrong the way ADR-0036's Alternatives
   Rejected found for Qdrant's filter/payload semantics — Ollama's surface is small enough
   that this is not that risk. Taking the package anyway would be `DEP-002`'s drift, declared
   on purpose rather than discovered by a gate.
3. **`llamacpp` ships as in-process bindings: `llama-cpp-python` (MIT, current 0.3.35).** Not
   the HTTP-server shape. A second supervised process is a second thing that can fail to
   start, and `llama-cpp-python` is exactly the class of package `scripts/check_env.sh`
   already has a preflight row for — the groundwork exists, it is simply pointed at the wrong
   gate (see item 5).
4. **All three declared directly in `pyproject.toml`, each naming this ADR**, the way
   ADR-0036 declared `qdrant-client` and `fastembed` rather than through an extra.
5. **`ci/policy/policy.yaml`'s `preflight.tools` row for `cl` moves from `required_at: G6`
   to `required_at: G3`.** It was scoped to `whisper.cpp` (G6) because nothing earlier
   needed a C++ toolchain. `llama-cpp-python` does, from the moment `pyproject.toml`
   declares it — `uv sync` fails for everyone, not only operators who select `llamacpp` as
   their runtime provider, because Python has no concept of "installed but not chosen." The
   row's `why` gains a second sentence naming both consumers.
6. **`core/turn_executor` still imports `BrainProvider` and nothing else** (ADR-0001,
   `ARCH-018`). None of the three clients above changes that; each is imported only from
   inside `src/lionel/brain/providers/`.

**Version bounds are not written in this document.** They are whatever `uv add` resolves on
acceptance, recorded in `uv.lock` and bounded in `pyproject.toml` per `DEP-001`. The version
numbers above are what PyPI reported on 2026-09-10, recorded so the proposal names real
software — the same discipline ADR-0036 held itself to, and for the same reason: a number
typed here from memory would be the seventh instance of the exact failure ADR-0036's own
Context describes, one ADR later.

**Credential handling needs no new mechanism.** `lionel.secrets` already resolves
`secret://` URIs and redacts them in log output (ADR-0015). The `anthropic` adapter reads
its API key the same way every other secret-bearing capability does.

**L0 isolation is provider selection, and that is sufficient.** `l0-conformance` already
asserts `network_allowed: "false"` and rejects `provider = "anthropic"` at L0
(`l0_forbidden_providers`). A credential sitting unread behind `secret://` resolution while
unused at L0 is inert configuration, the same shape the L0 `fallback_chain` already is when
it names providers a given tier will never select. No additional gate assertion is added —
the alternative, asserting that `secrets.resolve()` is never called for an
`anthropic`-scoped URI while `tier == l0`, is recorded below and rejected: it would duplicate
what provider selection already guarantees, checking the same fact from two places that can
drift against each other.

## Consequences

**What gets better.** `ADR-0001`'s Verification clause — *"the same golden transcript
produces equivalent tool calls under `anthropic` and `ollama`"* — has something to run
against. `Phase3_Entry_Checklist.md` item 5 (`src/lionel/brain/`) can be written against real
clients instead of the contracts alone.

**What this costs.**

- **Two new dependencies, one of them a networked SDK.** `anthropic` is the first package in
  this repository whose entire purpose is talking to a service outside Efe's machine on the
  ordinary path (not a fallback, not opt-in like the GitHub MCP server's `--live` checks).
  ADR-0007's guarantee is unaffected only because L0 already forbids selecting it — this ADR
  does not change that guarantee, it depends on it already existing.
- **`llama-cpp-python` moves the C++ toolchain requirement three phases earlier.** Anyone
  running `uv sync` from G3 onward needs VS Build Tools, not just G6 operators building
  `whisper.cpp`. `check_env.sh`'s preflight catches this before it becomes an hour-long stack
  trace, which is the entire reason that script exists, but the requirement is real and
  earlier than MASTER_PLAN_v2's original phase sketch implied.
- **Three code paths to test, as ADR-0001's own Consequences already said they would be.**
  [ADR-0027](ADR-0027-testing-strategy.md) makes this a replay-test obligation; ADR-0041
  is where that obligation gets a mechanism.

**What is deliberately not decided here.** Whether `llamacpp`'s model file is fetched,
where it is cached, or which quantization ships — a model artifact is `ADR-0013`'s territory
and needs its own lock entry the way the embedding model got one under ADR-0036, once a
specific model is chosen rather than a client library.

## Alternatives Rejected

| Alternative | Why rejected |
|---|---|
| **The `ollama` PyPI package instead of raw `httpx`** | A second HTTP client for one provider, which is precisely what `DEP-002` calls drift. The package's own value proposition — typed request/response models — is smaller than the cost of a caller needing to know two HTTP libraries exist in this codebase |
| **`llama.cpp`'s HTTP server instead of in-process bindings** | Trades a compiled Python extension for a second supervised process. `ProcessSupervisor` (ADR-0014) could own it, but a process that must be started, health-checked and torn down is more moving parts than a library import, for a provider whose whole point is running locally with the fewest possible failure modes |
| **Defer `anthropic` to a later ADR, ship `ollama`+`llamacpp` only this phase** | Without a reference implementation, ADR-0001's golden-transcript comparison has nothing on the other side of the comparison — "is the local model good enough yet?" stays folklore, which is the exact failure ADR-0021 was written to prevent |
| **Defer `llamacpp` to a later ADR, ship `ollama`+`anthropic` only this phase** | Reduces this phase's surface, but ADR-0001 already committed to three providers shipping, and un-committing to one is a decision about that ADR's scope, not about client libraries — it would need to amend ADR-0001, not sit inside this one |
| **An additional `l0-conformance` assertion that no `anthropic` credential is ever resolved while `tier == l0`** | Duplicates what provider selection already guarantees. Two mechanisms checking one fact is how they drift against each other silently — the exact shape ADR-0039 found four times over in the brain contracts, one layer down from schemas into gates |
| **`httpx` for `anthropic` too, hand-rolling the API** | Anthropic's SDK handles streaming SSE framing, retries, and the tool-use block shapes `ProviderResponse` and `StreamEvent` need translated at the adapter edge. Reimplementing that is exactly the risk ADR-0036's Alternatives Rejected named for a hand-rolled Qdrant layer, at higher stakes: a subtly wrong stream parse looks like a working assistant until it doesn't |

## Verification

**Withheld until this ADR is Accepted.** Neither `anthropic` nor `llama-cpp-python` is in
`pyproject.toml` while this is `Proposed`, `uv.lock` is unchanged, and
`ci/policy/policy.yaml`'s `cl` row still reads `required_at: G6`. `Architecture_Freeze.md`
§4 requires an ADR *and* Efe's approval before a new dependency exists; ADR-0029, ADR-0032,
ADR-0033, ADR-0034, ADR-0035, ADR-0036, ADR-0037, ADR-0038 and ADR-0039 each practised this
withholding. This is the tenth.

On acceptance:

| | |
|---|---|
| `pyproject.toml` | `anthropic` and `llama-cpp-python`, each with a bound and an `# ADR-0040` comment |
| `uv.lock` | regenerated; `DEP-001` and `licenses` see both — MIT, allowlisted |
| `ci/policy/policy.yaml` | the `cl` preflight row's `required_at` moves `G6` → `G3`; `why` names both `llama-cpp-python` and `whisper.cpp` |
| `tests/unit/test_preflight.py` | `V1_PREFLIGHT_TOOLS` and the `required_at` regex test both already cover this without change; `test_the_gate_dependencies_are_all_required_now` is what would catch a row moved to the wrong gate |
| `src/lionel/brain/providers/` | three adapters, each importing exactly one client, none importing another's |

Gate **G3**, alongside `ADR-0041`'s replay comparison — which is the thing this ADR exists
to make possible, not to verify itself.

## Erratum — 2026-09-10: Accepted; the withholding is discharged, and the resolver had an opinion

This ADR was written while `Proposed`, and its Verification section describes that pending
state as ongoing. Efe accepted it on 2026-09-10, the same day it was drafted. The decision is
unchanged — what follows corrects text that has stopped being true, per ADR-0029 rule 2, and
records one thing the acceptance surfaced that the proposal did not anticipate.

The Verification section opened:

> **Withheld until this ADR is Accepted.** Neither `anthropic` nor `llama-cpp-python` is in
> `pyproject.toml` while this is `Proposed`, `uv.lock` is unchanged, and
> `ci/policy/policy.yaml`'s `cl` row still reads `required_at: G6`. `Architecture_Freeze.md`
> §4 requires an ADR *and* Efe's approval before a new dependency exists; ADR-0029,
> ADR-0032, ADR-0033, ADR-0034, ADR-0035, ADR-0036, ADR-0037, ADR-0038 and ADR-0039 each
> practised this withholding. This is the tenth.

Discharged for the configuration and dependency half of the Decision. As of architecture
1.23.0:

| | |
|---|---|
| `pyproject.toml` | `anthropic>=1.4` and `llama-cpp-python>=0.3.35`, each carrying this ADR's number |
| `uv.lock` | regenerated; 69 packages resolved |
| `ci/policy/policy.yaml` | the `cl` preflight row's `required_at` moved `G6` → `G3`, `why` names both consumers |
| `tests/unit/test_preflight.py` | all 27 cases pass unchanged, confirming the ADR's own prediction that this needed no test edit |

**Not yet discharged: `src/lionel/brain/providers/`.** The Decision's sixth item and the
Verification table both name three provider adapters. None exist. That is real engineering
— translating each SDK's streaming shape into `StreamEvent`/`ProviderResponse`, handling
tool-call deltas, cancellation and health per-adapter — not a configuration change, and
writing it under this Erratum would be describing delivery that has not happened, the exact
failure this repository's own history exists to catch (`Phase2_Final_Signoff.md` §1: *"every
one of the four defects was in something reviewed, frozen, and never executed"*). It is
`Phase3_Entry_Checklist.md` item 2's remaining half, tracked there rather than claimed here.

### What the resolver did that this ADR did not predict

`uv lock` pulled **`httpx2`** — a second, distinct package (`httpx`'s own in-progress v2
rewrite, published separately), not a duplicate resolution of the `httpx` already declared.
`anthropic` depends on it directly for its transport. `DEP-002`'s principle — *"httpx is
already a dependency. Two HTTP clients is drift, not choice"* — did not anticipate a second
client arriving under a different name, and `dependencies.forbid_packages` is name-based:
`httpx2` is not `httpx`, so nothing caught it. `bash ci/run_gates.sh dependencies` passed
green with a second, unreviewed HTTP client silently in `uv.lock`.

This is `ADR-0036`'s `requests`-via-`fastembed` finding, one dependency later.
`httpx2` was added to `forbid_packages` and given a `transitive_exemptions` entry — pulled
by `anthropic`, owner `brain`, unblocked by `anthropic` moving to `httpx` (v1) or this
repository replacing the SDK — following the exact shape the `requests` entry already set.
`bash ci/run_gates.sh dependencies` now names it explicitly rather than missing it.
