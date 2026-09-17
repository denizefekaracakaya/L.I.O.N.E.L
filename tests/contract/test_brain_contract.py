"""ADR-0027 layer 2 — the five brain contracts, checked against each other.

Phase 3 builds `src/lionel/brain/` against `tool-spec`, `stream-event`, `provider-request`,
`provider-response` and `provider-capabilities`. All five are `stability: stable`, all five
are inside the architecture checksum set, and until ADR-0039 none had ever had a consumer.

That was the same position `memory-record.schema.json` was in for twenty-six days before its
first consumer found that it described a state it forbade (ADR-0037). `Phase2_Final_Signoff.md`
§1 records the pattern: every one of G2's four defects was in something reviewed, frozen, and
never executed. `Phase3_Entry_Checklist.md` item 5 said the first thing to write is the
contract test, not the provider — this file, run before any provider code existed, found
four disagreements between contracts that ADR-0037's Consequences had flagged as the open
class: *"a schema's prose and its examples can disagree, and nothing notices"*, one level up,
between two schemas rather than within one.

ADR-0039 (accepted 2026-09-02) fixed all four by `$ref`, so one contract is now the single
source for each concept: `core/v1/health-status.schema.json` for HealthStatus,
`cancellation.schema.json#/properties/token_id` for a cancellation token,
`tool-spec.schema.json#/properties/name` for a tool name, and `stream-event.schema.json`'s
`StopReasonValues` for a stop reason. This file now pins that coherence — the same shape
ADR-0037's own pinning test took: `test_a_redacted_record_still_validates` inverted into
`test_a_tombstone_validates` on acceptance. The four tests below are that inversion.

WHAT A GATE CANNOT SEE, AND THIS CAN
    `jsonschema` (JSON-004) validates each schema against its metaschema and each schema's
    own examples. It never compares two schemas to each other, so two independently correct
    schemas that describe one concept differently pass every existing gate. This file is the
    comparison.

CROSS-FILE $REFS NEED A REGISTRY
    ADR-0039 introduced `$ref`s that cross file boundaries (a provider-request field into
    `cancellation.schema.json`, `tool-spec.schema.json`, and `stream-event.schema.json` into
    each other). `validator_for` below builds an offline registry exactly the way
    `test_memory_contract.py` does: nothing is fetched, the `https://lionel.local/...` URIs
    are identifiers, and the store maps them onto files on disk. ADR-0007's guarantee would
    be a lie if this suite needed the network to check the offline configuration.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

try:
    import jsonschema
except ImportError:  # pragma: no cover - jsonschema is CI tooling
    jsonschema = None

try:
    import tomllib
except ImportError:  # pragma: no cover - 3.11+ per pyproject
    tomllib = None

CONTRACTS = ROOT / "contracts"
EVENTS = CONTRACTS / "events" / "v1"
CORE = CONTRACTS / "core" / "v1"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry_arg(schema):
    store = {}
    for p in CONTRACTS.rglob("*.schema.json"):
        doc = load(p)
        if "$id" in doc:
            store[doc["$id"]] = doc
    try:
        from referencing import Registry, Resource
        registry = Registry().with_resources(
            [(uri, Resource.from_contents(doc)) for uri, doc in store.items()])
        return {"registry": registry}
    except ImportError:
        return {"resolver": jsonschema.RefResolver(base_uri="", referrer=schema, store=store)}


def validator_for(schema: dict):
    cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft202012Validator)
    return cls(schema, **_registry_arg(schema))


def valid(schema: dict, instance) -> bool:
    return validator_for(schema).is_valid(instance)


class BrainContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool_spec = load(EVENTS / "tool-spec.schema.json")
        cls.stream = load(EVENTS / "stream-event.schema.json")
        cls.request = load(EVENTS / "provider-request.schema.json")
        cls.response = load(EVENTS / "provider-response.schema.json")
        cls.caps = load(EVENTS / "provider-capabilities.schema.json")
        cls.cancellation = load(EVENTS / "cancellation.schema.json")
        cls.core_health = load(CORE / "health-status.schema.json")


class TestTheContractsAgreeWhereTheyShould(BrainContracts):
    """The coherence that already holds. Here so that losing it is a failure rather than a
    thing somebody notices later."""

    def test_the_provider_enum_is_the_same_everywhere_it_appears(self):
        enums = {
            "provider-capabilities": self.caps["properties"]["provider"]["enum"],
            "provider-response": self.response["properties"]["provider"]["enum"],
            "stream-event": self.stream["properties"]["provider"]["enum"],
        }
        first = enums["provider-capabilities"]
        for where, values in enums.items():
            with self.subTest(schema=where):
                self.assertEqual(first, values,
                                 f"{where} lists different providers. ADR-0001 ships three; "
                                 f"a fourth added in one schema and not the others is a "
                                 f"provider that exists for telemetry and not for health.")

    @unittest.skipIf(tomllib is None, "tomllib requires Python 3.11+")
    def test_the_configured_provider_and_its_fallbacks_are_in_the_enum(self):
        """`[brain] provider = "ollama"` is what actually gets constructed. A value the
        contract does not list is a startup failure that no gate would have caught."""
        cfg = tomllib.loads((ROOT / "config" / "lionel.toml").read_text(encoding="utf-8"))
        allowed = set(self.caps["properties"]["provider"]["enum"])
        brain = cfg["brain"]
        self.assertIn(brain["provider"], allowed)
        for name in brain["fallback_chain"]:
            with self.subTest(provider=name):
                self.assertIn(name, allowed)

    def test_the_request_offers_tools_as_the_tool_spec_ir(self):
        """ADR-0009's whole argument: nothing above the adapter constructs a vendor shape.
        If `tools` ever stops being a `$ref` to ToolSpec, provider independence has become
        a comment."""
        self.assertEqual(
            "https://lionel.local/contracts/events/v1/tool-spec.schema.json",
            self.request["properties"]["tools"]["items"]["$ref"])


@unittest.skipIf(jsonschema is None, "jsonschema not installed (pyproject `ci` extra)")
class TestHealthStatusIsOneContractNow(BrainContracts):
    """**ADR-0039 item 1, inverted.** `provider-capabilities.$defs.HealthStatus` was a
    second, incompatible definition of the health report — `additionalProperties: false`
    with no `service` field, next to a core schema that required one. No object could
    satisfy both. It is now a `$ref` to `core/v1/health-status.schema.json`, so there is one
    HealthStatus, and Phase 3's `health()` DoD clause has a shape to return.
    """

    def setUp(self):
        self.report = {"service": "brain_gateway", "live": True, "ready": False,
                       "state": "loading", "checked_at": "2026-09-02T06:00:00Z",
                       "load_progress": 0.4}

    def test_the_core_schema_claims_the_brain_gateway_as_a_producer(self):
        """What makes the two definitions the same concept rather than unrelated shapes."""
        self.assertIn("brain_gateway", self.core_health["x-lionel"]["producer"])

    def test_provider_capabilities_health_status_refs_the_core_schema(self):
        ref = self.caps["$defs"]["HealthStatus"].get("$ref")
        self.assertEqual(
            "https://lionel.local/contracts/core/v1/health-status.schema.json", ref,
            "provider-capabilities.$defs.HealthStatus is no longer a $ref to the core "
            "schema. If a second inline definition was reintroduced, ADR-0039 item 1 has "
            "regressed.")

    def test_a_core_shaped_report_satisfies_both(self):
        self.assertTrue(valid(self.core_health, self.report))
        self.assertTrue(valid(self.caps["$defs"]["HealthStatus"], self.report),
                        "provider-capabilities.HealthStatus rejects a report the core "
                        "schema accepts — they are supposed to be the same schema now.")

    def test_starting_and_shutting_down_are_valid_through_either_name(self):
        for state in ("starting", "shutting_down"):
            with self.subTest(state=state):
                report = dict(self.report, state=state)
                self.assertTrue(valid(self.core_health, report))
                self.assertTrue(valid(self.caps["$defs"]["HealthStatus"], report),
                                f"`{state}` is valid in the core schema and not reachable "
                                f"through provider-capabilities' HealthStatus — the two "
                                f"state enums have drifted apart again.")


@unittest.skipIf(jsonschema is None, "jsonschema not installed (pyproject `ci` extra)")
class TestUsageCanSayTheCountsAreEstimatedInBothPlaces(BrainContracts):
    """**ADR-0039 item 2, inverted.** `token_counts_estimated` existed only on the terminal
    `ProviderResponse.usage` and not on `StreamEvent.$defs.Usage`, both
    `additionalProperties: false` — so the flag telling the quota guard not to trust the
    number was unavailable at the one point (mid-stream) where the guard, which *halts
    generation*, actually runs. It is now on both.
    """

    def setUp(self):
        self.stream_usage = self.stream["$defs"]["Usage"]
        self.response_usage = self.response["properties"]["usage"]

    def test_a_streamed_usage_event_can_say_the_counts_are_estimated(self):
        counted = {"input_tokens": 100, "output_tokens": 50, "token_counts_estimated": True}
        self.assertTrue(valid(self.response_usage, counted))
        self.assertTrue(valid(self.stream_usage, counted),
                        "StreamEvent.Usage rejects token_counts_estimated again — the quota "
                        "guard has nothing to read mid-stream, which is ADR-0039 item 2's "
                        "whole point.")

    def test_the_two_usage_objects_now_carry_the_same_fields(self):
        stream_fields = set(self.stream_usage["properties"])
        response_fields = set(self.response_usage["properties"])
        self.assertEqual(response_fields, stream_fields,
                         "StreamEvent.Usage and ProviderResponse.usage have different "
                         "fields again. ADR-0039 made them identical; anything not "
                         "reachable on both was the exact gap it closed.")


@unittest.skipIf(jsonschema is None, "jsonschema not installed (pyproject `ci` extra)")
class TestIdentifiersArePinnedInOnePlaceOnly(BrainContracts):
    """**ADR-0039 items 3 and 4, inverted.** Both were the G2 defect shape one step earlier:
    `QdrantBackend` could not store a conforming record because ids were pinned in the
    contract and unpinned in the adapter. Here two brain contracts named an identifier
    without carrying the constraint that defines it. Both now `$ref` the defining schema
    instead of re-typing `string`.
    """

    def test_the_request_cancellation_token_id_refs_the_cancellation_schema(self):
        """`cancellation.schema.json` pins `token_id` to a ULID; `ProviderRequest` called
        its copy `string` with no pattern, so the empty string satisfied ADR-0025's
        "Non-optional" cancellation token. It now refs the definition directly."""
        field = self.request["properties"]["cancellation_token_id"]
        self.assertEqual(
            "https://lionel.local/contracts/events/v1/cancellation.schema.json#/properties/token_id",
            field.get("$ref"))
        self.assertFalse(valid(field, ""),
                         "the empty string is still a valid cancellation token id")
        self.assertTrue(valid(field, "01JQ4XB2M5N8P1QRST2VWX3YZA"))

    def test_reported_tool_names_ref_tool_specs_pattern(self):
        """`ToolSpec.name` is `<capability>.<operation>`, lowercase by construction, citing
        ADR-0023: naive `.lower()` under a Turkish locale maps `I` to dotless `ı` and
        silently breaks comparison. `ToolCallDelta.name` and
        `ProviderResponse.tool_calls[].name` name the same tool and used to constrain
        nothing — `İSTANBUL.read` validated in both. It no longer does."""
        expected_ref = "https://lionel.local/contracts/events/v1/tool-spec.schema.json#/properties/name"
        delta_name = self.stream["$defs"]["ToolCallDelta"]["properties"]["name"]
        call_name = self.response["properties"]["tool_calls"]["items"]["properties"]["name"]
        for where, field in (("StreamEvent.ToolCallDelta", delta_name),
                             ("ProviderResponse.tool_calls", call_name)):
            with self.subTest(schema=where):
                self.assertEqual(expected_ref, field.get("$ref"),
                                 f"{where}.name no longer refs ToolSpec.name")
                self.assertFalse(valid(field, "İSTANBUL.read"),
                                 f"{where} still accepts a tool name ToolSpec forbids")
                self.assertTrue(valid(field, "fs.read"))


@unittest.skipIf(jsonschema is None, "jsonschema not installed (pyproject `ci` extra)")
class TestStopReasonIsOneEnumNow(BrainContracts):
    """**ADR-0039 item 5, inverted.** `StreamEvent.$defs.StopReason` and
    `ProviderResponse.stop_reason` were two verbatim copies of one enum with no `$ref`
    between them — identical the day this was written, and nothing would have noticed the
    day they stopped being identical. Both now resolve to `StreamEvent.$defs.StopReasonValues`.
    """

    def test_stream_event_stop_reason_resolves_to_stop_reason_values(self):
        self.assertEqual(
            "https://lionel.local/contracts/events/v1/stream-event.schema.json#/$defs/StopReasonValues",
            self.stream["$defs"]["StopReason"].get("$ref"))

    def test_provider_response_stop_reason_refs_the_same_definition(self):
        self.assertEqual(
            "https://lionel.local/contracts/events/v1/stream-event.schema.json#/$defs/StopReasonValues",
            self.response["properties"]["stop_reason"].get("$ref"))

    def test_both_accept_every_value_and_reject_an_unknown_one(self):
        values = self.stream["$defs"]["StopReasonValues"]["enum"]
        for value in values:
            with self.subTest(value=value):
                self.assertTrue(valid(self.stream["$defs"]["StopReason"], value))
                self.assertTrue(valid(self.response["properties"]["stop_reason"], value))
        self.assertFalse(valid(self.stream["$defs"]["StopReason"], "refusal"))
        self.assertFalse(valid(self.response["properties"]["stop_reason"], "refusal"))


@unittest.skipIf(jsonschema is None, "jsonschema not installed (pyproject `ci` extra)")
class TestQuotaGuardAgreesWithTheStopReasonContract(BrainContracts):
    """`QuotaGuard` (`Phase3_Entry_Checklist.md` item 8) hands its `stop_reason` string
    straight to whichever terminal event a caller is about to emit. If that string ever
    stops being a member of `StopReasonValues`, the guard would produce an event the
    contract rejects — silently, since `QuotaGuard` has no schema of its own to check
    against. This is the check."""

    def test_quota_guards_stop_reason_is_a_valid_stop_reason(self):
        from lionel.brain.accounting import BrainQuotaConfig, QuotaGuard

        cfg = BrainQuotaConfig(max_tokens_per_turn=10, max_spend_per_day_usd=5.0,
                               on_exceeded="halt")
        guard = QuotaGuard(cfg)
        verdict = guard.observe("turn-1", {"output_tokens": 100})
        self.assertTrue(verdict.must_halt)
        self.assertTrue(valid(self.stream["$defs"]["StopReasonValues"],
                              verdict.stop_reason))


class TestIdenticalToolSpecProducesAValidNativeSchemaForAllThreeProviders(BrainContracts):
    """`MASTER_PLAN_v2.md` §10 Phase 3 DoD, first clause: *"identical `ToolSpec` produces a
    valid native tool schema for all three providers."* Each provider's own unit test
    exercises its `_translate_tool` against a tool dict it invents for itself — correct,
    but not what the DoD actually asks: the SAME `ToolSpec` instance, fed to all three, each
    producing a shape valid under that provider's own native contract. Nothing before this
    test did that in one place; three individually-correct translators is not the same claim
    as one shared input producing three individually-correct outputs.
    """

    def test_one_tool_spec_survives_all_three_translators(self):
        from lionel.brain.providers.anthropic_provider import _translate_tool as to_anthropic
        from lionel.brain.providers.llamacpp_provider import _translate_tool as to_llamacpp
        from lionel.brain.providers.ollama_provider import _translate_tool as to_ollama

        tool = {
            "name": "fs.read", "description": "Read a file's contents.",
            "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                             "required": ["path"]},
            "side_effect": "read", "trust_required": "any",
        }
        self.assertTrue(valid(self.tool_spec, tool),
            "the shared fixture must itself be a valid ToolSpec, or the test proves nothing")

        anthropic_native = to_anthropic(tool)
        self.assertEqual({"name", "description", "input_schema"}, set(anthropic_native))
        self.assertEqual("fs.read", anthropic_native["name"])
        self.assertEqual(tool["input_schema"], anthropic_native["input_schema"])

        for name, translate in (("ollama", to_ollama), ("llamacpp", to_llamacpp)):
            with self.subTest(provider=name):
                native = translate(tool)
                self.assertEqual("function", native["type"])
                fn = native["function"]
                self.assertEqual({"name", "description", "parameters"}, set(fn))
                self.assertEqual("fs.read", fn["name"])
                self.assertEqual(tool["input_schema"], fn["parameters"])


class TestNoAdapterSelfAssertsToolCallReliability(unittest.TestCase):
    """`ProviderCapabilities.tool_call_reliability`'s own schema description: *"Set from
    the eval harness (ADR-0021), not self-asserted."* The first draft of both `ollama`
    and `anthropic` violated this — each hardcoded a value — until writing `llamacpp`
    surfaced the inconsistency by comparison. Fixed in all three at once; this is what
    keeps a fourth adapter from quietly reintroducing it."""

    def test_none_of_the_three_adapters_set_the_field(self):
        from lionel.brain.providers.anthropic_provider import AnthropicProvider
        from lionel.brain.providers.llamacpp_provider import LlamaCppProvider
        from lionel.brain.providers.ollama_provider import OllamaProvider

        providers = [
            ("ollama", OllamaProvider("http://x", "m", 8192)),
            ("anthropic", AnthropicProvider("sk-fake", "m", 200000, 4096)),
            ("llamacpp", LlamaCppProvider("m.gguf", 8192, 4096)),
        ]
        for name, provider in providers:
            with self.subTest(provider=name):
                self.assertNotIn("tool_call_reliability", provider.capabilities())


if __name__ == "__main__":
    unittest.main()
