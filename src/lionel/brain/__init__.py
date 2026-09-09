"""The Brain Gateway.  ADR-0001, ADR-0009.

EMPTY BY DESIGN, FOR NOW
    `brain/providers/`, `brain/contract/` and `brain/toolspec/` are scaffolding with no
    code in them yet. `Phase3_Entry_Checklist.md` items 2-4 are decisions reserved to
    Efe (`Architecture_Freeze.md` §4) -- which provider clients to declare, how the
    transcript-replay gate works, and whether `anthropic` may hold a credential at L0 --
    and nothing here gets written ahead of those decisions. Writing a `BrainProvider`
    against contracts and a client library nobody has chosen yet is exactly the failure
    §4 exists to prevent.

`brain/accounting/` IS THE EXCEPTION
    `[brain.quota]` was already chosen by ADR-0009. Enforcing it needs no provider and
    no ADR -- `Architecture_Freeze.md` §4 permits "implementation under `src/lionel/`
    conforming to frozen contracts" without one, and `Phase3_Entry_Checklist.md` item 8
    asked for exactly this: "`[brain.quota]` already exists ... Enforcement is
    implementation."
"""
from __future__ import annotations
