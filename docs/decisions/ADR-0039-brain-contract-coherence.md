# ADR-0039: Four brain contracts describe one thing twice, and Phase 3 is the first consumer

| | |
|---|---|
| Status | **Accepted** — Efe, 2026-09-02. In force. See the Erratum |
| Date | 2026-09-02 |
| Phase | 3 |
| Related | [ADR-0009](ADR-0009-extended-brain-provider-contract.md), [ADR-0001](ADR-0001-swappable-brain-provider.md), [ADR-0025](ADR-0025-cancellation-backpressure.md), [ADR-0023](ADR-0023-turkish-locale-correctness.md), [ADR-0037](ADR-0037-tombstone-record-shape.md) |

## Context

`Phase3_Entry_Checklist.md` item 5 says the first thing to write is the contract test, not
the provider, because the five brain contracts are in the position
`memory-record.schema.json` was in for twenty-six days: `stability: stable`, inside the
architecture checksum set, frozen on 2026-08-02, and **never once consumed**.
`tests/contract/test_brain_contract.py` is that test. It found four disagreements, and
none of them is a corner.

**All four are the class ADR-0037's Consequences left open.** That ADR closed one instance
of *"a schema's prose and its examples can disagree, and nothing notices"* and recorded the
class as open, owner `architecture`. One level up, two schemas can disagree, and `JSON-004`
cannot see it either: it validates each schema against its metaschema and each schema's own
examples, never one schema against another.

### 1. No object can satisfy both HealthStatus contracts

`contracts/core/v1/health-status.schema.json` calls itself the

> Uniform health report for every service and provider.

names `brain_gateway` in its own `producer` list, **requires `service`**, and sets
`additionalProperties: false`. `provider-capabilities.schema.json` defines a *second*
`HealthStatus` in `$defs`, with **no `service` field** and `additionalProperties: false`.

So the core schema rejects a provider's health report for omitting `service`, and the
provider schema rejects the identical report for including it. Their `state` enums differ
too: the core one has `starting` and `shutting_down` and the provider one does not.

**This blocks a DoD clause outright.** MASTER_PLAN_v2 §10 Phase 3 requires *"`health()`
correctly reports not ready while Ollama loads a model"*. It cannot be written until one of
these two definitions wins, and picking one silently at the keyboard is how a contract
becomes decorative.

### 2. The streamed usage cannot say what the terminal usage can

`ProviderResponse.usage` carries `token_counts_estimated`, described as:

> True when the provider lacks `token_counting`; the quota guard then applies a safety
> margin rather than trusting the number.

`StreamEvent.$defs.Usage` does not have the field, and is `additionalProperties: false` — so
a `usage` event carrying it is invalid.

**The missing side is the side that matters.** ADR-0009's ceiling *halts generation*, so the
quota guard runs while tokens are still being produced, off the streamed events. The flag
that tells it not to trust the number is available only in the object that arrives after the
generation it was supposed to stop.

### 3. A cancellation token is a ULID in one contract and any string in the other

`cancellation.schema.json` pins `token_id` to `^[0-9A-HJKMNP-TV-Z]{26}$`. `ProviderRequest`
requires `cancellation_token_id`, types it `string` with no pattern, and describes it in
full as *"ADR-0025. Non-optional."* The empty string satisfies it.

This is G2's fourth defect one step earlier. `QdrantBackend` could not store a conforming
record because ids were pinned in the contract and unpinned in the adapter; here they are
pinned in the contract that defines them and unpinned in the contract that carries them.
ADR-0025's 200 ms clause is a lookup by that token.

### 4. A tool name is pinned where it is declared and free where it is reported

`ToolSpec.name` is `^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$`, and its description gives the
reason:

> Lowercase-only by construction so no case folding is ever needed — see ADR-0023, where
> naive `.lower()` under a Turkish locale maps `I` to dotless `ı` and silently breaks
> comparison.

`StreamEvent.ToolCallDelta.name` and `ProviderResponse.tool_calls[].name` name the *same
tool* and constrain nothing. `İSTANBUL.read` validates in both. The hazard the pattern
exists to prevent re-enters through the two contracts that report what the model asked for
— which is exactly where untrusted text arrives.

## Decision

**Withheld until this ADR is Accepted.** All five schemas are `stability: stable` and inside
the architecture checksum set; `Architecture_Freeze.md` §4 requires an ADR *and* Efe's
approval before a stable surface moves. ADR-0029, ADR-0032, ADR-0033, ADR-0034, ADR-0035,
ADR-0036 and ADR-0037 each practised this withholding; this is the eighth.

On acceptance:

1. **`provider-capabilities.$defs.HealthStatus` is deleted and replaced by a `$ref` to
   `contracts/core/v1/health-status.schema.json`.** The core schema wins because it says it
   does — it names `brain_gateway` as a producer and calls itself uniform — and because
   health is the one place in this architecture where many producers is a feature rather
   than a smell, which that schema also says. → `provider-capabilities` **1.1.0**.
2. **`StreamEvent.$defs.Usage` gains `token_counts_estimated`**, identical in type and
   description to the response's. → `stream-event` **1.1.0**. A widening: every existing
   instance stays valid.
3. **`ProviderRequest.cancellation_token_id` gains the ULID pattern**, by `$ref` to
   `cancellation.schema.json#/properties/token_id` rather than a copied regex — a copied
   pattern is finding 4 waiting to happen. → `provider-request` **1.1.0**.
4. **`ToolCallDelta.name` and `ProviderResponse.tool_calls[].name` take `ToolSpec.name`'s
   constraint**, by `$ref`. → `stream-event` and `provider-response` **1.1.0**.
5. **`ProviderResponse.stop_reason` becomes a `$ref` to `StreamEvent.$defs.StopReason`.**
   The two enums are identical today; `test_stop_reason_is_duplicated_and_still_identical`
   exists only because nothing else would notice the day they stop.

**A model that asks for a malformed tool name is refused at the adapter, not represented.**
Item 4 makes an invalid name unrepresentable, which is deliberate: the union already has an
`error` event, and that is where an unparseable tool call belongs. The alternative — a
contract that can carry `İSTANBUL.read` inward so a caller can decide — is how the ADR-0023
hazard reaches a comparison.

## Consequences

**What gets better.** Phase 3's `health()` clause becomes writable. The quota guard can read
the estimation flag at the point it enforces the ceiling. Two identifiers that name the same
thing in two contracts stop having two shapes, which is the defect G2 spent a session on.

**What this costs.**

- **Item 1 is breaking, and it is the right moment because nothing produces one yet.** A
  `HealthStatus` from a provider will now require `service`. There is no implementation to
  migrate: `src/lionel/brain/` does not exist. After Phase 3 this same change costs a
  coordinated edit across the gateway and every consumer.
- **Items 3 and 4 are narrowings**, which are breaking in principle. Same argument, same
  moment, and both are recorded here rather than described as widenings, because a narrowing
  called a widening in a `compatibility` block is how a contract's own version stops meaning
  anything.
- **Five `$ref`s across four files replace copies.** A `$ref` graph is harder to read than an
  inlined object, and `test_brain_contract.py`'s note that nothing there crosses a file
  boundary stops being true — the test gains a resolver, as `test_memory_contract.py`
  already has.
- **The class stays open.** This fixes four instances. Nothing in the repository compares two
  schemas to each other; `test_brain_contract.py` does it for these five by hand, and the
  next five contracts will need their own. A gate that could do it generally would have to
  know which two definitions are meant to be the same thing, which is a judgement.

## Alternatives Rejected

**Leave them and let the implementation pick.** Rejected: that is what "reviewed, frozen,
never executed" means in practice, and `Phase2_Final_Signoff.md` §1 records four defects that
reached a frozen contract exactly this way. A contract nothing tests against reality cannot
be wrong, and these were not wrong so much as unexercised.

**Keep both HealthStatus definitions and rename the provider one.** Honest about them being
different objects, and cheap. Rejected: they are not different objects. The provider one is a
subset of the core one with two enum values missing, and the core one names `brain_gateway`
as a producer. Renaming would preserve the duplication and remove the evidence that it is
duplication.

**Give the provider schema `service` and leave the two in sync by hand.** Rejected for the
reason finding 4 exists: `StopReason` is already two verbatim copies, and the only thing
keeping them equal is a test written the day someone happened to look.

**Constrain the reported tool names with a looser pattern** — lowercase, no dot required —
so a provider's slightly-off name still round-trips. Rejected: "slightly off" is not a
property a schema can express, and the value of ADR-0023's constraint is that it is
`.lower()`-free *by construction*. A second, looser name shape is a second case-folding
question.

## Verification

`tests/contract/test_brain_contract.py` exists **now**, while this is `Proposed`, and pins
the current behaviour: 12 assertions, four of which assert that the defect is present and
say in their message that a change in the result means the schema moved and needs a
decision. The other eight pin the coherence that already holds — the provider enum, the
configured provider being inside it, `tools` being the ToolSpec IR, and the two `StopReason`
copies still agreeing.

That is the same shape ADR-0037's Verification used, and the same friction: those four tests
are what has to be rewritten on acceptance, which is the right amount.

On acceptance:

| | |
|---|---|
| `provider-capabilities.schema.json` → 1.1.0 | `$defs.HealthStatus` replaced by a `$ref` to `core/v1/health-status.schema.json`; `compatibility.breaking_changes` records that it is breaking and why now |
| `stream-event.schema.json` → 1.1.0 | `Usage.token_counts_estimated`; `ToolCallDelta.name` by `$ref` to `ToolSpec.name` |
| `provider-request.schema.json` → 1.1.0 | `cancellation_token_id` by `$ref` to `cancellation.schema.json#/properties/token_id` |
| `provider-response.schema.json` → 1.1.0 | `tool_calls[].name` by `$ref`; `stop_reason` by `$ref` to `StreamEvent.$defs.StopReason` |
| `test_brain_contract.py` | the four pinning tests invert: each defect becomes an assertion that the fix holds |
| `ci/self_test.sh` | a planted `usage` StreamEvent carrying `token_counts_estimated` with the field removed again, asserting `JSON-004` |

Gate **G3**, alongside the `health()` and cancellation clauses these unblock.

## Erratum — 2026-09-02: Accepted; the withholding is discharged

This ADR was written while `Proposed`, and its Decision section describes that pending state
as ongoing. Efe accepted it on 2026-09-02, the same day it was drafted. The decision is
unchanged — what follows corrects text that has stopped being true, per ADR-0029 rule 2.

The Decision section opened:

> **Withheld until this ADR is Accepted.** All five schemas are `stability: stable` and
> inside the architecture checksum set; `Architecture_Freeze.md` §4 requires an ADR *and*
> Efe's approval before a stable surface moves. ADR-0029, ADR-0032, ADR-0033, ADR-0034,
> ADR-0035, ADR-0036 and ADR-0037 each practised this withholding; this is the eighth.

That is discharged. All five items in the Decision were delivered exactly as specified,
each versioned to **1.1.0**:

| | |
|---|---|
| `provider-capabilities.schema.json` | `$defs.HealthStatus` is now `{"$ref": ".../core/v1/health-status.schema.json"}`, with a `$comment` recording why. `compatibility.breaking_changes` records the change |
| `stream-event.schema.json` | `Usage.token_counts_estimated` added; `ToolCallDelta.name` refs `tool-spec.schema.json#/properties/name`; `$defs.StopReason` refs the new `$defs.StopReasonValues`, which holds the enum `StopReason` used to carry directly |
| `provider-request.schema.json` | `cancellation_token_id` refs `cancellation.schema.json#/properties/token_id` in place of an unconstrained `string` |
| `provider-response.schema.json` | `tool_calls[].name` refs `tool-spec.schema.json#/properties/name`; `stop_reason` refs `stream-event.schema.json#/$defs/StopReasonValues` |
| `test_brain_contract.py` | rewritten rather than patched: the four defect-pinning tests became four coherence-pinning test classes (`TestHealthStatusIsOneContractNow`, `TestUsageCanSayTheCountsAreEstimatedInBothPlaces`, `TestIdentifiersArePinnedInOnePlaceOnly`, `TestStopReasonIsOneEnumNow`), and the file gained an offline `$ref` registry — cross-file refs did not exist in these five schemas before this ADR, and the file's own docstring had said none did |
| `ci/self_test.sh` | 32 → **33**: a planted `usage` StreamEvent example with `Usage.token_counts_estimated` removed from the schema again, asserting `JSON-004` |

**One example was extended rather than only the schema.** `stream-event.schema.json`'s
existing `usage` example — `provider: "ollama"`, which `provider-capabilities.schema.json`'s
own example already marks `token_counting: false` — gained
`"token_counts_estimated": true`. Without it the new field would have shipped with no
example exercising it, which is the same gap ADR-0037's Context found: an unexercised part
of a schema is a part that cannot be wrong because nothing tests it against anything.

**The cross-file `$ref`s needed an offline registry the test file did not have.** The first
run after the schema edits failed seven of twelve tests with `jsonschema.exceptions.
_WrappedReferencingError: Unresolvable`, because `valid()` validated each fragment with no
knowledge of the other four files. `test_memory_contract.py` had already solved this —
`_registry_arg` maps every `https://lionel.local/...` `$id` in `contracts/` onto its file on
disk, so nothing is fetched and ADR-0007's guarantee holds. Copied rather than re-derived.
