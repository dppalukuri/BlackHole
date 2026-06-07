# Visa Verifier Agent

Background agent that verifies visa requirements against authoritative government sources and writes a curated dataset the WanderWise site consumes.

## Why it exists

The bulk visa matrix (`data-products/wanderwise/public/data/visa-matrix.json`) comes from the open-source Passport Index Dataset. It's the best starting corpus we have but is community-maintained — accuracy varies and nothing is individually sourced. This agent fills that gap by re-verifying high-traffic pairs against embassy / ministry / gov-portal pages and producing `verified-visas.json`, which the site prefers over the bulk matrix when present.

## Auth — uses the Claude Code subscription, not an API key

The verifier invokes `claude -p --output-format json --model haiku --allowed-tools WebSearch,WebFetch` as a subprocess. This uses the OAuth session the `claude` CLI already has (no `ANTHROPIC_API_KEY` required). If you're logged into Claude Code, the agent works.

Cost: Claude Max subscription covers it. Per query roughly ~2 web_search calls + extraction; reported `total_cost_usd` lands around $0.01–0.11 depending on how much the model searches.

## Architecture

```
config.json                      — passports × destinations to verify (edit to expand scope)
verifier.py                      — one-pair `claude -p` subprocess call + JSON parsing + domain trust
bulk_verifier.py                 — one-destination Claude call → many passports at once (~50-100x cheaper)
reclassify.py                    — re-apply domain-trust gate against existing file (no API calls)
agent.py                         — per-pair iterator: plans pending pairs, persists incrementally
bulk_agent.py                    — per-destination iterator (preferred for big sweeps)
validate.py                      — second-opinion pass with Sonnet, flags disagreements
output/verified-visas.json       — the dataset (committed; sync --sync copies to site)
output/validation-issues.json    — disagreement report (written by validate.py)
```

### Two verification modes — when to use which

The codebase ships **two** verifier engines. They produce identical on-disk schema
(`VerifiedEntry` dicts in `output/verified-visas.json`), so they're interchangeable
and even compatible with already-verified entries — newer runs overwrite older ones.

**`bulk_agent.py` — per-destination (preferred for sweeps)**
- One Claude call per destination resolves visa-status for many passports at once
- Works because most countries publish a single official "visa policy" page
  (e.g. Japan's MOFA, Singapore's ICA, US travel.state.gov) that lists rules
  for every nationality on one URL.
- ~50-100x fewer subprocess calls, fewer WebSearch billings.
- Trade-off: if the destination's source page is poor or missing,
  every entry for that destination is marked `unknown` rather than verified one-by-one.

**`agent.py` — per-pair (precision mode)**
- One Claude call per (passport, destination) pair.
- Slower and ~50x more expensive but each pair gets independent reasoning.
- Use for: single-pair re-verifies, targeted patches, low-quality bulk destinations
  where the master-page approach failed.

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
# === bulk mode (PREFERRED for big sweeps) ===
python bulk_agent.py --parallel 2 --sync                  # all pending destinations, 2 workers
python bulk_agent.py --only-destination Japan             # one destination, all passports
python bulk_agent.py --limit 10 --parallel 2 --sync       # cap to 10 destinations per run
python bulk_agent.py --chunk 60                           # max passports per Claude call (default 60)
python bulk_agent.py --dry-run --limit 5                  # preview plan, no API calls

# === per-pair mode (precision / patching) ===
python agent.py                                            # all configured pairs
python agent.py --only-passport India                      # one passport, all destinations
python agent.py --only-destination Japan                   # one destination, all passports
python agent.py --limit 5                                  # cheap smoke test
python agent.py --parallel 4 --sync                        # 4x parallel on big batches
python agent.py --watch 21600 --sync                       # continuous every 6h
python agent.py --dry-run                                  # preview, no API calls

# === maintenance ===
python reclassify.py                                       # re-gate after TRUSTED_PATTERNS edit
python validate.py --parallel 4 --sync                     # Sonnet second-opinion pass
python validate.py --limit 20                              # quick sanity
python validate.py --only-passport India                   # subset
```

## Two-model workflow (recommended)

1. **Haiku (fast bulk)** — `python agent.py --parallel 4 --sync` covers the passports × destinations in `config.json`. Writes to `output/verified-visas.json`.
2. **Sonnet (validation)** — `python validate.py --parallel 4 --sync` re-checks each entry with Sonnet and annotates it with `validation_result: agree | differ-status | differ-days`. Disagreements land in `output/validation-issues.json` for review.
3. **Manual review of disagreements** — open `validation-issues.json`, look at the 5-20% of entries where models disagreed, pick the correct answer, and either (a) update `config.json` and re-run just those pairs, or (b) hand-edit `verified-visas.json` and bump `last_verified`.

Validation metadata is automatically cleared when Haiku re-verifies an entry
(on the next scheduled run). Validation TTL defaults to 30 days.

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
