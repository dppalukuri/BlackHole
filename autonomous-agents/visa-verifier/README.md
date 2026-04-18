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
```

## How to expand scope

Edit `config.json` — add passports or destinations to the arrays. The agent is idempotent: already-verified pairs within TTL are skipped.

## Full docs

See `CLAUDE.md`.
