# Visa Matrix 2026 — Gumroad / LemonSqueezy Ready

**Product folder.** Everything a buyer downloads lives in this directory. Regenerate anytime:

```bash
cd data-products/visa-matrix-2026
python generate.py
```

## Files

| File | Purpose |
|---|---|
| `verified-matrix.csv` | The main deliverable — every gov-sourced passport → destination pair with source URL, confidence, day-limit, and Sonnet-validation status |
| `residence-permits.csv` | 69 hand-curated residence permit exemptions (UAE, Green Card, Schengen, UK BRP, Canada PR, valid US/Schengen visas) with source URLs |
| `bulk-matrix.csv` | Full 199 × 199 baseline from the community-maintained Passport Index Dataset — shipped as reference, not verified |
| `report.html` | Printable overview — open in browser, print-to-PDF for the buyer PDF |
| `VERSION` | Snapshot date + row counts |

## Suggested Gumroad product setup

**Title:** `Visa Matrix 2026 — Government-Sourced Visa Requirements Database (CSV + PDF)`

**Price:** $29 (intro). Raise to $49 once the verifier reaches 1000+ entries.

**Cover image:** Render `report.html`'s first page to PDF, screenshot page 1 at 1200×900.

**Product description** (paste below):

---

### Stop guessing visa rules. Start citing them.

**Visa Matrix 2026** is the most transparent visa-requirements dataset on the open web. Every "verified" entry carries a live link to the official embassy, MFA, or e-visa portal we used to confirm it. Nothing is guessed. Nothing is scraped from travel-blog aggregators.

#### What's inside

- **✓ Verified matrix** — passport → destination pairs with status (visa-free / VoA / e-visa / ETA / required), day-limit, and a gov-domain source URL for each. Growing continuously; see VERSION.txt for the current count.
- **✓ Residence permit exemptions** — 69 hand-curated entries covering UAE Residence, US Green Card, Schengen Residence, UK BRP, Canadian PR, valid US B1/B2 visa, valid Schengen visa. Each with source URL and day-limit.
- **✓ Full 199×199 baseline** — the entire open-source Passport Index matrix (19 639 609 combined status codes) as a CSV starting point for edge-case queries we haven't verified yet.
- **✓ Printable PDF report** — methodology, confidence tiers, license, updated date.
- **Two confidence sources per entry** — each verified pair is double-checked: Haiku extracts from the gov source, Sonnet re-verifies. Disagreements are flagged in a `validator_agreed` column so you can prioritize review.

#### Who buys this

- **Immigration lawyers / relocation consultants** — cite sources to clients.
- **Travel bloggers & nomad newsletters** — fact-check before publishing.
- **Expat forums, investor communities** — residence-permit benefits are the most commonly misrepresented info online.
- **Researchers & analysts** — import CSVs into pandas/Excel, run passport-strength and regional-trend analyses.

#### What you get

- Immediate CSV + PDF download
- Free updates for 12 months (product auto-regenerates when the verifier publishes new entries)
- Attribution-based license — use in commercial research, internal business, client work. Redistribution as a competing dataset not permitted.

#### About the pipeline

Data is produced by an open-source [verification agent](https://github.com/dppalukuri/BlackHole/tree/main/autonomous-agents/visa-verifier) that queries Claude with web search, requires a government-domain source URL for every entry, and re-verifies with a second model. The full pipeline, trusted-domain allowlist, and methodology are published — you can audit how every row was produced.

---

## Gumroad upload checklist

- [ ] Generate a clean PDF from `report.html` (Chrome → print → save as PDF at A4 / Letter)
- [ ] Zip: `verified-matrix.csv` + `residence-permits.csv` + `bulk-matrix.csv` + `report.pdf` + `VERSION` + `README-buyer.txt`
- [ ] Upload .zip to Gumroad, set price
- [ ] Set product URL slug: `visa-matrix-2026`
- [ ] Category: Data / Research
- [ ] Tags: visa, immigration, travel, passport, data, csv
- [ ] Generate cover image (screenshot of report.html first page, 1200×900)
- [ ] Turn on affiliate program (30% to affiliates)

## Marketing angles for launch

1. **Post on HN** — "Show HN: I scraped embassy sites with Claude and here's the CSV" → links to Gumroad
2. **r/digitalnomad, r/IWantOut, r/travel** — "Open-source visa dataset, $29 for the CSV bundle"
3. **LinkedIn** → relocation industry folks
4. **Email to travel bloggers** — offer free copies for review in exchange for a link back

## Update workflow

After each major verifier milestone:

```bash
cd data-products/visa-matrix-2026
python generate.py                  # rebuild CSVs + report
# manually convert report.html → report.pdf
# re-zip + upload new version to Gumroad (replaces buyers' download silently)
git add . && git commit -m "visa-matrix-2026: refresh data snapshot (VERSION)"
```
