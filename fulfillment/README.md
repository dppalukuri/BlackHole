# Fulfillment Scripts — Operator Guide

Turn the MCP servers into **sellable, one-click deliverables**. Each script
takes order parameters, calls the MCP's core Python code directly (bypassing
the MCP protocol), and produces a zipped delivery ready to attach to an email.

**Pattern:** `operator runs script → buyer gets a zip with CSV + README-buyer.txt`.

## Scripts

| Script | MCP used | Sellable product | Suggested price |
|---|---|---|---|
| `leads_maps.py` | `google-maps` | Niche lead list (name, email, phone, website, lead score) | $49–$199 |
| `uae_properties.py` | `uae-realestate` | Live Dubai/Abu Dhabi property listings with agent contacts | $29–$99 |
| `serp_report.py` | `serp-scraper` | SEO competitor report (top-50/100 organic + ads + PAA) | $19–$49 |
| `linkedin_jobs.py` | `linkedin` | Job-market snapshot (public job postings, hiring-company trends) | $29–$79 |

Each produces: `orders/order-YYYYMMDD-HHMM-<product>-<slug>.zip`.

## CAPTCHA Solver

Not packaged as a standalone fulfillment script — it's a *tool used inside
workflows*, not a deliverable. Two ways to monetize it:

1. **Inside this fulfillment stack** — it runs silently when Bayut or Google
   shows a CAPTCHA, so paid orders keep flowing without manual intervention.
2. **As a paid API** — run `python ../mcp-servers/captcha-solver/api.py` and
   expose the `/solve` endpoint behind Stripe metering. That's a separate
   SaaS product, not a per-order deliverable. See `api.py` for the REST shape.

## Running a fulfillment job

```bash
cd fulfillment

# Google Maps — "dentist" leads in Dubai, 50 results with email enrichment
python leads_maps.py --niche "dentist" --location "Dubai Marina" --count 50

# UAE real estate — 2-bedroom apartments for sale in Downtown Dubai
python uae_properties.py --location "Downtown Dubai" --purpose for-sale \
    --bedrooms 2 --min-results 40

# SERP — top 50 Google results for a keyword
python serp_report.py --query "best crm software 2026" --depth 50

# LinkedIn — 100 ML engineer jobs in Remote-friendly roles
python linkedin_jobs.py --query "ML engineer" --location "Remote" --count 100
```

Each run prints the zip path at the end — attach that to the buyer's email.

## First-time setup

1. Install Playwright browsers: `playwright install chromium`
2. Optional env vars (improve fulfillment success rate):
   - `GEMINI_API_KEY` — free Gemini VLM (250/day) for auto-CAPTCHA solving on Bayut/Google
   - `BAYUT_RAPIDAPI_KEY` — Bayut RapidAPI fallback (free tier: 750/mo) for uae-realestate
3. The first time you run `leads_maps.py` it will warm up the stealth browser
   (~10 sec). Subsequent runs reuse the process.
4. LinkedIn public-jobs path does **not** require a login. People/profile
   search does — that path is out-of-scope for these fulfillment scripts.

## Selling checklist

1. **List a gig on Upwork/Fiverr** with your niche (e.g. "500 verified dental
   practice leads in any city — 24-hour delivery — $99"). Use the CSV from
   `leads_maps.py` as your sample portfolio item.
2. **Accept the order, get the niche + location** from the buyer.
3. **Run the script**, attach the zip to the delivery.
4. **Re-runs are free to you** — if the buyer wants to tweak filters, one
   more command. Your only cost is ~15 min of browser time.

## Why this architecture

- **Scripts are standalone** — no MCP client, no Claude, no subscription cost
  per fulfillment. Runs off your flat-rate laptop.
- **Bypasses MCP protocol** — directly imports the scraper classes. Faster
  than running the MCP server and talking to it via JSON-RPC, and it means
  fulfillment doesn't compete with your Claude Desktop workflow for resources.
- **One deliverable shape** — every order ships the same way (zip of CSV +
  README-buyer.txt). Buyers don't need technical knowledge to open it.
- **Centralized, not per-MCP** — we keep all order-fulfillment code in
  `fulfillment/` so the MCP server directories stay clean and open-source-able
  without business logic mixed in.

## Adding a new product

1. Copy `serp_report.py` (simplest template).
2. Change the `sys.path.insert` target + imports to point at the target MCP.
3. Adjust `fulfill()` to call the MCP's async entry point.
4. Define `CSV_COLUMNS` to match the output dataclass.
5. Write a per-product summary + disclaimers block.
6. Update the table at the top of this README.

Each new product is ~100 lines of code once you've copied the template.
