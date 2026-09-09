#!/usr/bin/env python3
"""GATE: architecture conformance — ADRs as executable policy.

This is the gate that makes the CI pipeline enforce the architecture rather than
merely tidy it. Every check here corresponds to a decision that would otherwise be
enforced only by everyone remembering it, which is to say not enforced.

An architectural rule with no test is a preference. These are the tests.
"""
import json, re
from pathlib import Path
from _lib import Gate, load_policy, ROOT, rel, read_text, repo_files, load_json

def main():
    p = load_policy(); g = Gate("architecture", "Architecture conformance",
        ["ADR-0001", "ADR-0006", "ADR-0007", "ADR-0009", "ADR-0010", "ADR-0011", "ADR-0012",
         "ADR-0025", "ADR-0026"])
    cfg = p["architecture"]

    # ── ADR-0011: shell execution abolished ──────────────────────────────────
    g.check()
    if (ROOT / "src/lionel/capabilities/shell").exists():
        g.fail("ARCH-001", "`src/lionel/capabilities/shell/` exists",
            "ADR-0011 abolished arbitrary shell execution. An allowlist gates the verb and "
            "leaves arguments open to injection; with L.I.O.N.E.L reading untrusted documents "
            "that is remote code execution on Efe's primary machine.",
            "Delete the directory. Express the capability as typed tools instead.")

    # ── ADR-0009: callers branch on capabilities, never on provider identity ──
    prov = "|".join(cfg["provider_names"])
    branch = re.compile(rf'(==|!=|is)\s*["\']({prov})["\']|provider\s*==\s*["\']({prov})')
    for f in repo_files(include={".py"}):
        r = rel(f)
        if any(r.startswith(d) for d in cfg["provider_branch_allowed_dirs"]):
            continue
        for i, line in enumerate(read_text(f).splitlines(), 1):
            if branch.search(line):
                g.check()
                g.fail("ARCH-002", "branching on provider name",
                    "ADR-0009: callers branch on ProviderCapabilities, never on provider "
                    "identity. Provider-name branching is how ADR-0001's independence becomes "
                    "nominal — the abstraction exists but every caller works around it.",
                    "Branch on a capability flag (`native_tools`, `structured_output`, …). "
                    "If the capability you need is not declared, add it to the contract.", r, i)

    # ── ADR-0001: no module outside brain/providers/ imports a concrete provider ─
    # "core/turn_executor imports BrainProvider and nothing else. No module outside
    # brain/providers/ may import a concrete provider or branch on a provider name." The
    # second half is ARCH-002, above. This is the first half, and until Phase 3's contract
    # test (ADR-0039) it had no check at all — the same "step 6 gets skipped" gap this
    # gate's own module docstring warns about, one rule over.
    provider_import = re.compile(r'^\s*(?:from|import)\s+lionel\.brain\.providers\b')
    for f in repo_files(include={".py"}):
        r = rel(f)
        if any(r.startswith(d) for d in cfg["provider_branch_allowed_dirs"]):
            continue
        for i, line in enumerate(read_text(f).splitlines(), 1):
            if provider_import.search(line):
                g.check()
                g.fail("ARCH-018", "importing a concrete provider from outside brain/providers/",
                    "ADR-0001: 'No module outside brain/providers/ may import a concrete "
                    "provider or branch on a provider name.' A caller that imports "
                    "AnthropicProvider directly has the same problem branching on the string "
                    "\"anthropic\" does — it can only be swapped by editing that caller, which "
                    "is what the BrainProvider abstraction exists to make unnecessary.",
                    "Import `lionel.brain.BrainProvider` (or the factory that selects one from "
                    "`[brain] provider`) instead of a concrete adapter.", r, i)

    # ── ADR-0006: the control plane never carries media payload ──────────────
    for d in cfg["control_plane_dirs"]:
        for f in sorted((ROOT / d).rglob("*.json")) if (ROOT / d).is_dir() else []:
            txt = read_text(f)
            for key in cfg["media_payload_keys"]:
                if f'"{key}"' in txt:
                    g.check()
                    line = next((i for i, l in enumerate(txt.splitlines(), 1) if f'"{key}"' in l), None)
                    g.fail("ARCH-003", f"media payload key `{key}` in a control-plane schema",
                        "ADR-0006: PCM must never traverse MCP. Base64 inflates by ~33% on the "
                        "highest-volume path, and the control plane has no backpressure, no jitter "
                        "buffer, and head-of-line blocking behind unrelated tool calls.",
                        "Move the descriptor to contracts/media/ and keep payload on the data "
                        "plane (protobuf `bytes`).", rel(f), line)

    # ── ADR-0012: authorization metadata must not leave the system ───────────
    mt = ROOT / "contracts/mcp/v1/mcp-tool.schema.json"
    if mt.exists():
        d = load_json(mt)
        props = set((d.get("properties") or {}).keys())
        for bad in cfg["mcp_tool_forbidden_fields"]:
            g.check()
            if bad in props:
                g.fail("ARCH-004", f"MCPTool exposes `{bad}`",
                    "ADR-0012: side_effect, trust_required, rate limits and audit flags are "
                    "L.I.O.N.E.L's authorization metadata. Emitting them over MCP tells a remote "
                    "peer exactly which tool is the soft target.",
                    f"Remove `{bad}` from the wire projection. It belongs in the ToolSpec IR only.",
                    rel(mt))

    # ── ADR-0026 / ADR-0012: tools declare consequences and required trust ───
    ts = ROOT / "contracts/events/v1/tool-spec.schema.json"
    if ts.exists():
        req = set(load_json(ts).get("required", []))
        for field in ("side_effect", "trust_required"):
            g.check()
            if field not in req:
                g.fail("ARCH-005", f"ToolSpec does not require `{field}`",
                    "ADR-0026: classification is declared, never inferred from a tool name. "
                    "Retry safety, cancellation semantics, confirmation and audit all read this "
                    "one field, and a name heuristic fails on the first tool called `cleanup`.",
                    f"Add `{field}` to ToolSpec `required`.", rel(ts))

    # ── ADR-0012: trust cannot be laundered through a tool result or memory ──
    for path, field, why in [
        ("contracts/mcp/v1/tool-result.schema.json", "trust_of_output",
         "A tool result is content of unknown provenance. Without a declared trust level, a tool "
         "that fetches a web page returns attacker-controlled text at whatever trust the turn "
         "already had — reopening the injection path ADR-0012 closes."),
        ("contracts/mcp/v1/tool-call.schema.json", "trust",
         "The Policy Engine cannot authorize anything without a trust context. Optional trust "
         "would either break the system or tempt someone to default it to user_originated."),
    ]:
        f = ROOT / path
        if f.exists():
            g.check()
            if field not in set(load_json(f).get("required", [])):
                g.fail("ARCH-006", f"`{Path(path).name}` does not require `{field}`", why,
                    f"Add `{field}` to `required`.", path)

    mq = ROOT / "contracts/events/v1/memory-query.schema.json"
    if mq.exists():
        d = load_json(mq)
        r_ = ((d.get("$defs") or {}).get("MemoryQueryResult") or {}).get("required", [])
        g.check()
        if "trust_floor" not in r_:
            g.fail("ARCH-007", "MemoryQueryResult does not require `trust_floor`",
                "ADR-0012: a memory ingested from external content stays external content. "
                "Without a trust floor on recall, laundering hostile text through memory silently "
                "upgrades it.",
                "Add `trust_floor` to MemoryQueryResult `required`.", rel(mq))

    # ── ADR-0025: cancellation is not optional ───────────────────────────────
    pr = ROOT / "contracts/events/v1/provider-request.schema.json"
    if pr.exists():
        g.check()
        if "cancellation_token_id" not in set(load_json(pr).get("required", [])):
            g.fail("ARCH-008", "ProviderRequest does not require `cancellation_token_id`",
                "ADR-0025: optional cancellation is cancellation some call sites will omit, and "
                "those are exactly the ones that hang during barge-in. The 300 ms budget cannot "
                "be met by a path that has no token to cancel with.",
                "Make `cancellation_token_id` required.", rel(pr))

    # ── ADR-0012: policy fails closed ────────────────────────────────────────
    pol = ROOT / "contracts/mcp/v1/policy-ruleset.schema.json"
    if pol.exists():
        d = load_json(pol)
        try:
            const = d["properties"]["defaults"]["properties"]["decision"]["const"]
        except KeyError:
            const = None
        g.check()
        if const != "deny":
            g.fail("ARCH-009", f"policy default is not pinned to `deny` (found {const!r})",
                "ADR-0012: allow-by-default means a forgotten tool registration becomes an open "
                "door. Pinning by `const` rather than `default` means changing it requires a "
                "schema change, which requires an ADR — it cannot be done quietly.",
                'Set `properties.defaults.properties.decision.const` to "deny".', rel(pol))

    # ── ADR-0010: forgetting is not optional ─────────────────────────────────
    ms = ROOT / "contracts/mcp/v1/memory-service.schema.json"
    if ms.exists():
        d = load_json(ms)
        req = ((d.get("properties") or {}).get("tools") or {}).get("required", [])
        g.check()
        if "memory.forget" not in req:
            g.fail("ARCH-010", "`memory.forget` is not a required tool",
                "ADR-0010: a memory system without a forget path accumulates errors permanently. "
                "'No, that's wrong' has to be actionable.",
                "Add `memory.forget` to the required tool set.", rel(ms))

    # ── ADR-0007: L0 is the autonomy guarantee ───────────────────────────────
    l0 = ROOT / cfg["l0_tier_file"]
    g.check()
    if not l0.exists():
        g.fail("ARCH-011", f"L0 tier config missing: `{cfg['l0_tier_file']}`",
            "ADR-0007: L0 is the offline autonomy guarantee and the blocking CI gate. Without "
            "its config there is nothing to assert offline behaviour against.",
            f"Create `{cfg['l0_tier_file']}`.")
    else:
        txt = read_text(l0)
        for key, want in cfg["l0_required_settings"].items():
            g.check()
            m = re.search(rf"^{re.escape(key)}\s*=\s*(\S+)", txt, re.M)
            if not m or m.group(1).strip().rstrip(",") != want:
                g.fail("ARCH-012", f"L0 `{key}` is not `{want}`",
                    "ADR-0007: L0 must be provably offline. A tier that permits network access is "
                    "not the autonomy guarantee, it is a configuration that happens to work "
                    "offline today.",
                    f"Set `{key} = {want}` in {cfg['l0_tier_file']}.", rel(l0))
        for bad in cfg["l0_forbidden_providers"]:
            g.check()
            if re.search(rf'provider\s*=\s*"{bad}"', txt):
                g.fail("ARCH-013", f"L0 selects network provider `{bad}`",
                    "ADR-0007: a requires_network provider at L0 breaks the offline guarantee. "
                    "This is exactly the erosion the ladder exists to prevent — nobody decides to "
                    "abandon offline operation, it just stops being true one config at a time.",
                    "Use a local provider (ollama / llamacpp) at L0.", rel(l0))

    # ── ADR-0018: English-only models are rejected project-wide ──────────────
    for f in repo_files(include={".yaml", ".yml", ".toml", ".json"}):
        for i, line in enumerate(read_text(f).splitlines(), 1):
            if re.search(r"ggml-[a-z0-9.\-]*\.en\.bin", line):
                g.check()
                g.fail("ARCH-014", "English-only `.en` whisper model referenced",
                    "ADR-0018: `.en` models are English-only by construction, not merely "
                    "English-optimised. With Turkish required this is a hard incompatibility "
                    "that would surface at the final sensory gate, after the pipeline was built "
                    "around the wrong model class.",
                    "Use a multilingual model (large-v3-turbo).", rel(f), i)

    # ── ADR-0008: no god object ──────────────────────────────────────────────
    g.check()
    if (ROOT / "src/lionel/host/loop.py").exists():
        g.fail("ARCH-015", "`src/lionel/host/loop.py` exists",
            "ADR-0008 replaced the v1.0 god loop with five coordinators. A single module owning "
            "perceive/think/act/speak accumulates state until cancellation and barge-in become "
            "unimplementable.",
            "Split into session_coordinator, turn_executor, context_assembler, tool_router, "
            "interrupt_controller under src/lionel/core/.")

    # ── ADR-0016: ADRs are indexed, not orphaned ─────────────────────────────
    idx = ROOT / "docs/decisions/README.md"
    if idx.exists():
        listed = set(re.findall(r"ADR-(\d{4})-[a-z0-9-]+\.md", read_text(idx)))
        on_disk = set(re.findall(r"ADR-(\d{4})-", " ".join(
            q.name for q in (ROOT / "docs/decisions").glob("ADR-*.md"))))
        g.check()
        missing = on_disk - listed
        if missing:
            g.fail("ARCH-016", f"ADR(s) not listed in the index: {sorted(missing)}",
                "ADR-0016: ADRs must be discoverable. An unindexed ADR is a decision nobody will "
                "find when they need it, which defeats the point of writing it down.",
                "Add the entries to docs/decisions/README.md.", rel(idx))

    # ── ADR-0002: Windows paths in config use forward slashes ────────────────
    # MASTER_PLAN_v1 §2 (HAZ-BACKSLASH) and ADR-0002 both say it, and neither was
    # enforced. The failure is silent by construction: Bash consumes a backslash as
    # an escape, so the value that reaches the program is a DIFFERENT STRING that
    # nothing reports. `C:\Users\deniz` arrives as `C:Usersdeniz`, the filesystem
    # server is scoped to a root that does not exist, and the first symptom is a
    # capability that mysteriously returns nothing.
    for f in sorted((ROOT / "config").rglob("*")):
        if f.suffix not in {".toml", ".json"} or not f.is_file():
            continue
        for i, line in enumerate(read_text(f).splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            g.check()
            m = re.search(r"[\"']([A-Za-z]:\\[^\"']*)[\"']", line)
            if m:
                g.fail("ARCH-017", f"backslashed Windows path `{m.group(1)}` in config",
                    "ADR-0002: config values carrying Windows paths use FORWARD slashes, "
                    "because Bash consumes a backslash as an escape and the value that "
                    "reaches the program is silently a different string. Nothing errors; "
                    "the path simply points somewhere else.",
                    "Rewrite with forward slashes. Python, Docker and Git Bash all accept "
                    "them on Windows.", rel(f), i)

    g.report_and_exit()

if __name__ == "__main__": main()
