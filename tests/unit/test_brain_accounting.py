"""The Brain Gateway's quota enforcement.  ADR-0009, ADR-0027 layer 1.

`Phase3_Entry_Checklist.md` item 8: "`[brain.quota]` already exists ... Enforcement is
implementation." No provider, no gateway, and no ADR is needed for this file — only the
decision ADR-0009 already made, read from config the way `MemoryConfig` reads `[memory]`.

Both fields the config-loading tests exercise are the reason `QuotaGuard` exists at all:
`max_tokens_per_turn` is a per-turn ceiling on a still-streaming generation, and
`max_spend_per_day_usd` is what ADR-0009 calls "a liability" without one. The clock is
scripted throughout — a day-boundary test that had to wait for midnight UTC would be a test
nobody could run.
"""
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from lionel.brain.accounting import (  # noqa: E402
    ESTIMATED_TOKEN_SAFETY_MARGIN,
    BrainConfigurationError,
    BrainQuotaConfig,
    QuotaGuard,
)

T0 = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def usage(output_tokens: int, *, estimated: bool = False, cost=None) -> dict:
    return {
        "input_tokens": 0,
        "output_tokens": output_tokens,
        "token_counts_estimated": estimated,
        "estimated_cost_usd": cost,
    }


class ScriptedClock:
    """A callable `now`, advanced by the test rather than by the wall clock."""

    def __init__(self, start: datetime):
        self.t = start

    def __call__(self) -> datetime:
        return self.t

    def advance(self, **kwargs) -> None:
        self.t += timedelta(**kwargs)


class TestConfig(unittest.TestCase):
    def test_the_shipped_config_loads(self):
        c = BrainQuotaConfig.from_toml()
        self.assertEqual(c.max_tokens_per_turn, 8192)
        self.assertEqual(c.max_spend_per_day_usd, 5.0)
        self.assertEqual(c.on_exceeded, "halt")

    def test_a_missing_file_is_refused(self):
        with self.assertRaises(BrainConfigurationError) as cm:
            BrainQuotaConfig.from_toml(ROOT / "no-such-config.toml")
        self.assertIn("ADR-0009", str(cm.exception))

    def test_a_missing_quota_section_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "lionel.toml"
            p.write_text('[brain]\nprovider="ollama"\n', encoding="utf-8", newline="")
            with self.assertRaises(BrainConfigurationError) as cm:
                BrainQuotaConfig.from_toml(p)
            self.assertIn("[brain.quota]", str(cm.exception))

    def test_a_missing_key_names_itself(self):
        """Every key here is load-bearing; a missing one must not be silently
        substituted by a default nobody chose."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "lionel.toml"
            p.write_text(
                '[brain.quota]\nmax_tokens_per_turn=100\non_exceeded="halt"\n',
                encoding="utf-8", newline="")
            with self.assertRaises(BrainConfigurationError) as cm:
                BrainQuotaConfig.from_toml(p)
            self.assertIn("max_spend_per_day_usd", str(cm.exception))

    def test_an_unknown_on_exceeded_value_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "lionel.toml"
            p.write_text(
                '[brain.quota]\nmax_tokens_per_turn=100\nmax_spend_per_day_usd=1.0\n'
                'on_exceeded="ignore"\n', encoding="utf-8", newline="")
            with self.assertRaises(BrainConfigurationError) as cm:
                BrainQuotaConfig.from_toml(p)
            self.assertIn("halt", str(cm.exception))
            self.assertIn("warn", str(cm.exception))

    def test_a_non_positive_token_ceiling_is_refused(self):
        """A ceiling of 0 halts every turn before it starts -- a different decision
        than 'no ceiling', and one that has to be made on purpose."""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "lionel.toml"
            p.write_text(
                '[brain.quota]\nmax_tokens_per_turn=0\nmax_spend_per_day_usd=1.0\n'
                'on_exceeded="halt"\n', encoding="utf-8", newline="")
            with self.assertRaises(BrainConfigurationError):
                BrainQuotaConfig.from_toml(p)

    def test_negative_spend_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "lionel.toml"
            p.write_text(
                '[brain.quota]\nmax_tokens_per_turn=100\nmax_spend_per_day_usd=-1.0\n'
                'on_exceeded="halt"\n', encoding="utf-8", newline="")
            with self.assertRaises(BrainConfigurationError):
                BrainQuotaConfig.from_toml(p)


class TestPerTurnTokenCeiling(unittest.TestCase):
    def setUp(self):
        self.cfg = BrainQuotaConfig(max_tokens_per_turn=100, max_spend_per_day_usd=5.0,
                                    on_exceeded="halt")
        self.clock = ScriptedClock(T0)
        self.guard = QuotaGuard(self.cfg, now=self.clock)

    def test_under_the_ceiling_does_not_halt(self):
        v = self.guard.observe("turn-1", usage(50))
        self.assertFalse(v.must_halt)
        self.assertEqual(v.turn_tokens, 50)
        self.assertIsNone(v.stop_reason)

    def test_tokens_accumulate_across_deltas_within_one_turn(self):
        self.guard.observe("turn-1", usage(60))
        v = self.guard.observe("turn-1", usage(30))
        self.assertEqual(v.turn_tokens, 90)
        self.assertFalse(v.must_halt)

    def test_crossing_the_ceiling_halts(self):
        v = self.guard.observe("turn-1", usage(150))
        self.assertTrue(v.must_halt)
        self.assertEqual(v.stop_reason, "quota_exceeded")
        self.assertIn("150", v.reason)
        self.assertIn("100-token", v.reason)

    def test_exactly_at_the_ceiling_does_not_halt(self):
        """A ceiling is crossed, not touched -- `max_tokens_per_turn=100` permits
        exactly 100."""
        v = self.guard.observe("turn-1", usage(100))
        self.assertFalse(v.must_halt)

    def test_a_new_turn_id_resets_the_count(self):
        self.guard.observe("turn-1", usage(90))
        v = self.guard.observe("turn-2", usage(10))
        self.assertEqual(v.turn_tokens, 10)
        self.assertFalse(v.must_halt)

    def test_explicit_start_turn_resets_a_repeated_id(self):
        """`observe()`'s auto-reset only fires on a CHANGED id. A caller that knows a
        turn genuinely restarted under the same id needs the explicit call."""
        self.guard.observe("turn-1", usage(90))
        self.guard.start_turn("turn-1")
        v = self.guard.observe("turn-1", usage(10))
        self.assertEqual(v.turn_tokens, 10)


class TestEstimatedCountsGetASafetyMargin(unittest.TestCase):
    """ADR-0009's Usage field description, verbatim: "the quota guard then applies a
    safety margin rather than trusting the number." """

    def setUp(self):
        self.cfg = BrainQuotaConfig(max_tokens_per_turn=100, max_spend_per_day_usd=5.0,
                                    on_exceeded="halt")
        self.guard = QuotaGuard(self.cfg, now=ScriptedClock(T0))

    def test_an_estimated_count_is_inflated_by_the_margin(self):
        v = self.guard.observe("turn-1", usage(80, estimated=True))
        self.assertEqual(v.turn_tokens, round(80 * ESTIMATED_TOKEN_SAFETY_MARGIN))

    def test_a_real_count_is_trusted_exactly(self):
        v = self.guard.observe("turn-1", usage(80, estimated=False))
        self.assertEqual(v.turn_tokens, 80)

    def test_the_margin_can_turn_a_pass_into_a_halt(self):
        """80 real tokens is under a 100 ceiling; 80 estimated tokens, with 20%
        headroom, is 96 -- still under. 85 estimated is 102, and now it is not."""
        v = self.guard.observe("turn-1", usage(85, estimated=True))
        self.assertTrue(v.must_halt)


class TestOnExceededWarnDoesNotHalt(unittest.TestCase):
    def test_warn_reports_the_breach_but_lets_generation_continue(self):
        cfg = BrainQuotaConfig(max_tokens_per_turn=100, max_spend_per_day_usd=5.0,
                               on_exceeded="warn")
        guard = QuotaGuard(cfg, now=ScriptedClock(T0))
        v = guard.observe("turn-1", usage(150))
        self.assertFalse(v.must_halt)
        self.assertIsNotNone(v.reason)
        self.assertIsNone(v.stop_reason)

    def test_warn_keeps_accumulating_past_the_ceiling(self):
        """A caller that ignores a warn verdict and keeps calling should see the count
        keep climbing -- 'warn' is not 'stop counting'."""
        cfg = BrainQuotaConfig(max_tokens_per_turn=100, max_spend_per_day_usd=5.0,
                               on_exceeded="warn")
        guard = QuotaGuard(cfg, now=ScriptedClock(T0))
        guard.observe("turn-1", usage(150))
        v = guard.observe("turn-1", usage(10))
        self.assertEqual(v.turn_tokens, 160)


class TestDailySpendCeiling(unittest.TestCase):
    def setUp(self):
        self.cfg = BrainQuotaConfig(max_tokens_per_turn=1_000_000,
                                    max_spend_per_day_usd=1.0, on_exceeded="halt")
        self.clock = ScriptedClock(T0)
        self.guard = QuotaGuard(self.cfg, now=self.clock)

    def test_spend_accumulates_across_turns_within_one_day(self):
        self.guard.observe("turn-1", usage(1, cost=0.4))
        v = self.guard.observe("turn-2", usage(1, cost=0.4))
        self.assertAlmostEqual(v.day_spend_usd, 0.8)
        self.assertFalse(v.must_halt)

    def test_crossing_the_daily_ceiling_halts(self):
        self.guard.observe("turn-1", usage(1, cost=0.7))
        v = self.guard.observe("turn-2", usage(1, cost=0.7))
        self.assertTrue(v.must_halt)
        self.assertIn("/day ceiling", v.reason)

    def test_a_null_cost_contributes_nothing(self):
        """Null is how a local provider reports zero monetary cost, per the contract's
        own description. A guard that treated null as a KeyError would make ollama
        unusable; one that treated it as $0 by coincidence would be luck, not policy."""
        v = self.guard.observe("turn-1", usage(1, cost=None))
        self.assertEqual(v.day_spend_usd, 0.0)

    def test_spend_resets_at_the_day_boundary(self):
        self.guard.observe("turn-1", usage(1, cost=0.9))
        self.clock.advance(hours=13)  # past UTC midnight from T0 = 12:00
        v = self.guard.observe("turn-2", usage(1, cost=0.9))
        self.assertAlmostEqual(v.day_spend_usd, 0.9)
        self.assertFalse(v.must_halt)

    def test_spend_does_not_reset_within_the_same_day(self):
        self.guard.observe("turn-1", usage(1, cost=0.5))
        self.clock.advance(hours=2)  # still 2026-09-10
        v = self.guard.observe("turn-2", usage(1, cost=0.5))
        self.assertAlmostEqual(v.day_spend_usd, 1.0)


class TestTheTerminalUsageObjectIsAlsoAccepted(unittest.TestCase):
    """ADR-0039 made `StreamEvent.Usage` and `ProviderResponse.usage` the same shape.
    `observe()` does not care which one it was handed."""

    def test_a_provider_response_shaped_usage_is_accepted(self):
        cfg = BrainQuotaConfig(max_tokens_per_turn=100, max_spend_per_day_usd=5.0,
                               on_exceeded="halt")
        guard = QuotaGuard(cfg, now=ScriptedClock(T0))
        provider_response_usage = {
            "input_tokens": 40, "output_tokens": 30, "cached_input_tokens": 0,
            "estimated_cost_usd": 0.01, "token_counts_estimated": False,
        }
        v = guard.observe("turn-1", provider_response_usage)
        self.assertEqual(v.turn_tokens, 30)
        self.assertFalse(v.must_halt)


if __name__ == "__main__":
    unittest.main()
