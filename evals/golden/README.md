# `evals/golden/` — golden cases for the G3 replay harness

**Empty as of this writing.** `evals/harness`'s own module docstring explains why: no
`anthropic` credential and no reachable `ollama` were available while the harness
(`ADR-0041`) was built, and a case directory's presence here is meant to mean *recorded*,
never *fabricated to make a run green*. This file exists so the directory itself survives
being committed — git does not track empty directories — and so the format is written down
before the first real case needs it.

## Adding a case

```
evals/golden/<case_id>/
  case.json          # required
  anthropic.json      # present once `--live` has recorded against anthropic
  ollama.json          # present once `--live` has recorded against ollama
```

`case.json`:

```json
{
  "messages": [{"role": "user", "content": "read config.toml for me"}],
  "tools": [{
    "name": "fs.read", "description": "Read a file's contents.",
    "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                     "required": ["path"]},
    "side_effect": "read", "trust_required": "any"
  }],
  "expected_tool_calls": [{"name": "fs.read", "arguments": {"path": "config.toml"}}],
  "notes": "why this case exists, and what it is meant to catch"
}
```

`expected_tool_calls` compares by `name` and `arguments` only — `evals/harness`'s
`tool_calls_equivalent()`, order-insensitive. `call_id` and `index` are adapter-internal
correlation fields, not part of what a case can pin.

`<provider>.json` is a `StreamEvent` sequence — literally
`json.dumps(list(provider.stream(request)))` from a real `--live` run, written by
`evals.harness.record_response()`, never hand-typed. A case directory with a `case.json`
but no `<provider>.json` reports `not_recorded` for that provider when replayed —
`bash`-equivalent `skip`, not a failure, and not silently absent from the report either.

## Running the suite

```bash
python3 evals/harness/run.py
```

Replays every case against `anthropic` and `ollama`. Not `llamacpp` — `ADR-0041`'s own
reasoning: its tool-calling reliability is the thing under study, not a fixture to measure
against.

## Recording (`--live`)

Not wired into `evals/harness/run.py` yet. Recording needs a reachable `ollama` and a real
`anthropic` credential, neither of which existed in the environment this harness was built
in — the same gap every `BrainProvider` adapter's own docstring already names. Building the
recording CLI without being able to run it end-to-end would be exactly the kind of
unexercised code this repository's own history (`Phase2_Final_Signoff.md` §1: *"every one
of the four defects was in something reviewed, frozen, and never executed"*) keeps finding.
It is the next piece, written the day a host with both is available.
