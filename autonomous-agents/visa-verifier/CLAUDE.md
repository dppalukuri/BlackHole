# Visa Verifier Agent

Background agent that verifies visa requirements against authoritative government sources and writes a curated dataset the VisaPathway site consumes.

## Why it exists

The bulk visa matrix (`data-products/visapathway/public/data/visa-matrix.json`) comes from the open-source Passport Index Dataset. It's the best starting corpus we have but is community-maintained — accuracy varies and nothing is individually sourced. This agent fills that gap by re-verifying high-traffic pairs against embassy / ministry / gov-portal pages and producing `verified-visas.json`, which the site prefers over the bulk matrix when present.

## Architecture

```
config.json              — passports × destinations to verify (edit to expand scope)
verifier.py              — one-pair Claude API call (web_search tool) → VerifiedEntry
agent.py                 — iterator: plans pending pairs, persists incrementally
output/verified-visas.json  — the dataset (gitignored by default; sync --sync copies to site)
```

Model: `claude-haiku-4-5` by default (~$0.0015/query). Override via `VISA_VERIFIER_MODEL` or `--model`.

## Confidence gating

We only mark an entry `verified` if the source URL matches a trusted-domain pattern (`.gov`, `.gov.<cc>`, `mfa.*`, `evisa.*`, `embassy|consulate|immigration|travel.state.gov`, EU official, VFS). Untrusted sources downgrade to `low`; no source at all sets status to `unknown` — and unknown entries are not shown on the site.

See `verifier.py::TRUSTED_PATTERNS`. Add domains here when they've been proven accurate.

## Running it

```bash
# one-off
python agent.py                              # all configured pairs
python agent.py --only-passport India        # just Indian passport
python agent.py --only-destination Japan     # just destination Japan
python agent.py --limit 5                    # throttle for test

# with site sync (copies output into the Astro public/data dir)
python agent.py --sync

# continuous (every 6h)
python agent.py --watch 21600 --sync

# preview, no API calls
python agent.py --dry-run
```

## Output schema

```json
{
  "meta": { "last_run": "2026-04-18T15:30:00", "total_entries": 100, ... },
  "data": {
    "India": {
      "United States": {
        "status": "vr",           // vf | voa | ev | eta | vr | unknown
        "days": null,
        "source": "https://in.usembassy.gov/visas/",
        "notes": "B-1/B-2 tourist visa required; apply at the US Embassy.",
        "confidence": "high",     // high | medium | low | unknown
        "verified_at": "2026-04-18",
        "model": "claude-haiku-4-5"
      }
    }
  }
}
```

## Cost

Per query, Haiku 4.5: ~$0.0015. 100 pairs → ~$0.15. Full 5×20 seed runs for under a dollar.

## Dependencies

- Python 3.10+ (tested on 3.14)
- `anthropic>=0.92` (Claude API)
- `python-dotenv` (for `.env` loading)
- `ANTHROPIC_API_KEY` in `.env` or environment

## Safety

- Rate-limit handling: auto-retries once after 30s on 429
- Incremental persist: each verified pair is written immediately, so Ctrl-C loses at most one pair
- No writes outside `output/` and the configured site-sync path
