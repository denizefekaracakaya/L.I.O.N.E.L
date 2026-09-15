"""Concrete `BrainProvider` adapters.  ADR-0001, ADR-0009, ADR-0040.

The only package that may import a vendor SDK or a provider's own HTTP surface directly.
`ARCH-002` and `ARCH-018` enforce the two halves of the same ADR-0001 sentence from outside
this package: nothing elsewhere may branch on a provider's name, and nothing elsewhere may
import a module from in here.

Each adapter implements `lionel.coordinators.BrainProvider` structurally (`stream`,
`capabilities`, `health`) — by duck typing, so this package does not import
`lionel.coordinators` and `lionel.coordinators` does not import this package. ADR-0001's
sentence, both directions: *"core/turn_executor imports BrainProvider and nothing else."*
"""
from __future__ import annotations
