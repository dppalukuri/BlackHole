# Google Maps Extractor MCP Server

Lead generation engine built on Google Maps — search, enrich, score, export.

## Architecture

```
server.py              — FastMCP server (6 tools, 1 resource)
scraper.py             — Google Maps scraper (search, details, reviews)
enrichment.py          — Website enrichment (emails, socials, phones, tech stack)
models.py              — Business (with lead scoring), Review dataclasses
export.py              — CSV/JSON export for leads
retry.py               — Retry with backoff + file-based result cache
stealth_browser.py     — Shared Playwright browser with stealth + geolocation
.sessions/             — Session state persistence (gitignored)
.cache/                — Enrichment result cache, 24h TTL (gitignored)
exports/               — Exported CSV/JSON files (gitignored)
```

## Tools

| Tool | Description |
|------|-------------|
| `search_businesses` | Quick Google Maps search (no enrichment) |
| `get_business_details` | Full details for a specific business |
| `get_reviews` | Reviews with rating, text, date |
| `find_leads` | Search + enrich with emails/socials + lead scoring |
| `generate_lead_report` | Full pipeline: Maps + enrichment + SERP + LinkedIn |
| `export_leads` | Export last results to CSV or JSON |

## Lead Generation Pipeline

```
Google Maps search
  → Detail extraction (phone, website, address)
    → Website enrichment (emails, socials, tech stack)
      → SERP check (optional: do they rank on Google?)
        → LinkedIn lookup (optional: company data)
          → Lead scoring (0-100)
            → Export CSV/JSON
```

## Lead Scoring (0-100)

| Signal | Points |
|--------|--------|
| Personal email found | 25 |
| Any email found | 15 |
| Has phone | 15 |
| Has website | 10 |
| Social links (5 each) | max 15 |
| Rating >= 4.0 | 10 |
| 50+ reviews | 10 |
| Has address | 5 |

## Cross-Server Integration

When sibling MCP servers are present:
- `../serp-scraper` — checks if leads rank for the search query
- `../linkedin` — pulls company data from LinkedIn pages

Both are optional — works standalone without them.

## Key Conventions

- No API keys needed — fully browser-based scraping
- Browser geolocation auto-matched to search location (30 cities)
- Enrichment results cached for 24h to avoid re-scraping
- Concurrent enrichment (3 parallel) with retry + backoff
- Emails ranked: personal > role-based > generic
- Tech stack detection: WordPress, Shopify, React, HubSpot, etc.

## Environment Variables

None required.

## Run

```bash
python server.py                    # MCP server (stdio)
```

## Dependencies

Core: `mcp[cli]`
Scraping: `playwright`, `playwright-stealth`

## Parent Repo

This is a subproject of `BlackHole` (`../../`).
