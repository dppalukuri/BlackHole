# Visa Verifier Agent

Background agent that verifies visa requirements against authoritative government sources and writes a curated dataset the VisaPathway site consumes.

## Why it exists

The bulk visa matrix (`data-products/visapathway/public/data/visa-matrix.json`) comes from the open-source Passport Index Dataset. It's the best starting corpus we have but is community-maintained — accuracy varies and nothing is individually sourced. This agent fills that gap by re-verifying high-traffic pairs against embassy / ministry / gov-portal pages and producing `verified-visas.json`, which the site prefers over the bulk matrix when present.

## Auth — uses the Claude Code subscription, not an API key

The verifier invokes `claude -p --output-format json --model haiku --allowed-tools WebSearch,WebFetch` as a subprocess. This uses the OAuth session the `claude` CLI already has (no `ANTHROPIC_API_KEY` required). If you're logged into Claude Code, the agent works.

Cost: Claude Max subscription covers it. Per query roughly ~2 web_search calls + extraction; reported `total_cost_usd` lands around $0.01–0.11 depending on how much the model searches.

## Architecture

```
config.json              — passports × destinations to verify (edit to expand scope)
verifier.py              — one-pair `claude -p` subprocess call + JSON parsing + domain trust
reclassify.py            — re-apply domain-trust gate against existing file (no API calls)
agent.py                 — iterator: plans pending pairs, persists incrementally
output/verified-visas.json  — the dataset (committed; sync --sync copies to site)
```

## Confidence gating

We only mark an entry `verified` if the source URL matches a trusted-domain pattern. The list lives in `verifier.py::TRUSTED_PATTERNS` and covers:

- English-world: `.gov`, `.gov.<cc>`, `travel.state.gov`, `canada.ca`, `u.ae`
- Spanish-world: `.gob.<cc>`
- French-world: `.gouv.<cc>`, `france-visas.gouv.fr`
- Asian: `.go.jp`, `.go.kr`, `.go.th`, `.go.id`
- European gov sub-systems: `.admin.ch`, `.bund.de`, `diplo.de`, `.esteri.it`, `vistoperitalia.it`, `netherlandsworldwide.nl`
- EU: `europa.eu`, `ec.europa.eu`, `eeas.europa.eu`
- Generic signals: `embassy|consulate`, `evisa.*`, `e-visa.*`, `mfa.*`, `mofa.*`, `immigration.*`
- Contractors: `vfsglobal.com`, `gvcworld.eu`

Anything outside the allowlist → `low` confidence (no ✓ on site). Missing source → `unknown` (hidden from site).

**Add a new trusted domain:** edit `TRUSTED_PATTERNS` in `verifier.py`, then run `python reclassify.py` to re-gate existing entries without making new API calls.

## Running it

```bash
# one-off — all configured pairs
python agent.py

# single passport or destination
python agent.py --only-passport India
python agent.py --only-destination Japan

# cheap smoke test
python agent.py --limit 5

# with site sync (copies output into the Astro public/data dir)
python agent.py --sync

# continuous (every 6h)
python agent.py --watch 21600 --sync

# preview, no API calls
python agent.py --dry-run

# re-apply confidence gating to existing file (after updating TRUSTED_PATTERNS)
python reclassify.py
```

## Output schema

```json
{
  "meta": { "last_run": "2026-04-18T16:13:07+00:00", "total_entries": 148, ... },
  "data": {
    "India": {
      "United States": {
        "passport": "India",
        "destination": "United States",
        "status": "vr",           // vf | voa | ev | eta | vr | unknown
        "days": 180,
        "source": "https://travel.state.gov/content/travel/en/us-visas/tourism-visit/visitor.html",
        "notes": "B-1/B-2 tourist visa required; apply at the US Embassy.",
        "confidence": "high",     // high | medium | low | unknown
        "verified_at": "2026-04-18",
        "model": "claude-code:haiku"
      }
    }
  }
}
```

## Dependencies

- Python 3.10+ (tested on 3.14)
- `claude` CLI installed and logged in (Claude Code)
- No Python packages required — the agent uses stdlib `subprocess` + `json`

## Safety

- Rate-limit handling: auto-retries once after 30s if CLI reports rate-limit
- Incremental persist: each verified pair is written immediately, so Ctrl-C loses at most one pair
- No writes outside `output/` and the configured site-sync path
- Subprocess uses `--no-session-persistence` so verifier calls don't pollute the user's claude-code session list
