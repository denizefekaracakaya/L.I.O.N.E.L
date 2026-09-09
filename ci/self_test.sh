#!/usr/bin/env bash
# ci/self_test.sh — do the gates actually catch anything?
#
# ci-policy: allow SH-STRICT — must survive non-zero exits from the gates it is
# deliberately provoking; `set -e` would abort on the first (expected) failure.
#
# A gate that passes a clean repository but would miss a real violation is decoration.
# This plants a known violation, asserts the matching gate rejects it, and restores.
# It is the only test that answers "is this pipeline load-bearing?"

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export NO_COLOR=1 PYTHONPATH="$ROOT/ci/gates"

pass=0; fail=0
declare -a RESTORE=()

# Five of the plants below go into files that ARE the architecture (Architecture_Freeze.md
# §2). Each restores itself, but "restores itself" is a claim, and this suite exists
# because claims about tests are worth less than tests. Snapshot the checksum now and
# assert it at the end: if any plant survives, the number moves.
arch_checksum() { python3 scripts/architecture_checksum.py 2>/dev/null | grep -oE 'sha256:[0-9a-f]{64}' | head -1; }
CHECKSUM_BEFORE="$(arch_checksum)"
cleanup() { for c in "${RESTORE[@]}"; do eval "$c"; done; }
trap cleanup EXIT

# plant_in <path> — back a file up byte-exactly before planting in it, and register the
# restore. Use for any file that must come back unchanged, and ALWAYS for the five paths
# inside the architecture checksum set (docs/decisions/ADR-*.md, contracts/**,
# config/**/*.toml, config/*.json, ci/policy/policy.yaml, artifacts.lock.yaml). A plant
# left behind there does not merely litter — it moves the architecture checksum, and the
# next reader sees an unexplained architecture change rather than a broken test.
# Echoes the backup path; pass it to `unplant`.
plant_in() {
  local f="$1" b; b="$(mktemp)"
  cp "$f" "$b"
  RESTORE+=("[[ -f '$b' ]] && cp '$b' '$ROOT/$f'; rm -f '$b'")
  printf '%s' "$b"
}
unplant() { cp "$2" "$1"; rm -f "$2"; }

# expect_violation <gate> <rule-substring> <description>
expect_violation() {
  local gate="$1" rule="$2" desc="$3"
  local out; out="$(python3 "ci/gates/gate_$(echo "$gate" | tr '-' '_').py" 2>&1)"
  local rc=$?
  if [[ $rc -eq 1 && "$out" == *"$rule"* ]]; then
    printf '  \033[32mok\033[0m    %-16s catches %s\n' "$gate" "$desc"; ((pass++))
  else
    printf '  \033[31mFAIL\033[0m  %-16s did NOT catch %s (exit %s)\n' "$gate" "$desc" "$rc"; ((fail++))
  fi
}

echo
echo "══ gate self-test — planting known violations"
echo

# 1. Secret scanning. AUD-C02 REMEDIATION:
# selftest-covers: secrets — asserted by hand rather than through expect_violation,
# because the credential is GENERATED and planted OUTSIDE the repository and the gate is
# pointed at it with --root. gate-coverage reads this pragma; see its module docstring.
#    The credential is GENERATED from sample_parts in policy.yaml and planted in a
#    TEMP TREE OUTSIDE THE REPOSITORY. No matching literal exists in any repo file,
#    so gate_secrets needs no path exclusion in order for this test to pass.
#    The gate is pointed at the temp tree with --root.
SECRET_TMP="$(mktemp -d)"
RESTORE+=("rm -rf '$SECRET_TMP'")
mkdir -p "$SECRET_TMP/config"
PYTHONPATH="$ROOT/ci/gates" python3 - "$SECRET_TMP/config/planted.yaml" <<'PYGEN'
import sys, yaml, pathlib
pol = yaml.safe_load(open(pathlib.Path(__file__).parent / "ci/policy/policy.yaml")) \
      if False else yaml.safe_load(open("ci/policy/policy.yaml"))
aws = next(p for p in pol["secrets"]["patterns"] if p["id"] == "SEC-AWS")
pathlib.Path(sys.argv[1]).write_text("aws_key: " + "".join(aws["sample_parts"]) + "\n")
PYGEN
out="$(python3 ci/gates/gate_secrets.py --root "$SECRET_TMP" 2>&1)"; rc=$?
if [[ $rc -eq 1 && "$out" == *"SEC-AWS"* ]]; then
  printf '  \033[32mok\033[0m    %-16s catches %s\n' "secrets" "a generated AWS key (planted outside the repo)"; ((pass++))
else
  printf '  \033[31mFAIL\033[0m  %-16s did NOT catch %s (exit %s)\n' "secrets" "a generated AWS key" "$rc"; ((fail++))
fi
rm -rf "$SECRET_TMP"

# 1b. The regexes themselves must be exercised, not merely present.
out="$(python3 ci/gates/gate_secrets.py --verify-patterns-only 2>&1)"; rc=$?
if [[ $rc -eq 0 && "$out" == *"pattern self-tests"* ]]; then
  printf '  \033[32mok\033[0m    %-16s %s\n' "secrets" "regex self-test: every pattern matches its sample and rejects its near-miss"; ((pass++))
else
  printf '  \033[31mFAIL\033[0m  %-16s regex self-test failed (exit %s)\n' "secrets" "$rc"; ((fail++))
fi

# 2. Mutable image tags.
printf 'image: qdrant/qdrant:latest\n' > config/_selftest.yaml
RESTORE+=("rm -f '$ROOT/config/_selftest.yaml'")
expect_violation no-latest "DOCKER-002" "a :latest tag"
rm -f config/_selftest.yaml

# 3. Placeholder pins.
printf 'sha256: PENDING\n' > config/_selftest.yaml
expect_violation no-pending "PLACEHOLDER-001" "a PENDING placeholder"
rm -f config/_selftest.yaml

# 4. ADR-0011: the shell capability must never come back. Two gates guard it from
#    different angles, and both are asserted: `architecture` because ARCH-001 is the
#    recorded prohibition, `structure` because the path is also in `forbidden_paths`.
mkdir -p src/lionel/capabilities/shell
RESTORE+=("rmdir '$ROOT/src/lionel/capabilities/shell' 2>/dev/null || true")
expect_violation architecture "ARCH-001" "a resurrected shell capability"
expect_violation structure "STRUCT-003" "a path whose absence is a recorded decision"
rmdir src/lionel/capabilities/shell

# 4b. ADR-0002 / HAZ-BACKSLASH: a Windows path written with backslashes in config.
#     Silent by construction — Bash eats the backslash as an escape, so the value
#     that reaches the program is a DIFFERENT STRING and nothing errors. The
#     filesystem capability ends up scoped to a root that does not exist, and the
#     first symptom is a tool that mysteriously returns nothing. This is the hazard
#     table's seventh row, and it was `operator` (i.e. unenforced) until 1.8.0.
B_TOML="$(plant_in config/lionel.toml)"
printf '\n[selftest]\nroot = "C:\\Users\\deniz\\nowhere"\n' >> config/lionel.toml
expect_violation architecture "ARCH-017" "a backslashed Windows path in config"
unplant config/lionel.toml "$B_TOML"

# 4c. ADR-0009 / ARCH-002: a caller branching on provider identity by string rather than
#     on a ProviderCapabilities flag. Existed since Phase 0 with no planted violation of
#     its own -- the `architecture` gate was already covered via ARCH-001 and ARCH-017, so
#     `gate-coverage` (which tracks gates, not rules) would not have noticed ARCH-002
#     silently stop firing. This is that missing assertion, closed the same day ADR-0039
#     found the pattern's sibling four times over in the brain contracts.
mkdir -p src/lionel/brain/_selftest
cat > src/lionel/brain/_selftest/branch.py <<'PY'
def route(provider):
    if provider == "anthropic":
        return "native_tools"
PY
RESTORE+=("rm -rf '$ROOT/src/lionel/brain/_selftest'")
expect_violation architecture "ARCH-002" "a caller branching on provider identity"
rm -rf src/lionel/brain/_selftest

# 4d. ADR-0001: a module outside brain/providers/ importing a concrete provider directly.
#     "core/turn_executor imports BrainProvider and nothing else" is ADR-0001's other half
#     of ARCH-002, and had no check or planted violation at all until now -- the import
#     restriction and the branching restriction are one sentence in the ADR and were one
#     gap in the gate.
mkdir -p src/lionel/core/_selftest
cat > src/lionel/core/_selftest/caller.py <<'PY'
from lionel.brain.providers.anthropic import AnthropicProvider
PY
RESTORE+=("rm -rf '$ROOT/src/lionel/core/_selftest'")
expect_violation architecture "ARCH-018" "a caller importing a concrete provider directly"
rm -rf src/lionel/core/_selftest

# 5. STRUCT-004 — no runtime code — was LIFTED at architecture 1.6.0, when Phase 1 opened
#    and `repository.runtime_code_forbidden_until` went to null. The rule cannot fire, so
#    an assertion against it would fail for the right reason and still leave a red suite.
#    It is dormant rather than deleted: re-arming it is one policy value, and a later phase
#    that needs a code freeze should not have to rewrite the gate. `structure` keeps its
#    coverage through STRUCT-003 immediately above — a gate that has never rejected
#    anything is unproven whichever of its rules happens to be reachable today.

# 6. Unregistered TODO.
printf '# TODO: unregistered\n' > scripts/_selftest.sh
RESTORE+=("rm -f '$ROOT/scripts/_selftest.sh'")
expect_violation no-todo "TODO-001" "an unregistered TODO"
rm -f scripts/_selftest.sh

# 7. Shell strict mode.
printf '#!/usr/bin/env bash\necho hi\n' > scripts/_selftest.sh
expect_violation shell "SH-STRICT" "a script without strict mode"
rm -f scripts/_selftest.sh

# 7b/7c. The Git Bash hazard rules (MASTER_PLAN_v1 §2, carried forward by v2 Phase 1).
#     These two rows are the only ones in that seven-row table that can be checked
#     statically in this repository's own scripts; the rest describe what an operator
#     types at a terminal and live in scripts/check_env.sh instead. Both plants are
#     lines that LOOK correct and are not, which is the whole difficulty: the Store
#     stub exits 9009 with no useful message, and a mangled bind mount silently lands
#     in C:/Program Files/Git and the container comes up empty.
printf '#!/usr/bin/env bash\nset -euo pipefail\npython -m unittest\n' > scripts/_selftest.sh
expect_violation shell "SH-BARE-PYTHON" "a bare interpreter name (the Store stub)"
rm -f scripts/_selftest.sh

printf '#!/usr/bin/env bash\nset -euo pipefail\ndocker run -v /qdrant/storage:/s qdrant\n' > scripts/_selftest.sh
expect_violation shell "SH-MSYS-DOCKER" "a container path MSYS would rewrite"
rm -f scripts/_selftest.sh

# 8. Broken internal doc link.
printf '# t\n\n[x](does-not-exist.md)\n' > docs/_selftest.md
RESTORE+=("rm -f '$ROOT/docs/_selftest.md'")
expect_violation markdown "MD-LINK" "a broken internal link"
rm -f docs/_selftest.md

# 9. L0 offline conformance — the keystone gate. Finding M1: it enforces 8 invariants
#    and 18 rules and had no standing regression protection, so a change could silently
#    disarm the autonomy guarantee (ADR-0007) and every run would stay green.
#
#    Unlike the tests above, this one mutates a file that is IN the architecture
#    checksum set (config/**/*.toml). It is restored from a byte-exact backup and the
#    restoration is verified below — a self-test that leaves this file altered would
#    move the architecture checksum and read as an unexplained architecture change.
L0_CFG="config/tiers/l0.toml"
L0_BAK="$(mktemp)"
cp "$L0_CFG" "$L0_BAK"
# Guarded: the happy path restores and deletes the backup below, so by the time the
# EXIT trap runs there is normally nothing left to do. This entry exists for the path
# where the script dies mid-test with the violation still planted.
RESTORE+=("[[ -f '$L0_BAK' ]] && cp '$L0_BAK' '$ROOT/$L0_CFG'; rm -f '$L0_BAK'")
sed -i 's/^network_allowed = false/network_allowed = true/' "$L0_CFG"
if ! grep -q '^network_allowed = true' "$L0_CFG"; then
  printf '  \033[31mFAIL\033[0m  %-16s could not plant the violation (l0.toml changed shape?)\n' "l0-conformance"
  ((fail++))
else
  expect_violation l0-conformance "L0-OFFLINE-002" "L0 declaring network_allowed = true"
fi
cp "$L0_BAK" "$L0_CFG"; rm -f "$L0_BAK"

# ── 10–17: the eight gates that had never rejected anything ────────────────────────
# At the 1.0.0 freeze the suite covered 9 of 17 gates. CI_Architecture.md §7 step 6 has
# always said a gate that has never rejected anything is unproven; nothing enforced it,
# so eight gates went unproven for the whole of Phase 0. `gate-coverage` now enforces it,
# and these are the assertions that satisfy it.

# 10. The ADR set is complete and contiguous.
cat > docs/decisions/ADR-9999-selftest.md <<'ADRX'
# ADR-9999: self-test plant

| | |
|---|---|
| Status | **Accepted** |
ADRX
RESTORE+=("rm -f '$ROOT/docs/decisions/ADR-9999-selftest.md'")
expect_violation adr "ADR-001" "an ADR count that no longer matches policy"
rm -f docs/decisions/ADR-9999-selftest.md

# 10b. ADR-0029: an undated correction cannot be ordered against what it corrects.
cat > docs/decisions/ADR-9999-selftest.md <<'ADRX'
# ADR-9999: self-test plant

| | |
|---|---|
| Status | **Accepted** |

## Context
## Decision
## Consequences
## Alternatives Rejected
## Verification

## Erratum

No date in the heading. ADR-009 must reject this.
ADRX
expect_violation adr "ADR-009" "an Erratum with no ISO date"
rm -f docs/decisions/ADR-9999-selftest.md

# 11. Contract metadata. Every schema declares who owns it and what plane it is on;
#     without that a contract has no reviewer and no blast radius.
cat > contracts/core/v1/_selftest.schema.json <<'SCHEMA'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://lionel.local/schemas/core/v1/_selftest.schema.json",
  "title": "selftest",
  "type": "object"
}
SCHEMA
RESTORE+=("rm -f '$ROOT/contracts/core/v1/_selftest.schema.json'")
expect_violation contracts "CONTRACT-001" "a contract with no x-lionel block"
rm -f contracts/core/v1/_selftest.schema.json

# 12. Examples must satisfy the schema they illustrate. An example that does not is the
#     one a consumer copies.
cat > contracts/core/v1/_selftest.schema.json <<'SCHEMA'
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://lionel.local/schemas/core/v1/_selftest.schema.json",
  "title": "selftest",
  "type": "object",
  "required": ["a"],
  "properties": { "a": { "type": "string" } },
  "examples": [ { "a": 123 } ],
  "x-lionel": {
    "version": "1.0.0", "adr": "ADR-0027", "stability": "provisional",
    "plane": "internal", "owner": "platform", "producer": "platform",
    "consumers": ["platform"],
    "compatibility": { "since": "1.0.0", "breaking_changes": [], "notes": "self-test plant" }
  }
}
SCHEMA
expect_violation jsonschema "JSON-004" "an example that fails its own schema"
rm -f contracts/core/v1/_selftest.schema.json

# 12b. ADR-0034 rule 4: a rule must decide or constrain. A rule with neither validated
#      under policy-ruleset 1.0.0 and did nothing at all — silently, while reading in the
#      file as though it did something. That is the defect ADR-0034 was written about, so
#      the schema must now reject the shape rather than the reviewer having to spot it.
#      Planted in the real schema's own examples, because a plant in a throwaway file
#      would prove the plant and not the contract. It is in the checksum set: byte-exact
#      backup, verified restore.
PR_SCHEMA="contracts/mcp/v1/policy-ruleset.schema.json"
PR_BAK="$(plant_in "$PR_SCHEMA")"
python3 - "$PR_SCHEMA" <<'PLANT'
import json, sys
p = sys.argv[1]
with open(p, encoding="utf-8", newline="") as f:
    raw = f.read()
d = json.loads(raw)
d["examples"][0]["rule"].append({"name": "inert", "match": {"any": True}})
with open(p, "w", encoding="utf-8", newline="") as f:
    # chr(10), not a backslash escape. This block is written into a heredoc, and a
    # backslash-n here becomes a real newline before python ever sees it.
    f.write(json.dumps(d, indent=2, ensure_ascii=False) + chr(10))
PLANT
expect_violation jsonschema "JSON-004" "a policy rule that neither decides nor constrains"
unplant "$PR_SCHEMA" "$PR_BAK"

# 12c. ADR-0037: a LIVE record with empty text. Redaction clears the text and the schema's
#      if/then allows it there; everywhere else `minLength: 1` still stands, because an
#      empty-texted live record recalls nothing, matches nothing, and looks like a working
#      memory in every listing. The plant flips `redacted` to false on the tombstone
#      example, which is the smallest edit that makes the conditional take the other branch
#      -- and it is exactly what a careless "just relax minLength" would have permitted.
MR_SCHEMA="contracts/events/v1/memory-record.schema.json"
MR_BAK="$(plant_in "$MR_SCHEMA")"
python3 - "$MR_SCHEMA" <<'PLANT'
import io, json, sys
p = sys.argv[1]
with io.open(p, encoding="utf-8", newline="") as f:
    d = json.loads(f.read())
tomb = next(e for e in d["examples"] if e.get("redacted") is True)
tomb["redacted"] = False
with io.open(p, "w", encoding="utf-8", newline="") as f:
    # chr(10), not a backslash escape. This block is written into a heredoc, and a
    # backslash-n here becomes a real newline before python ever sees it.
    f.write(json.dumps(d, indent=2, ensure_ascii=False) + chr(10))
PLANT
expect_violation jsonschema "JSON-004" "a live memory record with empty text"
unplant "$MR_SCHEMA" "$MR_BAK"

# 12d. ADR-0039: a planted `usage` StreamEvent example carries `token_counts_estimated`
#      (added to the real example on acceptance, since the quota guard reads it mid-stream,
#      not from the terminal ProviderResponse). The plant removes the field from
#      $defs.Usage.properties again -- reverting one file to its pre-ADR-0039 shape while
#      leaving the example untouched -- which is what "the schema and its example disagree"
#      looks like from this side, the same defect ADR-0037 closed one level down.
SE_SCHEMA="contracts/events/v1/stream-event.schema.json"
SE_BAK="$(plant_in "$SE_SCHEMA")"
python3 - "$SE_SCHEMA" <<'PLANT'
import io, json, sys
p = sys.argv[1]
with io.open(p, encoding="utf-8", newline="") as f:
    d = json.loads(f.read())
del d["$defs"]["Usage"]["properties"]["token_counts_estimated"]
with io.open(p, "w", encoding="utf-8", newline="") as f:
    # chr(10), not a backslash escape. This block is written into a heredoc, and a
    # backslash-n here becomes a real newline before python ever sees it.
    f.write(json.dumps(d, indent=2, ensure_ascii=False) + chr(10))
PLANT
expect_violation jsonschema "JSON-004" "a usage StreamEvent example the schema no longer describes"
unplant "$SE_SCHEMA" "$SE_BAK"

# 13. Protobuf must compile. A .proto that does not is a data plane that does not exist.
cat > contracts/grpc/v1/_selftest.proto <<'PROTO'
syntax = "proto3";
package lionel.selftest.v1;
message Broken { string a = ; }
PROTO
RESTORE+=("rm -f '$ROOT/contracts/grpc/v1/_selftest.proto'")
expect_violation protobuf "PROTO-001" "a .proto that does not compile"
rm -f contracts/grpc/v1/_selftest.proto

# 14. Unresolved artifacts block the gate (ADR-0013). This one mutates a checksum-set
#     file — see plant_in.
ART_BAK="$(plant_in artifacts.lock.yaml)"
sed -i '0,/status: RESOLVED/s//status: UNRESOLVED/' artifacts.lock.yaml
expect_violation artifacts "ART-000" "an unresolved artifact in the lockfile"
unplant artifacts.lock.yaml "$ART_BAK"

# 15. Image references in runnable config must be digest-pinned, not merely non-`:latest`.
#     A specific tag still points wherever the registry decides tomorrow.
printf 'image: qdrant/qdrant:v1.9.0\n' > config/_selftest.yaml
expect_violation docker-digests "DOCKER-006" "a tagged image with no digest"
rm -f config/_selftest.yaml

# 16. An unrecognised licence has not been assessed, and unassessed is not permissive.
LIC_BAK="$(plant_in artifacts.lock.yaml)"
sed -i '0,/^    license: MIT$/s//    license: Frobnicate-9.9/' artifacts.lock.yaml
expect_violation licenses "LIC-004" "a licence that is on no allowlist"
unplant artifacts.lock.yaml "$LIC_BAK"

# 17. Unbounded dependency (ADR-0013): a rebuild months later resolves a different tree.
DEP_BAK="$(plant_in pyproject.toml)"
sed -i 's|^dependencies = \[|dependencies = [\n    "unbounded-selftest-package",|' pyproject.toml
expect_violation dependencies "DEP-001" "a dependency with no version bound"
unplant pyproject.toml "$DEP_BAK"

# 17b. ADR-0032: an MCP server that resolves its package at launch. `.mcp.json` is not
#      in the architecture checksum set — it is workstation tooling, not architecture — so
#      the checksum assertion at the end would NOT catch a surviving plant here. The
#      content check below the litter list is what covers it.
MCP_BAK="$(plant_in .mcp.json)"
sed -i 's|@upstash/context7-mcp@4\.0\.0"|@upstash/context7-mcp"|' .mcp.json
expect_violation mcp "MCP-001" "an MCP server that resolves its package at launch"
unplant .mcp.json "$MCP_BAK"

# ── 18–20: the meta-gates (ADR-0030) ───────────────────────────────────────────────
# These check the pipeline rather than the repository, so they are the ones most likely
# to be quietly wrong: nothing else in CI would notice.

# 18. Architecture checksum. `config/**/*.toml` is inside the checksum set, so a new file
#     there changes both the policy group's membership and the checksum. This is the
#     failure that went undetected for eight days when *.proto was unpinned in
#     .gitattributes and a Windows clone hashed CRLF.
printf 'selftest = true\n' > config/_selftest.toml
expect_violation checksum "CHECKSUM-001" "a change to the architecture checksum set"
rm -f config/_selftest.toml

# 18b. Line endings are part of the checksum, and CHECKSUM-001 cannot notice on its own:
#      it compares the recorded value against one computed from the same contaminated bytes,
#      so both sides agree and the gate goes green. `.gitattributes` governs what git checks
#      OUT; it does not stop a tool from writing CRLF afterwards, which is exactly what
#      happened while 1.4.0 was being prepared.
CRLF_BAK="$(plant_in artifacts.lock.yaml)"
sed -i 's/$/\r/' artifacts.lock.yaml
expect_violation checksum "CHECKSUM-004" "a CRLF file inside the architecture checksum set"
unplant artifacts.lock.yaml "$CRLF_BAK"

# 19. Generated documents. Both say "regenerate rather than hand-edit"; this proves the
#     gate notices when someone does the opposite.
GEN_BAK="$(plant_in CI_Inventory.md)"
printf '\nhand-edited line the generator would never produce\n' >> CI_Inventory.md
expect_violation generated-docs "GEN-001" "a hand-edited generated document"
unplant CI_Inventory.md "$GEN_BAK"

# 19b. Hand-written counts. `generated-docs` covers documents that have a generator;
#      this covers the current-state claims in the ones that do not. The gate found a real
#      stale claim on its first run — `CLAUDE.md` promised `20/20, 0 broken` under a heading
#      reading "Verify before you claim anything", four gates after that stopped being true.
DOC_BAK="$(plant_in CLAUDE.md)"
sed -i 's|run_gates.sh                    # [0-9]*/[0-9]*, 0 broken|run_gates.sh                    # 99/99, 0 broken|' CLAUDE.md
expect_violation doc-claims "CLAIM-001" "a hand-written count that disagrees with the pipeline"
unplant CLAUDE.md "$DOC_BAK"

# 19c. Quoted files. `doc-claims` checks the numbers a document states; this checks the
#      FILES it quotes. The plant is deliberately NOT gibberish: it takes a block that
#      really does quote config/policy/default.toml and changes one number, which is the
#      exact shape of the defect — ADR-0034 and §9.14 quoted that rule minus one line and
#      argued from its absence, with all 22 gates green. A gate proved against nonsense
#      proves only that it can tell text from a file.
#      Architecture_Freeze.md is NOT in the checksum set, but plant_in is used anyway:
#      an unrestored plant here would leave a false quotation in the document that records
#      what the architecture is.
QUOTE_BAK="$(plant_in Architecture_Freeze.md)"
sed -i '/^match\.any = true$/,+1 s/^max_calls_per_turn = 40$/max_calls_per_turn = 41/' Architecture_Freeze.md
if ! grep -q '^max_calls_per_turn = 41' Architecture_Freeze.md; then
  printf '  [31mFAIL[0m  %-16s could not plant the violation (§9.15 changed shape?)
' "doc-quotes"
  ((fail++))
else
  expect_violation doc-quotes "QUOTE-001" "a quoted config block that differs from the file by one line"
fi
unplant Architecture_Freeze.md "$QUOTE_BAK"

# 19d. A forbidden package that arrives as somebody else's dependency. DEP-002 reads
#      pyproject.toml, so until 2026-08-28 it expressed a decision about what may be
#      INSTALLED while checking only what was DECLARED. Accepting ADR-0036 put `requests`
#      in uv.lock via fastembed with every gate green. The plant forbids a package that is
#      genuinely in the lock and genuinely not declared, so DEP-003 is exercised against
#      the real lock rather than against a fixture.
DEP_BAK="$(plant_in ci/policy/policy.yaml)"
python3 - <<'PLANT'
import io
p = "ci/policy/policy.yaml"
with io.open(p, encoding="utf-8", newline="") as f:
    s = f.read()
anchor = "  forbid_packages:" + chr(10)
assert anchor in s, "forbid_packages anchor moved"
s = s.replace(anchor, anchor + "    - name: tqdm" + chr(10) +
              '      why: "self-test plant"' + chr(10), 1)
with io.open(p, "w", encoding="utf-8", newline="") as f:
    f.write(s)
PLANT
expect_violation dependencies "DEP-003" "a forbidden package installed transitively"
unplant ci/policy/policy.yaml "$DEP_BAK"

# 20. Gate coverage itself. The plant goes into a COPY of this script: bash reads a script
#     incrementally as it executes, so editing the running file could change the behaviour
#     of the test doing the editing. The gate takes --suite for exactly this, the same way
#     gate_secrets takes --root.
# selftest-covers: gate-coverage — asserted inline against a doctored copy of this suite.
COV_TMP="$(mktemp -d)"
RESTORE+=("rm -rf '$COV_TMP'")
grep -v 'expect_violation structure' ci/self_test.sh > "$COV_TMP/self_test.sh"
out="$(python3 ci/gates/gate_gate_coverage.py --suite "$COV_TMP/self_test.sh" 2>&1)"; rc=$?
if [[ $rc -eq 1 && "$out" == *"COV-001"* && "$out" == *"structure"* ]]; then
  printf '  \033[32mok\033[0m    %-16s catches %s\n' "gate-coverage" "a gate whose planted violation was deleted"; ((pass++))
else
  printf '  \033[31mFAIL\033[0m  %-16s did NOT catch %s (exit %s)\n' "gate-coverage" "a deleted assertion" "$rc"; ((fail++))
fi
rm -rf "$COV_TMP"

# Cleanup must be verified, not assumed. A self-test that leaves its planted
# violations behind turns every subsequent run red for the wrong reason — and the
# first person to see it will "fix" the gate rather than the litter.
leftover=0
for f in config/_selftest.toml config/_selftest.yaml \
         scripts/_selftest.sh docs/_selftest.md \
         docs/decisions/ADR-9999-selftest.md \
         contracts/core/v1/_selftest.schema.json contracts/grpc/v1/_selftest.proto; do
  [[ -e "$f" ]] && { printf '  \033[31mFAIL\033[0m  self-test litter not removed: %s\n' "$f"; leftover=1; }
done
[[ -d src/lionel/capabilities/shell ]] && { echo "  FAIL  self-test litter: src/lionel/capabilities/shell"; leftover=1; }
grep -q '^network_allowed = false' config/tiers/l0.toml || {
  echo "  FAIL  config/tiers/l0.toml was not restored — L0 still reads network_allowed = true"; leftover=1; }
grep -q '@upstash/context7-mcp@4\.0\.0' .mcp.json || {
  echo "  FAIL  .mcp.json was not restored — the context7 pin is missing"; leftover=1; }
grep -q '99/99' CLAUDE.md && {
  echo "  FAIL  CLAUDE.md was not restored — the planted 99/99 count survived"; leftover=1; }
(( leftover )) && { echo; echo "  Planted files survived cleanup. Remove them before re-running."; exit 1; }

echo
if (( fail )); then
  printf '  \033[31mSELF-TEST FAIL\033[0m  %d/%d gates did not catch their planted violation\n\n' "$fail" "$((pass+fail))"
  echo "  A gate that cannot catch a violation is decoration. Fix the gate."
  exit 1
fi
# The suite must leave the architecture byte-identical. A plant that survives in the
# checksum set does not merely litter: it silently changes what Architecture_Freeze.md §2
# describes, and the next person to recompute sees an architecture change with no commit
# behind it. The litter check above lists files it knows about; this catches the ones it
# does not — including in-place edits, which leave no file to look for.
CHECKSUM_AFTER="$(arch_checksum)"
if [[ -n "$CHECKSUM_BEFORE" && "$CHECKSUM_BEFORE" != "$CHECKSUM_AFTER" ]]; then
  printf '  \033[31mSELF-TEST FAIL\033[0m  the suite changed the architecture checksum\n'
  printf '        before  %s\n        after   %s\n\n' "$CHECKSUM_BEFORE" "$CHECKSUM_AFTER"
  echo "  A plant inside the checksum set was not restored. Find it before trusting this run."
  exit 1
fi
printf '  \033[32mSELF-TEST PASS\033[0m  %d/%d planted violations caught\n' "$pass" "$pass"
printf '                    architecture checksum unchanged — %s\n\n' "${CHECKSUM_AFTER:-unavailable}"
