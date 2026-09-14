# L.I.O.N.E.L — working rules

A local-first voice assistant whose defining constraint is an **offline autonomy guarantee**
(ADR-0007). Phase 0 is complete and frozen at `architecture-1.2.0`. **G2 was signed by Efe
on 2026-09-02** — `Phase2_Final_Signoff.md` is now a dated record and out of `doc-claims`
scope, and **Phase 3 (Brain Gateway, G3) is open**. Its DoD is MASTER_PLAN_v2 §10 Phase 3,
and `Phase3_Entry_Checklist.md` separates the three clauses blocked on an ADR from the work
that is permitted without one.

**This repository is an architecture first, and runtime code second.** 41 ADRs, 27
JSON Schemas + 3 protobuf contracts, a pinned artifact lock — and a policy pipeline that
enforces them: 23 gates, 151 rules, 27 CI jobs.

---

## The four rules that will bite you

These are not style preferences. Each is enforced, and the first two are enforced by a
human, not a gate.

### 1. Never commit, push or tag without being asked

`Architecture_Freeze.md` §5: **"No autonomous commit or push — ever."** This binds an agent
exactly as it binds a person. Ask once, covering the whole chain (commit + push + tag), so
the work is not interrupted at each step.

Commits use the `[LIONEL-CORE]` prefix.

### 2. A new dependency needs an ADR and Efe's approval

`Architecture_Freeze.md` §4. Also: any new subsystem or technology, any change to a
contract's `stable` surface, the tier/trust/plane models, capability governance fields, any
**relaxation** of a gate, and the phase plan.

`pyproject.toml` declares only packages an Accepted ADR already chose, each naming its ADR
in a comment. Adding one because it is obviously needed is precisely the failure §4 exists
to prevent.

**Permitted without an ADR:** implementation under `src/lionel/` conforming to frozen
contracts · tests · gate work that enforces an *existing* decision more completely ·
regenerating generated documents · errata · artifact version bumps within an existing
artifact.

### 3. An Accepted ADR is append-only

`ADR-0029`. The `Status` line may be edited. **The body may not.** Three operations:

| | When | How |
|---|---|---|
| **Supersede** | The decision changes | New ADR; original's `Status` gets a forward link. Original text untouched |
| **Amend** | Adds scope, contradicts nothing | Append `## Amendment — YYYY-MM-DD` |
| **Erratum** | Text was wrong; the decision was always this | Append `## Erratum — YYYY-MM-DD`, **quoting the original verbatim in a blockquote** |

The quote is the mechanism, not decoration — it is the only thing separating a correction
from a rewrite. `ADR-009` checks the shape. Rule 2's quote requirement is enforced from
`adr.errata_quote_required_from` (2026-08-11); two earlier sections are grandfathered and
reported as notes on every run.

If a sentence in an Accepted ADR becomes false — **including its own `Status`** — append an
Erratum. Do not edit the sentence. (Every ADR accepted on 2026-08-11 needed exactly this.)

### 4. Changing the architecture moves the checksum

`Architecture_Freeze.md` §2 records a SHA-256 over 72 files in five groups. Touch any of
them and `gate_checksum` goes red until §2 is updated and the version bumped (§5 step 7).

**The checksum set:**

```
docs/decisions/ADR-*.md            contracts/{core,mcp,events,media}/v1/*.schema.json
contracts/grpc/v1/*.proto          contracts/MANIFEST.json
config/**/*.toml   config/*.json   ci/policy/policy.yaml
artifacts.lock.yaml                MASTER_PLAN_v2.md
```

`Architecture_Freeze.md` is **not** in the set, so recording the new value does not perturb
it — no fixed point to chase. Record it **last**.

> Line endings are part of the checksum. `.gitattributes` sets `* text=auto eol=lf`. That
> line is load-bearing: before it existed, `*.proto` was unpinned, a Windows clone got CRLF,
> and the same commit produced two different checksums for eight days.

---

## Verify before you claim anything

```bash
bash ci/run_gates.sh                    # 23/23, 0 broken
bash ci/run_gates.sh <gate>             # one gate
bash ci/self_test.sh                    # 35/35 assertions, 23/23 gates covered
python3 scripts/architecture_checksum.py --verify
python3 scripts/generate_ci_docs.py --check
bash scripts/check_env.sh               # the host, not the repository
bash scripts/verify_memory.sh           # G2's live clauses. Starts and stops Qdrant
bash scripts/memory_backup.sh selftest  # ADR-0038. Round-trips a real snapshot, live data untouched
```

Requires `pyyaml`, `jsonschema` and **`grpcio-tools`**. Without the last one the `protobuf`
gate exits **2** — a *broken gate*, not a passing repository, and the runner says so.
`check_env.sh` checks for all four and tells you which is missing before you spend an hour
reading a stack trace.

**`check_env.sh` is not a gate and never will be.** It describes the *host*, and CI is not
the host runtime (ADR-0002) — a gate red because a laptop lacks VS Build Tools is asserting
something true about the wrong computer. Its table lives in `ci/policy/policy.yaml` under
`preflight`; `tests/unit/test_preflight.py` checks the table's shape, which is the part that
*is* portable. It reaches the network only under `--live`, and says so before it does.

**Exit codes are a contract:** `0` pass · `1` policy violation (fix the repo) · `2` the gate
itself is broken (fix the gate). Never collapse 1 and 2.

---

## Phase discipline

**`STRUCT-004` was lifted at architecture 1.6.0.** G0 was signed off on 2026-08-10 and
`repository.runtime_code_forbidden_until` is now `null`, so `src/lionel/` holds runtime code.
The rule is **dormant, not deleted** — setting that value back to a gate name re-arms the
ban, which is the right move if a later phase needs a code freeze. `structure` keeps its
self-test coverage through `STRUCT-003` (`forbidden_paths`).

`ARCH-001` is unaffected and permanent.

`ARCH-001` forbids `src/lionel/capabilities/shell/` from ever existing again (ADR-0011).

**Tests run on `unittest`, not pytest.** ADR-0027 defines five layers and names no runner;
pytest would be a new dependency and needs an ADR. `python3 -m unittest discover -s tests -t .`

### Phase 1 (G1) — what exists

| Module | ADR | The G1 clause it makes executable |
|---|---|---|
| `lionel.secrets` | ADR-0015 | a `secret://` URI resolves and its value redacts in log output |
| `lionel.platform.process_supervisor` | ADR-0014 | kill-tree verified by terminating a parent — zero orphaned children |
| `lionel.capabilities` | ADR-0003, ADR-0007 | the capability registry replacing `mcp.servers.json` |
| `lionel.policy` | ADR-0012 | the Policy Engine denies an unregistered tool by default |
| `lionel.coordinators` | ADR-0008 | the five coordinators satisfy contract tests with stubs |
| `tests/contract/test_pinned_artifacts.py` | ADR-0013 | the pinned GitHub MCP image digest is verified |

**All six G1 DoD items now have an executable test.** v1.0's Phase 1 DoD, which
MASTER_PLAN_v2 carries forward in full, is executable too as of 1.7.0: `bash
scripts/check_env.sh` runs the tooling preflight table, and two of the seven Git Bash hazard
rows became `SH-BARE-PYTHON` and `SH-MSYS-DOCKER`.

**Two of its clauses need `--live`** — both need the network or a credential, so they are
opt-in; an offline default is not laziness here, it is ADR-0007. **Both passed on the host on
2026-08-25**, which closes v1.0's Phase 1 DoD in full:

| `--live` check | Evidence |
|---|---|
| filesystem refuses a read outside its root | both halves: `.python-version` reads, `C:/Windows/…/hosts` returns `isError` with *"path outside allowed directories"*. ADR-0002's Verification clause, owed since 2026-08-01 |
| `get_me` returns Efe's login | `denizefekaracakaya`, from the digest-pinned container, credential resolved through `secret://env/GITHUB_PAT` |

**The first version of that GitHub check could not have passed.** It was
`printf … | docker run -i`, which closes stdin the moment printf finishes; the server reads
EOF as a hangup and tears the session down before writing a byte. It reported *"no login"*
for every input, a valid credential included. Both handshakes now go through `MCPClient` in
`scripts/_preflight_table.py`, which holds stdin open and matches responses by id. §9.13.

The preflight's first run found the `filesystem` capability rooted at a directory that does
not exist (`Desktop/`, not `Projects/`), written identically in two config files, with every
gate green — a host fact, and nothing that runs on another machine can check one.
ADR-0002 carries the Erratum; **R-A20** carries the residual risk, which is that nothing
forces the preflight to run and nothing can.

**The seven-row Git Bash hazard table** is `ci/policy/policy.yaml` → `preflight.hazards`.
Four rows are gate rules (`SH-MSYS-DOCKER`, `SH-BARE-PYTHON`, `SH-CRLF`, `ARCH-017`), one is
executed by the preflight (`HAZ-DOCKER-BACKEND`, which asks the daemon — `docker --version`
answers about the CLI and says nothing about whether anything can be launched), and two are
`operator`. **`operator` is capped at two by a test**: it is the one label here carrying
neither an owner nor a route to removal, so it is bounded rather than trusted.

Three traps in what is already there:

- `PolicyEngine` evaluates **constraint rules** — limits with no `decision` — in a pass of
  their own, before first-match-wins. This is now the contract: ADR-0034, accepted
  2026-08-27, and `policy-ruleset.schema.json` **1.1.0**. A rule that neither decides nor
  constrains is a load error, not a rule that silently does nothing. Constraints bound; they
  never authorise, which is why an out-of-order pass is safe.
- `TrustContext.level` is recomputed from `sources` on every read rather than cached, so no
  code path can forget to lower it.
- The four stateless coordinators are **frozen dataclasses**. That is ADR-0008's
  state-ownership rule enforced by the language: caching on `self` raises rather than
  passing review.

---

## Generated documents — do not hand-edit

`CI_Inventory.md` and `Policy_Gates.md` come from `scripts/generate_ci_docs.py`. Run it after
changing any gate; `gate_generated_docs` fails otherwise.

Both documents said "regenerate rather than hand-edit" for months while no generator existed.
They drifted to 16 gates against 17, 88 rules against 127, and `l0-conformance` — the
keystone gate — absent from the rule catalogue entirely.

**Hand-written documents that assert counts are still unenforced**, and they go stale fast:
`CI_Architecture.md` §8, `Architecture_Risk_Register.md`, `Phase0_Final_Signoff.md`,
`Phase1_Entry_Checklist.md`, `Architecture_Freeze.md`. ADR-0030's Costs section records this
as an open gap. Use the `doc-claim-auditor` agent before a version bump.

---

## Adding a gate

`CI_Architecture.md` §7 — seven steps, of which step 6 is the one that gets skipped:

1. ADR first · 2. config in `ci/policy/policy.yaml` · 3. `ci/gates/gate_<name>.py` using
`_lib.Gate` · 4. add to `ORDER` in `ci/run_gates.sh` · 5. job in `.github/workflows/ci.yml` ·
6. **planted violation in `ci/self_test.sh`** · 7. regenerate the docs

`gate-coverage` now fails if step 6 is skipped. The `/add-gate` skill walks the whole thing.

Every `Finding` carries four things: what is wrong, where, **why the rule exists** (cite the
ADR), and how to fix it. A gate that prints `FAIL: rule R-014` has moved the work of
understanding onto whoever reads the log, at the least convenient moment.

---

## Platform

Windows + Git Bash is the **host runtime**, not a developer convenience (ADR-0002,
ADR-0014). Turkish is a first-class locale (ADR-0023) — `tr`, `grep -i` and `[[ = ]]` consult
`LC_CTYPE`, so shell code is where the dotted/dotless `İ`/`ı` failure lives. Python's
`str.lower()` is Unicode-based and safe.

CI covers `ubuntu-latest`, `windows-latest` (Git Bash) and `tr_TR.UTF-8`. **If the Turkish
job fails, the shell is wrong. Do not relax the locale.**

Gates must not assume a UTF-8 console: `ci/gates/_lib.py` reconfigures stdout, because
Windows defaults to cp1252 and every gate used to die in `report_and_exit` *after* passing
its checks.

---

## Known open items

| | |
|---|---|
| **Turkish TTS blocks distribution** | `tr_TR-dfki-medium` is **CC-BY-NC-SA-4.0** and is the only Turkish voice. Personal use is unaffected. Replacing it needs an ADR amending ADR-0017. Risk **R-A15**, Major |
| **ADR-0029 rule 1 has no gate** | The append-only rule is enforced by a `PreToolUse` hook, which sees `Edit`/`Write` but not `sed` through `Bash`. A guardrail, not a proof |
| **Hand-written count claims** | Narrowed, not closed. `doc-claims` (ADR-0033) checks the count-shaped claims in three registered documents; `Phase1_Entry_Checklist.md`, `Phase0_Final_Signoff.md` and `Architecture_Risk_Register.md` are out of scope with owners, and a claim in an unregistered document is still unchecked |

---

## Where things are

```
docs/decisions/          41 ADRs + README index (ARCH-016 requires the index be complete)
contracts/               27 JSON Schemas + 3 protobuf, 5 planes, MANIFEST.json
ci/gates/                23 gates + _lib.py (Finding, exit codes) + _checksum.py
ci/policy/policy.yaml    ALL thresholds, allowlists and registries
ci/run_gates.sh          ORDER is the canonical gate list
ci/self_test.sh          plants violations; proves the gates bite
scripts/                 architecture_checksum.py · generate_ci_docs.py · verify_artifacts.sh
                         check_env.sh — the host preflight, table in policy.yaml `preflight`
                         verify_memory.sh — G2's two live clauses; needs Docker
                         memory_backup.sh — create · list · restore · selftest (ADR-0038)
Phase3_Entry_Checklist.md  8 items, 1 blocking. What must be decided before G3 work starts
MASTER_PLAN_v2.md        11 gated phases, G0–G10. Phase 3 scope is §10
Architecture_Freeze.md   the frozen state, the checksum, and the change-control rules
.mcp.json                dev-tooling MCP servers (ADR-0032). Pinned, egress-declared,
                         credential-free. NOT in the checksum set; no gate may depend on it
```

Every exemption anywhere in this repo carries an **owner** and a **route to removal**. One
with neither is not an exemption; it is a silently lowered standard.
