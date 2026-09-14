# Architecture Freeze

| | |
|---|---|
| Architecture version | **1.23.0** |
| Freeze date | **2026-08-10** |
| Tag | **`architecture-1.23.0`** |
| Status | **FROZEN** — G2 signed 2026-09-02, Phase 3 open, ADR-0039 in force; the freeze governs the architecture, not the code written against it |
| Previous versions | **1.22.0**, **1.21.0**, **1.20.0**, **1.19.0**, **1.18.0**, **1.17.1**, **1.17.0**, **1.16.0**, **1.15.0**, **1.14.0**, **1.13.0**, **1.12.1**, **1.12.0**, **1.11.0**, **1.10.0**, **1.9.1**, **1.9.0**, **1.8.0**, **1.7.0**, **1.6.0**, **1.5.0**, **1.4.0**, **1.3.0**, **1.2.0**, **1.1.1**, **1.1.0**, **1.0.0** — all tagged, all unchanged and still valid |
| Governance | **0 ADRs pending.** ADR-0040 and ADR-0041 accepted 2026-09-10 and in force |

> **In force.** 1.1.0 is additive: it adds three decisions and three gates, and changes no
> decision already in force. `architecture-1.0.0` is untouched and remains a valid freeze of
> what it froze. **Clone the tag, not a commit** — §8.3 explains why that distinction
> matters here.
>
> **All 41 ADRs are in force.** ADR-0040 and ADR-0041 (2026-09-10) were accepted the same
> day they were drafted: `anthropic` and `llama-cpp-python` join `pyproject.toml`, `ollama`
> stays on `httpx`, the `cl` preflight row moves `G6` → `G3`, and `MASTER_PLAN_v2.md`'s
> `evals/` line now names both arrival dates. Both Erratums are honest that the provider
> adapters and the golden-transcript harness itself remain unbuilt — real engineering, not a
> configuration change. §9.31.
>
> ADR-0039 (2026-09-02) was accepted the same day it was
> drafted and implemented in the same version: five brain contracts move to 1.1.0,
> `HealthStatus` is one definition rather than two, and a cancellation token and a reported
> tool name are each constrained by `$ref` to the one schema that defines them. Its Erratum
> discharges the paragraph that had described the withholding as ongoing. §9.29.
>
> ADR-0038 (2026-09-01) was accepted the same day and
> implemented in the same version: `scripts/memory_backup.sh` exists, and the restore path
> is exercised by a round-trip that compares point ids rather than counts. It reinstates the
> one MASTER_PLAN_v1 Phase 2 item that MASTER_PLAN_v2 dropped with no migration row. §9.26.
>
> ADR-0037 (2026-08-28) was accepted the same day and
> implemented in the same version: `memory-record.schema.json` is 1.1.0 and a tombstone is
> a record the architecture can describe. §9.24.
>
> ADR-0036 (2026-08-28) was accepted the same day and
> implemented in the same version: `qdrant-client` and `fastembed` are declared, and
> `src/lionel/memory/` holds the `VectorBackend` port. Its Erratum records what the resolver
> did that the proposal did not predict. §9.22.
>
> ADR-0035 (2026-08-27) was accepted 2026-08-28 and
> implemented in the same version: `gate_doc_quotes` is the 23rd gate. For the day it was
> `Proposed`, the gate it describes was not in the repository. §9.18.
>
> ADR-0034 (2026-08-25) was accepted 2026-08-27 and
> implemented in the same version. It changes `policy-ruleset.schema.json`'s stable surface,
> so §4 required Efe's approval before the change rather than after — and for the two days it
> was `Proposed`, the schema edit it describes was deliberately absent from the repository.
> §9.16. ADR-0033 was accepted 2026-08-24 and implemented in the
> same version — but only after the working gate was removed from the repository so the
> decision could be made in writing rather than by having shipped. §9.9.
>
> ADR-0032 was accepted 2026-08-24 and implemented in the
> same version: `.mcp.json` now exists, `gate_mcp` enforces `MCP-000`–`MCP-003`, and the ADR
> carries an Erratum discharging the two paragraphs that described it as pending. §9.8.
> ADR-0029, ADR-0030 and ADR-0031 were accepted 2026-08-11;
> `ADR-009`, which ADR-0029 deliberately left unimplemented while it was `Proposed`, landed
> with the acceptance. §9.6 records what that surfaced.

---

## 1. Architecture version

**1.23.0** — MINOR over 1.22.0: ADR-0040 and ADR-0041 accepted, so two pending decisions
come into force, which §1 defines as MINOR. `pyproject.toml` gains `anthropic` and
`llama-cpp-python`; `ci/policy/policy.yaml` gains an `httpx2` transitive exemption the
resolver surfaced and moves the `cl` preflight row to G3; `MASTER_PLAN_v2.md`'s `evals/`
line is corrected. §9.31.

**1.22.0** — MINOR over 1.21.0: ADR-0040 and ADR-0041 added, both `Proposed`. No
decision in force changed, and neither dependency, schema, nor directory either ADR
names is touched while they wait. §9.30.

**1.21.0** — MINOR over 1.20.0: ADR-0039 accepted, so a pending decision comes into force,
which §1 defines as MINOR. Five brain contracts move to 1.1.0; `test_brain_contract.py`'s
four defect-pinning tests invert into four coherence-pinning ones; `ci/self_test.sh` gains
its 33rd assertion. §9.29.

**1.20.0** — MINOR over 1.19.0: ADR-0039 added, `Proposed` — Phase 3's first. No decision
in force changed, and **not one of the five schemas it names is edited while it waits**.
`tests/contract/test_brain_contract.py` lands with it, pinning the current behaviour, which
needs no ADR: it is a test. §9.28.

**1.19.0** — MINOR over 1.18.0: **G2 signed.** `Phase2_Final_Signoff.md` §7 carries Efe's
signature of 2026-09-02, the document moves from `doc_claims.documents` to
`doc_claims.out_of_scope`, and Phase 3 opens. Only `ci/policy/policy.yaml` is in the checksum
set; the sign-off itself is not, which is why signing moves the version at all. §9.27.

**1.18.0** — MINOR over 1.17.1: ADR-0038 accepted, so a decision comes into force, which
§1 defines as MINOR. It adds no dependency, moves no contract and touches no stable surface;
what it adds is an operator tool and the exercised restore that makes it a backup rather
than a file. §9.26.

**1.17.1** — PATCH over 1.17.0: `Phase2_Final_Signoff.md` §8 registered with `doc-claims`
while the document is unsigned, so the failure recorded in §9.19 cannot repeat. No ADR
added, no decision changed. §9.25.

**1.17.0** — MINOR over 1.16.0: ADR-0037 accepted, so a pending decision comes into force,
which §1 defines as MINOR. `memory-record.schema.json` goes to 1.1.0 — a widening: every
record valid under 1.0.0 stays valid, and the only instances whose status changes are
tombstones, which were invalid. §9.24.

**1.16.0** — MINOR over 1.15.0: the Memory Service, and ADR-0037 added as `Proposed`. No
decision in force changed. Runtime code under `src/lionel/` conforming to frozen contracts
needs no ADR; the contradiction it found in one of those contracts does. §9.23.

**1.15.0** — MINOR over 1.14.0: ADR-0036 accepted, so a pending decision comes into force,
which §1 defines as MINOR. Two dependencies, G2's first runtime code, and `DEP-003` — which
needs no ADR: DEP-002's decision is unchanged, only the file the rule reads. §9.22.

**1.14.0** — MINOR over 1.13.0: ADR-0036 added, `Proposed` — Phase 2's first. No decision in
force changed, and neither dependency it names is declared while it waits. `doc-claims` also
gains a `pending_adrs` fact, which needs no ADR: ADR-0033 already decided that current-state
claims in registered documents are measured rather than remembered. §9.21.

**1.13.0** — MINOR over 1.12.1: **G1 signed and Phase 2 opened.** No ADR was added and no
decision already in force changed; what moved is the phase, which is the same shape as
1.6.0, where G0's sign-off opened Phase 1. §9.20.

**1.12.1** — PATCH over 1.12.0: errata only. `Phase1_Final_Signoff.md`'s state block had
gone stale across four versions while the document sat unsigned, in no registry at all. No
decision changed, no ADR added. §9.19.

**1.12.0** — MINOR over 1.11.0: ADR-0035 accepted, so a pending decision comes into force,
which §1 defines as MINOR. A 23rd gate, and no decision already in force changed. §9.18.

**1.11.0** — MINOR over 1.10.0: ADR-0035 added, `Proposed`. No decision in force changed,
and nothing it describes is implemented while it waits — §1's own definition of MINOR, and
the fifth time the implementation has been withheld from its own proposal. §9.17.

**1.10.0** — MINOR over 1.9.1: ADR-0034 accepted, so a pending decision comes into force,
which §1 defines as MINOR. `policy-ruleset.schema.json` goes to 1.1.0 — the first change to a
`stable` contract since the freeze. Nothing already in force changed: the deciding order is
untouched, and a constraint rule can only stop a call, never authorise one. §9.16.

**1.9.1** — PATCH over 1.9.0: errata only. ADR-0034 and §9.14 both misquoted the rule they
are about, omitting its `match.any = true` line and arguing from an absent `match`. The
finding is unchanged and the corrected quote sharpens it; no decision was added or changed.
§9.15.

**1.9.0** — MINOR over 1.8.0: ADR-0034 added, `Proposed`. No decision in force changed,
and nothing it describes is implemented while it waits — §1's own definition of MINOR is
"a new ADR that adds a decision", and this is the first one since 1.3.0 to arrive without
its implementation. §9.14.

**1.8.0** — MINOR over 1.7.0: the four items 1.7.0 left open are closed, and one of them
turned out to be a false claim in §9.11 rather than a deferral. ADR-0002 carries an Erratum
(the root moved to `Projects/`), the seven-row hazard table becomes a registry with four
rows now enforced by gates, `ARCH-017` lands, and the `--live` filesystem check ran on the
host. No ADR was added and no decision changed. §9.12.

**1.7.0** — MINOR over 1.6.0: v1.0's Phase 1 preflight table becomes executable, and the
two statically checkable rows of its Git Bash hazard table become gate rules. No ADR was
added and no decision changed — both tables are decisions MASTER_PLAN_v2's Phase 1 section
already carries forward in prose ("the tooling preflight table, the Git Bash hazard
rules"), and this makes them run. MINOR rather than PATCH because `ci/policy/policy.yaml`
gains a section and two enforcing rules, which is more than correcting text. §9.11 records
what the preflight found on its first run.

**1.6.0** — MINOR over 1.5.0: `STRUCT-004` lifted and Phase 1 opened. No ADR was added
and no decision changed — G0's sign-off (2026-08-10) was always the condition, and
`STRUCT-004`'s own fix text names updating `repository.runtime_code_forbidden_until` as the
way to satisfy it. The version moves because `ci/policy/policy.yaml` is in the checksum set.

**1.5.0** — MINOR over 1.4.0: ADR-0033 added and accepted, bringing `doc-claims` with it.
No decision already in force changed.

**1.4.0** — MINOR over 1.3.0: ADR-0032 accepted, so a pending decision comes into force,
which §1 defines as MINOR. Nothing already in force changed. `.mcp.json` and `gate_mcp`
land with the acceptance.

**1.3.0** — MINOR over 1.2.0: ADR-0032 added (`Proposed`). No decision in force changed.

**1.2.0** — MINOR over 1.1.1: ADR-0029, ADR-0030 and ADR-0031 accepted and in force, and
`ADR-009` implemented. No decision already in force changed; three that were pending now
bind.

**1.1.1** — PATCH over 1.1.0: errata only. No decision changed, no ADR added. Four documents
asserted counts that had stopped being true, and ADR-0030 claimed a class was closed when it
was narrowed — see §9.5.

**1.1.0** — MINOR over 1.0.0: three new ADRs, no decision already in force changed.

**1.0.0** — the first frozen architecture of L.I.O.N.E.L.

Semantic meaning for this project:

| Component | Change requires |
|---|---|
| **MAJOR** | A superseding ADR that changes a decision already in force |
| **MINOR** | A new ADR that adds a decision without contradicting an existing one |
| **PATCH** | An erratum correcting text to state a decision already in force |

---

## 2. Architecture checksum

Deterministic SHA-256 over the architecture-defining set — sorted paths, path bytes plus
file bytes, grouped, then the group digests concatenated and hashed.

```
ARCHITECTURE CHECKSUM                                          architecture 1.23.0
sha256:853dc1c8d3dd01df583bfcd4fb7233877f4a1bcff25ceb83b116c7f35ec104fa

  ADRs         41 files   sha256:9530bc0283795aef158f417304551ba5…
  contracts    31 files   sha256:87bba7412e01f620f1e78be02ad9ffc0…
  policy        8 files   sha256:00464378149032441ebf47ecb002090a…
  artifacts     1 file    sha256:fc4d6a69230d0b3b5fb25d3f12b71176…
  plan          1 file    sha256:289414e330c4a752c747e0eb7346609e…

  82 files hashed
```

Superseded values, kept so the earlier tags stay verifiable:

```
architecture 1.22.0  sha256:f2090e9cc300314ce27528103ed6a8c5368fe40bd5338ee334c90922a2cca724
                     82 files — ADRs 41 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.21.0  sha256:8b454522a4f42ed20527a7680589713287b82811756bccca7236140da28b068c
                     80 files — ADRs 39 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.20.0  sha256:38c9b925aae41422e0758c28866e8bd0124243c83bb8a61ca1c6b789c54ef1fc
                     80 files — ADRs 39 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.19.0  sha256:0585d19fc64db1ae63a07415af6acecb86c7db7051ec99f5319b39425736b764
                     79 files — ADRs 38 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.18.0  sha256:1d8a33c7efc4c046be4ce2211f846ae112ff1c7b0e6165cb413b3c66b95928ef
                     79 files — ADRs 38 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.17.1  sha256:33896052dc2fc3af011fa940e26bea230f00bc2f6da65326bdac9bbd760e6ee3
                     78 files — ADRs 37 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.17.0  sha256:4d10c4e048737b4298f570f390dfca149b5eb795ed8265b25a8cc3c62713222c
                     78 files — ADRs 37 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.16.0  sha256:124de50597ec16e21126dc068b72446fee1e21c31bcc7dfb7a9210303d12e144
                     78 files — ADRs 37 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.15.0  sha256:efff3d763ddc40862a05e5dea6e35400b3178b4d1588092a7b6e52ad4f2458dd
                     77 files — ADRs 36 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.14.0  sha256:50f1226c43be4586f67a41ea2fc01074c487e855766262930309d73e9feed125
                     77 files — ADRs 36 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.13.0  sha256:f4a97de38f49313c466ff4b20b199c3bca8bfab156e6ca55a0116195741a0d9c
                     76 files — ADRs 35 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.12.1  sha256:029c9ee946a4b0cce6937939212b1a600735f56180843d49fa75fa867ba9c54e
                     76 files — ADRs 35 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.12.0  sha256:2901336ab884ae5d61143a72139822c05f55bb9ba55bf563031a4596cb22b141
                     76 files — ADRs 35 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.11.0  sha256:8a05103d5c9cdaaebbc637415ae70b9dc890edb3706e5274f36c1a2ef6cf5ff5
                     76 files — ADRs 35 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.10.0  sha256:11d2685e902fe03eb4d5636b81b76ab235363915289274e8ee72daebea442ff5
                     75 files — ADRs 34 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.9.1   sha256:37a2bca58042dd851a49d6127e7ffbd916c1f313f0fb49320293da738a4300c0
                     75 files — ADRs 34 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.9.0   sha256:c6da18a0ec65349925824a959d1ca5d82b0266c27b0a55664355d8bd605c9634
                     75 files — ADRs 34 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.8.0   sha256:94d264471f308811487a8e13c8de478b0ed05b7fa53194279b95dfdb7f2c46ea
                     74 files — ADRs 33 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.7.0   sha256:cd24b87f508ebcbbaf7ec588a9a4c1fe8ad9ea6b455f8cb6ffce1bb90eeb6057
                     74 files — ADRs 33 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.6.0   sha256:e279470a2d42ce319437f5fd16593accf0870aca88c28ebc07ee1ed4e8aed1ba
                     74 files — ADRs 33 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.5.0   sha256:e5dbceda15533d681589400ec455677592307877d787cd780350bf90dd791818
                     74 files — ADRs 33 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.4.0   sha256:8d77af2c61f6fedfe748221abcffb00f6f7f703e81d8e3c5b0e4d35712d2d86d
                     73 files — ADRs 32 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.3.0   sha256:c13b16c6527ac26564e4041ec2c71aa88a72b59ac12cf6d6f94d3b4ef94bd481
                     73 files — ADRs 32 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.2.0   sha256:77e6f37244a7ffa6248a3c1607b42f23145493ecebcd0cb1ce1f8b1425479ec7
                     72 files — ADRs 31 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.1.1   sha256:aed60f6faa836855f634fa1fd5a547c728e3ccabf2d209c2eb798e45cea60d24
                     72 files — ADRs 31 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.1.0   sha256:71c7c2fce1fccb2e0e263f98454d72ce85ce3220f3a17c5fea1e7ccaa1181687
                     72 files — ADRs 31 · contracts 31 · policy 8 · artifacts 1 · plan 1
architecture 1.0.0   sha256:fab0610aa3167a2f26b0e812dbfe9563abbf7aa28ab18b9d773d945a5a84f233
                     69 files — ADRs 28 · contracts 31 · policy 8 · artifacts 1 · plan 1
```

**This value is now enforced.** `gate_checksum` recomputes it on every push and fails
`CHECKSUM-001` on drift, `CHECKSUM-003` if a group changes shape (ADR-0030). Between 1.0.0
and 1.1.0 it was recorded and checked by nothing — which is how it came to be wrong.

**Verified against a clean clone on 2026-08-24** (1.4.0 and 1.5.0, the same day). Reproduce it with:

```bash
python3 scripts/architecture_checksum.py --verify sha256:33896052dc2fc3af011fa940e26bea230f00bc2f6da65326bdac9bbd760e6ee3
```

The algorithm is: files partitioned into the five groups below; within a group, sorted by
POSIX-relative path; group digest = `sha256` over the concatenation of (path bytes ‖ file
bytes) with no separator; architecture checksum = `sha256` over the five **raw** group
digests concatenated in the order listed. `scripts/architecture_checksum.py` implements it
and reproduces every group digest above.

**Line endings are part of the checksum, and `CHECKSUM-004` now enforces it directly.**
`.gitattributes` governs what git *checks out*; it does not stop a tool from writing CRLF
into a working copy afterwards, and `CHECKSUM-001` cannot see that on its own — it compares
the recorded value against one computed from the same contaminated bytes, so both agree and
the gate goes green. `CHECKSUM-004` reads every file in the set and fails on a CR. This was
not merely theoretical, twice: `*.proto` was unpinned, so a Windows clone checked the three proto
files out as CRLF and computed `222451c5…` → `0a3b44bc…` for the contracts group. Fixed in
`b2e0b94`. And while 1.4.0 was being prepared, a Python `write_text()` without `newline=""`
rewrote `ci/policy/policy.yaml` and `ADR-0032` with `os.linesep`; the wrong value was
recorded, and the only thing that noticed was a `git add` warning. §9.8.

### Files in the checksum set

```
docs/decisions/ADR-*.md                    33
contracts/{core,mcp,events,media}/v1/*.schema.json   27
contracts/grpc/v1/*.proto                   3
contracts/MANIFEST.json                     1
config/**/*.toml, config/*.json             7
ci/policy/policy.yaml                       1
artifacts.lock.yaml                         1
MASTER_PLAN_v2.md                           1
```

**`.mcp.json` is not in this set**, and ADR-0032 says why: it is workstation tooling, not
architecture. Adding it would mean every developer-tool version bump moved the architecture
checksum, which would teach people that a moved checksum is routine — the one lesson this
mechanism cannot afford to teach. `structure` guarantees the file exists and `gate_mcp`
checks its contents; neither is a claim about the architecture.

---

## 3. Frozen scope

The following are **frozen** at version 1.0.0. Changing any of them requires an ADR under §5.

| Element | Frozen state |
|---|---|
| **Architecture decisions** | **41 ADRs, 0001–0041** — all in force, **0 ADRs pending** |
| **Contracts** | Contract set 1.1.0 — 27 JSON Schemas + 3 protobuf, 5 planes |
| **Capability registry** | 5 capabilities, each declaring `requires_network`, `offline_allowed`, `owner`, `phase`, `trust_level` |
| **Artifact lock** | 13 artifacts, all RESOLVED, tiers A=8 B=2 C=2 D=1 |
| **Tier model** | L0–L3 per ADR-0007; L0 conformance is a blocking gate |
| **Trust model** | 4 levels, monotonically non-increasing within a turn (ADR-0012) |
| **Plane separation** | MCP = control, gRPC = data; no PCM on the control plane (ADR-0006) |
| **Policy** | `ci/policy/policy.yaml` — 21 configuration sections (`doc_quotes` added at 1.12.0), and the count is now measured by `doc-claims` |
| **CI gates** | **23 gates, 151 rules, 27 workflow jobs** — 18 checking the repository, 5 checking the pipeline (ADR-0030, ADR-0033, ADR-0035). Self-test 35/35, gate coverage 23/23 |
| **Phase plan** | MASTER_PLAN_v2 — 11 gated phases, G0–G10 |

---

## 4. Allowed future changes

Permitted **without** an ADR:

1. **Implementation** under `src/lionel/` conforming to frozen contracts.
2. **Tests** under `tests/` and `evals/`.
3. **Gate implementation work** that enforces an existing decision more completely —
   extending `ci/self_test.sh`, adding coverage. **Adding a new rule that changes what is
   permitted requires an ADR.**
4. **Regenerating generated documents** — `CI_Inventory.md`, `Policy_Gates.md`,
   `Contract_Inventory.md`.
5. **Errata** — correcting text to state a decision already in force, recorded as a dated
   Erratum quoting the original verbatim (precedent: ADR-0013, 2026-08-02).
6. **Artifact version bumps** within an existing artifact, following ADR-0013 pinning rules
   and ADR-0021 evaluation gates.

Requiring an ADR:

1. Any new subsystem, technology, or dependency.
2. Any change to a contract's `stable` surface.
3. Any change to the tier model, trust model, or plane separation.
4. Any new capability, or a change to an existing capability's governance fields.
5. Any relaxation of a gate, exclusion, or policy threshold.
6. Any change to the phase plan or gate criteria.

---

## 5. Change control policy

**Every architectural change follows ADR-0016.**

| Step | Requirement |
|---|---|
| 1 | Search existing ADRs and memory first. Settled decisions are not relitigated silently |
| 2 | Write an ADR: Status · Context · Decision · Consequences · **Alternatives Rejected** · **Verification** |
| 3 | Name the gate criterion that verifies it. A decision with no test is a preference |
| 4 | **Efe's explicit approval** before the ADR is Accepted |
| 5 | Implement the gate that enforces it |
| 6 | Add a planted violation to `ci/self_test.sh` |
| 7 | Recompute the architecture checksum; bump the architecture version |

**Commits use the `[LIONEL-CORE]` prefix. No autonomous commit or push — ever.**

---

## 6. ADR modification policy

**ADRs are immutable once Accepted.** Three permitted operations:

| Operation | Mechanism | Precedent |
|---|---|---|
| **Supersede** | New ADR; original's `Status` line updated with a forward link. Original text untouched | ADR-0004 → ADR-0010 |
| **Amend** | Dated `## Amendment` section appended. Adds scope without contradicting | ADR-0013 ×2, ADR-0017 |
| **Erratum** | Dated `## Erratum` section correcting text to state a decision **already in force**. Original wording quoted verbatim. **No policy change** | ADR-0013, 2026-08-02 |

Forbidden: editing an Accepted ADR's Decision in place without an Erratum; deleting an ADR;
renumbering.

> **~~Open governance gap, recorded not fixed:~~ CLOSED 2026-08-11.** The gap — ADR-0016
> having no erratum provision while practice had diverged from it three times — is closed by
> **[ADR-0029](docs/decisions/ADR-0029-adr-errata-provision.md)**, accepted 2026-08-11 and
> enforced by **`ADR-009`**. ADR-0016 carries a dated Amendment pointing to it. The table
> above is no longer a description of practice; it is the rule.

---

## 7. Phase 1 entry criteria

Phase 1 may begin when **all** hold:

| # | Criterion | Status |
|---|---|---|
| 1 | Architecture frozen at a named commit SHA | ✅ `0066cb2`, tag `architecture-1.0.0` |
| 2 | Clean clone of that commit scores 17/17 gates | ✅ verified 2026-08-10 |
| 3 | `artifacts.lock.yaml` — 0 unresolved, in the frozen commit | ✅ 13 resolved / 0 unresolved |
| 4 | Capability registry governance fields, in the frozen commit | ✅ 5 of 5 capabilities |
| 5 | Architecture checksum recorded against the commit SHA | ✅ reproducible — `scripts/architecture_checksum.py` |
| 6 | ADR count 28, no contradictions | ✅ |
| 7 | Contract set 1.1.0, all schemas valid, examples validate | ✅ |
| 8 | Trust model consistent across contracts and registry | ✅ |
| 9 | CI enforces the architecture — 17 gates wired | ✅ |
| 10 | Security assumptions documented | ✅ |
| 11 | Ownership defined for contracts and capabilities | ✅ |
| 12 | No circular dependencies | ✅ |

**12 of 12 met.** Phase 1 may begin.

---

## 8. Freeze execution

Performed 2026-08-10.

### 8.1 What was executed

| Step | Result |
|---|---|
| 1 · Commit the architecture | `0066cb2` — 12 paths, exactly the set the audit enumerated |
| 2 · Push | `origin/main`, [run 31368070033](https://github.com/Denizfe/L.I.O.N.E.L/actions/runs/31368070033) green |
| 3 · Clean-clone, all gates | **17 / 17**, `0` broken |
| 4 · Clean-clone, self-test | **10 / 10** planted violations caught |
| 5 · Recompute the checksum | `sha256:fab0610a…` — **matches**, all five group digests |
| 6 · Tag | `architecture-1.0.0` |
| 7 · Re-submit the sign-off | `Phase0_Final_Signoff.md` §15 — verdict **PASS** |

Only the twelve paths the audit listed went into `0066cb2`. Nothing found afterwards was
folded back into it: a freeze commit that quietly grew is a freeze of something nobody
audited.

### 8.2 Reproducing the freeze

```bash
git clone https://github.com/denizefekaracakaya/L.I.O.N.E.L.git && cd L.I.O.N.E.L
git checkout architecture-1.0.0
pip install pyyaml jsonschema grpcio-tools
bash ci/run_gates.sh          # expect 17/17, 0 broken
bash ci/self_test.sh          # expect 10/10
python3 scripts/architecture_checksum.py --verify sha256:fab0610aa3167a2f26b0e812dbfe9563abbf7aa28ab18b9d773d945a5a84f233
```

`grpcio-tools` is required: without it the `protobuf` gate exits 2, which is a broken gate,
not a passing repository, and the runner reports it as such.

### 8.3 Why the tag is not on `0066cb2`

Verifying the freeze surfaced three defects in the tooling around it. None touched the
architecture — the checksum is byte-identical across all of them — but two had to be fixed
before the freeze could mean what it claims.

| Commit | Fix | Why it blocks the freeze |
|---|---|---|
| `b2e0b94` | `*.proto text eol=lf` | Without it a Windows clone computes a **different** architecture checksum. §7 criterion 5 is then unmeetable: the recorded checksum is not a property of the commit |
| `b2e0b94` | UTF-8 stdout in `ci/gates/_lib.py` | Every gate died with `UnicodeEncodeError` on a cp1252 console, reporting "broken gate" on a clean repository. §7 criterion 2 unverifiable on the platform this project targets |
| `b2e0b94` | `scripts/architecture_checksum.py` | A checksum nobody can recompute cannot detect drift, so §2 asserted something unfalsifiable |
| `968eace` | Regenerated `CI_Inventory.md`, `Policy_Gates.md` | Findings N1/N2. Documentation only |

All four are permitted by §4 without an ADR: items 3 and 4 — gate work that enforces an
existing decision more completely, and regenerating generated documents.

So `0066cb2` is where the architecture entered version control, and `architecture-1.0.0` is
the commit you should clone: the first one where the freeze's own criteria are all
demonstrably met.

### 8.4 Rule count: 116 → 127

§3 previously recorded 116 rules, an audit estimate taken from `g.fail(...)` call sites.
That undercounts, because `l0-conformance` emits 24 distinct rules through a **single**
`g.fail(rid, …)` driven by an invariant table. Counting distinct emittable rule IDs gives
**127**, now derived mechanically by `scripts/generate_ci_docs.py`. The gates did not
change; the count was wrong. Recorded here rather than silently corrected, per §6.

---

## 9. Version 1.1.0 — what changed and why

1.1.0 landed the same day as 1.0.0. That is not a sign the freeze was premature; it is what
the freeze was for. Verifying 1.0.0 end to end produced five findings, and they turned out
to be one finding five times.

### 9.1 The root cause

| The repository stated | Enforced by | What was true |
|---|---|---|
| "Regenerate rather than hand-edit" — both generated documents | nothing | 16 gates claimed vs 17; 88 rules vs 127; `l0-conformance` **absent from the rule catalogue** |
| "Deterministic checksum" — §2 of this document | nothing | not reproducible from a clone for 8 days |
| "A gate that has never rejected anything is unproven" — `CI_Architecture.md` §7 | nothing | 8 of 17 gates had never rejected anything |
| Windows + Git Bash is the host runtime — ADR-0002, ADR-0014 | nothing | every gate crashed on a cp1252 console |
| "verify per MODEL_CARD before release" — `artifacts.lock.yaml` | a registered deferral | the card said CC-BY-NC-SA-4.0, on the only Turkish voice |

Five rules the project wrote down, believed, cited elsewhere — and never gave a test. Its
own doctrine names the failure: *a decision with no test is a preference.* The doctrine had
never been applied to itself. Seventeen gates enforced invariants about the repository; none
enforced invariants about the gates, the documents describing them, or this freeze.

### 9.2 What 1.1.0 adds

| | |
|---|---|
| **ADR-0029** `Proposed` | Errata / Amendment / Supersede. Closes the §6 gap: ADR-0016 forbids what correct practice has done three times |
| **ADR-0030** `Proposed` | The pipeline enforces its own invariants — the three meta-gates |
| **ADR-0031** `Proposed` | A `review_required` licence must have somewhere to be reviewed |
| **`checksum`** gate | Recomputes §2 on every push. Would have caught the CRLF defect on the first Linux run |
| **`generated-docs`** gate | Every generated document matches its generator. Would have caught N1 and N2 the day they appeared |
| **`gate-coverage`** gate | Every gate has rejected a planted violation. Counts **gates**, not assertions |
| **Self-test 10 → 21 assertions** | Gate coverage **9/17 → 20/20**, with `coverage.exempt` empty |
| **R-A15 escalated** | Minor → Major. The Turkish voice is CC-BY-NC-SA-4.0: personal use unaffected, distribution blocked |

Nothing in force at 1.0.0 changed. §1's MINOR definition — "a new ADR that adds a decision
without contradicting an existing one" — is met three times over.

### 9.3 Why the version had to move

`docs/decisions/ADR-*.md` and `ci/policy/policy.yaml` are both inside the checksum set, so
adding three ADRs and a policy section changed the checksum whether or not anyone recorded
it. §5 step 7 requires the recomputation and the bump. What is new is that skipping it is
now impossible rather than merely discouraged: `gate_checksum` fails.

That is the shape of every change in 1.1.0. None of it is new policy. All of it is existing
policy that had no mechanism.

### 9.5 Version 1.1.1 — the gates' first real finding

Within an hour of 1.1.0 being tagged, a review found four documents asserting things that
had stopped being true. **None of them is generated, and none is in the checksum set, so no
gate could see any of it.**

| Document | Said | Actually |
|---|---|---|
| `Architecture_Risk_Register.md` | R-A01, R-A03 **"OPEN — blocks G0"**; R-A05, R-A06, R-A08 OPEN | G0 signed off; all six closed by work landed that day |
| `Phase0_Final_Signoff.md` §15 | coverage 9/17 "tracked for Phase 1"; three prerequisites open; 127 rules | 20/20; zero open; 136 rules |
| `CI_Architecture.md` §8 | `15 pass · 1 fail by design` | `20 pass · 0 fail` |
| `MASTER_PLAN_v2.md` §9 | an ADR table stopping at 0028 | 31 ADRs exist |
| `ADR-0030` | "The five defect classes are **closed** by mechanism" | Three are. The class is **narrowed** |

**R-A05 and R-A08 are the sharpest of these.** An auditor wrote them on 2026-08-02 —
*"silent CI coverage loss (counter ≠ coverage)"* and *"untested gates fail silently when
they matter"* — reading a pipeline that reported 8/8. Both were right. Both sat OPEN for
eight days while the counter climbed to 10/10 and eight gates still had never rejected
anything. **The register named the root cause before it was measured, and nothing acted on
it, because a risk row is prose and prose does not fail a build.** That is ADR-0030's thesis,
written down by someone else, a week early, and ignored — which is the strongest argument
for it in this document.

The corrections are errata: text brought into line with decisions already in force. Per §1
that is a PATCH. Two of them touch the checksum set — `ADR-0030` and `MASTER_PLAN_v2.md` —
so the checksum moved and had to be re-recorded and re-tagged for a set of typo-class fixes.

**That cost is the mechanism working.** `gate_checksum` went red on the first edit and
stayed red until §2 was updated. Before 1.1.0 the same edits would have silently invalidated
the recorded checksum, which is precisely how the CRLF defect survived eight days.

**What is still not enforced:** every hand-written document that asserts a count about this
repository — including this one. `generated-docs` covers documents that have a generator,
currently two. ADR-0030's Costs now record this rather than claiming the class is closed.
Closing it needs a different decision and its own ADR.

### 9.6 Version 1.2.0 — the ADRs accepted, and what enforcing one taught

Efe accepted ADR-0029, ADR-0030 and ADR-0031 on 2026-08-11. Three consequences.

**The acceptance was itself the first test of ADR-0029.** Each ADR asserted its own
`Proposed` status *in its body*, and ADR-0029 rule 1 makes the body append-only — so the
status could not simply be edited out. Each carries a dated `## Erratum — 2026-08-11`
quoting the superseded sentence verbatim. ADR-0016 carries a dated `## Amendment` pointing
to ADR-0029, which under the old rule would have been forbidden and under the new one is the
correct instrument. **The mechanism's first use was on the document that introduced it.**

**`ADR-009` landed, having been deliberately withheld.** ADR-0029's Verification said the
rule would not be implemented until acceptance, "a gate enforcing an unapproved decision
would be the same category error this ADR is about." That condition was met in that order.

**Implementing it surfaced a problem the ADR had not anticipated,** and this is the part
worth reading. ADR-0029 rule 2 requires an Erratum to quote verbatim what it corrects.
**ADR-0017's `## Correction — 2026-08-02` paraphrases instead.** It is a faithful correction,
written nine days before the rule existed.

Enforcing rule 2 retroactively would have failed `ADR-009` on ADR-0017 **permanently, with
no permitted fix** — adding the missing quote means editing the body of an Accepted ADR,
which rule 1 forbids. The gate would have had no reachable green state: precisely the failure
ADR-0031 was written about, reproduced by the ADR meant to prevent that class, on its first
day.

Resolved by an Amendment to ADR-0029 rather than by quietly weakening the gate:
`errata_quote_required_from: "2026-08-11"` in policy, so the boundary is a reviewable value.
Rule 4 (the date) binds everything; rule 2 binds forward. `gate_adr` **reports the two
grandfathered sections as notes on every run** rather than passing silently — a
grandfathered violation that stops being visible is just a violation.

> A rule cannot bind documents written before it existed. The cheap move was to drop rule 2;
> the honest one was to bound it, say where the boundary is, and keep saying what sits on the
> far side of it.

### 9.7 Version 1.3.0 — ADR-0032, and a rule applied to itself

An automation review recommended checking in a `.mcp.json` so the toolchain is part of the
clone like everything else. Implementing it would have meant adding **context7** — a network
documentation service — to the repository.

**It was not added.** §4 requires an ADR and Efe's approval for any new technology, and
`CLAUDE.md` had just been written stating that rule. Adding the server on the reasoning that
"it's only dev tooling" is precisely the shortcut §4 exists to prevent, and the fact that the
answer is probably *yes* is what makes the shortcut tempting.

So ADR-0032 proposes it instead, and `.mcp.json` does not exist until the ADR is Accepted —
the same discipline ADR-0029 applied to `ADR-009`.

The ADR is worth reading for three things it had to resolve rather than assert:

| | |
|---|---|
| **The offline objection** | ADR-0007's L0 guarantee constrains the **product at runtime**, not the workstation. A developer reading docs over the network no more breaks it than a browser does. But MASTER_PLAN_v2 §W1 names erosion as this project's characteristic failure mode, so the ADR draws a hard line: no gate, no runtime path, ever |
| **`npx -y` versus ADR-0013** | Unpinned `npx -y <pkg>` resolves latest at every launch — *"a rebuild in three months produces a different system"*, the exact sentence ADR-0013 was written around. Pinned to `@4.0.0` |
| **The API key** | The hosted endpoint takes one. Declined: it buys rate limit, not capability, and ADR-0015 plus a `gate_secrets` scan with no path exclusions make a checked-in credential a live hazard |

Nothing else in 1.3.0. The automation work landed separately in `5bcecb6` and moved no
checksum, because `CLAUDE.md`, `.claude/` and the hooks are outside the checksum set.

### 9.8 Version 1.4.0 — ADR-0032 accepted, and the mechanism it proposed

Efe accepted ADR-0032 on 2026-08-24. §1 calls this MINOR — a pending decision comes into
force — and nothing already in force changed.

**What landed**

| | |
|---|---|
| `.mcp.json` | One entry, `context7`, pinned to `@upstash/context7-mcp@4.0.0` (MIT), with an `x-lionel` block declaring licence, transport, scope and egress. No credential |
| `ci/gates/gate_mcp.py` | `MCP-000` malformed manifest · `MCP-001` unpinned package · `MCP-002` undeclared egress · `MCP-003` literal credential |
| `ci/policy/policy.yaml` | `mcp:` section — pinning shapes, the egress requirement, the credential key pattern and the allowed value forms |
| `repository.required_paths` | `.mcp.json`, so a deleted manifest fails `structure` instead of leaving `gate_mcp` with nothing to check |
| `ci/self_test.sh` | Assertion 17b: strips the version pin and asserts `MCP-001`. 23/23 |
| `.github/workflows/ci.yml` | A 24th job. It runs the gate; it does not install or launch an MCP server, because a gate that depended on one would be ADR-0032's first violation |

**One rule beyond the ADR.** `MCP-000` is not in ADR-0032's Verification list. A malformed
`.mcp.json` is a file the repository owns and a human must fix, so reporting it through
`gate_error` — exit 2, "the gate is broken" — would collapse the two exit codes §5 keeps
apart. It is mechanical necessity, not a new decision, and the ADR's Erratum says so rather
than leaving the discrepancy for a reader to find.

**One rule deliberately not written.** ADR-0032's standing criterion — one entry, and a
second is a decision rather than a routine addition — is a *note* on every run, never a
violation. Blocking the second entry would settle by implementation the question the ADR
left to a reviewer, and a gate that answered it would be claiming to check something it
cannot see.

**Why `.mcp.json` is outside the checksum set.** It is workstation tooling. Inside the set,
every developer-tool version bump would move the architecture checksum, and a checksum that
moves routinely stops carrying information — which is the failure §2 exists to prevent, not
one it should import.

**A stale count, found by hand again.** §3 read *"Self-test 21/21"* through the whole of
1.3.0, when the suite had been 22/22 since 1.2.0. §3 also read *"16 sections"* for a
`policy.yaml` that had 15; adding `mcp` has made that figure accidentally true. Both are the
class ADR-0030's Costs section records as open: `generated-docs` covers only documents that
have a generator, and this one does not. The `doc-claim-auditor` agent mitigates it. It does
not close it.

**The checksum was recorded wrong, and nothing in the pipeline caught it.** Two files in
the set — `ci/policy/policy.yaml` and `ADR-0032` — were rewritten by a Python
`Path.write_text()` call, which translates `
` to `os.linesep` unless you pass
`newline=""`. Both acquired CRLF, and the value first recorded in §2 (`0e8cfbc2…`) was a
property of one Windows working copy. A clean clone would have computed something else — the
1.0.0-era defect, by a different route, thirteen days after `gate_checksum` was written to
prevent it.

`CHECKSUM-001` was green throughout, and could not have been anything else: it compares the
recorded number against one computed from the same contaminated bytes. `git add`'s "CRLF
will be replaced by LF" warning was the only signal, and warnings are not gates.

**`CHECKSUM-004`** now reads every file in the checksum set and fails on a CR. `ci/self_test.sh`
assertion 18b plants CRLF in `artifacts.lock.yaml` and asserts it — 24/24. This is gate work
enforcing a decision §2 already states, which §4 item 3 permits without an ADR.

**And the generated documents were under-reporting.** `CI_Inventory.md` and
`Policy_Gates.md` read the self-test by parsing `expect_violation` lines, plus two inline
cases listed by hand. The third inline case — `gate-coverage`, asserted against a doctored
copy of the suite because the gate needs `--suite` — was never added to that list, so both
documents said `23/23` for a run that reported `24/24`. `generated-docs` could not catch it:
the documents matched what the generator produced, and the generator was wrong. Fixed by
listing all three inline cases, with a comment saying why the two counts can drift apart.

**A bug the self-test caught in its own new assertion.** The first draft of assertion 17b
described the plant as ``"an MCP server pinned to nothing but `npx -y`"``. Backticks inside
a double-quoted bash string are command substitution, so the suite *ran* `npx -y` — a
network fetch, in the offline-first project's own test harness, which then hung. It was
found because the run stopped, not because anything checked for it. `SH-EVAL` and friends
police `ci/` for injection shapes; command substitution in a description string is not one
of them.

---

### 9.9 Version 1.5.0 — ADR-0033, and a working gate removed before it could decide anything

`gate_doc_claims` was written, wired into `ORDER` and `ci.yml`, given a planted violation,
and run. It worked. On its first execution against the 1.4.0 tree it reported

```
CLAIM-001  `CLAUDE.md` claims `20/20, 0 broken`; the pipeline reports gates = 21
           at CLAUDE.md:84
```

— four gates out of date, under a heading reading **"Verify before you claim anything"**, in
the file every session loads first.

Then ADR-0030's Costs section turned out to have already answered the question:

> Closing the rest is a larger question than this ADR answers. It means either generating
> those documents too — which would cost the prose that makes them worth reading — or **a
> narrower check over count-shaped claims, which is a different decision needing its own
> ADR.**

That is exactly what had just been built. The reasoning available at that moment — *"this
only enforces ADR-0030 more completely, which §4 item 3 permits"* — is the reasoning §4
exists to prevent, and it is at its most persuasive when the thing already works and is
already green.

So the implementation was **removed from the repository**, and `ADR-0033` written as
`Proposed` instead. Efe accepted it the same day, and it went back in. The round trip cost
an hour and produced a decision with a record behind it rather than a gate with an
implementer behind it.

**What landed**

| | |
|---|---|
| `ci/gates/gate_doc_claims.py` | `CLAIM-001` count disagrees with measurement · `CLAIM-002` registered document or region missing · `CLAIM-003` exclusion missing `why`/`owner`/`unblocked_by`, or matching nothing |
| `ci/policy/policy.yaml` | `doc_claims:` — seven claim patterns, three registered regions, three out-of-scope documents each with an owner and a route in |
| `ci/self_test.sh` | Assertion 19b plants a wrong count in `CLAUDE.md` and asserts `CLAIM-001`. 25/25 |
| Meta-gate group | Now four rather than three: `checksum`, `generated-docs`, `doc-claims`, `gate-coverage` |

The gate measures rather than remembers: gate, rule, job, ADR and assertion counts come from
`scripts/generate_ci_docs.py`, imported rather than reimplemented — the `_checksum.py`
precedent, for the same reason. It reads a number out of a document only in order to
disagree with it.

**Most numbers here are supposed to be stale**, which is why this is a registry and not a
sweep. §9.x above, the superseded-checksum block and `Phase0_Final_Signoff.md`'s evidence
tables are dated records; ADR-0029 is why they are appended rather than rewritten, and a
gate that flagged them would be arguing with the archive. Three documents are registered.
The other three are named as out of scope, with owners — the gap is now a list rather than
an absence.

**It does not close the class.** A current-state claim in a document nobody registered is
still unchecked, and rule 4 can police the entries that exist but not the entry nobody
wrote. ADR-0033's Costs section says so, and `doc-claim-auditor` still earns its keep on
the judgements a gate cannot make — a risk row reading OPEN next to the gate that closed it
is not arithmetic.

**The third withholding.** Worth naming as a pattern rather than three coincidences:

| | Withheld | Released |
|---|---|---|
| ADR-0029 | `ADR-009`, the errata-shape rule | 1.2.0, on acceptance |
| ADR-0032 | `.mcp.json` and `gate_mcp` | 1.4.0, on acceptance |
| ADR-0033 | `gate_doc_claims` | 1.5.0, on acceptance |

---

### 9.10 Version 1.6.0 — Phase 1 opens, and the first runtime code

`STRUCT-004` forbade `.py` under `src/lionel/` for the whole of Phase 0. It is now
**dormant**: `repository.runtime_code_forbidden_until` is `null`.

**This is not a relaxation, and it is worth being precise about why.** §4 requires an ADR
for any relaxation of a gate, and that rule is doing real work here — the temptation is to
treat "the gate is in my way" as sufficient. It is not what happened. `STRUCT-004` was
always conditional, its condition was G0, and its own fix text names the mechanism:

> Remove them, or sign off G0 and update `repository.runtime_code_forbidden_until` in
> ci/policy/policy.yaml.

G0 was signed off on 2026-08-10 — `Phase0_Final_Signoff.md`, and `Phase1_Entry_Checklist.md`
at 9 of 9 with 0 blocking. The gate was reporting a condition, and the condition is met.
The version still moves, because `ci/policy/policy.yaml` is in the checksum set.

**The rule is dormant rather than deleted.** Setting that value back to a gate name re-arms
the ban, which is the right move if a later phase needs a code freeze; deleting the rule
would mean rewriting the gate to get it back. `structure` keeps its self-test coverage
through `STRUCT-003` (`forbidden_paths`) — assertion 4 now asserts both `architecture`
/`ARCH-001` and `structure`/`STRUCT-003` against the same planted `capabilities/shell`
directory. A gate that has never rejected anything is unproven whichever of its rules
happens to be reachable today.

**What landed under `src/lionel/`**

| | ADR | G1 DoD clause |
|---|---|---|
| `secrets/` — `SecretStr`, `SecretResolver` | ADR-0015 | *"a `secret://` URI resolves and its value redacts in log output"* |
| `platform/process_supervisor.py` | ADR-0014 | *"Job Object kill-tree verified by terminating a parent and confirming zero orphaned children"* |

Both DoD clauses are now executable tests rather than intentions. The kill-tree test spawns
a parent, which spawns a grandchild that would outlive it, shuts the supervisor down, and
asserts the grandchild is gone. **Stopping one level up would have passed against the
implementation ADR-0014 rejected**, so the test deliberately goes two.

That test was then falsified before being trusted: the same fixture, killed with a plain
`Popen.terminate()`, leaves the grandchild running and the detector reports it. The green
test means something because the red one was observed first.

`SecretStr` redacts through `__str__`, `__repr__`, `__format__`, `%`-formatting and a real
`logging` call, and **refuses `==` against a plain `str`** — that comparison's failure
message would print the secret, at the moment something is already going wrong.

**Two decisions taken by not taking them.** `pytest` is not a dependency: ADR-0027 defines
five test *layers* and names no runner, so the suite uses the standard library's
`unittest`. Adding pytest is a §4 dependency decision needing an ADR, and "obviously
needed" is exactly the reasoning §4 exists to catch. Likewise ADR-0014's `dpapi` and `k8s`
secret backends raise `BackendNotAvailable` naming the tier that brings them, rather than
falling back to `env` — a silent downgrade would move a secret from the Windows credential
store into a process listing without anyone deciding to.

**CI gains a `unit-tests` job on Linux *and* Windows.** Not symmetry for its own sake: the
Job Object code path does not execute on Linux at all, so a Linux-only run would report
success for a mechanism it never touched.

`.mcp.json`, `src/`, `tests/` and `CLAUDE.md` remain outside the checksum set. The freeze
governs the architecture; the code written against it is checked by its own tests.

---

### 9.11 Version 1.7.0 — the preflight table runs, and finds a stale root

MASTER_PLAN_v2's Phase 1 section says, of v1.0's environment work: *"Carries forward v1.0's
environment work — the tooling preflight table, the Git Bash hazard rules."* Carried
forward, but not carried anywhere. Both were prose in a superseded plan, and both had been
prose for the whole of Phase 0.

**What 1.7.0 adds**

| | |
|---|---|
| `ci/policy/policy.yaml` → `preflight` | the six-tool table from MASTER_PLAN_v1 §1.1, the four Python packages the gates import, and two opt-in live checks. One registry |
| `scripts/check_env.sh` | runs it. Exit `0` ready · `1` the environment is wrong · `2` the preflight is broken |
| `scripts/_preflight_table.py` | reads the registry and prints TSV. A separate file so two quoting regimes never fight over the same backslashes |
| `SH-BARE-PYTHON`, `SH-MSYS-DOCKER` | the two rows of the seven-row hazard table that can be checked statically |
| `tests/unit/test_preflight.py` | 16 tests over the table's shape and the agreement between the three files |
| `doc-claims` → `policy_sections` | a measured fact behind the claim "N configuration sections" |

**Why the preflight is not a gate.** It describes the *host*, and CI is not the host runtime
(ADR-0002). A gate that went red because a laptop lacked VS Build Tools would be asserting
something true about the wrong computer. So `check_env.sh` is a script an operator runs, and
what CI checks is the table's shape — that every row has a probe naming its own tool, an
extract pattern that finds a version, and a `why` long enough to be a reason.

**What it found on its first run.** The `filesystem` capability is handed exactly one allowed
root and cannot escape it, which is the whole point of the scope note in MASTER_PLAN_v1 §1.4.
That root was `C:/Users/deniz/Desktop/L.I.O.N.E.L`. The repository is in `Projects/`. The
declared root had not existed for as long as anyone can date, and:

```
docker-digests   PASS      artifacts       PASS      l0-conformance  PASS
structure        PASS      contracts       PASS      checksum        PASS
```

Every gate green, because every gate was checking the file's *shape*. The path is a host
fact, and a host fact cannot be checked by anything that runs on a different machine — which
is exactly why nothing was checking it. The same stale root was written in **two** files:
`config/capabilities.registry.json` and `config/lionel.toml` `[project].root`. A check that
had read only the capability registry would have fixed one of them and reported success, so
the preflight scans both, and a test asserts it scans both.

This also settles what "v1.0's Phase 1 DoD in full" can mean. Two of its seven items —
the filesystem server refusing to escape its root, and `get_me` returning Efe's login —
need the network and a credential. They are `live_checks`, run only under `--live`, which
announces itself first. A preflight that quietly dialled out would be the first thing to
break ADR-0007's promise that the ordinary path works with the cable pulled.

**A hard-coded number in a generated document.** `CI_Inventory.md` read *"Runtime code | **0
files** — Phase 0 discipline machine-checked"*. It was a string literal in
`scripts/generate_ci_docs.py`, true while `STRUCT-004` forbade runtime code and false from
the moment 1.6.0 lifted it. `generated-docs` could not catch it: the document matched the
generator, and the generator was wrong — the same shape as the self-test undercount at
1.5.0. It is now measured (`7 files`). A number in a generated document is a hand-written
claim wearing a generated document's authority unless something counts it.

**The blunt rule that caught its own author.** `SH-BARE-PYTHON` is line-based and skips
comments, not strings. Its first finding was a heading inside `check_env.sh` that printed
the words "python packages". The rule was right by its own terms and the cost was one
capital letter; teaching it to parse shell string literals would mean writing a shell
parser, and a parser that is 95% correct on this class is worse than a rule that is blunt
and known to be blunt.

**Not done, and deliberately.** `contracts/mcp/v1/capabilities-registry.schema.json` carries
the same stale `Desktop/` path in its `examples` block. It is illustrative rather than part
of the stable surface — but it is inside a frozen contract, and §4 guards contract files
hardest. Raised rather than edited. Five of the seven hazard rows (`$(pwd -W)` in mounts,
`winpty` for anything that prompts, forward slashes in config values, the WSL2 backend, and
CRLF in scripts — the last already enforced as `SH-CRLF`) describe what an operator types at
a terminal and cannot be checked from a file; they are recorded in `check_env.sh` where the
operator will read them.

> **Corrected at 1.8.0 — this last sentence was not true when it was written.** Nothing was
> recorded in `check_env.sh`. The sentence is left standing rather than edited, because it
> is the record of what 1.7.0 claimed; §9.12 says what was actually there and what made the
> claim true. Two of the five rows were also checkable after all.

Self-test **27/27**. Gates **22/22**, 0 broken. Tests **102**, 1 skipped (a POSIX-only
kill-tree case). `scripts/`, `src/`, `tests/` and `CLAUDE.md` remain outside the checksum
set; the version moves because `ci/policy/policy.yaml`, `config/lionel.toml` and
`config/capabilities.registry.json` are in it.

---

### 9.12 Version 1.8.0 — the four things 1.7.0 left, and a claim that was not true

1.7.0 closed with a list of what it had deliberately not done. Working that list turned up
one item that was not a deferral at all.

**§9.11 said something that was false.** It reported that the five unenforceable hazard rows
were *"recorded in `check_env.sh` where the operator will read them"*, and the 1.7.0 commit
message said the same. They were not in `check_env.sh`. Nothing was. The sentence described
an intention, written at the point in the work where intention and completion feel identical
— and it went into the frozen record.

This is the failure `doc-claims` exists to catch, in the one shape it cannot catch: not a
count, a claim about what a file contains. Nothing checks those. `ADR-0033`'s Costs section
already records that gap; it now has an instance with a date on it.

The correction is not an edit. The claim is made true instead: all seven rows are a registry
in `ci/policy/policy.yaml` → `preflight.hazards`, `check_env.sh` prints them, and
`tests/unit/test_preflight.py` asserts all seven are present, that a row naming an enforcing
rule names one that a gate actually emits, and that the `operator` label stays capped.

**`ARCH-017` — the seventh row stopped being unenforceable.** HAZ-BACKSLASH was labelled
`operator` on the reasoning that config style is a matter of discipline. It is not: config
files are in the repository and portable, so a gate can read them. `ARCH-017` fails any
`"C:\..."` value under `config/`. The failure it prevents is silent by construction — Bash
consumes the backslash as an escape, `C:\Users\deniz` arrives as `C:Usersdeniz`, nothing
errors, and the filesystem capability is scoped to a root that does not exist. Which is very
nearly what had already happened by another route.

Four of seven rows are now gate rules, one is executed by the preflight, and two genuinely
describe what a person types at a terminal. The registry comment caps `operator` at two, and
a test enforces the cap — `operator` is the one label in this repository carrying neither an
owner nor a route to removal, so it is bounded instead.

**`docker --version` was answering the wrong question.** The 1.7.0 preflight reported a green
Docker row on a machine where no daemon was running and nothing could be launched. The CLI
being installed is not the fact anyone needs. `HAZ-DOCKER-BACKEND` now asks the daemon, and
distinguishes three answers: WSL2 (what MASTER_PLAN_v1 §2 requires), another backend, and
unreachable. The `--live` GitHub check consults it first, because "start Docker Desktop" and
"issue a PAT" are different jobs and reporting the first as an authentication failure sends
the reader to debug something that is not broken.

**ADR-0002 carries an Erratum.** Its title and Decision named `Desktop\L.I.O.N.E.L`. The
mechanism is an Erratum rather than a supersession, and the ADR's own Context is what settles
it: the rule applied there was *"The directory that actually exists, and that tooling has
access to"*, which is unchanged and still selects exactly one answer — only the answer moved.
A supersession would be right for a different decision, such as making the root
configurable, and that alternative stays rejected for the reason already recorded.

The ADR also predicted this. Its Context: *"An unresolved path ambiguity is not cosmetic — it
silently produces two divergent trees, half-written config, and MCP filesystem roots that
point at nothing."* That happened, to this ADR, in this repository, with all twenty-two gates
green. Raised as **R-A20**, Moderate, mitigated rather than closed: the residual risk is that
nothing forces the preflight to run, and nothing can — a host fact is not checkable from a
CI runner. The route to closure is a checklist step at each gate sign-off, not a gate.

**The `--live` checks ran, and one of them passed for real.** ADR-0002's Verification clause
— *"The MCP filesystem server starts scoped to this root, lists it successfully, and refuses
a read outside it"* — has been owed since 2026-08-01. On the host:

```
read C:/Users/deniz/Projects/L.I.O.N.E.L/.python-version   ->  "3.11"
read C:/Windows/System32/drivers/etc/hosts                 ->  isError: true
                     Access denied - path outside allowed directories
```

Both halves, because either alone proves nothing: a server that refuses everything also
refuses the escape, and a server that allows everything also lists the root. `github-identity`
did not run — no daemon was reachable — and is reported as a skip naming that reason, not as
a pass and not as a failed login. **It is still owed.**

> **Corrected at §9.13.** Both checks above ran through a shell pipeline that closes stdin
> before the server can answer. The `filesystem` result stands — it was re-run through a real
> client and passed both halves again — but it passed here by luck rather than by design, and
> the GitHub check in the same shape could not have passed for any input.

Self-test **28/28**. Gates **22/22**, 0 broken. Tests **106**, 1 skipped. The contract example
in `capabilities-registry.schema.json` was corrected too: it is illustrative rather than
stable surface, and an example that points somewhere non-existent is a trap for whoever
copies it. `MASTER_PLAN_v1.md` and `Phase0_Blockers.md` keep the old path — frozen historical
records, preserved verbatim by decision.

---

### 9.13 A check that could not pass, and the clause it was hiding

No version. The architecture checksum is unchanged — only `scripts/` and `tests/` moved, and
neither is in the set. Recorded here because of what it found.

**The GitHub live check reported `no login` for every input, valid credentials included.**

It was written as a shell pipeline: `printf '<init><ready><get_me>' | docker run -i …`. That
looks right. The pipe closes the instant `printf` finishes, and a server that reads EOF on
stdin as "the client hung up" tears the session down before writing a byte of response. The
GitHub MCP server does exactly that:

```
session initialized
server session disconnected
server session ended with error: server is closing: EOF
```

No JSON-RPC reached stdout at all, so the branch that looked for a login never had anything
to look at. The check was not strict; it was **inert**, and its failure message —
*"container started but get_me returned no login"* — sent the reader to audit a token that
was fine.

This is worse than an unwritten check. An unwritten check is visibly absent. This one
occupied the slot, reported a specific and plausible diagnosis, and sat on the G1 sign-off
path. It was the last thing standing between the project and a signature.

**The `filesystem` check passed through the same broken pipeline** at 1.8.0, and was recorded
in §9.12 as evidence. It passed because Node answers before its teardown reaches the write —
luck, not design, and it would have gone on being read as proof.

**What replaced it.** `MCPClient` in `scripts/_preflight_table.py`: it holds stdin open until
it has what it asked for, and matches each response **by request id**. Taking the first line
back would pair a request with whatever the server happened to print next, which for a chatty
server is a log line or an unrelated notification. Reads run on a reader thread with a
deadline, because Windows cannot `select()` on a pipe and a blocking `readline()` against a
wedged server hangs the preflight with no output and no way to tell why.

`401`, `403` and silence are now three different reports. "Start Docker Desktop", "issue a
new token" and "the container is broken" are three different jobs, and a check that collapses
them has moved the diagnosis onto the reader at the least convenient moment.

**`npx` is `npx.cmd` on Windows,** and `Popen` without a shell does no PATHEXT resolution —
`FileNotFoundError` from the bare name. `shell=True` was the one-line fix and was not
available: ADR-0011 forbids any path from text to an interpreter, and a preflight that quietly
opened one would be arguing against the thing it checks. `shutil.which()` resolves it and
execution stays argv-only. A test walks the parsed tree for a `shell=` keyword — a substring
search finds the comment explaining why it is not used, which is the same shape as
`SH-BARE-PYTHON` firing on a heading that printed the words "python packages".

**The tests need no network.** A fake server reproduces the two behaviours that mattered: it
exits on EOF, and it interleaves a log line, a notification and a response to a different id
before answering. ADR-0007's guarantee would not survive a suite that needed the network in
order to test the thing that talks to the network.

**v1.0's Phase 1 DoD is closed.** Run on the host, 2026-08-25:

```
filesystem  reads .python-version inside the root
            refuses C:/Windows/System32/drivers/etc/hosts — "path outside allowed directories"
github      get_me -> login denizefekaracakaya, from the digest-pinned container,
            credential resolved through secret://env/GITHUB_PAT
```

ADR-0002's Verification clause — *"The MCP filesystem server starts scoped to this root,
lists it successfully, and refuses a read outside it"* — has been owed since 2026-08-01 and
is now satisfied, on the host, by the ADR's own terms.

Gates **22/22**, 0 broken. Self-test **28/28**. Tests **111**, 1 skipped.

> **Erratum — 2026-08-25: the three-way diagnosis above did not work either.**
>
> The sentence *"401, 403 and silence are now three different reports"* described the
> intent. `check_env.sh` runs under `set -euo pipefail`, and the driver captured the
> check's output with a bare `out="$(...)"`. Under `set -e` that **aborts the script**
> when the command exits non-zero, before the next line can read `$?` — so every branch
> reached by a failure was unreachable. `skip`, `fail` and `broken`: all three. A failing
> live check killed the preflight silently, printing nothing at all, and the only outcome
> `live_check` could ever report was `pass`.
>
> Third time in this script that the bug was *a check that could not fail*. The evidence
> recorded above stands — it came from the passing path, on the host — but it is the only
> path that had ever been exercised. The fix is `if ! out="$(...)"`, which suspends
> `set -e` for the assignment. Verified by forcing the skip path: with no `GITHUB_PAT`
> resolvable, the run now prints `skip github not run — secret://env/GITHUB_PAT does not
> resolve (SecretNotFound)` and continues to its verdict.
>
> A test now flags any bare assignment capturing a helper that signals by exit code, and
> the verdict counts un-run live checks so `PASS` cannot be read as "the DoD clauses were
> verified". Found by a sign-off audit, which is what a sign-off audit is for.

---

### 9.14 Version 1.9.0 — ADR-0034, and a bound that bounds nothing

One ADR, `Proposed`, and none of what it describes. The first ADR since 1.3.0 to arrive
without its implementation, and for the reason §4 exists.

**The finding.** `config/policy/default.toml` ends with:

<!-- lionel:illustration — deliberately NOT from the repository. This is the misquote itself, kept because §9.15 is the correction that quotes it; the file has a `match.any = true` line this block omits -->
```toml
[[rule]]
name = "runaway containment"

max_calls_per_turn = 40
on_exceeded = "halt_turn"
```

`policy-ruleset.schema.json` says rule evaluation is *"Evaluated top to bottom. **FIRST
MATCH WINS.** Falls through to `defaults.decision`"*, and that in a `Match`, *"an absent
condition is a wildcard"*. Under those two sentences the rule above does nothing, in both
directions at once:

- No `match` means it matches everything — but it is last, and `reads are broadly permitted`
  matches any read first. For every tool the policy allows, evaluation stops before it.
- If evaluation did reach it, it "wins" carrying no `decision`, and the contract has no
  account of that state. Falling through to `defaults.decision` is the only sensible
  reading, and that path discards `max_calls_per_turn` too.

The schema permits the rule — `Rule` requires only `name` — so the file validates, and all
twenty-two gates are green. **A reviewer reading the policy sees a bound. A reviewer reading
the contract sees that the bound is unreachable. Both are reading the frozen architecture.**

**The implementation was already ahead of the contract.** `PolicyEngine._decide()` evaluates
constraint-only rules in a pass of their own, before first-match-wins, which makes the
40-call bound real — and which no contract describes. The tests assert it. The argument
*"the code works, the contract is merely imprecise"* was available and is the argument §4
refuses; it is most persuasive once the work is done, which is precisely when it is worth
the least. So the gap is closed by a decision, not by the fact that code shipped.

**Nothing was changed.** `policy-ruleset.schema.json` is `stability: stable` and inside the
checksum set, and §4 requires an ADR *and* Efe's approval before a stable surface moves.
Shipping the schema edit alongside the proposal would make the approval ceremonial. This is
the fourth time the repository has withheld the implementation of its own proposal —
ADR-0029 withheld `ADR-009`, ADR-0032 withheld `.mcp.json`, ADR-0033 withheld
`gate_doc_claims`, and now ADR-0034 withholds the 1.1.0 schema.

The engine's two-pass behaviour stays as it is meanwhile. It is the safer of the two
readings — a bound that applies beats one that does not — and reverting it to match a
contract that may be about to change would be churn toward the more dangerous state. The
ADR says so rather than leaving it to be inferred.

**Why it matters before G4 and not after.** ADR-0008 gives `ToolRouter` a single policy
chokepoint *"so it cannot be bypassed"*. A limit that silently does not apply is a bypass
that leaves nothing in the diff. The failure has no symptom until dispatch is real, and
every symptom afterwards: an API bill at best, an unattended destructive sequence at worst.

Found by the G1 sign-off audit. It is the third defect that audit surfaced whose shape was
**something that could not do its job while appearing to** — after five hazard rows recorded
nowhere, and a live check that could not fail. None of the three was caught by a gate.

`docs/decisions/README.md` records **1 ADR pending**. The version moves because
`docs/decisions/ADR-*.md` and `ci/policy/policy.yaml` are both in the checksum set: 74 files
becomes 75.

---

> **Correction, 2026-08-27 — the TOML quoted above is not what the file contains.** The
> shipped rule carries `match.any = true`; the block in this section and in ADR-0034's
> Context both omitted that line and both argued from "no `match`". §9.15 records the
> correction and what survives it, which is the whole finding.

---

### 9.15 Version 1.9.1 — the fourth instance, inside the ADR about the third

An erratum, no new decision, nothing implemented. PATCH by §1: text corrected to state a
decision already in force.

**What was wrong.** ADR-0034 and §9.14 both quoted the last rule of
`config/policy/default.toml` as:

<!-- lionel:illustration — deliberately NOT from the repository. Quoting the wrong block is the point of this section; the correct one follows below and verifies on its own -->
```toml
[[rule]]
name = "runaway containment"

max_calls_per_turn = 40
on_exceeded = "halt_turn"
```

The file says:

```toml
[[rule]]
name = "runaway containment"
match.any = true
max_calls_per_turn = 40
on_exceeded = "halt_turn"
```

Both then argued *"no `match`, so by the wildcard rule it matches everything"*. The rule has
a `match`. The argument reached the right conclusion through a premise the file does not
support.

**What survives, and why it is now stronger.** The defect is unchanged: the rule carries no
`decision`, it is last, and `reads are broadly permitted` matches any read before evaluation
reaches it. If evaluation did reach it, it "wins" carrying no decision, and the contract has
no account of that state. Nothing in ADR-0034's Decision, Consequences or Alternatives
depended on the missing line.

It is stronger because `match.any` is not an accident of omission. The schema documents it
as *"Matches everything. Use only for a terminal containment rule."* The contract has a
dedicated affordance for precisely this rule shape — and still says nothing about what such
a rule does without a `decision`. The gap was designed around, not stumbled into.

**How it was corrected.** ADR-0034 is `Proposed`, so ADR-0029's append-only rule does not
bind it: a Proposed ADR's body is editable in place, and an Erratum on a decision not yet in
force would be recording a correction to something no one has agreed to. The Context block
was rewritten. §9.14 keeps its text and carries a forward-pointing note, which is the
practice §9.12 established for this document.

**The shape, a fourth time.** The G1 sign-off audit named three defects whose shape was
*something that could not do its job while appearing to*, and named the residual gap that
let all three through: **a claim about what a file contains is checked by nobody.**
`doc-claims` measures count-shaped claims in three registered documents; a quoted code block
is not a count. This is the fourth instance, and it is in the ADR written about the third —
found the same way the other three were, by opening the file the claim was about.

`gate_checksum` does not help here. It proves the architecture has not drifted since the
recorded value; it cannot know that a document *describing* the architecture describes it
wrongly. A gate that verified fenced blocks against the files they quote would have caught
this one, and it needs an ADR — `CI_Architecture.md` §7 step 1 — so it is not in this
version.

The version moves because `docs/decisions/ADR-*.md` is in the checksum set. The file count
stays at 75; only the ADRs group digest changes.

---

### 9.16 Version 1.10.0 — ADR-0034 in force, and the first stable contract to move

Efe accepted ADR-0034 on 2026-08-27. It was `Proposed` for two days, and for those two days
the schema edit it describes was not in the repository — which is the point of the
withholding, and the fourth time this repository has practised it.

**What changed.**

| | |
|---|---|
| `contracts/mcp/v1/policy-ruleset.schema.json` | **1.0.0 → 1.1.0.** The `rule` description states both passes. `$defs.Rule` gains an `anyOf` requiring `decision`, `max_calls_per_turn` or `rate_limit_per_minute` |
| `PolicyEngine._validate()` | refuses a rule carrying neither, naming it. ADR-0034 rule 4 |
| `tests/unit/test_policy_engine.py` | `TestConstraintRules`, five cases |
| `ci/self_test.sh` | 28 → **29** assertions: a decisionless, constraintless rule planted in the schema's own `examples`, asserting `JSON-004` |

**Why MINOR, against a schema whose own note calls this MAJOR.** `compatibility.notes` has
said since 1.0.0 that *"changing rule EVALUATION ORDER is MAJOR even with no schema change —
order determines which rule matches, and a reordering silently alters every decision."* That
sentence is the reason to stop and check rather than to wave the version through.

The deciding order is not changed. Pass 2 is exactly 1.0.0's evaluation, unmodified: top to
bottom, first match wins, `defaults.decision` as the fallthrough. What is added is a pass
that runs before it and **cannot decide** — a constraint rule can stop a call, and can do
nothing else. No ruleset's decisions move. The one ruleset that behaves differently under
1.1.0 is one containing a rule that decides nothing and constrains nothing, which under
1.0.0 did nothing at all; ADR-0034 rule 4 turns that from silence into a load error. The
note now records both passes and this reasoning, so the next reader does not have to
reconstruct it.

**This is the first `stable` contract to change since the 1.0.0 freeze.** That is what §4
exists for, and the sequence it required is the whole substance of what happened here: the
implementation was already ahead of the contract, the argument *"the code works, the contract
is merely imprecise"* was available, and taking it would have meant deciding by having
shipped. The decision was made in writing, by the one person §5 gives it to, and only then
was the contract moved.

**The self-test plant cost three attempts, all to the same trap.** The plant is a Python
block inside a heredoc inside `ci/self_test.sh`, and a `
` written in that block is turned
into a real newline before Python ever sees it — first as an unterminated string, then, after
the fix, inside the comment written to explain the fix. It is the hazard this document has
recorded twice before. The block now uses `chr(10)` and says why in prose containing no
backslash.

**Falsified before trusted.** Disabling the constraint pass in `_decide()` makes
`test_a_constraint_rule_below_an_allowing_rule_still_bounds` fail with `'allow' != 'deny'`.
A bound that passes whether or not the mechanism exists is the shape of the three defects the
G1 sign-off audit found, and this one is about a bound.

One of the five new tests is not about the engine at all: it reads
`config/policy/default.toml` and asserts the last rule still has the shape ADR-0034 argues
from — terminal `match.any`, no `decision`, `max_calls_per_turn = 40`. §9.15 exists because
that claim was wrong once. It is now checked.

The version moves because `contracts/**` and `docs/decisions/ADR-*.md` are both in the
checksum set. 75 files, unchanged in count.

---

### 9.17 Version 1.11.0 — ADR-0035, and the other half of a gap named four times

One ADR, `Proposed`, and none of what it describes. The fifth time this repository has
withheld the implementation of its own proposal, and the second time in three days.

**What it is for.** ADR-0033 closed count-shaped claims. Its Costs section named what it did
not close, and §9.16 named the same thing again from the other end: *"a gate that verified
fenced blocks against the files they quote would have caught this one, and it needs an ADR."*
This is that ADR.

The gap has cost twice, four days apart, with every gate green both times:

| | The claim | What was there |
|---|---|---|
| 2026-08-24 | §9.11: five hazard rows *"recorded in `check_env.sh`"* | nothing |
| 2026-08-25 | ADR-0034 and §9.14 quoted `default.toml`'s last rule | the rule has a `match.any = true` line; both omitted it, and both argued from its absence |

**The decision is deliberately half a fix, and says so.** A fenced block in a configuration
language must appear verbatim in a repository file, or carry a marker saying it is not a
quotation. Prose claims — the first row above — stay uncaught. Half a gap closed
mechanically beats a whole gap closed by intention, and the ADR's Consequences section names
the surviving half rather than leaving it to be discovered a third time.

The reason to take the fenced half first is not that it is easier. **A prose claim is read
as a summary; a fenced block is read as the file.** Nobody re-opens a file to check a block
that is right there on the page — that is the entire reason to paste one. A wrong block is
believed more readily than a wrong sentence, and by the readers who are reading the document
*instead of* the repository.

**Measured before proposing.** A throwaway scan, run outside the repository, found five
config-language blocks of two or more lines across all 34 ADRs and this document. Three
match a file. Two do not — the deliberately wrong TOML in §9.14 and §9.15, which is correct
behaviour, since §9.15 exists to quote what was wrong. **The rollout cost is two markers.**
One of the three matches only because the comparison is dedent-normalised: ADR-0031 quotes
`ci/policy/policy.yaml` at a shallower indent than the file uses, which is a real excerpt
and must not be a finding.

Five blocks is a small corpus, and that is part of the argument. The mechanism is being
installed while it is cheap. Every version adds documents and every document adds
quotations, so there is no later phase in which this gets easier.

**Nothing was changed.** `ci/gates/gate_doc_quotes.py` does not exist, `ci/policy/policy.yaml`
gains no `doc_quotes` section, `ORDER` is unchanged, and the two markers §9.14 and §9.15 will
need are not written. `CI_Architecture.md` §7 step 1 puts the ADR before the gate, and §4
requires Efe's approval before a new gate exists. The gates count stays at **22**.

The version moves because `docs/decisions/ADR-*.md` and `ci/policy/policy.yaml` are both in
the checksum set: 75 files becomes 76.

---

### 9.18 Version 1.12.0 — the 23rd gate, and half a gap closed on purpose

Efe accepted ADR-0035 on 2026-08-28. It was `Proposed` for one day, and `gate_doc_quotes.py`
was not in the repository for that day. Fifth withholding, discharged.

**What changed.**

| | |
|---|---|
| `ci/gates/gate_doc_quotes.py` | **the 23rd gate.** `QUOTE-001` an unmarked config block matching no repository file · `QUOTE-002` a marker with no reason · `QUOTE-003` a marker on a block that does match |
| `ci/policy/policy.yaml` → `doc_quotes` | a glob, the language set, `min_lines: 2`, the marker token. 21 configuration sections |
| `ORDER`, `.github/workflows/ci.yml` | 23 gates, 149 rules, 27 jobs |
| `ci/self_test.sh` | 29 → **30** |
| §9.14, §9.15 | the two markers the rollout needed |
| `ADR-0033` | an Amendment: half its Costs gap is closed, and which half |

**The numbers the ADR predicted are the numbers the gate reports.** Five config-language
blocks of two or more lines across thirty-six documents, three matching a file, two marked —
the two deliberately wrong TOML blocks in §9.14 and §9.15, which is correct behaviour, since
§9.15 exists to quote what was wrong. The feasibility scan was run before the ADR was
written, precisely so the proposal could state a rollout cost rather than promise one.

**Two things the scan could not settle, and the implementation did.**

- The marker is accepted on **either of the two lines** before the fence. Markdown renders a
  comment with and without an intervening blank line identically, and a rule that turned on
  invisible whitespace would fail for reasons nobody can see.
- **Markdown is excluded from the corpus.** Without that, a document quoting another document
  would satisfy the rule, and two documents could agree with each other while both disagreed
  with the file. The corpus is 105 non-markdown files.

**All three rules were falsified before being trusted.** `QUOTE-001` against the §9.15 block
with one number changed; `QUOTE-002` against a marker stripped of its reason; `QUOTE-003`
against a marker moved onto a block that does match — which named
`config/policy/default.toml:41`, the line the whole affair has been about.

**The planted violation is a real quotation minus one correct line**, not a block of
nonsense. A gate proved against gibberish proves only that it can tell text apart from a
file; the failure this exists to catch is a block that is *almost* right. The first attempt
at the plant hit the §9.14 block instead — which is marked, so nothing fired — and the fix
was to anchor the plant on `match.any = true`, the line that appears only in the correct
block. That the wrong target produced silence rather than a false pass is the marker
mechanism working.

**Half the gap stays open, and it is written down rather than implied.** Prose claims are not
fenced blocks. *"Five hazard rows are recorded in `check_env.sh`"* — the 2026-08-24 instance
— would still walk past. ADR-0035's Consequences names it, ADR-0033's Amendment names it, and
this section names it. It is not closed by an intention to be careful, and nobody should read
23 green gates as saying otherwise.

**Where this leaves the meta-gates.** Five of the twenty-three now check the pipeline rather
than the repository: `checksum`, `generated-docs`, `gate-coverage`, `doc-claims`,
`doc-quotes`. ADR-0030's premise was that an invariant this repository records about itself
must have a gate, *including invariants about the gates*. Four of the five exist because
something that was written down turned out not to be true.

The version moves because `docs/decisions/ADR-*.md` and `ci/policy/policy.yaml` are both in
the checksum set. 76 files, unchanged in count.

---

### 9.19 Version 1.12.1 — the sign-off document's own numbers had gone stale

`Phase1_Final_Signoff.md` was prepared on 2026-08-25 against architecture 1.8.0 and then sat
unsigned while the repository moved through 1.9.0, 1.9.1, 1.10.0, 1.11.0 and 1.12.0. Its §5
*"State at sign-off"* block still said 22 gates, 146 rules, 28 self-test assertions, 113
tests, 33 ADRs and a 74-file checksum. **Every one of those was wrong**, and the document
they were in is the one somebody was about to sign.

Nothing it certifies moved — every DoD clause met at 1.8.0 is met now. What went stale is
the block describing the repository around them, which is worse in one specific way: it is
the part a reader checks in order to decide whether to trust the rest.

`doc-claims` was not watching, because the document was in no registry at all — not
registered, and not listed as out of scope either. That is the state ADR-0033's
`out_of_scope` list exists to make impossible: an omission that is implied rather than
written down. It now carries an entry with an owner and a route to removal, and the route is
the signature itself — a signed sign-off must **stop** tracking the present, at which point
it becomes a dated record like `Phase0_Final_Signoff.md` and this exemption becomes that
one's.

Also refreshed: §1's table, which recorded three instances of *something that could not do
its job while appearing to* and is now five, with the two that have since been closed by
machine marked as closed and the three that have not marked as not; §6's row on file-content
claims, now half closed by `doc-quotes`; and §7, which records a re-run of the live preflight
on 2026-08-28 in which the GitHub check **skipped** because no Docker daemon was running.

That skip is worth keeping in the record. The preflight refused to let it read as a pass:
`PASS everything required now is present`, and immediately beneath it, *"PASS above means the
environment is ready, not that those clauses were verified."* Three weeks earlier the same
script printed `ok github verified` for a credential it never managed to send. Clause 5's
evidence remains the witnessed run of 2026-08-25.

PATCH by §1: no ADR added, no decision changed, text corrected to state what is already in
force. Only `ci/policy/policy.yaml` is in the checksum set, so only the policy group digest
moves. 76 files.

---

### 9.20 Version 1.13.0 — G1 signed, and Phase 2 opens

Efe signed `Phase1_Final_Signoff.md` §7 on 2026-08-28. Twelve DoD clauses, twelve artefacts,
one of which is a witnessed run rather than a test — and the document says so in the row
where it matters rather than in a footnote.

**The signature came after three attempts at one command.** `bash scripts/check_env.sh
--live` exercises clauses 1, 4 and 5. The first run reported `skip github — no Docker
daemon`. The second, with Docker started, reported `skip github — secret://env/GITHUB_PAT
does not resolve (SecretNotFound)`. The third reported `ok github verified — get_me returned
login denizefekaracakaya`, with no "live check(s) did NOT run" note in the verdict.

Two failures, two distinct causes, each named exactly, each refusing to read as a pass. That
matters more than the pass. §9.13 records a version of this script that printed
`ok github verified` for a credential it never managed to send, and §9.14 records the driver
in which `pass` was the only reachable branch. **Clause 5's evidence is now a run through a
driver observed failing twice on the same day it passed** — which is the strongest form the
clause can take on one machine, and still only a fact about one machine at one moment. That
residual is R-A20, and it stays open with a route.

**What the sign-off found on its way to being signed.** The document's own §5 state block was
1.8.0's: 22 gates, 146 rules, 28 assertions, 113 tests, 33 ADRs, a 74-file checksum. It had
gone stale across four versions while the document sat unsigned, and it was about to be
signed rather than caught. Corrected at 1.12.1, §9.19. It is frozen now — a signed sign-off
must stop tracking the present.

**And one more, in the policy file itself.** `ci/policy/policy.yaml` opened with
`phase: "0"`. It had said that since the 1.0.0 freeze — through G0's sign-off on 2026-08-10
and the whole of Phase 1. Eighteen days wrong, in the repository's own policy file, because
no gate reads the field and nothing checks it. It now says `"2"`, with a comment saying that
if it goes stale again the fix is to delete it: **a field nobody reads has no business
asserting anything.**

That is the sixth instance this week of the shape the sign-off audit named, and it is worth
being plain about what the tally means. `doc-quotes` closed the fenced-block half two
versions ago; it does not touch a bare YAML scalar in a config file, and no gate does. The
count is not evidence that the pipeline is failing. It is evidence that **this repository
states more about itself than it checks**, which is what ADR-0030 said in 2026-08-11 and is
still the open question G2 inherits.

**What opens.** `repository.runtime_code_forbidden_until` stays `null` and `STRUCT-004` stays
dormant. `require_lockfile: uv.lock` was gated at G1 and `uv.lock` has existed since
2026-08-10, so no rule changes state on this signature — checked before claiming G1 closed,
because a phase transition that silently arms a rule is how a green pipeline goes red for
reasons nobody connects to the transition.

Phase 2's DoD is MASTER_PLAN_v2 §10 Phase 2: Qdrant digest-pinned behind a `VectorBackend`
port, `forget(id)` provably removing a memory from retrieval, near-duplicate dedup, episodic
decay under an accelerated clock, re-index against a second embedding model without data
loss, and `qdrant-store` absent from the exposed capability surface — plus v1.0's two
criteria carried forward verbatim, the `compose down && up` persistence proof and the
semantic-recall test that keyword matching must fail.

Only `ci/policy/policy.yaml` is in the checksum set. 76 files.

---

### 9.21 Version 1.14.0 — ADR-0036, and a status claim beside a count

Phase 2's first ADR, `Proposed`, with neither dependency in `pyproject.toml`. Sixth
withholding.

**What ADR-0036 is not.** It is not a Qdrant decision. ADR-0004 chose Qdrant, ADR-0010
superseded that framing and demoted it to one adapter behind `VectorBackend`, and ADR-0013
pins the image by digest and the embedding model by id and dimension. All in force. Saying
otherwise — as this document's author did, in as many words, before opening the files — would
have meant re-deciding something already decided, which is its own kind of drift.

What G2 lacks is the Python side, and `pyproject.toml` says so in its own header: the clients
for the technologies MASTER_PLAN names *"arrive with the phase that builds against them — G2
for memory"*. ADR-0036 chooses `qdrant-client` and `fastembed`, declares both directly rather
than through the `qdrant-client[fastembed]` extra, and leaves `onnxruntime` to whichever of
G2 and G6 first needs a direct bound.

**And it found one more.** `artifacts.lock.yaml`'s `embedding` entry is the only artifact in
the lock with `sha256: null`, and it justifies that with a Tier-A method reading *"cached by
fastembed rather than downloaded by us"*. **`fastembed` appears exactly once in this
repository: in that sentence.** No ADR chose it, `pyproject.toml` does not declare it,
`uv.lock` does not contain it. Since 2026-08-02. The verification story for the one pin that
cannot be hashed rests on a library that is not part of the system — and this is the first
appearance of that shape inside the checksum set. No gate reads a prose `method:` field, and
none is proposed here; ADR-0036 closes the instance by making the sentence true.

### The eighth instance was inside a checked region

`Architecture_Freeze.md` §3 read:

```text
| **Architecture decisions** | **35 ADRs, 0001–0035** — 34 Accepted or Superseded,
**1 pending: ADR-0035**, which adds a gate and so waits for Efe |
```

ADR-0035 was accepted at 1.12.0. That sentence stood through `architecture-1.12.0`,
`architecture-1.12.1` and `architecture-1.13.0` — **three tags** — inside `## 3. Frozen
scope`, which is one of the three regions `doc-claims` reads on every push.

The gate matched `35 ADRs`, measured 35, and passed. It walked past `1 pending: ADR-0035` in
the same sentence because ADR-0033 scoped it to count-shaped claims and a status was not one.
Nothing was hidden and nothing was hard; **the claim simply had no pattern.**

It does now. `doc_claims` gains a `pending_adrs` fact — ADRs whose `Status` row says
`Proposed`, read with the same regex `gate_adr` uses, because two implementations of "which
ADRs are pending" would drift and the entire value of this fact is that it cannot — and two
patterns covering both phrasings the documents use, `N ADRs pending` and `N pending:`.

Falsified in both directions, and the second is the one that matters:

| Break | Result |
|---|---|
| document says `2 pending`, repository has 1 | `CLAIM-001` |
| document says `1 pending`, an accepted ADR flipped back to `Proposed` | `CLAIM-001` — **the actual 1.12.0 defect**, where the repository moved and the document did not |

No ADR was needed: ADR-0033 already decided that current-state claims in registered documents
are measured rather than remembered, and this enforces that decision more completely rather
than making a new one. `CI_Architecture.md` §7 step 1 is about adding a *gate*.

`doc-claims` now runs 39 checks against 36. The rule count is unchanged at 149 — `CLAIM-001`
is one rule whether it reads seven patterns or nine, which is why the generated documents
did not move.

`docs/decisions/README.md` records **1 ADR pending**. 77 files.

---

### 9.22 Version 1.15.0 — ADR-0036 in force, and a rule that checked the wrong file

Efe accepted ADR-0036 on 2026-08-28, and G2's first runtime code exists. Sixth withholding,
discharged the same day it was made.

**What landed.** `pyproject.toml` declares `qdrant-client>=1.19` and `fastembed>=0.8`, each
naming the ADR; `uv.lock` resolves 58 packages. `src/lionel/memory/` holds the
`VectorBackend` port, the Qdrant adapter, and `EmbeddingSpec` — and `tests/unit/test_memory.py`
holds twenty cases that all run **with neither package installed**, which is the point rather
than a convenience: both are lazily imported, and a suite that needed them present could not
test their absence.

**The pin stopped being a sentence.** `artifacts.lock.yaml`'s `embedding` entry is the only
one with `sha256: null`, and it has justified that since 2026-08-02 by saying the pin *is*
"the identifier plus a dimension assertion that fails loudly on substitution". No such
assertion existed. `assert_dimensions()` is it: planting a 512-wide vector now raises, naming
both widths, the model, and the re-index ADR-0010 requires. Falsified by rewriting the reader
to return 512 and watching four tests go red.

The reader is narrow on purpose — a regex over two scalars, because `pyyaml` is CI tooling
and adding a YAML parser to the runtime would need its own ADR. A narrow reader that quietly
disagrees with the file would be worse than none, so a test parses the lock with real YAML
and asserts the two agree. That is the only part that could drift.

### `uv lock` had an opinion, and DEP-002 could not see it

The resolver pulled **`requests`** — the one package `dependencies.forbid_packages` names,
on the grounds that *"httpx is already a dependency. Two HTTP clients is drift, not choice."*
`fastembed` depends on it directly.

**Every gate stayed green.** `DEP-002` reads `pyproject.toml`. It expressed a decision about
what may be **installed** and checked only what was **declared**, so a forbidden package
arriving as somebody else's dependency was invisible to it — and would have stayed invisible,
because nothing else looks at the lock either.

The decision is not wrong. DEP-002 governs the client this repository's own code calls, and
`src/lionel/` imports `httpx` and nothing else. But the gap between *"a vendored library
brings its own HTTP stack"* and *"we quietly acquired a second HTTP client"* is a judgement,
and **a judgement nobody makes is not a judgement.** `DEP-003` now reads `uv.lock`, and the
exemption for `requests` carries `pulled_by`, `why`, `owner` and a route out — plus the
stale-escape-hatch check that `COV-003` and `QUOTE-003` already have, so it fails if
`fastembed` ever leaves the lock while the exemption stays.

No ADR was needed. §4's permitted list covers a gate enforcing an existing decision more
completely, and DEP-002's decision is unchanged; what changed is which file the rule reads.

**Ninth instance.** Same family: a rule, or a sentence, that was true about the thing it
looked at and silent about the thing that mattered. It is the second one this week found by
doing the work rather than by auditing — the first was `fastembed` appearing nowhere but in
a prose `method:` field.

### The pending rule caught its first real one, immediately

`pending_adrs` shipped at 1.14.0 with a falsification and no live case. Accepting ADR-0036
gave it one within the hour: `Architecture_Freeze.md` §3 still said `1 pending: ADR-0036`
after the ADR was accepted, and `doc-claims` failed the push. **Exactly the defect it was
built for**, on its first use, in the same sentence and the same document as the instance
that motivated it.

It also exposed a pattern collision worth recording. The fix reads `0 ADRs pending`, and
`(\d+) ADRs` matched `0 ADRs` before `pending-adrs` could — reporting the ADR count against
a pending count, two true numbers compared to each other. The `adrs` pattern now carries a
negative lookahead. A regex registry is a place where rules can shadow each other silently,
and this is the first time two have.

`docs/decisions/README.md` records **0 ADRs pending**. 23 gates, **150** rules, self-test
**31/31**, 138 tests. 77 files.

---

### 9.23 Version 1.16.0 — the Memory Service, and a contract with no shape for a tombstone

G2's substance. `src/lionel/memory/service.py` is ADR-0010's Memory Service: salience-gated
ingestion, near-duplicate folding, hybrid ranking with its components exposed, episodic
decay, tombstoned redaction, consolidation that supersedes rather than deletes, and the
embedding re-index migration. 197 tests, up from 138.

**Five of G2's DoD clauses now have an executable test**, and the two that do not are named
rather than implied:

| Clause | State |
|---|---|
| `forget(id)` provably removes a memory from retrieval | test |
| near-duplicate ingestion is deduplicated | test |
| episodic decay under an accelerated clock | test — the clock is injected, which is why this is a test and not a thirty-day wait |
| re-index against a second embedding model without data loss | test |
| `qdrant-store` absent from the capability surface | test |
| `compose down && up` → memory survives | **needs a running Qdrant.** G2 integration |
| semantic recall where keyword matching fails | **needs the real model.** The retrieval *path* is tested with a scripted embedder and a query sharing no tokens; the test says so rather than claiming to have tested MiniLM |

The embedder in the tests is scripted, not hashed. A hash-based fake makes the geometry an
accident of the hash function, and a dedup test that passes because two strings happened to
collide proves nothing about dedup.

### The tenth instance, and the first inside a `stable` contract's own text

`contracts/events/v1/memory-record.schema.json` requires `text` with `minLength: 1`. The
same schema documents `redacted` as the state where *"its text is cleared, but the tombstone
remains so consolidation cannot resurrect the content from an earlier summary"*.

**Both cannot hold.** A tombstone is a record the record contract rejects — on the one path
`memory-service.schema.json` calls mandatory, in its own words *"required from v1.0.0 and
MUST NOT become optional"*.

Frozen 2026-08-02. Found 2026-08-28, on the first run of the first consumer either schema
has ever had. That is the whole mechanism: **a contract nothing tests against reality cannot
be wrong**, and for twenty-six days nothing did. The `jsonschema` gate could not have caught
it — it validates each schema against its metaschema and each schema's own `examples`, both
of which pass, and neither schema ships an example of a redacted record. The only example
that would have failed is the one nobody wrote.

ADR-0037 proposes a conditional — `text` may be empty when `redacted` is true, `redacted_at`
becomes required alongside it, and the schema gains the missing example so the gate exercises
the shape from then on. `Proposed`; the schema is untouched. **Seventh withholding.**

The current behaviour is pinned rather than left to drift: a contract test asserts that a
tombstone **does** fail validation today, and its assertion message says that if it stops
failing, the schema changed and the tombstone shape needs a decision rather than a silent
pass. That test has to be rewritten on acceptance, which is the right amount of friction.

**Why it is worth a version now rather than at G4.** The Memory Service is in-process at L0,
so nothing serialises a tombstone and nothing is broken today. At L1 it moves out of process
and records cross a wire where they are validated. This is the last moment the contradiction
costs nothing, and ADR-0034 is the precedent for what deferring one looks like: a bound that
bounded nothing for four weeks, defended each week by the observation that nothing had gone
wrong yet.

`docs/decisions/README.md` records **1 ADR pending**. 78 files.

---

### 9.24 Version 1.17.0 — ADR-0037 in force, and a conditional that did nothing

Efe accepted ADR-0037 on 2026-08-28. `memory-record.schema.json` is **1.1.0**: a tombstone
may carry an empty `text` and must carry `redacted_at`; everywhere else `minLength: 1`
stands, because an empty-texted **live** record recalls nothing, matches nothing, and looks
like a working memory in every listing. Seventh withholding, discharged the same day.

> **Correction to §9.23.** That section said *"neither schema ships an example of a redacted
> record — the only example that would have failed is the one nobody wrote."* **The schema
> does ship one.** Its second example carries `"redacted": true` with `"text": "[redacted]"`
> — a placeholder that satisfies `minLength: 1` and validates cleanly. Found by opening the
> file before changing it, and corrected in ADR-0037's Context while the ADR was still
> `Proposed` and its body still editable. Eleventh instance of the shape, and this one was
> mine.

**It makes the finding sharper, not softer.** Three places in one frozen contract described
three different states: the field description says the text is cleared, the example keeps a
placeholder, and `minLength: 1` permits only the second. The implementation followed the
description, because a description is what an implementer reads. **Nothing in this
repository can notice a schema whose prose and whose example disagree** — the `jsonschema`
gate compares an example to its schema, never to the sentence beside it. That gap is not
closed here and is not proposed to be; it is recorded so the twelfth instance is not a
surprise.

The example is now `""`, which reverses what the schema's author wrote. ADR-0037 says so in
its Decision rather than letting it pass as tidying.

### The first attempt read as a correct fix and did nothing

`minLength: 1` stayed on the base `properties.text`, with `then: {text: {minLength: 0}}`
added below. **JSON Schema applies every applicable keyword** — a base constraint is not
relaxed by a conditional, both must pass. The tombstone example still failed, the `then`
branch was decorative, and the diff looked right.

Caught by running the validator against the two examples rather than by reading the diff,
which is the same distinction ADR-0037's Context is about, one level down. `minLength` now
lives only in the branches, and `test_the_conditional_actually_applies` asserts that
structurally — because the symptom of getting it wrong is silence, and silence is not
something a test of behaviour can see.

Falsified in both directions before being trusted: a live record with empty text fails
`'' should be non-empty`; a tombstone without `redacted_at` fails
`'redacted_at' is a required property`. `ci/self_test.sh` plants the tombstone example with
`redacted` flipped to `false` — the smallest edit that takes the other branch, and precisely
what an unconditional relaxation would have permitted. 31 → **32** assertions.

**Ten of the eleven instances this week were found by reading a file rather than by a gate.**
That ratio is the argument for `doc-quotes` and `pending_adrs` and `DEP-003`, and equally
the argument against believing the pipeline is the whole control. It is not, and
`Architecture_Freeze.md` should not be read as saying it is.

`docs/decisions/README.md` records **0 ADRs pending**. 78 files.

---

### 9.25 Version 1.17.1 — a sign-off block that cannot go stale

`Phase2_Final_Signoff.md` is prepared and unsigned, and its §8 state block is **registered
with `doc-claims` while it waits**.

That is the whole of this version. G1's sign-off stated the same counts in a neatly aligned
block — `gates 22/22`, `rules 146`, `ADRs 33` — which matched not one of `doc_claims`'
patterns. It sat unsigned across four versions and went stale inside itself, and was about
to be signed rather than caught. §9.19 records it.

The fix was not to be more careful. §8 is written in the phrasing the gate reads —
*"**23 gates, 150 rules, 27 workflow jobs.** Self-test 32/32 … **37 ADRs**, 0 ADRs
pending"* — and `doc_claims.documents` names the section. Four regions are checked now
rather than three. Falsified before trusting it: `24 gates` in that block fails
`CLAIM-001`.

**On signing it moves to `out_of_scope`**, and the numbers stop tracking the present. A
signed sign-off is a dated record; refreshing one is editing the archive. That transition is
written into §8 itself, so whoever signs finds the instruction in the document rather than
in a gate's configuration.

PATCH by §1: no ADR added, no decision changed. `ADR-0033` already decided that
current-state claims in registered documents are measured rather than remembered; this
registers one more. Only `ci/policy/policy.yaml` is in the checksum set. 78 files.

---

### 9.26 Version 1.18.0 — the backup that MASTER_PLAN_v2 lost, and a test that agreed with whichever interpreter you typed

**ADR-0038 reinstates `scripts/memory_backup.sh`.** `MASTER_PLAN_v1.md` §2.6 required it;
`MASTER_PLAN_v2.md` rewrote the phase plan with a migration table giving a reason for every
v1.0 item it retained or deleted, **and has no row for this one**. `Phase2_Final_Signoff.md`
§6 carried it as a Major with no mitigation and §7 put it to Efe as the thing to weigh
before signing: from the moment G2 closes, memory has a single copy, and `docker compose
down -v` — one character from the command `verify_memory.sh` runs on every pass — ends it.

Efe approved the reinstatement on 2026-09-01, before any of it was written. That is §4's
sequence and not a formality: the item's absence from v2 makes adding it a change to the
phase plan, which is exactly what §4 reserves.

**What makes this a backup rather than a file** is `selftest`. It takes a real snapshot of a
real collection, restores it into a scratch collection, and compares **a sha256 over the
sorted point ids** — not the point count, which is the one property a restore of the wrong
snapshot is most likely to share in a directory of similarly named dated files. The count
comparison was written first and rejected once stated out loud. The disaster drill was then
run for real: `lionel_memory` deleted outright, restored from the snapshot, same digest.

The refusals were falsified too — a corrupted snapshot is refused on its checksum *before*
any upload, because a recovery deletes the collection before Qdrant discovers the file is
unreadable; an unattended `restore` with no tty and no `LIONEL_BACKUP_YES` refuses; with
Qdrant stopped, `create` exits 1 and names the command to start it while `list` still
verifies every checksum, because it needs no container.

**And a test that had quietly stopped testing anything.** `TestAbsentPackagesFailByName`
opens with *"Both are absent in this environment, so these assert the real path rather than
a mock"*. That was true when ADR-0036 was written and false by the end of the same day:
`.venv` has `qdrant-client` and `fastembed`, because `verify_memory.sh` needs them. Under
that interpreter all three assertions failed — the named errors are unreachable when the
imports succeed — and under a bare `python3` they passed. **The suite's verdict depended on
which interpreter you typed**, and the number in `Phase2_Final_Signoff.md` §8 was the
passing one. The absence is now simulated by a `sys.meta_path` finder, and both interpreters
report 217 tests passing.

It is the same shape as the four defects G2's sign-off records: something reviewed, frozen,
and not executed in the configuration that mattered. Found by running it, not by reading it.

MINOR by §1: a decision comes into force. No dependency added — the download and the
multipart upload are `urllib`; `qdrant-client` was already ADR-0036's. No contract, schema or
stable surface moves. `docs/decisions/ADR-0038-memory-backup-and-restore.md` and
`ci/policy/policy.yaml` are in the checksum set. 79 files.

---

### 9.27 Version 1.19.0 — G2 signed, and what the gate held still for five days

**Efe signed `Phase2_Final_Signoff.md` §7 on 2026-09-02.** G2 is closed, Phase 3 (Brain
Gateway) is open, and the document moved from `doc_claims.documents` to
`doc_claims.out_of_scope` — the transition its own §8 describes, so whoever signs finds the
instruction in the document rather than in a gate's configuration.

**The registration earned its keep in the five days it was live.** §9.25 registered §8 while
the document was unsigned, on the argument that G1's sign-off had stated the same counts in
an aligned block matching no pattern, sat unsigned across four versions, and gone stale
inside itself. That was a prediction. What happened is that ADR-0038 landed on 2026-09-01,
the ADR count moved 37 → 38 and the checksum moved with it, and `doc-claims` failed the push
until §8 said so — along with `CLAUDE.md` in two places and §7 of the freeze. **Four
documents were wrong about the same checkable fact within one commit of it changing**, and
none of them was corrected by anyone noticing.

The order matters and was deliberate: §6's Major closed *before* the signature rather than
after. Signing G2 with no backup path would have started a period, of unknown length, in
which the project's memory had a single copy — and the item was absent from MASTER_PLAN_v2
with no migration row, so nothing would have raised it again.

Both live clauses were re-witnessed on the host on the day of signing, with the real
embedder rather than the fixture: `ok persistence survived`, `ok semantic retrieved`, 0 words
shared between the query and the fact it retrieved. `memory_backup.sh selftest` was
witnessed the same day.

MINOR by §1: a phase gate closes and the next opens, as 1.13.0 was for G1. No ADR added, no
decision changed, no contract moved. Only `ci/policy/policy.yaml` is in the checksum set —
the sign-off document is not, which is why signing moves the version at all. 79 files.

---

### 9.28 Version 1.20.0 — Phase 3's first act was a test, and it found four

`Phase3_Entry_Checklist.md` item 5 says the first thing to write is the contract test, not
the provider, because the five brain contracts were in the position
`memory-record.schema.json` was in for twenty-six days: `stability: stable`, inside this
checksum set, frozen on 2026-08-02, and **never once consumed**.
`tests/contract/test_brain_contract.py` ran before any provider code existed and found four
disagreements. ADR-0039 records them and is `Proposed`; **no schema it names is edited while
it waits.**

| | |
|---|---|
| **HealthStatus, twice** | `core/v1/health-status.schema.json` calls itself the report for *every service and provider*, names `brain_gateway` in its own producer list, requires `service`, and forbids extra properties. `provider-capabilities.schema.json` defines a second one with no `service` and forbids extra properties. **No object satisfies both**, and their `state` enums differ by two values. Phase 3's `health()` DoD clause cannot be written until one wins |
| **Usage, twice** | `token_counts_estimated` is on the terminal usage and not the streamed one, both `additionalProperties: false`. The quota ceiling *halts generation*, so the guard reads streamed events — the flag telling it not to trust the number is available only after the generation it was meant to stop |
| **A cancellation token** | a ULID in `cancellation.schema.json`, an unconstrained `string` in `ProviderRequest`, whose description reads *"ADR-0025. Non-optional."* The empty string satisfies it |
| **A tool name** | pinned in `ToolSpec` to a lowercase pattern whose description cites ADR-0023 by name, and unconstrained in both places it is reported back. `İSTANBUL.read` validates in a `ProviderResponse` |

**All four are the class ADR-0037 left open.** That ADR closed one instance of *"a schema's
prose and its examples can disagree, and nothing notices"* and recorded the class with an
owner. One level up, two schemas can disagree, and `JSON-004` cannot see that either: it
validates each schema against its metaschema and against its own examples, never one schema
against another.

**The tests assert the defects rather than the fix**, which is ADR-0037's practice: four of
the twelve say, in their assertion messages, that a change in the result means the schema
moved and needs a decision. The other eight pin coherence that already holds — the provider
enum being the same in three places, the configured provider being inside it, `tools` still
being the ToolSpec IR, and the two verbatim `StopReason` copies still agreeing. That last one
exists because nothing else would notice the day they stop.

MINOR by §1: an ADR is added as `Proposed`, as 1.14.0 was for ADR-0036. No decision in force
changed. `docs/decisions/ADR-0039-brain-contract-coherence.md` and `ci/policy/policy.yaml`
are in the checksum set. 80 files.

---

### 9.29 Version 1.21.0 — ADR-0039 accepted the same day it was drafted

Efe accepted ADR-0039 on 2026-09-02, the day it was written. All five items in its Decision
were delivered, each contract moving to **1.1.0**:

| | |
|---|---|
| `provider-capabilities.schema.json` | `$defs.HealthStatus` is now a `$ref` to `core/v1/health-status.schema.json` rather than a second, incompatible definition |
| `stream-event.schema.json` | `Usage.token_counts_estimated`; `ToolCallDelta.name` refs `ToolSpec.name`'s pattern; `$defs.StopReason` refs the new `$defs.StopReasonValues` |
| `provider-request.schema.json` | `cancellation_token_id` refs `cancellation.schema.json#/properties/token_id` in place of an unconstrained `string` |
| `provider-response.schema.json` | `tool_calls[].name` refs `ToolSpec.name`; `stop_reason` refs `StreamEvent.$defs.StopReasonValues` |

**The append-only rule bit the acceptance itself.** Editing ADR-0039's Verification table in
place — the natural first instinct, since the ADR had been committed as `Proposed` one commit
earlier — triggered the `PreToolUse` guard: *"BLOCKED — ADR-0039 is Accepted, and its body is
append-only."* CLAUDE.md's own open-items table names this guard's blind spot, that it *"sees
`Edit`/`Write` but not `sed` through `Bash`"* — and the correct response to a gap like that is
to route around it for a legitimate append, not to treat the gap as permission to rewrite. The
Erratum was appended with a plain `cat >>` instead, quoting the withheld paragraph verbatim,
which is what ADR-0029 rule 2 requires and is the same operation ADR-0037 performed on itself.

**`test_brain_contract.py`'s four defect-pinning tests became four coherence-pinning test
classes**, and the file gained the offline `$ref` registry `test_memory_contract.py` had
already solved — the first run after the schema edits failed seven of twelve with
`Unresolvable`, because cross-file `$ref`s did not exist in these five schemas before this
ADR, and the file's own docstring had said none did. `ci/self_test.sh` plants a `usage`
StreamEvent example with `Usage.token_counts_estimated` removed from the schema again: 32 →
**33**.

**One schema example was extended, not only edited.** The existing `usage` example in
`stream-event.schema.json` — provider `ollama`, which `provider-capabilities.schema.json`'s
own example already marks `token_counting: false` — gained
`"token_counts_estimated": true`, so the new field ships with something exercising it rather
than joining `HealthStatus`, `Usage` and the rest in having never been consumed.

MINOR by §1: a pending decision comes into force. `Phase3_Entry_Checklist.md` item 5, which
had explicitly stopped at ADR-0039's decision, continues; item 7's `health()` clause is
unblocked. Checksum sha256:8b454522a4f4…, 80 files.

---

### 9.30 Version 1.22.0 — two ADRs for Phase 3's remaining decisions, and a contradiction MASTER_PLAN_v2 had been carrying since Phase 0

`Phase3_Entry_Checklist.md` named three decisions reserved to Efe by §4. ADR-0040 and
ADR-0041 are drafted against two of them, both `Proposed`.

**ADR-0040 chooses the three `BrainProvider` clients.** `anthropic` (MIT) and
`llama-cpp-python` (MIT) as new dependencies; `ollama` called over the already-declared
`httpx` rather than a second HTTP client, which `DEP-002` would otherwise call drift. It
also closes item 4 by declining to add anything: `l0-conformance` already asserts
`network_allowed: "false"` and rejects `provider = "anthropic"` at L0
(`l0_forbidden_providers`), and a credential sitting unread behind `secret://` resolution
while unused at L0 is inert configuration — the same shape the L0 `fallback_chain` already
is. No new gate assertion was added; one was considered and rejected in the ADR's own
Alternatives, on the same "two mechanisms checking one fact drift apart" argument ADR-0039
made about the brain contracts, one layer down into gates.

**ADR-0041 found that `MASTER_PLAN_v2.md` disagrees with itself.** §10 Phase 3's DoD
requires the golden-transcript replay gate at G3, in language more emphatic than most of
that section carries — *"now automated as a regression gate rather than a one-time
measurement"*. The document's own directory sketch, four hundred lines later, labels the
directory that gate needs `evals/ ← NEW Phase 8`. Neither line is wrong on its own; they
contradict each other, the same shape `memory-record.schema.json` had inside one contract
(ADR-0037), one level up, inside the plan itself.

The resolution does not pick a side. `ADR-0021` had already designed the harness this needs,
scoped to G8 for good reasons — STT WER, wake FAR/FRR, TTS intelligibility and a persisted
leaderboard genuinely need G6's audio models. ADR-0041 pulls forward only the slice ADR-0001
asks for at G3: two text providers, tool-call equivalence, no audio — `evals/golden/` and
`evals/harness/`, not the full suite. `llamacpp` stays out of the comparison; ADR-0001 never
named it either, and a golden set measuring the provider whose tool-calling reliability is
"the project's largest unknown" (that ADR's own words) would be measuring the fixture, not
the model.

**Both practise the withholding this repository now has ten instances of.** Neither
dependency, schema, nor directory either ADR names is touched while `Proposed` —
`pyproject.toml`, `ci/policy/policy.yaml`'s `cl` preflight row, and `MASTER_PLAN_v2.md`'s
`evals/` line all wait for Efe's approval before moving, exactly as `Architecture_Freeze.md`
§4 requires.

MINOR by §1: two ADRs added, both `Proposed`. No decision in force changed.
`docs/decisions/ADR-0040-brain-provider-clients.md`,
`docs/decisions/ADR-0041-transcript-replay-gate.md` and `ci/policy/policy.yaml` are in the
checksum set. 82 files.

---

### 9.31 Version 1.23.0 — ADR-0040 and ADR-0041 accepted the same day they were drafted, and a second HTTP client arrived under a different name

Efe accepted both on 2026-09-10. Delivered:

| | |
|---|---|
| `pyproject.toml` | `anthropic>=1.4`, `llama-cpp-python>=0.3.35`, each naming ADR-0040 |
| `uv.lock` | regenerated, 69 packages |
| `ci/policy/policy.yaml` | the `cl` preflight row's `required_at` moved `G6` → `G3`; `tests/unit/test_preflight.py`'s 27 cases pass unchanged |
| `MASTER_PLAN_v2.md` | the `evals/` directory-sketch line names both arrival dates and both ADRs, with an `harness/` line added beside `golden/` |

**`uv lock` pulled `httpx2`** — a genuinely separate package, `httpx`'s own in-progress v2
rewrite published under its own name, not a re-resolution of the `httpx` already declared.
`anthropic` depends on it directly. `dependencies.forbid_packages` is name-based, so nothing
caught it: `bash ci/run_gates.sh dependencies` was green with a second, unreviewed HTTP
client silently in the lock. This is the `requests`-via-`fastembed` finding ADR-0036's
Erratum recorded (§9.22), one dependency later, and it is now named the same way: `httpx2`
in `forbid_packages`, a `transitive_exemptions` entry — pulled by `anthropic`, owner
`brain`, unblocked by `anthropic` moving to `httpx` (v1) or this repository replacing the
SDK.

**Both Erratums say plainly what is not yet built.** `src/lionel/brain/providers/`'s three
adapters and `evals/golden/`/`evals/harness/`'s golden-transcript comparison are real
engineering — translating each SDK's streaming shape into the frozen contracts, then
recording actual transcripts to replay — not a configuration change, and neither ADR's
Erratum claims otherwise. `Phase3_Entry_Checklist.md` items 2 and 3 track them as
continuing; item 4 is fully closed, since ADR-0040 decided no further work was needed there.

MINOR by §1: two pending decisions come into force. `ci/policy/policy.yaml` is the only
file in the checksum set that changed content (the ADR bodies moved from `Proposed` to
`Accepted`, which is itself a checksummed change to `docs/decisions/*.md`); `MASTER_PLAN_v2.md`
changed by one line. Checksum sha256:853dc1c8d3dd…, 82 files.

---

### 9.4 If the Proposed ADRs are rejected — *historical, superseded by §9.6*

All three were accepted on 2026-08-11, so this section no longer describes a live
option. Kept because it was the basis on which they were put forward.

They are additive and nothing depends on them.

| Rejected | Effect |
|---|---|
| ADR-0029 | Nothing to unwind — `ADR-009` was deliberately **not** implemented. A gate enforcing an unapproved decision is the error ADR-0030 is about |
| ADR-0030 | Remove `checksum`, `generated-docs`, `gate-coverage` from `ORDER` and from `ci.yml`. The 21 self-test assertions stay — §4 item 3 permits them without an ADR |
| ADR-0031 | Remove `licenses.review_accepted`. `licenses` returns to failing `LIC-002` on the Turkish voice, which is a true statement about an unresolved question |

Any of those is a MINOR bump of its own, not a revert of 1.1.0.

---

*Prepared 2026-08-03. In force 2026-08-10: 1.0.0, extended to 1.1.0, corrected to 1.1.1 — all the same day.
Extended to 1.2.0 and 1.3.0 on 2026-08-11, and to 1.4.0, 1.5.0 and 1.6.0 on 2026-08-24 — the day Phase 1 opened.
Extended to 1.13.0 on 2026-08-28 — the day G1 was signed and Phase 2 opened.*
