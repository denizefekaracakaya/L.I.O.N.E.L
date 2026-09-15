"""The five coordinators.  ADR-0008.

WHAT THIS REPLACES
    v1.0's single loop. W1 of MASTER_PLAN_v2 calls it "The God Loop" and the ADR's
    Alternatives Rejected says why "refactor later" was not an option: *"'Later' arrives
    after the state is already entangled."*

    | Coordinator | Owns | Explicitly does not know |
    |---|---|---|
    | SessionCoordinator | session lifecycle, turn queue, conversation state, wake/sleep | how a turn is executed |
    | TurnExecutor | one turn: brain call, tool loop, response assembly | where the brain runs; which provider |
    | ContextAssembler | system prompt, memory recall, history windowing, token budget | the brain's wire format |
    | ToolRouter | capability discovery, policy evaluation, MCP dispatch, result normalisation | what any specific tool does |
    | InterruptController | barge-in detection, cancellation fan-out, cleanup | what is being cancelled |

THE STATE-OWNERSHIP RULE, MADE MECHANICAL
    ADR-0008: *"SessionCoordinator holds all mutable session state. Every other component
    is stateless and receives what it needs as arguments."* And, in the same breath, why:
    it is what lets a cluster service be restarted mid-conversation without losing the
    conversation, and it is a hard prerequisite for L2 (ADR-0007).

    A rule like that decays the first time someone caches something on `self` "just for
    now". So the four stateless coordinators are **frozen dataclasses**: assigning an
    attribute after construction raises. Injected collaborators are fields; conversation
    state cannot be. The verbosity ADR-0008 calls "the property doing the work" is now
    enforced by the language rather than by review.

WHY THESE ARE SHELLS
    MASTER_PLAN_v2 §10 puts these at G1 as *"empty, contract-conforming shells"*. The
    collaborators they need do not exist yet — the Memory Service is G2, the Brain Gateway
    is G3, MCP dispatch is G4. Methods that need them raise `NotYetImplemented` naming the
    gate that brings them, rather than returning a plausible-looking stub. A shell that
    returns `[]` for "recall memories" is indistinguishable from a working recall that
    found nothing, and that difference matters at exactly the wrong moment.

    ToolRouter is the exception, and deliberately: its policy chokepoint is real, because
    `lionel.policy` and `lionel.capabilities` exist. ADR-0008 says policy enforcement has
    *"exactly one chokepoint — ToolRouter — so it cannot be bypassed"*, and a chokepoint
    that is a stub at G1 is a chokepoint someone routes around at G2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Protocol

from lionel.capabilities import CapabilityRegistry
from lionel.policy import Decision, PolicyDecision, PolicyEngine, TrustContext

__all__ = [
    "NotYetImplemented",
    "SessionState",
    "SessionCoordinator",
    "TurnExecutor",
    "ContextAssembler",
    "ToolRouter",
    "InterruptController",
    "STATELESS_COORDINATORS",
]


class NotYetImplemented(NotImplementedError):
    """A shell method whose collaborators arrive at a later gate.

    Distinct from `NotImplementedError` so a test can tell "not built yet" apart from
    "abstract method someone forgot to override".
    """

    def __init__(self, what: str, gate: str) -> None:
        super().__init__(
            f"{what} is not implemented at G1; it arrives with {gate}. This raises rather "
            f"than returning an empty result, because an empty result is indistinguishable "
            f"from a real one that found nothing.")
        self.gate = gate


# ── SessionCoordinator: the one place mutable state is allowed ─────────────────────

class SessionPhase(str, Enum):
    ASLEEP = "asleep"
    LISTENING = "listening"
    EXECUTING = "executing"


@dataclass
class SessionState:
    """Everything mutable about a conversation, in one object with one owner."""
    session_id: str
    phase: SessionPhase = SessionPhase.ASLEEP
    history: list[dict[str, Any]] = field(default_factory=list)
    queued_turns: list[str] = field(default_factory=list)
    current_turn: str | None = None


class SessionCoordinator:
    """Session lifecycle, turn queue, conversation state, wake/sleep.

    The only coordinator with mutable state, and the reason the other four can be frozen.
    It does not know how a turn is executed — `TurnExecutor` is injected and called, never
    inspected.
    """

    def __init__(self, session_id: str, executor: "TurnExecutor | None" = None) -> None:
        self.state = SessionState(session_id=session_id)
        self._executor = executor

    def wake(self) -> None:
        self.state.phase = SessionPhase.LISTENING

    def sleep(self) -> None:
        self.state.phase = SessionPhase.ASLEEP
        self.state.current_turn = None

    def enqueue(self, turn_id: str) -> None:
        self.state.queued_turns.append(turn_id)

    def run_next(self) -> Any:
        if not self.state.queued_turns:
            return None
        if self._executor is None:
            raise NotYetImplemented("turn execution", "G3 (Brain Gateway)")
        turn_id = self.state.queued_turns.pop(0)
        self.state.current_turn = turn_id
        self.state.phase = SessionPhase.EXECUTING
        try:
            return self._executor.execute(turn_id=turn_id, state=self.state)
        finally:
            self.state.current_turn = None
            self.state.phase = SessionPhase.LISTENING


# ── The four stateless coordinators ────────────────────────────────────────────────

class BrainProvider(Protocol):
    """ADR-0001 / ADR-0009. Declared here — not in `lionel.brain` — because ADR-0001 says
    so exactly: *"core/turn_executor imports BrainProvider and nothing else."* This module
    IS `core/turn_executor`, and importing the Protocol from `lionel.brain.providers` would
    put a concrete-adapter package on TurnExecutor's import path even for the Protocol
    alone. `ARCH-018` enforces the consequence: nothing outside `brain/providers/` may
    import a concrete provider.

    Every argument and return value here is the corresponding contract in
    `contracts/events/v1/` as a plain `dict` — `ProviderRequest` in, `StreamEvent` objects
    out of `stream()`, `ProviderCapabilities` from `capabilities()`,
    `contracts/core/v1/health-status.schema.json`'s shape from `health()`. Not typed
    dataclasses: these three methods exist entirely to move JSON-Schema-governed wire
    objects between layers, and a parallel dataclass hierarchy with a `to_dict` for every
    nested `$ref` would be ceremony around objects whose only job is validating against the
    schemas that already define them.

    G1 shipped this as `generate(*, messages, tools)`, untyped and unexercised — no test in
    the repository ever called it. G3's real shape replaces it rather than extending it;
    `ADR-0040`'s adapters (`lionel.brain.providers.*`) implement this structurally, by
    duck typing, with no import of this module required in the other direction.
    """

    def stream(self, request: dict[str, Any]) -> Iterable[dict[str, Any]]:
        """`request` is a `ProviderRequest`. Yields `StreamEvent` objects in order,
        ending with exactly one `type: "done"` event (or `type: "error"`) — the same
        guarantee `contracts/events/v1/stream-event.schema.json`'s discriminated union
        describes. Closing the iterator early (`generator.close()`) is how a caller
        cancels a streaming generation; an adapter must treat `GeneratorExit` as "stop and
        release the connection," not as an error to report through the stream itself."""
        ...

    def capabilities(self) -> dict[str, Any]:
        """A `ProviderCapabilities` object. Never used by a caller to decide behaviour by
        provider identity (ADR-0009) — only by capability flag."""
        ...

    def health(self) -> dict[str, Any]:
        """`contracts/core/v1/health-status.schema.json`'s shape. `live` and `ready` are
        DISTINCT — a model mid-load is live and not ready — which is the entire reason
        this method exists rather than a boolean."""
        ...


@dataclass(frozen=True)
class ContextAssembler:
    """System prompt, memory recall, history windowing, token budget.

    Does not know the brain's wire format: it produces messages, and the Brain Gateway
    (G3) translates them per provider. ADR-0001's rule that no caller branches on provider
    name starts here — if this class knew a wire format, every caller would inherit it.
    """
    token_budget: int = 8192
    memory = None  # G2. A field would imply the collaborator exists.

    def assemble(self, *, state: SessionState, utterance: str) -> list[dict[str, Any]]:
        raise NotYetImplemented("context assembly with memory recall", "G2 (Memory Service)")

    def window(self, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """History windowing needs no collaborator, so it is real rather than a stub."""
        return history[-self.token_budget:] if self.token_budget else list(history)


@dataclass(frozen=True)
class ToolRouter:
    """Capability discovery, policy evaluation, MCP dispatch, result normalisation.

    Does not know what any specific tool does. It authorises and routes by name, side
    effect and trust; a router that understood tool semantics would be the place per-tool
    special cases accumulate, and each one would be a policy decision made outside the
    policy.

    **The single policy chokepoint (ADR-0008).** `authorize()` is real at G1 even though
    `dispatch()` is not, because a chokepoint that does nothing until G4 is a chokepoint
    people learn to route around before G4 arrives.
    """
    registry: CapabilityRegistry
    policy: PolicyEngine

    def discover(self, tier: str = "l1") -> list[str]:
        """Capability names available at a tier. ADR-0007 filters this, not a config flag."""
        return [c.name for c in self.registry.available_at(tier)]

    def authorize(self, *, tool_name: str, trust: TrustContext,
                  call_id: str = "") -> PolicyDecision:
        return self.policy.evaluate(tool_name=tool_name, trust=trust, call_id=call_id)

    def dispatch(self, *, tool_name: str, arguments: dict[str, Any],
                 trust: TrustContext, call_id: str = "") -> Any:
        """Authorize, then dispatch. The order is the invariant.

        A denial raises before anything is sent anywhere. There is deliberately no
        `force`, no `skip_policy`, and no code path that reaches an MCP server without
        passing through `authorize()` first — ADR-0008's chokepoint only means something
        if it is the *only* door.
        """
        decision = self.authorize(tool_name=tool_name, trust=trust, call_id=call_id)
        if decision.decision == Decision.CONFIRM:
            raise NotYetImplemented(
                f"per-invocation confirmation for `{tool_name}`", "G4 (Capability Services)")
        if not decision.allowed:
            raise PermissionError(
                f"{tool_name}: {decision.decision} by rule {decision.rule_name!r}"
                + (f" — {decision.reason}" if decision.reason else ""))
        raise NotYetImplemented(f"MCP dispatch of `{tool_name}`", "G4 (Capability Services)")


@dataclass(frozen=True)
class TurnExecutor:
    """One turn: brain call, tool loop, response assembly.

    Does not know where the brain runs or which provider answers — that is the Brain
    Gateway's business (ADR-0001, ADR-0009), and it is why L2 can move inference into the
    cluster without this class changing.
    """
    router: ToolRouter
    assembler: ContextAssembler
    brain: BrainProvider | None = None

    def execute(self, *, turn_id: str, state: SessionState) -> Any:
        if self.brain is None:
            raise NotYetImplemented("turn execution", "G3 (Brain Gateway)")
        raise NotYetImplemented("the tool loop", "G3 (Brain Gateway)")


@dataclass(frozen=True)
class InterruptController:
    """Barge-in detection, cancellation fan-out, cleanup.

    Does not know what is being cancelled. ADR-0025 gives cancellation an owner and a
    defined fan-out path; the things it fans out to register themselves.
    """
    supervisor: Any = None  # lionel.platform.process_supervisor.ProcessSupervisor

    def cancel(self, *, turn_id: str) -> None:
        raise NotYetImplemented("cancellation fan-out", "G7 (ADR-0025)")

    def kill_supervised_processes(self) -> None:
        """The one cancellation primitive that exists at G1 (ADR-0014)."""
        if self.supervisor is None:
            raise NotYetImplemented("process cancellation", "a supervisor being injected")
        self.supervisor.shutdown()


# Named here rather than inferred, so the contract test asserts a list someone wrote down.
STATELESS_COORDINATORS: tuple[type, ...] = (
    TurnExecutor, ContextAssembler, ToolRouter, InterruptController,
)
