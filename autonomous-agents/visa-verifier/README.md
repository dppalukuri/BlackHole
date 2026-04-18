# visa-verifier

Background agent that verifies visa requirements against official government sources and produces a curated dataset for the VisaPathway site.

**Auth:** uses the user's Claude Code subscription (no ANTHROPIC_API_KEY required). The agent invokes the `claude` CLI in non-interactive mode, which authenticates via the same OAuth Claude Code already uses.

## Prerequisites

- `claude` CLI installed and logged in (`claude setup-token` or `/login` once)
- Python 3.10+

## First run (seed the top 5 passports × top 20 destinations = 100 entries)

```bash
cd autonomous-agents/visa-verifier
python agent.py --sync
```

`--sync` copies `output/verified-visas.json` into the Astro site's `public/data/` so the next site build picks it up.

Model: `haiku` by default. Override with `--model sonnet` (better quality, slower) or `--model opus` (best, much slower).

## See what it's about to do without spending anything

```bash
python agent.py --dry-run
```

## Common invocations

```bash
python agent.py --only-passport India          # one passport, all destinations
python agent.py --only-destination Japan       # one destination, all passports
python agent.py --limit 5                      # cheap smoke test
python agent.py --watch 21600 --sync           # run every 6 hours
python agent.py --ttl-days 7                   # re-verify anything older than a week
python agent.py --parallel 4 --sync            # 4 workers in parallel (~4x faster)
```

## Second-opinion validation (Sonnet over Haiku)

Haiku does the bulk verification (fast, cheap). For quality polish, run a
second pass with Sonnet and flag disagreements:

```bash
python validate.py --parallel 4 --sync              # full sonnet re-check
python validate.py --only-passport India            # subset
python validate.py --model opus --limit 20          # paranoid-mode for top entries
python validate.py --dry-run                        # preview, no API calls
```

Each entry gets inline validation metadata (`validated_by`, `validated_at`,
`validation_result` ∈ `agree|differ-status|differ-days|error`). Disagreements
are also aggregated into `output/validation-issues.json` for quick review.

When Haiku re-verifies an entry (e.g. on the next scheduled run), it replaces
the entry — which automatically clears stale validation metadata. Validation
TTL defaults to 30 days, so you won't re-spend tokens on entries already
checked recently.

## Parallel runs

Each `claude -p` call is an independent subprocess, so `--parallel N` spawns
N workers concurrently. The main thread serializes all writes to
`output/verified-visas.json`, so there's no race.

- `--parallel 1` (default) — sequential, ~85s per pair
- `--parallel 3` — conservative; ~30s per pair effective
- `--parallel 4–6` — aggressive; watch for rate-limit retries in the output

Subscription usage is bursty with N>3 — if you see many `rate-limited; sleeping 30s`
lines, back off. The agent auto-retries rate-limited calls once after 30s.

## How to expand scope

Edit `config.json` — add passports or destinations to the arrays. The agent is idempotent: already-verified pairs within TTL are skipped.

## Full docs

See `CLAUDE.md`.
