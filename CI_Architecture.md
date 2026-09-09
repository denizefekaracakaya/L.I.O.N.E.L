# CI Architecture

**How the L.I.O.N.E.L policy pipeline is built, and why.** Phase 0 / M3.

---

## 1. The thesis

> **An architectural rule with no test is a preference.**

L.I.O.N.E.L has 33 ADRs. Without machine enforcement, every one of them survives only as
long as everyone remembers it — which in practice means until the first deadline. The
decisions that erode first are the ones that cost something today and pay off later:
offline operation, the absence of a shell capability, trust propagation. Exactly the ones
that matter most.

This pipeline exists to convert decisions into tests. It does not lint style. It enforces
architecture.

The clearest example: **ADR-0007 says a change that improves L2/L3 while breaking L0 is a
rejected change.** That sentence is worth nothing without a job that goes red. The job is
stubbed until Phase 6 — but it is *wired*, because the failure mode being defended against
is not "someone breaks L0", it is "nobody notices for a year".

---

## 2. Layer model

```
┌───────────────────────────────────────────────────────────────────────────┐
│  DECISIONS            docs/decisions/ADR-0001 … ADR-0028                   │
│                       prose; the source of authority                       │
└──────────────────────────────┬────────────────────────────────────────────┘
                               │ each ADR names a Verification gate
                               ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  POLICY               ci/policy/policy.yaml                                │
│                       thresholds · allowlists · registries · exemptions    │
│                       declarative, reviewable as a diff                    │
└──────────────────────────────┬────────────────────────────────────────────┘
                               │ read at gate startup
                               ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  GATES                ci/gates/gate_*.py            16 standalone scripts  │
│                       ci/gates/_lib.py              Finding · exit codes   │
│                       ── no gate imports another ──                        │
└──────────────────────────────┬────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ci/run_gates.sh   .github/workflows   ci/self_test.sh
     local, one or all  18 parallel jobs   proves gates bite
```

**Authority flows down, never up.** A gate never invents a rule; it enforces one an ADR
already made. When a gate and an ADR disagree, the ADR wins and the gate is the bug.

---

## 3. Five design decisions

### 3.1 Three exit codes, not two

```
0  PASS         no violations
1  VIOLATION    the repository breaks a policy — fix the repo
2  GATE_ERROR   the gate could not run     — fix the gate
```

Most pipelines collapse 1 and 2. The result is a red build that might mean "you broke
something" or might mean "the linter can't find its config", and people learn to check
which — then learn to skip checking. A gate that cannot run is **not** a passing gate and
**not** a failing repository. Separating them keeps red meaningful.

### 3.2 Gates are independent

No `needs:` between policy jobs. A dependency chain means one early failure marks fifteen
jobs "skipped", and you learn one problem per push.

The cost is duplicated setup per job. The benefit is that a contributor sees every problem
in one run, so fixing CI is one afternoon rather than five round-trips. For a pipeline that
runs on every push and is read by someone who wants to be doing something else, that trade
is not close.

### 3.3 Every finding explains itself

```
  ✗ ARCH-003  media payload key `payload_b64` in a control-plane schema
      at    contracts/mcp/v1/tool-result.schema.json:88
      why   ADR-0006: PCM must never traverse MCP. Base64 inflates by ~33% on the
            highest-volume path, and the control plane has no backpressure, no jitter
            buffer, and head-of-line blocking behind unrelated tool calls.
      fix   Move the descriptor to contracts/media/ and keep payload on the data
            plane (protobuf `bytes`).
```

Four things, always: **what** is wrong, **where**, **why the rule exists** (with the ADR),
and **how to fix it**.

A gate that prints `FAIL: rule ARCH-003` has moved the work of understanding onto whoever
reads the log, usually at the least convenient moment. Worse, a rule whose reason is
invisible looks arbitrary — and arbitrary rules get deleted by the next person who is in a
hurry. The `why` line is not documentation; it is what stops the rule from being removed.

### 3.4 Policy is data, gates are mechanism

Thresholds, allowlists, registries and exemptions live in `ci/policy/policy.yaml`. Gate
code reads them.

Same reasoning as ADR-0012 putting tool authorization in config rather than code: **a
policy you can read as a diff is a policy that gets reviewed.** Raising `max_tier_d` from 1
to 3 is a visible one-line change in a file whose whole purpose is to be scrutinised. The
same change buried in a Python conditional is invisible in review.

### 3.5 Exemptions are registered, never implicit

Three exemption mechanisms, one rule: **an owner and a route to removal, or it is not an
exemption.**

| Mechanism | Used for | Example |
|---|---|---|
| `todo.registry` | TODO markers | pattern + path glob + owner + `unblocked_by` |
| `licenses.unresolved_registry` | Unresolved licences | artifact + owner + `resolve_by` gate |
| Inline `# ci-policy: allow RULE — reason` | Shell scripts | reason is mandatory |

A blanket TODO ban gets worked around within a week; someone writes `# T-O-D-O` or drops
the marker and keeps the debt. A *registry* turns "we'll fix it later" into a dated
commitment with a name on it. The gate rejects a registry entry that lacks `owner` or
`unblocked_by`, so the escape hatch cannot itself become the loophole.

---

## 4. Anatomy of a gate

```python
from _lib import Gate, load_policy, repo_files, rel, read_text

def main():
    p = load_policy()
    g = Gate("no-latest", "Forbidden mutable image tags", ["ADR-0013"])
    ...
    g.check()                     # count what was examined
    g.fail("DOCKER-002",          # stable rule id
           "mutable tag …",       # what
           "ADR-0013: a tag is a movable pointer …",   # why
           "Resolve the digest and reference @sha256:…",  # fix
           path, line)
    g.report_and_exit()           # renders, then exits 0 or 1
```

`checks_run` is reported alongside violations, so a gate that silently examined nothing
is visible. `PASS 0 checks` is a bug, not a success — and without the counter it looks
identical to real coverage.

---

## 5. What CI does and does not do

**Does:** validate the repository. Read files, parse schemas, compile protobuf
descriptors, check structure and cross-references.

**Does not:** build containers, deploy, run L.I.O.N.E.L, or reach the network.

Every gate is offline and hermetic. That is not incidental — it is a property inherited
from ADR-0007. A pipeline that needs the network to check whether the project works
offline has a problem it cannot see.

Runtime dependencies of the *project* are irrelevant to CI: `pyyaml` for policy,
`jsonschema` for schemas, `grpcio-tools` for protobuf. Nothing else.

---

## 6. Coverage and its limits

Not every ADR has an executable test yet, and the ratio is not stated here: it was written as `19 of 28` and went stale twice over, which is the failure this section is about. `CI_Inventory.md` §2 is generated and carries the current mapping. The other 9 need running code and each names
the gate that will cover it — see [CI_Inventory.md](CI_Inventory.md) §2.

**Where the pipeline is genuinely weak, stated plainly:**

1. **Secret scanning is pattern-based.** It catches known key formats and a planted
   credential. It will not catch a novel format or a high-entropy string that is not
   shaped like a known token. A real secret-scanning service is better, and this is not a
   substitute for one.
2. **`architecture` checks structure, not semantics.** It can prove `MCPTool` has no
   `side_effect` property. It cannot prove the Policy Engine is *consulted* — that needs
   the contract tests at G4.
3. **Markdown link checking is internal-only.** External links rot silently.
4. **No gate reads git history.** A secret committed and then removed still sits in the
   history; `fetch-depth: 0` is set on the secrets job so a future history scan can be
   added without another workflow change.

Listing these is deliberate. A pipeline whose limits are undocumented gets trusted past
its actual coverage, which is worse than a smaller pipeline everyone understands.

---

## 7. Adding a gate

1. Write the ADR first. A gate with no decision behind it is someone's taste.
2. Add config to `ci/policy/policy.yaml` if it needs thresholds or an allowlist.
3. Create `ci/gates/gate_<name>.py` using `_lib.Gate`.
4. Add the name to `ORDER` in `ci/run_gates.sh`.
5. Add a job to `.github/workflows/ci.yml`.
6. **Add a planted violation to `ci/self_test.sh`.** A gate that has never rejected
   anything is unproven.
7. Update [CI_Inventory.md](CI_Inventory.md) and [Policy_Gates.md](Policy_Gates.md).

Step 6 is the one that gets skipped and the one that matters. Every gate here caught its
planted violation before this document was written; two gates had real bugs that only the
self-test surfaced.

---

## 8. Current state

```
22 pass · 0 fail · 0 broken          self-test 35/35 · gate coverage 23/23
```

Architecture 1.4.0. The `artifacts` gate was red by design through Phase 0 while one image
digest was unresolved — ADR-0013 blocks G0 until that count is zero. It is now pinned and
justified in [GHCR_Digest_Justification.md](GHCR_Digest_Justification.md).

**A red build that is red for a known, documented, owned reason is a working pipeline.**
The failure mode to fear is a green build that means nothing.

The last three gates — `checksum`, `generated-docs`, `gate-coverage` — check this pipeline
rather than the repository (ADR-0030, Accepted 2026-08-11). They exist because every defect found
verifying the 1.0.0 freeze had one shape: a rule stated in §7 of this very document, or in
`Architecture_Freeze.md`, and enforced nowhere. **Step 6 above is now a gate.**

> These counts are hand-maintained, and this document is not generated. That is the gap
> ADR-0030 explicitly does not close — see its Costs. If the numbers above disagree with
> `bash ci/run_gates.sh`, the command is right.
