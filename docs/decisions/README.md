# Architecture Decision Records

Per **ADR-0016**, these files replace ephemeral `<thought>` reasoning as the project's
durable decision artifact. They are diffable, greppable, citable in review, and indexed
into the Memory Service on merge so `memory.recall` surfaces them months later.

## Rules

1. **Any decision that constrains future work gets an ADR.** Smaller calls get a Decision
   Summary in the response instead.
2. **Query before you decide.** Before proposing a change to a module, search existing ADRs
   (and, once Phase 2 lands, the Memory Service). Settled decisions are not relitigated silently.
3. **ADRs are immutable once Accepted.** The *Decision* never changes and the body is never
   edited in place. [ADR-0029](ADR-0029-adr-errata-provision.md) defines the three
   append-only operations — **Supersede**, **Amend**, **Erratum** — and `ADR-009` checks
   their shape. An Erratum quotes verbatim what it corrects; that quote is what separates a
   correction from a rewrite.
4. **Every ADR names its verification.** A decision with no way to check it is a preference.

## Statuses

| Status | Meaning |
|---|---|
| `Accepted` | In force |
| `Provisional` | Direction agreed, details deferred to a named gate |
| `Superseded by ADR-NNNN` | Replaced. Kept for the historical record |
| `Proposed` | Drafted, not yet approved by Efe |

## Index

| ADR | Title | Status | Phase |
|---|---|---|---|
| [0001](ADR-0001-swappable-brain-provider.md) | Swappable BrainProvider | Accepted | 0 |
| [0002](ADR-0002-project-root-path.md) | Project root path | Accepted | 0 |
| [0003](ADR-0003-mcp-first-capability-model.md) | MCP-first capability model | Accepted | 0 |
| [0004](ADR-0004-qdrant-in-docker.md) | Qdrant in Docker as the memory system | Superseded by 0010 | — |
| [0005](ADR-0005-dual-runtime.md) | Dual runtime: Host + Cluster | Accepted | 0 |
| [0006](ADR-0006-control-data-plane-separation.md) | Control plane / data plane separation | Accepted | 0 |
| [0007](ADR-0007-degradation-ladder.md) | **Degradation Ladder L0–L3** | Accepted | 0 |
| [0008](ADR-0008-coordinator-decomposition.md) | Coordinator decomposition; no god loop | Accepted | 0 |
| [0009](ADR-0009-extended-brain-provider-contract.md) | Extended BrainProvider contract | Accepted | 0 |
| [0010](ADR-0010-memory-service.md) | Memory Service with pluggable vector backend | Accepted | 0 |
| [0011](ADR-0011-capability-tools-no-shell.md) | Capability tools; shell execution abolished | Accepted | 0 |
| [0012](ADR-0012-policy-engine.md) | Policy Engine, default-deny | Accepted | 0 |
| [0013](ADR-0013-artifact-pinning.md) | Artifact pinning and supply chain | Accepted | 0 |
| [0014](ADR-0014-process-supervisor.md) | ProcessSupervisor on Windows Job Objects | Accepted | 1 |
| [0015](ADR-0015-secret-resolver.md) | Layered config and SecretResolver URIs | Accepted | 0 |
| [0016](ADR-0016-adr-driven-decisions.md) | ADRs replace `<thought>` | Accepted | 0 |
| [0017](ADR-0017-dual-tts.md) | Dual TTS: Kokoro EN + Piper TR | Accepted | 6c |
| [0018](ADR-0018-multilingual-stt.md) | Multilingual STT mandatory | Accepted | 6b |
| [0019](ADR-0019-opentelemetry.md) | OpenTelemetry as observability substrate | Accepted | 5 |
| [0020](ADR-0020-kubernetes-cloud-portable.md) | Kubernetes-native, cloud-portable | Accepted | 7 |
| [0021](ADR-0021-eval-harness-gates.md) | Eval harness gates model/prompt changes | Accepted | 8 |
| [0022](ADR-0022-zero-trust-runtimes.md) | Zero-trust between runtimes; mTLS at L2+ | Accepted | 7 |
| [0023](ADR-0023-turkish-locale-correctness.md) | Turkish locale correctness (İ/ı) | Accepted | 6c |
| [0024](ADR-0024-robotics-capability-safety.md) | Robotics capability and safety model | Provisional | 10 |
| [0025](ADR-0025-cancellation-backpressure.md) | Cancellation and backpressure | Accepted | 0 |
| [0026](ADR-0026-side-effect-classification.md) | Side-effect classification on tools | Accepted | 0 |
| [0027](ADR-0027-testing-strategy.md) | Five-layer testing strategy | Accepted | 0 |
| [0028](ADR-0028-data-plane-transport.md) | Data-plane transport selection | Accepted | 6 |
| [0029](ADR-0029-adr-errata-provision.md) | Errata, Amendments and Corrections to Accepted ADRs | Accepted | 0 |
| [0030](ADR-0030-self-enforcing-ci.md) | The pipeline enforces its own invariants | Accepted | 0 |
| [0031](ADR-0031-reviewed-licence-register.md) | A licence that needs review must have somewhere to be reviewed | Accepted | 0 |
| [0032](ADR-0032-dev-tooling-mcp-servers.md) | Developer-tooling MCP servers are declared, pinned, and disclosed | Accepted | 1 |
| [0033](ADR-0033-hand-written-claim-checking.md) | Count-shaped claims in hand-written documents are measured, not remembered | Accepted | 0 |
| [0034](ADR-0034-constraint-only-policy-rules.md) | A policy rule may constrain without deciding | Accepted | 0 |
| [0035](ADR-0035-verified-file-quotes.md) | A document that quotes a file is checked against that file | Accepted | 0 |
| [0036](ADR-0036-memory-client-and-embedding-runtime.md) | The Memory Service's vector client and embedding runtime | Accepted | 0 |
| [0037](ADR-0037-tombstone-record-shape.md) | A tombstone is a MemoryRecord, and the contract has no shape for one | Accepted | 0 |
| [0038](ADR-0038-memory-backup-and-restore.md) | Memory has a second copy, and the restore is exercised rather than assumed | Accepted | 2 |
| [0039](ADR-0039-brain-contract-coherence.md) | Four brain contracts describe one thing twice, and Phase 3 is the first consumer | Accepted | 3 |
| [0040](ADR-0040-brain-provider-clients.md) | The three BrainProvider clients | Accepted | 3 |
| [0041](ADR-0041-transcript-replay-gate.md) | The golden-transcript replay gate, and the phase plan's contradiction about where it lives | Accepted | 3 |

**0 ADRs pending.** ADR-0040 and ADR-0041 were accepted 2026-09-10, the day they were
drafted, and implemented in the same version (architecture 1.23.0). ADR-0040 chose the
three `BrainProvider` clients — `anthropic>=1.4` and `llama-cpp-python>=0.3.35` as new
dependencies, `ollama` called over the already-declared `httpx` rather than a second
HTTP client — and closed the L0-credential question by declining to add a mechanism:
`l0-conformance` already forbids `provider = "anthropic"` at L0, which is sufficient.
Its Erratum records what `uv lock` pulled in that the proposal did not predict:
`httpx2`, `anthropic`'s own transport dependency and a genuinely second HTTP client
under a different name, now named in `dependencies.forbid_packages` with a
`transitive_exemptions` entry — the `requests`-via-`fastembed` finding, one dependency
later. ADR-0041 resolved a contradiction inside `MASTER_PLAN_v2.md` itself: §10 Phase 3's
DoD requires the golden-transcript replay gate at G3, while the directory sketch four
hundred lines later had labelled `evals/` `NEW Phase 8`; the sketch now names both dates
and both ADRs. **Both Erratums are honest about what remains**: the three provider
adapters and the golden-transcript harness itself are real engineering, not yet built,
and `Phase3_Entry_Checklist.md` items 2 and 3 track them as continuing.

ADR-0039 was accepted 2026-09-02 and implemented in the same version
(architecture 1.21.0): all five brain contracts move to 1.1.0, `HealthStatus` is one
definition rather than two, a cancellation token and a reported tool name are each
constrained by `$ref` to the one schema that defines them, and the two `StopReason` copies
became one. `test_brain_contract.py`'s four defect-pinning tests inverted into four
coherence-pinning test classes, and the file gained the offline `$ref` registry
`test_memory_contract.py` had already solved. Its Erratum records that the cross-file refs
needed that registry the first time the tests were re-run.

ADR-0038 was accepted 2026-09-01 and implemented in the same version
(architecture 1.18.0): `scripts/memory_backup.sh` and `scripts/_memory_snapshot.py` exist,
a snapshot restores to the same point ids rather than merely the same count, and the
disaster drill — delete the durable collection outright, restore it — was witnessed on the
host. It reinstates the one MASTER_PLAN_v1 Phase 2 item that MASTER_PLAN_v2 dropped without
a migration row, which `Phase2_Final_Signoff.md` §6 carries as a Major with no mitigation.

ADR-0037 was accepted 2026-08-28 and implemented in the same version
(architecture 1.17.0): `memory-record.schema.json` is 1.1.0, a tombstone is a record the
architecture can describe, and a live record with empty text is still a schema error. Its
Erratum records the trap in the first attempt — a conditional that could not relax a base
constraint, and read as a correct fix while doing nothing.

ADR-0036 was accepted 2026-08-28 and implemented in the same version
(architecture 1.15.0): `qdrant-client` and `fastembed` are declared, `src/lionel/memory/`
holds the `VectorBackend` port and its Qdrant adapter, and the embedding pin is an assertion
rather than a sentence. Its Erratum records what the resolver did that the proposal did not
predict — `fastembed` pulls `requests`, which `forbid_packages` names, and `DEP-002` could
not see it.

ADR-0035 was accepted 2026-08-28 and implemented in the same version
(architecture 1.12.0): `gate_doc_quotes` is the 23rd gate, `QUOTE-001`–`QUOTE-003`, and
ADR-0033 carries an Amendment recording that half of its Costs gap is now closed — the half
that can be closed mechanically. Prose claims remain uncaught, and both ADRs say so.

ADR-0034 was accepted 2026-08-27 and implemented in the same version
(architecture 1.10.0): `policy-ruleset.schema.json` is 1.1.0, `$defs.Rule` requires a
decision or a constraint, and `PolicyEngine._validate()` refuses a rule carrying neither.
Its Erratum of that date discharges the paragraph saying the change would be withheld —
which it was, for two days, because §4 wants the approval before the change and not after.

ADR-0033 was accepted 2026-08-24 and implemented in the same version —
after the already-working gate was removed from the repository so the decision could be made
in writing rather than by having shipped. `Architecture_Freeze.md` §9.9 records it.

**ADR-0032 was accepted 2026-08-24 and implemented in the same version
(architecture 1.4.0): `.mcp.json` holds one pinned entry and `gate_mcp` enforces
`MCP-000`–`MCP-003`. Its Erratum of that date discharges the two paragraphs that described
it as pending — including the one saying `.mcp.json` would not be created until acceptance.

**0029–0031 accepted 2026-08-11.** All three carry a dated `## Erratum` recording the status
change, because each asserted its own `Proposed` status in its body and the body is
append-only — the first use of the mechanism ADR-0029 introduced, on ADR-0029 itself.
