# L.I.O.N.E.L — Master Execution Plan v2.0

**Logical Interface for Orchestrated Network & Execution Layers**

| Field | Value |
|---|---|
| Document | `MASTER_PLAN_v2.md` — **authoritative** |
| Supersedes | `MASTER_PLAN_v1.md` (preserved verbatim as historical record) |
| Project root | `C:\Users\deniz\Desktop\L.I.O.N.E.L` |
| Host OS | Windows + Git Bash (MSYS2) |
| Runtimes | Host Runtime (Windows) + Cluster Runtime (Minikube → cloud-portable) |
| Reviewer | Principal AI Architect |
| Owner / approver | Efe |
| Status | **AWAITING APPROVAL — PHASE 0** |
| Implementation started | **No.** Repository contains planning documents only |

---

# 1. Executive Summary

## 1.1 Verdict

v1.0 is a **good single-machine plan and a poor distributed one**. Its core intuitions — MCP as the universal capability boundary, a swappable brain, hard phase gates with binary exit criteria — are correct and survive intact into v2.0. What it lacks is everything that only becomes visible once you stop assuming one process on one box: plane separation, service boundaries, failure semantics, telemetry, and a deployment story.

The review recommends **adopting all fifteen proposed changes**, with four of them amended and two resequenced. It adds five changes the proposal list did not contain, one of which — the **Degradation Ladder (ADR-0007)** — is the single most important addition in this document.

## 1.2 The finding that matters most

**"Cloud-deployable Kubernetes" and "fully local and autonomous" are in direct tension, and v1.0 has no mechanism to stop the second one from quietly dying.**

This is the standard failure mode of local-first projects that add a cluster. Nobody decides to abandon offline operation. It erodes: one service assumes the network is there, then another, and eighteen months later the airplane-mode test has been skipped for a year and nobody can make it pass again. v1.0's DoD contained exactly the right test (airplane mode, Ollama provider, full voice loop) and exactly zero machinery to keep it passing.

v2.0 answers this with a **four-rung Degradation Ladder** — L0 fully offline, L1 host + local cluster, L2 host + remote cluster, L3 cloud brain — where **L0 conformance is a permanent, blocking CI gate on every release**. If L0 breaks, the build is red, regardless of what L2 and L3 can do. That single rule is what converts "local-first" from a slogan into an invariant.

## 1.3 The timing finding

**Nothing has been implemented yet.** The repository contains planning documents and no source. This is the cheapest possible moment to perform this review — the migration cost from v1.0 to v2.0 is measured in decisions, not refactors. Section 11 quantifies this: **zero lines of code require rewriting.** Had this review landed after Phase 3, the coordinator decomposition and the memory-service extraction alone would have cost multiple sessions of rework.

## 1.4 Disposition of the fifteen proposals

| # | Proposal | Verdict | Note |
|---|---|---|---|
| 1 | Dual-runtime (Host / Cluster) | **ADOPT — amended** | Two runtimes, but *four* deployment tiers. See ADR-0007 |
| 2 | Control plane / data plane separation | **ADOPT as-is** | Strongest proposal in the set. PCM must never traverse MCP |
| 3 | Split `host/loop.py` | **ADOPT — specified** | Five named coordinators, not an unspecified "split" |
| 4 | Expand `BrainProvider` | **ADOPT — extended** | Adds two the list missed: a Tool Schema IR and cost accounting |
| 5 | Capability tools over shell | **ADOPT — escalated** | Don't constrain shell execution. **Delete it.** Add a Policy Engine |
| 6 | Memory Service over Qdrant | **ADOPT as-is** | Qdrant becomes one adapter behind a port |
| 7 | Pin images and artifacts | **ADOPT — escalated** | Digest pinning + a checksummed artifact lockfile |
| 8 | Windows subprocess compatibility | **ADOPT — amended** | Job Objects, *and* structurally fewer subprocesses |
| 9 | `.env` expansion strategy | **ADOPT — escalated** | Not better interpolation — a typed `SecretResolver` with no interpolation at all |
| 10 | ADRs replace `<thought>` | **ADOPT — extended** | ADRs indexed into Memory Service, closing the project-memory rule |
| 11 | Turkish speech pipeline | **ADOPT — amended** | The STT model change is the larger issue; TTS is the visible one |
| 12 | Kubernetes-native phase | **ADOPT — scoped** | Cloud-portable per Efe. Phase 7 |
| 13 | MLOps phase | **ADOPT — resequenced** | Eval harness must precede Kubernetes, not follow it |
| 14 | Observability phase | **ADOPT — resequenced** | Must land *before* distribution. Moved to Phase 5 |
| 15 | Security review phase | **ADOPT — amended** | A continuous gate at every phase, plus a terminal audit |

## 1.5 Additions not in the proposal list

| ID | Addition | Why it is missing-critical |
|---|---|---|
| **A1** | **Degradation Ladder L0–L3** (ADR-0007) | Without it, cloud-deployability silently kills local-first |
| **A2** | **Cancellation & backpressure architecture** (ADR-0025) | v1.0 requires barge-in but has no way to cancel in-flight brain generation, tool calls, or TTS playback across process boundaries |
| **A3** | **Side-effect classification on every tool** (ADR-0026) | `read` / `write` / `destructive` tagging drives retry safety, policy, and confirmation. Retrying a read is free; retrying a write is a bug |
| **A4** | **Contract & replay testing strategy** (ADR-0027) | v1.0 had per-phase unit tests and no schema conformance, no golden-transcript replay, no hardware-free sensory harness. Phases 1–6 are untestable in CI as written |
| **A5** | **Turkish locale correctness** (ADR-0023) | The dotted/dotless `İ/ı` casing problem breaks naive `.lower()` on wake words, tool names, and config keys. A specific, real, silent bug class |

---

# 2. Strengths — What Survives Untouched

A review that rewrites everything has learned nothing. These v1.0 decisions are correct and are **carried into v2.0 unchanged**.

| # | Decision | Why it holds up |
|---|---|---|
| S1 | **MCP-first capability model** | Ages exceptionally well. A single protocol boundary for every capability means adding a skill never touches the core. This is the decision that makes Phases 7–10 possible at all. Preserved as ADR-0003, with one clarification: MCP is the *control* protocol, not the transport for everything |
| S2 | **Swappable `BrainProvider`** (ADR-0001) | Correct call. Defers an irreversible decision, makes the local-vs-API gap measurable rather than assumed. v2.0 widens the interface but does not touch the principle |
| S3 | **Hard phase gates with binary DoD** | Rare discipline. Checkboxes that are unambiguously true or false, not "mostly working." Every v2.0 phase inherits this format |
| S4 | **The Windows / Git Bash hazard table** | Real operational knowledge, not boilerplate. `MSYS_NO_PATHCONV`, CRLF-in-`.sh`, `pwd -W`, the Store-stub `python`. Carried forward verbatim and extended |
| S5 | **Latency budget as a first-class requirement** | Naming < 2.5 s wake-to-speech up front is what separates an assistant from a demo. v2.0 keeps the budget and adds the telemetry to *enforce* it — v1.0 could only aspire to it |
| S6 | **Named volume over bind mount, with reasoning** | Correct on both counts (MSYS path mangling, WSL2 NTFS I/O). Survives into the StatefulSet design |
| S7 | **Loopback-only port binding** | Right default. Extended in v2.0 to NetworkPolicy and mTLS |
| S8 | **Airplane-mode test as the DoD for "local"** | The single best idea in v1.0. v2.0 promotes it from a Phase 4 checkbox to a permanent CI gate (ADR-0007) |
| S9 | **Filesystem MCP scoped to one root** | Correct least-privilege instinct. Generalized in v2.0 into the Policy Engine |
| S10 | **Pinning the embedding model, with a re-index note** | Shows the author understood that vector stores have a hidden schema. Generalized into ADR-0013 |
| S11 | **Risk register with real mitigations** | Not decoration. R2 (local tool-calling unreliability) correctly identified the highest-impact unknown and tied it to a gate |
| S12 | **The GitHub golden rule** | No autonomous commits. Non-negotiable, carried forward verbatim |
| S13 | **CPU-before-CUDA sequencing for whisper.cpp** | Correct risk posture: ship the boring build, treat acceleration as optimization |
| S14 | **Two-collection memory split** (durable vs. episodic) | Correct instinct that retention policy differs by memory kind. v2.0 formalizes this inside the Memory Service rather than discarding it |

---

# 3. Weaknesses

Ordered by architectural cost of leaving them unaddressed.

## W1 — The God Loop
`host/loop.py` is specified as "the agent loop: perceive → think → act → speak." That is four distinct responsibilities, each with its own failure modes, concurrency model, and test strategy, fused into one module. It would accumulate session state, tool dispatch, prompt assembly, streaming, interrupt handling, and error recovery. By Phase 4 it becomes the file nobody wants to open.
**Cost if unfixed:** every future feature touches it; test coverage collapses; barge-in and cancellation become unimplementable.

### W2 — Allowlisted shell is not a security boundary
v1.0 correctly identified `shell_server.py` as "the sharpest edge in the entire project" and then reached for the wrong tool. An allowlist gates the *verb* and leaves the *arguments* wide open: path traversal, flag injection, TOCTOU races, and — most relevantly for an agent that reads documents — prompt injection converting untrusted text into a shell invocation. R6 in v1.0's own risk register names this and rates the mitigation as sufficient. It is not.
**Cost if unfixed:** a single injected document becomes arbitrary code execution on the developer's primary machine.

### W3 — Qdrant conflated with memory
v1.0 treats the vector store *as* the memory system. A vector store does similarity search. A memory system needs an ingestion policy (what is worth keeping), deduplication, consolidation, decay, hybrid retrieval ranking, provenance, and a redaction path. v1.0 gestures at this with `memory/policy.py` but leaves the boundary undefined and lets callers reach `qdrant-store` directly.
**Cost if unfixed:** memory quality degrades as volume grows; there is no way to forget; swapping or supplementing the backend requires touching every caller.

### W4 — Zero observability
There is no tracing, no metrics, no structured event model. The Phase 4 latency budget — six stages, each with a target — is **unmeasurable and therefore unenforceable** as written. The DoD says "measured wake→speech latency is under 2.5 s and recorded in `docs/RUNBOOK.md`", which is a manual stopwatch reading pasted into a Markdown file, once.
**Cost if unfixed:** no regression detection; distributed debugging in Phase 7 becomes guesswork.

### W5 — Non-reproducible builds
`qdrant/qdrant:latest`, `ghcr.io/github/github-mcp-server` with no tag, models fetched by URL with no checksum, `<pinned-tag>` left as a literal placeholder for whisper.cpp. A rebuild in three months produces a different system.
**Cost if unfixed:** "it worked last week" becomes unanswerable; vector store silently invalidated by an embedding model bump.

### W6 — Undefined secret expansion
`config/mcp.servers.json` contains `"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_PAT}"`. JSON does not expand variables. Docker does not expand them in that position. No component is named as the expander. It would fail, and the natural fix — string interpolation in the loader — is how tokens end up in log lines and crash dumps.
**Cost if unfixed:** either it doesn't work, or it works and leaks.

### W7 — English-only STT contradicts the Turkish requirement
v1.0 recommends `ggml-base.en.bin`. The `.en` models are English-only — not "better at English," but structurally incapable of Turkish. With Turkish now an explicit requirement, this is not a tuning choice but a hard incompatibility.
**Cost if unfixed:** Phase 6 fails at the last gate, after the pipeline is already built around the wrong model size.

### W8 — No failure or degradation model
v1.0 has no answer for: Qdrant is down mid-turn; Ollama is loading a model and times out; the API rate-limits; the audio device disappears mid-utterance. Every one of these produces an unhandled exception in a voice loop, which is indistinguishable from the assistant being broken.
**Cost if unfixed:** the system is brittle in exactly the situations where a user notices.

### W9 — No cancellation architecture
Barge-in is a stated requirement with a 300 ms budget. Meeting it requires cancelling, concurrently: TTS synthesis, audio playback, brain token generation, and any in-flight tool call — some of which will be in another process, and after Phase 7, on another machine. v1.0 describes the requirement and not the mechanism.
**Cost if unfixed:** barge-in either doesn't work or leaves orphaned work running.

### W10 — Phase 4 is overloaded
One gate covering native C++ compilation, ONNX TTS, wake-word training, VAD, full-duplex audio, and barge-in. Six risky components, one binary pass/fail. When it fails, the cause is ambiguous.
**Cost if unfixed:** the project's riskiest phase is also its least diagnosable.

### W11 — `<thought>` as the reasoning artifact
Ephemeral, unreviewable, ungreppable, and gone the moment the session ends. It cannot be diffed, cited in a PR, or retrieved six weeks later. It also does not satisfy the project's own project-memory rule, which requires decisions to be *stored*.
**Cost if unfixed:** design rationale evaporates; the same debates recur.

### W12 — Testing strategy is unit tests only
Four `test_phaseN_*.py` files. No MCP schema contract tests, no golden-transcript replay for provider comparison, no chaos tests, and — critically — no way to test the sensory pipeline without a live microphone, which means **no CI coverage of Phase 6 at all**.
**Cost if unfixed:** the highest-risk subsystem is the least tested.

### W13 — No deployment story
v1.0's deployment model is "run the scripts on the box." No packaging, no image build, no environment separation, no upgrade or rollback path.

### W14 — Secret scope and rotation undefined
The fine-grained PAT scoping is good. There is no rotation cadence, no revocation runbook, no story for the Anthropic API key, and no separation between dev and runtime credentials.

---

# 4. High Priority Changes

These are blocking. They change interfaces and must land before the code they constrain is written.

## H1 — Adopt the Degradation Ladder (ADR-0007) ★ keystone

Four deployment tiers, each independently testable, each with an owner-visible capability delta.

| Tier | Composition | Network | Brain | Purpose |
|---|---|---|---|---|
| **L0** | Everything in the Host Runtime on Windows | **None** | Ollama / llama.cpp | The autonomy guarantee. Airplane mode |
| **L1** | Host Runtime + Cluster Runtime on Minikube, same machine | Loopback only | Ollama in-cluster | Proves service boundaries without leaving the box |
| **L2** | Host Runtime on Windows + Cluster Runtime on remote k8s | mTLS over LAN/WAN | In-cluster or API | Scale-out; the cloud-portable target |
| **L3** | L2 + Claude API as brain | Internet | Claude API | Maximum capability, minimum independence |

**The invariant, stated as a rule:**

> **L0 conformance is a blocking CI gate on every release.** A change that improves L2/L3 while breaking L0 is a rejected change, not a tradeoff.

**Components that may never leave the Host Runtime**, and why:

| Component | Reason |
|---|---|
| Audio capture / playback | Physical device access. Not virtualizable across the boundary at acceptable latency |
| Wake-word detection | Latency *and* privacy — raw audio must not cross a network boundary before the wake word fires |
| Local filesystem capability | The files are on this machine |
| Interrupt controller | Must respond in 300 ms with no network in the path |

Everything else — memory, brain gateway, STT inference, TTS inference, non-local capabilities — is placement-flexible and addressed by URI, not by import.

## H2 — Separate control plane from data plane (ADR-0006)

MCP is JSON-RPC. Pushing 16 kHz PCM through it means base64 inflation, no backpressure, head-of-line blocking behind unrelated tool calls, and no jitter buffer. It would work in a demo and fall apart under load.

| | Control Plane | Data Plane |
|---|---|---|
| **Carries** | Tool calls, capability discovery, memory ops, config, health | Audio frames, partial transcripts, synthesized PCM, future video |
| **Protocol** | **MCP** (JSON-RPC 2.0) | **gRPC bidirectional streaming** |
| **Transport** | stdio (L0 local) → Streamable HTTP (L1+) | HTTP/2; WebRTC deferred to ADR-0028 if NAT traversal is ever needed |
| **Shape** | Request / response, low volume, high semantic value | Continuous, high volume, latency-critical |
| **Failure mode** | Retry with idempotency key | Drop frames, degrade quality, never block |
| **Ordering** | Per-request | Strict, sequence-numbered |

**Two hard rules:**
1. **No PCM ever crosses the control plane.**
2. **No control decision ever rides the media stream.**

**What binds them:** every turn carries a `turn_id` that serves as the OpenTelemetry trace ID on both planes. A single trace shows wake → capture → STT → memory recall → brain → tool calls → synthesis → playback, across both protocols and both runtimes. This is the reason Phase 5 (Observability) must precede Phase 7 (Kubernetes).

## H3 — Decompose the loop into five coordinators (ADR-0008)

Replaces `host/loop.py`. Each has one responsibility, one failure mode, and its own test suite.

| Coordinator | Owns | Explicitly does not know |
|---|---|---|
| **SessionCoordinator** | Session lifecycle, turn queue, conversation state, wake/sleep | How a turn is executed |
| **TurnExecutor** | One turn: brain call → tool loop → response assembly | Where the brain runs; which provider |
| **ContextAssembler** | Prompt construction: system prompt, memory recall, history windowing, token budget | The brain's wire format |
| **ToolRouter** | Capability discovery, policy evaluation, MCP dispatch, result normalization | What any specific tool does |
| **InterruptController** | Barge-in detection, cancellation fan-out, cleanup | What is being cancelled |

State ownership is explicit: **SessionCoordinator holds all mutable session state; every other component is stateless and receives what it needs as arguments.** This is what allows cluster services to be restarted mid-conversation without losing the conversation, and it is a prerequisite for H1's L2 tier.

## H4 — Abolish shell execution; adopt capability tools + Policy Engine (ADR-0011, ADR-0012)

**`shell_server.py` is deleted from the plan.** Not constrained — removed. There is no allowlist that makes arbitrary command execution safe on a developer's primary machine when the agent also reads untrusted text.

Replaced by **typed capability tools**: narrow, single-purpose, fully-schema'd operations with no free-text passthrough to an interpreter. `service.restart(name)` where `name` is an enum. `fs.read(path)` where `path` is a validated project-relative type. `process.list()` with no arguments at all. If a capability cannot be expressed as a typed schema, it does not become a tool.

Every tool declares metadata that the **Policy Engine** evaluates *before* dispatch:

| Field | Values | Drives |
|---|---|---|
| `side_effect` | `read` \| `write` \| `destructive` | Retry safety, confirmation requirement (A3 / ADR-0026) |
| `trust_required` | `any` \| `user_originated` \| `operator` | Blocks injected content from reaching write tools |
| `rate_limit` | per-tool budget | Runaway loop containment |
| `audit` | `bool` | Immutable audit log entry |

The Policy Engine sits in `ToolRouter`, is declarative (rules in config, not code), and **defaults to deny**. Its decisions are logged whether they allow or refuse.

## H5 — Memory Service, with Qdrant as one backend (ADR-0010)

Qdrant is demoted from "the memory system" to "the vector backend behind a port." The **Memory Service** owns the parts a vector store does not provide:

| Concern | Responsibility |
|---|---|
| **Ingestion policy** | What is worth remembering. Salience scoring, not "store everything" |
| **Deduplication** | Near-duplicate detection before write |
| **Consolidation** | Periodic summarization of episodic → durable |
| **Decay & TTL** | Episodic memory expires; durable memory does not |
| **Retrieval ranking** | Hybrid: vector similarity + recency + importance + provenance, not raw cosine |
| **Provenance** | Every memory records its source and confidence |
| **Redaction** | A real `forget(id)` path. "No, that's wrong" must be actionable |
| **Re-index** | Embedding model migration without data loss |

Ports: `VectorBackend` (Qdrant today; pgvector or a managed service later), and a reserved `EntityBackend` seam for a future relational or graph store for entity memory. Callers talk to the Memory Service's MCP interface only — **direct `qdrant-store` access is removed from the capability surface.** v1.0's two-collection split (durable / episodic) is preserved as the service's internal schema.

## H6 — Extended `BrainProvider` contract (ADR-0009)

ADR-0001's principle is untouched; the interface widens. The proposal's six additions are adopted, plus two it omitted.

| Capability | Purpose |
|---|---|
| `ProviderCapabilities` | Declares `native_tools`, `structured_output`, `streaming`, `vision`, `max_context`, `token_counting`. **Callers branch on capability, never on provider name** |
| `health()` | Liveness + readiness. Ollama loading a 30 GB model is *not* ready |
| Metrics emission | Latency, tokens, tool-call success rate, per-provider — feeds Phase 5 |
| Structured outputs | Schema-constrained generation, with a documented fallback for providers lacking native support |
| Cancellation token | On **every** call. Non-optional. Prerequisite for H3's InterruptController |
| Tool metadata normalization | See below |
| **Streaming abstraction** | A single `StreamEvent` union — `TextDelta`, `ToolCallDelta`, `Usage`, `Done`, `Error` — so callers never see provider-native chunk formats |
| **➕ Tool Schema IR** *(added)* | A provider-neutral `ToolSpec` intermediate representation, translated at the adapter edge into Anthropic tool blocks / OpenAI functions / Ollama format. **Without this, provider independence is fictional** — tool schemas leak provider shape into every skill server |
| **➕ Cost & quota accounting** *(added)* | Token and spend counters per provider, with a configurable ceiling. L3 without a budget is an unbounded liability |

## H7 — Observability before distribution (ADR-0019) — resequenced

Proposal 14 placed observability late. **It must land before Kubernetes.** Debugging a distributed system you cannot trace is the most expensive form of technical debt available, and Phase 7 creates exactly that system.

- **Traces:** OpenTelemetry, `turn_id` as trace ID, spanning both planes and both runtimes.
- **Metrics:** latency histograms per pipeline stage, mapped 1:1 to the v1.0 latency budget so the budget becomes an alert instead of a stopwatch reading. Plus token/cost counters, tool success rates, wake-word FAR/FRR.
- **Logs:** structured JSON (`structlog`), correlated by `turn_id`, **with secret redaction at the formatter** — not at the call site, where it will eventually be forgotten.
- **Backend:** OTel Collector → Prometheus / Tempo / Loki, Grafana on top. Runs in the Cluster Runtime; the Host Runtime exports to it, and **buffers to disk when it is unreachable** so L0 still produces telemetry.

## H8 — Artifact pinning and supply chain (ADR-0013)

| Artifact | Pinning requirement |
|---|---|
| Container images | Tag **plus** digest: `qdrant/qdrant:v1.x.y@sha256:…` |
| whisper.cpp | Submodule pinned to a release tag and commit SHA — the literal `<pinned-tag>` placeholder in v1.0 must be resolved |
| Models (whisper, Kokoro, Piper, wake word) | `artifacts.lock.toml`: URL, SHA-256, size, license, and the ADR that chose it. Download script verifies before use and **fails closed** |
| Python | `uv.lock`, `--require-hashes` |
| Node | `package-lock.json`, `npm ci` |
| Embedding model | Pinned; a change requires a documented full re-index (H5 owns the migration path) |

## H9 — Secrets: typed resolution, zero interpolation (ADR-0015)

Replaces the broken `${GITHUB_PAT}` mechanism. **No string interpolation anywhere.** Config references secrets by a typed URI that a `SecretResolver` dereferences at point of use:

- `secret://env/GITHUB_PAT` — local dev
- `secret://file/…` — mounted file
- `secret://dpapi/…` — Windows Credential Manager, for L0/L1 on the host
- `secret://k8s/lionel-github/token` — Kubernetes Secret via External Secrets Operator, L2+

Resolved values are wrapped in a `SecretStr` type whose `__repr__` and `__str__` redact, so a secret that reaches a log line prints as `***`. Config layering is explicit and ordered: defaults → `lionel.toml` → environment → CLI. **`.env` is developer-local only and never a production mechanism.**

## H10 — Cancellation and backpressure (ADR-0025) — added

Barge-in's 300 ms budget requires a cancellation mechanism that crosses process and network boundaries.

- A single `CancellationToken` per turn, propagated to every async operation.
- **Fan-out order matters:** stop audio playback first (the user-perceptible effect), then abort TTS synthesis, then cancel brain streaming, then cancel in-flight tool calls.
- Tool cancellation semantics depend on `side_effect` (A3): `read` tools abort freely; `write` tools must either complete or roll back, never be abandoned mid-flight.
- Data plane applies backpressure by dropping frames, never by blocking the control plane.
- gRPC stream cancellation carries the token across the runtime boundary.

---

# 5. Medium Priority Changes

Important, but they do not block the interfaces in Section 4.

## M1 — Windows subprocess handling (ADR-0014)
Two-part fix. **Structural:** reduce subprocess count by preferring HTTP-transport MCP servers over stdio wherever the server supports it — the best-handled subprocess is the one that does not exist. **Tactical:** for the ones that remain, a `ProcessSupervisor` abstraction wrapping Windows **Job Objects** (reliable kill-tree; POSIX process groups are not available and naive termination orphans children), `CREATE_NEW_PROCESS_GROUP`, non-blocking stdio to avoid pipe-buffer deadlock, `ProactorEventLoop` for asyncio subprocess pipes, and long-path awareness (260-char limit unless opted out).

## M2 — Turkish speech pipeline (ADR-0017, ADR-0018, ADR-0023)

**The TTS change is the visible one; the STT change is the larger one.**

| Layer | v1.0 | v2.0 | Note |
|---|---|---|---|
| **STT** | `ggml-base.en.bin` | Multilingual `large-v3-turbo` | `.en` models are structurally English-only. **This is a correctness fix, not a tuning choice** |
| **TTS (EN)** | Kokoro | Kokoro — unchanged | Preserves the v1.0 decision |
| **TTS (TR)** | *(absent)* | **Piper** `tr_TR-fettah-medium` / `tr_TR-dfki-medium` | Both ONNX, both CPU-fast, both local — same operational profile as Kokoro |
| **Routing** | n/a | `TTSProvider` port, language-routed | Same pattern as `BrainProvider`. Adding a third language is an adapter |
| **Wake word** | `hey_jarvis` → custom EN | Custom model trained on Turkish pronunciation | openWakeWord is language-agnostic; the training data is not |
| **Text normalization** | *(absent)* | Per-locale: numbers, dates, abbreviations, currency | Turkish number-to-words differs structurally from English |

**ADR-0023 — the dotted/dotless `i` trap.** Turkish has four `i` characters: `i I ı İ`. Invariant `.lower()` maps `I → i`, but Turkish maps `I → ı`. Any code that case-folds a wake word, tool name, config key, or user utterance for comparison will silently mismatch. **Rule: all internal identifier comparison uses invariant casing explicitly; only user-facing display text uses locale-aware casing.** This bug class is invisible in English testing and guaranteed in Turkish production.

**Latency note:** `large-v3-turbo` is materially heavier than `base.en`. The 800 ms STT budget must be re-measured, and this is a concrete driver for moving STT inference into the Cluster Runtime at L1+ where it can use a GPU — one of the clearest justifications for H1's tiering.

## M3 — ADR-driven decisions replace `<thought>` (ADR-0016)
Exploratory reasoning remains internal; the **artifact** changes. Every decision that constrains future work produces a lightweight ADR (MADR format: Context / Decision / Consequences / Alternatives Rejected). Smaller calls produce a short Decision Summary in the response. ADRs are diffable, greppable, citable in review, and — critically — **indexed into the Memory Service on merge**, so `memory.recall` retrieves them months later. This is what actually satisfies the project's project-memory rule, which `<thought>` never could.

## M4 — Testing strategy (ADR-0027) — added
Five layers, replacing v1.0's four unit-test files:

| Layer | Scope |
|---|---|
| **Unit** | Pure logic, no I/O |
| **Contract** | Every MCP server validated against its declared schema; every `BrainProvider` against the ABC. Catches drift before integration |
| **Replay** | Golden transcripts replayed across providers. This is how ADR-0001's Anthropic-vs-Ollama comparison becomes a *regression gate* rather than a one-time measurement |
| **Chaos** | Kill Qdrant mid-turn; time out the brain; unplug the audio device. Each must degrade, not crash — closes W8 |
| **Sensory harness** | Pre-recorded WAV fixtures injected at the audio-buffer boundary, so **the entire voice pipeline is CI-testable without a microphone**. Closes W12, the largest coverage hole in v1.0 |

## M5 — Failure and degradation semantics (closes W8)
Every cross-boundary call declares: timeout, retry policy (governed by `side_effect`), circuit breaker threshold, and **degraded behavior**. Concretely: memory unavailable → proceed without recall and tell the user; brain unavailable → fall back to the next provider in the configured chain; TTS unavailable → surface text; audio device lost → re-enumerate and resume. The system must **always produce a response**, even if the response is an honest statement that a subsystem is down.

## M6 — Phase 6 split into four gates (closes W10)
6a wake + VAD + audio I/O · 6b STT · 6c TTS bilingual · 6d full-duplex + barge-in. Four diagnosable gates instead of one ambiguous one.

## M7 — Capability surface versioning
Tool schemas will change. The MCP server declares a capability version at connect; the host negotiates and refuses incompatible majors with a clear error rather than failing at first call.

## M8 — Secret lifecycle (closes W14)
Rotation cadence per credential, a revocation runbook in `docs/RUNBOOK.md`, separate dev and runtime credentials, and a pre-commit secret scanner — added in Phase 0, not Phase 3, because the first leaked secret usually predates the scanner.

---

# 6. Optional Improvements

Genuinely optional. Recommended, but the plan is sound without them.

| # | Improvement | Value |
|---|---|---|
| O1 | **Robotics readiness** (ADR-0024, Phase 10) | The capability model already maps to actuators — `arm.move_to(pose)` is a typed tool with a policy. Concrete preparation: multi-arch (ARM64/Jetson) images, resource limits, a reserved seam for ROS 2 / DDS interop on the data plane, and **safety interlocks in the Policy Engine rather than in the prompt**. A model must never be the last line of defence before a motor |
| O2 | **Local eval leaderboard** | Extends Phase 8: a persistent scoreboard of provider × model × prompt-version across the golden set. Makes "is the local model good enough yet?" a query instead of an argument |
| O3 | **Memory consolidation as a background job** | Nightly episodic → durable summarization. Improves recall quality at scale; not needed at low volume |
| O4 | **Speaker verification** | Wake word confirms *what* was said; speaker ID confirms *who*. Gates `destructive` capabilities on voice identity |
| O5 | **Multi-session / multi-device** | The stateless-service design in H3 already permits it. Explicitly out of scope for v2.0 |
| O6 | **Streaming partial transcripts to the brain** | Start reasoning before the user finishes speaking. Meaningful latency win, significant complexity |
| O7 | **Emotion / prosody control in TTS** | Kokoro and Piper both expose limited control. Presentation polish |
| O8 | **Cost-aware provider routing** | Route cheap turns to the local model, hard turns to the API, using a difficulty classifier. Depends on H6's cost accounting |
| O9 | **GitOps deployment** | ArgoCD/Flux against the manifests from Phase 7. Justified only if L2 becomes the primary tier |

---

# 7. Updated Architecture Diagram

## 7.1 Runtimes and planes

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  HOST RUNTIME — Windows box.  Present at every tier L0–L3.                    ║
║  Owns: physical devices, session state, interrupts, local filesystem.         ║
║                                                                              ║
║   ┌────────────┐   ┌──────────────────────────────────────────────────────┐  ║
║   │ Audio I/O  │   │              ORCHESTRATION CORE                      │  ║
║   │ 16kHz mono │   │                                                      │  ║
║   │ ring buffer│──►│  SessionCoordinator ◄──── InterruptController        │  ║
║   └─────┬──────┘   │         │                        ▲                   │  ║
║         │          │         ▼                        │ cancel token      │  ║
║   ┌─────▼──────┐   │   TurnExecutor ──► ContextAssembler                  │  ║
║   │ WakeWord   │──►│         │                                            │  ║
║   │ + VAD      │   │         ▼                                            │  ║
║   │ (never     │   │    ToolRouter ──► [ Policy Engine: default-deny ]    │  ║
║   │  leaves    │   └─────────┬────────────────────────────┬───────────────┘  ║
║   │  host)     │             │ CONTROL PLANE              │ DATA PLANE       ║
║   └────────────┘             │ MCP / JSON-RPC             │ gRPC bidi stream ║
║                              │ stdio (L0) → HTTP (L1+)    │ HTTP/2           ║
║   ┌────────────────────┐     │                            │                  ║
║   │ Local capabilities │◄────┤                            │                  ║
║   │ fs · system · media│     │                            │                  ║
║   └────────────────────┘     │                            │                  ║
╚══════════════════════════════╪════════════════════════════╪══════════════════╝
                               │      mTLS at L2+           │
╔══════════════════════════════╪════════════════════════════╪══════════════════╗
║  CLUSTER RUNTIME — in-proc (L0) │ Minikube (L1) │ remote k8s (L2+)           ║
║                               ▼                            ▼                 ║
║  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  ║
║  │ MEMORY SVC   │  │ BRAIN GATEWAY  │  │ CAPABILITY   │  │ STT SERVICE    │  ║
║  │              │  │                │  │ SERVICES     │  │ whisper.cpp    │  ║
║  │ ingest·dedup │  │ BrainProvider  │  │              │  │ large-v3-turbo │  ║
║  │ decay·rank   │  │ ┌────────────┐ │  │ typed tools  │  │ multilingual   │  ║
║  │ provenance   │  │ │ anthropic  │ │  │ NO SHELL     │  └────────┬───────┘  ║
║  │ forget       │  │ │ ollama     │ │  │              │           │          ║
║  │              │  │ │ llamacpp   │ │  │ github · web │  ┌────────▼───────┐  ║
║  │ ┌──────────┐ │  │ └────────────┘ │  │ · future     │  │ TTS SERVICE    │  ║
║  │ │VectorPort│ │  │  ToolSpec IR   │  │   robotics   │  │ ┌────────────┐ │  ║
║  │ │  Qdrant  │ │  │  StreamEvent   │  │              │  │ │Kokoro  EN  │ │  ║
║  │ │(pgvector)│ │  │  Capabilities  │  │              │  │ │Piper   TR  │ │  ║
║  │ └──────────┘ │  │  Cost/quota    │  │              │  │ └────────────┘ │  ║
║  └──────┬───────┘  └───────┬────────┘  └──────┬───────┘  └────────┬───────┘  ║
║         │                  │                  │                   │          ║
║         └──────────────────┴─────────┬────────┴───────────────────┘          ║
║                                      ▼                                       ║
║                    ┌─────────────────────────────────┐                       ║
║                    │ OBSERVABILITY  (Phase 5)        │                       ║
║                    │ OTel Collector → Prom/Tempo/Loki│                       ║
║                    │ correlated by turn_id           │                       ║
║                    └─────────────────────────────────┘                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

LEGEND   ═══ runtime boundary    ─── control plane (MCP)    ▶▶▶ data plane (gRPC)
TIERS    L0 cluster services run in-process on host, no network  ·  L1 Minikube
         L2 remote cluster over mTLS  ·  L3 = L2 + Claude API brain
```

## 7.2 Turn lifecycle across both planes

```
  t=0     WakeWord fires ──────────────────────────────► turn_id assigned
                                                          (= OTel trace id)
  t+0     InterruptController: cancel any in-flight turn
  t+0     VAD opens capture window
  t+~     ═══ DATA PLANE ═══  PCM frames ──stream──► STT Service
                                          ◄─partial── (discarded, kept for O6)
  t+n     VAD closes (400ms trailing silence) ──► final transcript
  t+n     ─── CONTROL PLANE ───  ContextAssembler ──► Memory Service: recall
  t+n     ─── CONTROL PLANE ───  TurnExecutor ──► Brain Gateway (streaming)
            │  ToolCallDelta ──► ToolRouter ──► Policy Engine ──► Capability Svc
            │                                        └─ deny ──► audit + refuse
            └─ TextDelta, sentence-chunked ─┐
  t+m     ═══ DATA PLANE ═══                └──► TTS Service ──► PCM ──► speaker
  any t   barge-in ──► InterruptController ──► cancel fan-out:
                       playback → synthesis → brain stream → tool calls
  t+end   ─── CONTROL PLANE ───  Memory Service: ingest (salience-gated)
```

The `turn_id` threading both planes is what makes a single Grafana trace show the whole story. It is also why H7 precedes Phase 7: at L2 these boxes sit on different machines, and without the shared trace ID the system becomes undebuggable the day it is distributed.

---

# 8. Updated Repository Layout

Changes from v1.0 are marked. Unmarked paths are carried forward unchanged.

```
C:\Users\deniz\Desktop\L.I.O.N.E.L\
├── MASTER_PLAN_v1.md                   ← preserved verbatim, historical
├── MASTER_PLAN_v2.md                   ← NEW, authoritative
├── README.md  .gitattributes  .gitignore  .python-version
├── pyproject.toml  uv.lock
├── artifacts.lock.toml                 ← NEW  H8: model URLs + SHA-256 + license
│
├── contracts/                          ← NEW  Phase 0. Interfaces before implementations
│   ├── mcp/                            #  capability schemas + version manifest
│   ├── grpc/                           #  data-plane service definitions
│   └── events/                         #  StreamEvent, TurnEvent, telemetry schemas
│
├── config/
│   ├── lionel.toml                     #  non-secret config; secret:// URIs only
│   ├── tiers/                          ← NEW  H1: l0.toml · l1.toml · l2.toml · l3.toml
│   ├── policy/                         ← NEW  H4: declarative tool authorization rules
│   ├── capabilities.registry.json      ← RENAMED from mcp.servers.json
│   └── logging.yaml
│
├── docs/
│   ├── ARCHITECTURE.md   RUNBOOK.md
│   ├── THREAT_MODEL.md                 ← NEW  Phase 9
│   ├── LATENCY_BUDGET.md               ← NEW  H7: targets, wired to Prometheus alerts
│   └── decisions/                      ← EXPANDED  ADR-0001 … ADR-0028
│
├── src/lionel/
│   ├── core/                           ← REPLACES host/loop.py  (H3)
│   │   ├── session_coordinator/  turn_executor/  context_assembler/
│   │   ├── tool_router/                #  includes policy engine
│   │   └── interrupt_controller/       ← NEW  H10: cancellation fan-out
│   │
│   ├── brain/                          #  ADR-0001 preserved, interface widened (H6)
│   │   ├── contract/                   ← NEW  ProviderCapabilities · StreamEvent
│   │   ├── toolspec/                   ← NEW  provider-neutral tool schema IR
│   │   ├── providers/                  #  anthropic · ollama · llamacpp
│   │   └── accounting/                 ← NEW  cost & quota
│   │
│   ├── memory/                         ← ELEVATED to a service  (H5)
│   │   ├── service/                    #  ingest · dedup · consolidate · decay · rank
│   │   ├── ports/                      #  VectorBackend · (reserved) EntityBackend
│   │   └── backends/qdrant/            #  Qdrant is now one adapter
│   │
│   ├── capabilities/                   ← RENAMED from skills/  (H4)
│   │   ├── filesystem/  system/  media/  github/
│   │   └── ⚠ shell/  — DELETED. Not constrained. Removed
│   │
│   ├── sensory/
│   │   ├── audio_io/  wake/  vad/      #  host-resident, never relocatable
│   │   ├── stt/                        #  client → STT service; multilingual (M2)
│   │   ├── tts/
│   │   │   ├── port.py                 ← NEW  TTSProvider abstraction
│   │   │   └── providers/              ← NEW  kokoro (EN) · piper (TR)
│   │   └── locale/                     ← NEW  ADR-0023: TR normalization, İ/ı casing
│   │
│   ├── transport/                      ← NEW  H2: plane separation made explicit
│   │   ├── control/                    #  MCP client + server plumbing
│   │   └── data/                       #  gRPC streaming
│   │
│   ├── platform/                       ← NEW
│   │   ├── process_supervisor/         #  M1: Windows Job Objects
│   │   ├── secrets/                    #  H9: SecretResolver + SecretStr
│   │   ├── config/                     #  layered, typed
│   │   └── telemetry/                  #  H7: OTel init, redacting formatter
│   │
│   └── services/                       ← NEW  cluster-deployable entrypoints
│       ├── memory_service/  brain_gateway/  stt_service/  tts_service/
│
├── deploy/                             ← NEW  Phase 7 (cloud-portable per Efe)
│   ├── docker/                         #  per-service Dockerfiles, multi-arch
│   ├── compose/                        #  L0/L1 local
│   ├── helm/lionel/                    #  chart — the cloud-portability unit
│   ├── kustomize/overlays/             #  minikube · staging · cloud
│   └── observability/                  #  OTel Collector, Grafana dashboards
│
├── evals/                              ← NEW  golden/harness slice: Phase 3 (ADR-0041);
│   │                                       full suite: Phase 8 (ADR-0021)
│   ├── golden/                         #  utterance → expected tool-call set
│   ├── harness/                        #  replay runner (Phase 3: anthropic/ollama only)
│   ├── stt/                            #  WER fixtures, EN + TR
│   ├── tts/  wake/                     #  intelligibility · FAR/FRR corpus
│   └── harness/
│
├── tests/                              ← RESTRUCTURED  (M4)
│   ├── unit/  contract/  replay/  chaos/
│   └── fixtures/audio/                 #  pre-recorded WAV — CI without a microphone
│
├── scripts/                            #  Git Bash compatible, carried forward
├── vendor/whisper.cpp/                 #  pinned to tag + SHA (H8)
├── models/                             #  gitignored; verified against artifacts.lock
└── data/  logs/  backups/              #  gitignored
```

**Three structural notes.** `contracts/` exists so Phase 0 can define interfaces before any implementation — it is what makes the migration in Section 11 cost nothing. `services/` holds thin entrypoints wrapping the same libraries the host uses, which is what allows a component to run in-process at L0 and as a pod at L2 **without a code fork**. And `capabilities/shell/` is listed explicitly as deleted so its absence reads as a decision rather than an oversight.

---

# 9. Updated ADR List

`PRESERVED` = v1.0 decision unchanged · `AMENDED` = principle held, scope widened · `SUPERSEDED` = replaced

> **This table is the v1.0 → v2 migration record, not a live index.** It lists the ADRs
> that existed when this plan was written and what each did to a v1.0 decision. ADRs added
> since carry no migration status and are not listed here. The live index is
> [`docs/decisions/README.md`](docs/decisions/README.md), and `ARCH-016` enforces that it
> is complete.

| ADR | Title | Status | Phase |
|---|---|---|---|
| 0001 | Swappable `BrainProvider` | **PRESERVED**, amended by 0009 | 0 |
| 0002 | Project root is `C:\Users\deniz\Desktop\L.I.O.N.E.L` | **PRESERVED** | 0 |
| 0003 | MCP-first capability model | **PRESERVED**, amended by 0006 (MCP = control plane) | 0 |
| 0004 | Qdrant in Docker as memory | **SUPERSEDED by 0010** | — |
| 0005 | Dual-runtime: Host + Cluster | NEW | 0 |
| 0006 | Control plane / data plane separation | NEW | 0 |
| **0007** | **Degradation Ladder L0–L3; L0 is a blocking CI gate** | **NEW — keystone** | **0** |
| 0008 | Coordinator decomposition; no god loop | NEW | 0 |
| 0009 | Extended `BrainProvider` contract | NEW | 0 |
| 0010 | Memory Service with pluggable vector backend | NEW | 0 |
| 0011 | Capability tools; shell execution abolished | NEW | 0 |
| 0012 | Policy Engine, default-deny, for tool authorization | NEW | 0 |
| 0013 | Artifact pinning and supply-chain lockfile | NEW | 0 |
| 0014 | `ProcessSupervisor` on Windows Job Objects | NEW | 1 |
| 0015 | Layered config and `SecretResolver` URI scheme | NEW | 0 |
| 0016 | ADR-driven decision records replace `<thought>` | NEW | 0 |
| 0017 | Dual TTS — Kokoro EN + Piper TR behind `TTSProvider` | NEW | 6c |
| 0018 | Multilingual STT mandatory; `.en` models rejected | NEW, supersedes v1.0 model choice | 6b |
| 0019 | OpenTelemetry as the observability substrate | NEW | 5 |
| 0020 | Kubernetes-native, cloud-portable deployment | NEW | 7 |
| 0021 | Evaluation harness gates model and prompt changes | NEW | 8 |
| 0022 | Zero-trust between runtimes; mTLS at L2+ | NEW | 7 |
| 0023 | Turkish locale correctness — dotted/dotless `İ/ı` | NEW | 6c |
| 0024 | Robotics-compatible capability and safety model | NEW — **provisional** | 10 |
| 0025 | Cancellation and backpressure architecture | NEW | 0 |
| 0026 | Side-effect classification on every tool | NEW | 0 |
| 0027 | Five-layer testing strategy | NEW | 0 |
| 0028 | Data-plane transport selection (gRPC; WebRTC deferred) | NEW | 6 |

Seventeen of the twenty-eight land in **Phase 0**. That is deliberate: they are all interface-shaping, and an interface decision made after the implementation is a refactor, not a decision.

---

# 10. Updated Development Phases

v1.0's four phases become eleven. This is not scope inflation — Phases 5, 7, 8, 9 are new capability, while 0, 1–4 and 6 are v1.0's content redistributed along cleaner seams with diagnosable gates.

Every phase inherits v1.0's binary-DoD discipline (S3) and adds two universal exit criteria:

> **U1 — L0 conformance.** The L0 test suite passes. Non-negotiable, every phase, per ADR-0007.
> **U2 — Security gate.** Threat-model delta reviewed for the surface this phase added (ADR-0022 / Phase 9 is a deepening, not the first look).

---

## Phase 0 — Contracts & Foundations `NEW`
*Est. 1–2 sessions · Gate G0*

The phase that makes every later migration cheap. **No feature code.**

Deliverables: repository scaffold · all 28 ADRs drafted and accepted · `contracts/` interface definitions (MCP schemas, gRPC service definitions, `StreamEvent` / `ToolSpec` / `ProviderCapabilities` shapes) · `artifacts.lock.toml` · secret resolution and layered config design · CI skeleton with the L0 gate wired (failing is fine; **present is mandatory**) · pre-commit secret scanner · tier configs `l0`–`l3`.

**DoD:** every ADR has a decision and a consequences section · contract schemas validate against their own linters · CI runs and reports · secret scanner blocks a deliberately planted test credential · **`artifacts.lock.toml` fails closed on a corrupted checksum**.

---

### Phase 1 — Host Runtime Skeleton & Control Plane
*Est. 1–2 sessions · Gate G1 · was v1.0 Phase 1*

Carries forward v1.0's environment work — the tooling preflight table, the Git Bash hazard rules, filesystem and GitHub MCP — onto the new spine.

Adds: the five coordinators as **empty, contract-conforming shells** · `ProcessSupervisor` (ADR-0014) · `SecretResolver` (ADR-0015) · capability registry replacing `mcp.servers.json` · Policy Engine skeleton in default-deny.

**DoD:** v1.0's Phase 1 DoD in full, plus — coordinators satisfy contract tests with stub implementations · Job Object kill-tree verified by terminating a parent and confirming **zero orphaned children** · a `secret://` URI resolves and its value redacts in log output · Policy Engine denies an unregistered tool by default · pinned GitHub MCP image digest verified.

---

### Phase 2 — Memory Service
*Est. 2 sessions · Gate G2 · was v1.0 Phase 2, elevated per H5*

Qdrant pinned by digest behind a `VectorBackend` port; the Memory Service owns ingestion, dedup, decay, ranking, provenance, and forget.

**DoD:** v1.0's persistence proof retained (`compose down && up` → memory survives) · v1.0's semantic-recall test retained (dissimilar query retrieves the stored fact — keyword matching must fail it) · plus: **`forget(id)` provably removes a memory from retrieval** · near-duplicate ingestion is deduplicated · episodic decay observed under an accelerated clock · re-index against a second embedding model completes without data loss · **direct `qdrant-store` is absent from the exposed capability surface**.

---

### Phase 3 — Brain Gateway & Provider Abstraction
*Est. 2–3 sessions · Gate G3 · split from v1.0 Phase 3*

ADR-0001 realized against the widened ADR-0009 contract. `ToolSpec` IR, `StreamEvent`, capabilities, health, cancellation, cost accounting.

**DoD:** identical `ToolSpec` produces a valid native tool schema for all three providers · the same golden transcript replays correctly on `anthropic` and `ollama`, results recorded in ADR-0001 (v1.0's G3 requirement, now automated as a **regression gate** rather than a one-time measurement) · `health()` correctly reports *not ready* while Ollama loads a model · **a cancellation token aborts a streaming generation within 200 ms** · cost ceiling enforced · **no caller branches on provider name anywhere in the codebase** — capability flags only.

---

### Phase 4 — Capability Services & Policy Engine
*Est. 2 sessions · Gate G4 · rest of v1.0 Phase 3, reshaped by H4*

Typed capability tools: filesystem, system telemetry, media, GitHub. Policy Engine enforcing `side_effect`, `trust_required`, rate limits, audit.

**DoD:** every tool declares complete metadata; **the registry rejects any tool that does not** · contract tests pass for all servers · a `destructive` tool requires explicit confirmation · **a simulated prompt-injection payload embedded in a file read fails to reach any `write` tool** (closes W2 / v1.0's R6) · rate limiting contains a deliberate runaway loop · every allow *and* deny is audit-logged · **no shell execution path exists anywhere in the capability surface**.

---

### Phase 5 — Observability `NEW`
*Est. 1–2 sessions · Gate G5 · resequenced per H7 — before distribution*

OTel traces, metrics, structured logs; Collector, Prometheus, Tempo, Loki, Grafana; latency budget wired to alerts.

**DoD:** a single trace spans an entire turn end-to-end, correlated by `turn_id` · every v1.0 latency-budget stage emits a histogram · **a deliberate budget violation fires an alert** — this is the moment the budget stops being aspirational · secrets are absent from all log output under a fuzzing pass · **the host buffers telemetry to disk when the collector is unreachable and flushes on reconnect** (L0 must still produce telemetry) · Grafana dashboard for the full pipeline.

---

### Phase 6 — Sensory Data Plane
*v1.0 Phase 4, split into four gates per M6 · Est. 4–6 sessions total*

**6a — Audio I/O, wake word, VAD** *(Gate G6a, ~1–2 sessions)*
Ring buffer, openWakeWord (ONNX — the Windows tflite constraint from v1.0 is preserved), silero-VAD, device-change resilience.
**DoD:** 10-minute capture soak with zero dropouts · **zero false activations across 30 minutes of podcast audio** (v1.0's criterion, retained) · wake fires reliably at 3 m · **unplugging and replugging the audio device mid-session recovers without restart** (closes W8 at the device layer) · FAR/FRR recorded as a Phase 5 metric.

**6b — STT service** *(Gate G6b, ~1–2 sessions)*
whisper.cpp pinned to tag + SHA, **multilingual `large-v3-turbo`** per ADR-0018, gRPC streaming, CPU build before CUDA (v1.0's sequencing, retained).
**DoD:** WER measured on both an English and a **Turkish** fixture set · streaming partials emitted · **re-measured STT latency recorded against the budget** — if `large-v3-turbo` breaks 800 ms on CPU, the ADR-0007 tier decision to move inference to the cluster is triggered here, not discovered later.

**6c — TTS service, bilingual** *(Gate G6c, ~1 session)*
`TTSProvider` port; Kokoro EN + Piper TR; language routing; locale text normalization.
**DoD:** both engines synthesize through the port with no caller-visible difference · language routing selects correctly from detected input language · **Turkish output is intelligible to a native speaker** (Efe) · **the `İ/ı` casing test suite passes** (ADR-0023) · sentence-chunked streaming — first audio within 300 ms.

**6d — Full duplex & barge-in** *(Gate G6d, ~1–2 sessions)*
Pipeline orchestration, InterruptController fan-out, backpressure.
**DoD:** v1.0's headline test, retained verbatim — *"Hey Lionel, how much disk space do I have left?"* spoken, answered aloud with the real number, **no keyboard** · the Turkish equivalent also passes · barge-in aborts playback within 300 ms · **cancellation leaves zero orphaned work** — no running synthesis, no in-flight tool call · wake-to-speech latency under 2.5 s, now **measured by Phase 5 rather than by stopwatch** · **airplane-mode test at L0 with the Ollama provider** — v1.0's best idea, now backed by the standing CI gate.

---

### Phase 7 — Containerization & Kubernetes `NEW`
*Est. 3–4 sessions · Gate G7 · cloud-portable per Efe's scoping*

Multi-arch images (amd64 + arm64, the latter seeding O1) · Helm chart as the portability unit · Kustomize overlays for minikube / staging / cloud · Qdrant StatefulSet with PVC · External Secrets Operator · NetworkPolicy · mTLS host↔cluster (ADR-0022) · HPA on inference services · GHCR registry.

**DoD:** L1 runs end-to-end on Minikube · **L2 runs with host on Windows and cluster remote, over mTLS, with the latency budget re-measured and recorded** · the same chart deploys to a cloud cluster with **overlay-only changes — no chart edits** (this is the operative test of "cloud-portable") · Qdrant data survives pod deletion · NetworkPolicy blocks a deliberately unauthorized pod-to-pod call · **rollback to the previous release verified** · and, decisively: **L0 still passes** with the cluster entirely absent.

---

### Phase 8 — MLOps & Evaluation `NEW`
*Est. 2–3 sessions · Gate G8 · resequenced per proposal 13*

Golden-set eval harness (utterance → expected tool calls) · STT WER tracking EN + TR · wake FAR/FRR corpus · provider × model × prompt-version leaderboard · CI regression gates · model registry keyed to `artifacts.lock.toml` · drift monitoring.

**DoD:** the full eval suite runs in CI on every PR touching a model, prompt, or provider · **a deliberate prompt regression is caught by the gate and blocks merge** · provider comparison is reproducible from a command · WER and FAR/FRR trend over time in Grafana · **swapping the STT model is a lockfile change plus an eval run, not a code change**.

---

### Phase 9 — Security Hardening & Review `NEW`
*Est. 2 sessions · Gate G9 · amended per H4/M8 — a deepening of a continuous gate, not the first look*

STRIDE threat model in `docs/THREAT_MODEL.md` · prompt-injection red-team against the full capability surface · container hardening (non-root, read-only rootfs, dropped capabilities) · SBOM generation · dependency and image scanning in CI · secret rotation runbook · audit log review · Policy Engine rule audit.

**DoD:** threat model covers every trust boundary in §7.1 · **red-team campaign produces zero successful escalations from untrusted content to a `write` or `destructive` tool** · all images pass a hardening scan · SBOM generated per release · no critical CVEs unremediated or unaccepted-with-rationale · a rotation drill completes against the runbook · **a security review is recorded as a merge gate for every subsequent phase**.

---

### Phase 10 — Robotics Readiness `HORIZON — not committed`
*Gate G10 · O1 · scope defined at G9, not before*

Multi-arch validated on Jetson/ARM · ROS 2 / DDS interop seam on the data plane · actuator capabilities under the existing Policy Engine · **hardware safety interlocks in the Policy Engine, never in the prompt** · real-time constraints on the data plane.

Listed to ensure v2.0's decisions do not preclude it. **Explicitly not scheduled.**

---

## 10.1 Gate summary

| Gate | Unlocks | The one thing that must be true |
|---|---|---|
| G0 | All work | Contracts exist; L0 CI gate is wired |
| G1 | Memory | Host spine stands; no orphaned processes; secrets redact |
| G2 | Brain | Memory survives restart **and** can forget |
| G3 | Capabilities | Same transcript, both providers; cancellation works |
| G4 | Observability | Injected content cannot reach a write tool |
| G5 | Sensory | One trace spans a whole turn; budget violation alerts |
| G6a–d | Deployment | Full voice loop, EN **and** TR, offline, no keyboard |
| G7 | MLOps | Overlay-only cloud portability; **L0 still passes** |
| G8 | Hardening | A regression is caught before merge |
| G9 | Robotics | Zero injection escalations |
| G10 | — | Not committed |

## 10.2 Where v1.0's content went

| v1.0 | v2.0 |
|---|---|
| Phase 1 — Environment & core MCP | Phase 0 (contracts) + Phase 1 (host spine) |
| Phase 2 — Qdrant memory | Phase 2, elevated to a service |
| Phase 3 — venv + FastMCP skills | Phase 3 (brain) + Phase 4 (capabilities) |
| Phase 4 — Sensory | Phase 6a–6d |
| *(none)* | Phases 5, 7, 8, 9, 10 |

---

# 11. Migration Plan — v1.0 → v2.0

## 11.1 The governing fact

**No implementation exists.** The repository contains `MASTER_PLAN_v1.md` and now `MASTER_PLAN_v2.md`. There is no `src/`, no `config/`, no `docker-compose.yml`.

**Consequently: zero lines of code require rewriting, and no data requires migrating.** The migration is a *decision* migration — replacing a set of intended designs with a better set before either is built. Section 1.3's timing observation is the whole story: this is the cheapest possible moment for this review, and the cost curve from here is steep. The same review after Phase 3 would have required extracting a memory service from its callers, decomposing a god loop that already held state, and retrofitting cancellation through synchronous call paths — several sessions of pure rework, and the kind that tends to be deferred indefinitely.

## 11.2 Artifact disposition

| v1.0 artifact | v2.0 disposition | Action | Cost |
|---|---|---|---|
| `MASTER_PLAN.md` | Renamed `MASTER_PLAN_v1.md`, verbatim | **Done** | — |
| ADR-0001 brain adapter | **Preserved**, amended by ADR-0009 | Widen interface at authoring time | 0 |
| ADR-0002 project root | **Preserved verbatim** | None | 0 |
| ADR-0003 MCP-first | **Preserved**, clarified as control-plane by ADR-0006 | Add one paragraph | 0 |
| ADR-0004 Qdrant-in-Docker | **Superseded** by ADR-0010 | Mark superseded; Docker/volume/pinning reasoning carries into the backend adapter | 0 |
| Phase 1 environment work | **Absorbed** into Phases 0 + 1 | Preflight table, hazard rules, MCP setup all reused | 0 |
| Windows/Git Bash hazard table §2 | **Preserved and extended** | Add M1's Job Object rules | 0 |
| `docker-compose.yml` sketch | **Retained**, digest-pinned | Add digest; becomes the L1 compose file | 0 |
| Two-collection memory split | **Preserved** as Memory Service internal schema | None | 0 |
| `config/mcp.servers.json` | Renamed `capabilities.registry.json`; `${…}` replaced by `secret://` | Rewrite the token line | 0 |
| `shell_server.py` | **Deleted from the plan** | Remove; never write it | 0 (**avoided** ~1 session + a permanent liability) |
| `ggml-base.en.bin` | **Superseded** by `large-v3-turbo` (ADR-0018) | Change model in `artifacts.lock.toml` | 0 (**avoided** a Phase 6 rebuild) |
| Latency budget §4.4 | **Preserved**, promoted to `LATENCY_BUDGET.md` + alerts | Wire to Prometheus in Phase 5 | 0 |
| Risk register §6 | **Preserved**, R6 upgraded to Policy Engine | Update mitigations | 0 |
| §7.1 `<thought>` method | **Superseded** by ADR-0016 | Change working method | 0 |
| §7.3 GitHub golden rule | **Preserved verbatim — non-negotiable** | None | 0 |
| Airplane-mode DoD | **Promoted** to standing CI gate (ADR-0007) | Wire in Phase 0 | 0 |
| `test_phaseN_*.py` | **Superseded** by the five-layer strategy | Restructure `tests/` before writing tests | 0 |

**Net rework: zero.** Net *avoided* rework, conservatively: the shell server, the god-loop decomposition, the memory-service extraction, the STT model rebuild, and retrofitting cancellation — call it five to eight sessions, plus one security liability that would have shipped.

## 11.3 Migration sequence

Six steps. Only M0 is blocking.

| Step | Action | Blocking? |
|---|---|---|
| **M0** | Approve v2.0. `MASTER_PLAN_v2.md` becomes authoritative; v1.0 becomes historical | **Yes** |
| **M1** | Author all 28 ADRs. Carry 0001–0003 forward; mark 0004 superseded; draft the 24 new ones | Yes — for Phase 0 |
| **M2** | Define `contracts/` before any implementation. **This is the step that keeps future migrations cheap** | Yes — for Phase 1 |
| **M3** | Wire CI with the L0 gate, secret scanner, and `artifacts.lock.toml` verification. Red is acceptable; absent is not | Yes — for Phase 1 |
| **M4** | Build Phases 1–6 against contracts. Each phase gate re-verifies U1 (L0) and U2 (security) | No |
| **M5** | Phases 7–9 layer distribution, evaluation, and hardening onto a system that is already observable and contract-tested | No |

## 11.4 If implementation had already started

Recorded for the future, since some of these apply to any later mid-flight change:

1. **Contracts first, always.** Define the target interface, adapt existing code to it, *then* refactor behind it. Never refactor and re-interface simultaneously.
2. **Strangler pattern for the loop.** Extract coordinators one at a time — ToolRouter first (cleanest seam), InterruptController last (most entangled).
3. **Memory service as a facade first.** Put the interface in front of direct Qdrant calls, migrate callers, then move logic behind it. Data never moves.
4. **Shell removal is immediate, not phased.** A security boundary is not deprecated on a schedule. Enumerate real usages, build typed replacements for each, delete.
5. **Observability is retrofittable but painful.** Instrument at boundaries first; internals later.

## 11.5 Backward compatibility

None required. There are no users, no deployed instances, no persisted data, and no external consumers of any interface. **v2.0 is free to be correct rather than compatible** — a freedom that expires at the first deployment, which is precisely why the review happens now.

---

# 12. Working Method (v2.0)

## 12.1 ADRs replace `<thought>` — ADR-0016

Exploratory reasoning stays internal. The durable artifact changes: every decision that constrains future work produces a **lightweight ADR** (Context / Decision / Consequences / Alternatives Rejected). Smaller calls produce a short **Decision Summary** in-line. ADRs are diffable, greppable, citable in review, and **indexed into the Memory Service on merge** so `memory.recall` surfaces them months later. Before proposing a change to any module, I query memory for its prior ADRs — settled decisions are not relitigated silently.

## 12.2 GitHub — the golden rule, unchanged

> **I will never `commit` or `push` autonomously.**

Write and stage → present the diff and proposed message → **Efe explicitly approves** → only then commit, with the `[LIONEL-CORE]` prefix. No exceptions, no bundling an unapproved change into an approved commit. If a commit ever appears without approval, treat it as a bug and revert it.

## 12.3 Universal phase discipline

Every gate re-verifies **U1** (L0 conformance) and **U2** (security delta review). A phase is not done when the feature works. It is done when the feature works, the system still runs fully offline, and the new attack surface has been reviewed.

---

# 13. Immediate Next Action

**Phase 0, Step 1 (M1):** author the 28 ADRs in `docs/decisions/` — carrying ADR-0001 through 0003 forward from v1.0, marking 0004 superseded, and drafting the 24 new ones — beginning with **ADR-0007 (Degradation Ladder)**, since every other decision in this plan is downstream of it.

No implementation code until G0 is signed off.

**Awaiting Efe's approval of MASTER_PLAN v2.0.**
