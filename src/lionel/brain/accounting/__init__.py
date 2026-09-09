"""Quota enforcement for the Brain Gateway.  ADR-0009.

WHAT THIS ENFORCES
    `[brain.quota]` from `config/lionel.toml`, read rather than defaulted, the way
    `MemoryConfig` reads `[memory]`:

        max_tokens_per_turn      a per-turn ceiling on generated output tokens
        max_spend_per_day_usd    a per-calendar-day ceiling on estimated cost
        on_exceeded              "halt" stops generation; "warn" lets it continue and
                                  records that the ceiling was crossed

    ADR-0009's own words: "L3 without a ceiling is a liability." An autonomous loop
    against a metered API needs a hard stop, which is the reason `estimated_cost_usd`
    exists on every usage object in the first place.

WHAT THIS DOES NOT DO
    It does not call a provider, does not issue a `CancellationToken`, and does not
    know what a `BrainProvider` is -- none of the three exist yet
    (`Phase3_Entry_Checklist.md` items 2-4 are still Efe's to decide).
    `QuotaGuard` is the decision, not the action: it is fed `StreamEvent.Usage` and
    `ProviderResponse.usage` objects as they arrive and returns a verdict. The caller
    -- `turn_executor` or the brain gateway, once either exists -- is what turns
    `must_halt: True` into an actual `CancellationToken` (ADR-0025).

WHY MID-STREAM, NOT ONLY THE TERMINAL RESPONSE
    ADR-0039 found that `StreamEvent.Usage` and `ProviderResponse.usage` disagreed
    about `token_counts_estimated` -- the flag existed only on the object that arrives
    AFTER generation completes, at the one point where a ceiling meant to HALT
    generation is already too late to act on it. That was fixed by making the two
    objects identical; `observe()` below is written to be called on the streamed one,
    which is the object the fix was for. It also accepts the terminal
    `ProviderResponse.usage`, since ADR-0039 made the two shapes the same and a caller
    that only sees the aggregated result should still get a real verdict.

THE CLOCK IS INJECTED
    The daily ceiling needs a day boundary, and a guard that read the wall clock
    directly could only be tested by waiting until midnight UTC. `now` is a callable,
    defaulting to `datetime.now(timezone.utc)` -- the same shape `MemoryService`'s decay
    tests use it for.

AN ESTIMATED COUNT GETS A SAFETY MARGIN, NOT TRUST
    `ProviderResponse.usage.token_counts_estimated`'s own contract description: "the
    quota guard then applies a safety margin rather than trusting the number." That
    margin is `ESTIMATED_TOKEN_SAFETY_MARGIN` below -- a constant, not a config key,
    because `[brain.quota]` is ADR-0009's contract and a fourth key there is a decision
    for whoever amends that ADR, not a default this module gets to invent.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional

__all__ = [
    "BrainConfigurationError",
    "BrainQuotaConfig",
    "QuotaGuard",
    "QuotaVerdict",
]

ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = ROOT / "config" / "lionel.toml"

# ADR-0009's Usage field description names this by name: "the quota guard ... applies
# a safety margin rather than trusting the number." 20% headroom on a provider's own
# estimate -- chosen the way ADR-0009's ceiling itself was, conservative rather than
# measured, because the failure mode of guessing low is an ignored ceiling, and the
# failure mode of guessing high is a turn that halts a little early.
ESTIMATED_TOKEN_SAFETY_MARGIN = 1.2

_VALID_ON_EXCEEDED = ("halt", "warn")


class BrainConfigurationError(ValueError):
    """`[brain.quota]` is missing or malformed.

    Its own exception class, matching `MemoryConfigurationError` -- a caller that
    catches one class per config section is a caller that can tell which section
    broke without parsing the message.
    """


@dataclass(frozen=True)
class BrainQuotaConfig:
    """`[brain.quota]` from `config/lionel.toml`. Read rather than defaulted -- ADR-0009
    chose these three keys, and a fourth does not belong here without amending it.
    """

    max_tokens_per_turn: int
    max_spend_per_day_usd: float
    on_exceeded: str  # "halt" | "warn"

    @classmethod
    def from_toml(cls, path: Optional[Path | str] = None) -> "BrainQuotaConfig":
        p = Path(path) if path is not None else CONFIG_PATH
        if not p.is_file():
            raise BrainConfigurationError(
                f"{p} is missing; [brain.quota] is not optional and there is no "
                f"default. ADR-0009: 'L3 without a ceiling is a liability.'"
            )
        data = tomllib.loads(p.read_text(encoding="utf-8"))
        brain = data.get("brain")
        if not brain:
            raise BrainConfigurationError(f"no [brain] section in {p.name} (ADR-0001).")
        quota = brain.get("quota")
        if not quota:
            raise BrainConfigurationError(
                f"no [brain.quota] section in {p.name} (ADR-0009). An autonomous loop "
                f"against a metered API needs a hard stop; without this section there "
                f"is nothing to enforce."
            )
        try:
            cfg = cls(
                max_tokens_per_turn=int(quota["max_tokens_per_turn"]),
                max_spend_per_day_usd=float(quota["max_spend_per_day_usd"]),
                on_exceeded=str(quota["on_exceeded"]),
            )
        except KeyError as e:
            raise BrainConfigurationError(
                f"[brain.quota] in {p.name} is missing {e}. Every key here is "
                f"load-bearing; a missing one would be silently substituted by a "
                f"default that no reviewer chose."
            ) from None
        if cfg.on_exceeded not in _VALID_ON_EXCEEDED:
            raise BrainConfigurationError(
                f"[brain.quota].on_exceeded is {cfg.on_exceeded!r} in {p.name}; must "
                f"be one of {_VALID_ON_EXCEEDED} -- config/lionel.toml's own comment "
                f"names exactly these two."
            )
        if cfg.max_tokens_per_turn <= 0:
            raise BrainConfigurationError(
                f"[brain.quota].max_tokens_per_turn is {cfg.max_tokens_per_turn} in "
                f"{p.name}; a non-positive ceiling halts every turn before it starts, "
                f"which is a different decision than 'no ceiling' and has to be made "
                f"on purpose, not read off a stray value."
            )
        if cfg.max_spend_per_day_usd < 0:
            raise BrainConfigurationError(
                f"[brain.quota].max_spend_per_day_usd is {cfg.max_spend_per_day_usd} "
                f"in {p.name}; negative spend is not a ceiling, it is a typo."
            )
        return cfg


@dataclass(frozen=True)
class QuotaVerdict:
    """What `QuotaGuard.observe()` decided.

    `must_halt` is the only field a caller indifferent to the detail needs to read.
    `stop_reason` is `"quota_exceeded"` exactly when `must_halt` is true -- the same
    string `StreamEvent.StopReasonValues` and `ProviderResponse.stop_reason` (which
    `$ref`s it, per ADR-0039) both accept, so a caller can hand this straight to
    whichever terminal event it is about to emit.
    """

    must_halt: bool
    reason: Optional[str]
    turn_tokens: int
    day_spend_usd: float
    stop_reason: Optional[str] = None


class QuotaGuard:
    """Tracks per-turn tokens and per-day spend against `[brain.quota]`, and says when
    ADR-0009's ceiling has been reached.

    Stateful by necessity -- a ceiling that reset on every call would not be a
    ceiling -- and NOT thread-safe, matching every other turn-scoped object in this
    codebase (ADR-0008: coordinators own state, nothing else does). One guard per
    session, not a singleton: a shared guard would make one turn's spend count against
    another's.
    """

    def __init__(self, config: BrainQuotaConfig, *,
                now: Optional[Callable[[], datetime]] = None):
        self.config = config
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._turn_id: Optional[str] = None
        self._turn_tokens = 0
        self._day: Optional[date] = None
        self._day_spend_usd = 0.0

    def start_turn(self, turn_id: str) -> None:
        """Call once per turn, before its first usage event.

        A guard that inferred a new turn from the id changing would silently reset on
        a REPEATED id too -- `observe()` still does that inference as a safety net,
        but calling this explicitly is what makes "a new turn started" a caller
        decision rather than a guess.
        """
        self._turn_id = turn_id
        self._turn_tokens = 0

    def observe(self, turn_id: str, usage: Mapping[str, object]) -> QuotaVerdict:
        """`usage` is a `StreamEvent.Usage` or `ProviderResponse.usage` object -- ADR-0039
        made the two shapes identical, so either satisfies this.
        """
        if turn_id != self._turn_id:
            self.start_turn(turn_id)

        self._roll_day_if_needed()

        output_tokens = int(usage.get("output_tokens", 0) or 0)
        estimated = bool(usage.get("token_counts_estimated", False))
        self._turn_tokens += (
            round(output_tokens * ESTIMATED_TOKEN_SAFETY_MARGIN) if estimated
            else output_tokens
        )

        cost = usage.get("estimated_cost_usd")
        if cost is not None:
            self._day_spend_usd += float(cost)

        token_breach = self._turn_tokens > self.config.max_tokens_per_turn
        spend_breach = self._day_spend_usd > self.config.max_spend_per_day_usd

        if not (token_breach or spend_breach):
            return QuotaVerdict(False, None, self._turn_tokens, self._day_spend_usd)

        if token_breach:
            reason = (f"turn {turn_id}: {self._turn_tokens} tokens exceeds the "
                      f"{self.config.max_tokens_per_turn}-token ceiling")
        else:
            reason = (f"today: ${self._day_spend_usd:.4f} exceeds the "
                      f"${self.config.max_spend_per_day_usd:.2f}/day ceiling")

        halts = self.config.on_exceeded == "halt"
        return QuotaVerdict(
            must_halt=halts,
            reason=reason,
            turn_tokens=self._turn_tokens,
            day_spend_usd=self._day_spend_usd,
            stop_reason="quota_exceeded" if halts else None,
        )

    def _roll_day_if_needed(self) -> None:
        today = self._now().date()
        if self._day != today:
            self._day = today
            self._day_spend_usd = 0.0
