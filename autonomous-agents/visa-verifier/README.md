# visa-verifier

> Background agent that verifies passport → destination visa requirements against *official government sources*, using Claude + web-search. Zero API-key: runs on your Claude Code subscription.

**What this is:** a reproducible pipeline for producing a government-sourced visa-requirements dataset. Every "verified" entry in the output carries a URL back to the embassy / MFA / e-visa portal we used to confirm it. No aggregators, no guesses, no scraped blog posts.

**Why it exists:** the open-source [Passport Index Dataset](https://github.com/ilyankou/passport-index-dataset) is an excellent crowd-sourced baseline but contains ~40,000 unsourced entries. Commercial visa APIs (Sherpa, IATA Timatic) cost $500–$2,000/month. This is the gap-filler: a transparent, citable, open dataset — built one gov-domain URL at a time.

**Where the output ends up:**
- `output/verified-visas.json` — the dataset
- `output/validation-issues.json` — disagreements between models (second-opinion pass)
- Powers the visa-checker at [visapathway.techtools365.com](https://visapathway.techtools365.com) as the canonical source for high-traffic passport pairs

---

## Quick start

**Prerequisites**
- Python 3.10+
- [Claude Code](https://docs.anthropic.com/claude-code/cli-reference) installed and logged in (`claude` on `PATH`)

```bash
git clone https://github.com/dppalukuri/BlackHole.git
cd BlackHole/autonomous-agents/visa-verifier

python agent.py --dry-run                 # preview what will run — no API calls
python agent.py --limit 5                 # tiny smoke test
python agent.py --parallel 4 --sync       # real run — Top N passports × destinations
python status.py                          # progress report
```

Auth uses your existing Claude Code subscription — no `ANTHROPIC_API_KEY` needed.

---

## How it works

```
                   ┌─────────────────────────────────────┐
                   │         config.json                 │
                   │  passports[] × destinations[]       │
                   └──────────────┬──────────────────────┘
                                  │
                                  ▼
              ┌─────────────────────────────────────────┐
              │  agent.py  — plans pending pairs,       │
              │  respects TTL, supports --parallel N    │
              └──────────────┬──────────────────────────┘
                             │ for each (passport, destination)
                             ▼
                ┌────────────────────────────────────┐
                │  verifier.verify_pair()            │
                │    1. claude -p with WebSearch     │
                │       + WebFetch tool allowlisted  │
                │    2. Parse JSON from model        │
                │    3. Gate the source URL against  │
                │       TRUSTED_PATTERNS (gov TLDs)  │
                └──────────────┬─────────────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │  output/verified-visas.json      │
                │  { passport: {                   │
                │     destination: {               │
                │       status, days, source,      │
                │       confidence, verified_at, …  │
                │  } } }                           │
                └──────────────────────────────────┘
```

Two-model workflow (optional):

```
python agent.py     --parallel 4  (Haiku — fast + cheap)
   ↓
python validate.py  --parallel 4  (Sonnet — second opinion)
   ↓
output/validation-issues.json  (only disagreements — worth human review)
```

---

## Confidence gating

We only mark an entry "verified" if the source URL matches a trusted-domain pattern. The current allowlist (see `verifier.py::TRUSTED_PATTERNS`) covers:

- **English-world government TLDs** — `.gov`, `.gov.<cc>`, `travel.state.gov`, `canada.ca`, `u.ae`
- **Spanish-speaking government** — `.gob.<cc>`
- **French-speaking government** — `.gouv.<cc>`, `france-visas.gouv.fr`
- **Asian government** — `.go.jp`, `.go.kr`, `.go.th`, `.go.id`
- **European sub-systems** — `.admin.ch`, `.bund.de`, `diplo.de`, `.esteri.it`, `vistoperitalia.it`, `netherlandsworldwide.nl`
- **EU official** — `europa.eu`, `ec.europa.eu`, `eeas.europa.eu`
- **Generic signals** — `embassy|consulate`, `evisa.*`, `mfa.*`, `mofa.*`, `immigration.*`
- **Contractors** — `vfsglobal.com`, `gvcworld.eu` (officially gov-contracted)

Anything outside the allowlist → downgraded to `low` confidence (no ✓ badge on the site). Missing source → `unknown` (hidden from display).

**Add a new trusted domain:** edit `TRUSTED_PATTERNS` in `verifier.py`, then run `python reclassify.py` to re-gate existing entries without making new API calls.

---

## Output schema

```json
{
  "meta": {
    "last_run": "2026-04-19T10:02:11+00:00",
    "total_entries": 182,
    "model_default": "haiku",
    "generator": "autonomous-agents/visa-verifier v0.1"
  },
  "data": {
    "India": {
      "Thailand": {
        "passport": "India",
        "destination": "Thailand",
        "status": "vf",
        "days": 60,
        "source": "https://newdelhi.thaiembassy.org/en/page/visa",
        "notes": "Visa-free entry for tourism up to 60 days; Royal Thai Embassy page.",
        "confidence": "high",
        "verified_at": "2026-04-18",
        "model": "claude-code:haiku",

        "validated_by": "claude-code:sonnet",
        "validated_at": "2026-04-18",
        "validation_result": "agree",
        "validation_notes": "both agree: vf (60d)"
      }
    }
  }
}
```

Status codes: `vf` (visa-free) · `voa` (visa on arrival) · `ev` (e-visa) · `eta` (electronic travel authorization) · `vr` (visa required, embassy) · `na` (entry not permitted) · `unknown` (no authoritative source).

---

## Commands cheat sheet

```bash
# Verification (Haiku, bulk pass)
python agent.py                         # all configured pairs, sequential
python agent.py --parallel 4 --sync     # 4 workers, copy output to Astro site after
python agent.py --only-passport India   # single passport
python agent.py --only-destination Japan  # single destination
python agent.py --limit 5               # cheap smoke test
python agent.py --watch 3600 --sync     # run once per hour forever
python agent.py --dry-run               # no API calls, just list what would run

# Second-opinion validation (Sonnet)
python validate.py --parallel 4 --sync
python validate.py --only-passport India --limit 20
python validate.py --dry-run

# Housekeeping
python reclassify.py                    # re-gate confidence after updating TRUSTED_PATTERNS
python status.py                        # progress snapshot
```

---

## Cost

Running on Claude Code subscription — no API charges. For reference, equivalent API cost with Haiku 4.5 is ~$0.06 per pair (most of the time spent in 2 web_search iterations). The full 199 × 199 matrix = 39,402 pairs ≈ $2,400 equivalent. Your subscription quota is the relevant limit.

If you'd rather use a raw API key instead of Claude Code:
1. `pip install anthropic`
2. Replace `_run_claude()` in `verifier.py` with `anthropic.Anthropic().messages.create(...)` — see the git history for the pre-subprocess version (commit `108e5f2`).

---

## Related project

**[VisaPathway](https://visapathway.techtools365.com)** — the consumer-facing website this data powers. Interactive multi-passport visa checker, 96+ SEO pages covering individual passports, destinations, residence permits, ranking, and guides.

---

## License

MIT. See [LICENSE](./LICENSE).

Data usage: the *pipeline* is MIT. The *generated dataset* is released under the same terms — free for personal, research, and internal commercial use. Redistributing the raw CSVs as a standalone competing dataset product is not permitted.

---

## Acknowledgements

- Baseline matrix: [Passport Index Dataset](https://github.com/ilyankou/passport-index-dataset) by Ilya Ilyankou
- Verification is powered by [Claude](https://claude.ai) with its WebSearch + WebFetch tools
- Thanks to the open data / immigration-research communities for calling out errors
