# UAE Real Estate MCP Server

Live property search across Bayut, Dubizzle, and PropertyFinder for Claude Desktop.

## Architecture

```
server.py              — FastMCP server (7 tools, 2 resources, 2 prompts)
models.py              — Unified Property dataclass
analytics.py           — Yield calculator, area stats, comparison
captcha.py             — CAPTCHA detection + solving (uses ../captcha-solver)
stealth_browser.py     — Shared Playwright browser with playwright-stealth
slug_registry.py       — Loads location/property type slugs from slugs.json
slug_discovery.py      — Scrapes sites to discover new location slugs
slugs.json             — Centralized slug data (auto-updated by discovery)
scrapers/
  __init__.py          — UAEPropertyAggregator: unified search + post-filter + dedup
  bayut.py             — Bayut scraper (aria-label DOM, Algolia API, RapidAPI)
  dubizzle.py          — Dubizzle scraper (API intercept + DOM parsing)
  propertyfinder.py    — PropertyFinder scraper (__NEXT_DATA__ JSON)
.sessions/             — Playwright session state (cookies, gitignored)
```

## Scraper Flow

All scrapers: **headless-first**, escalate to headed only for CAPTCHA/WAF.

1. **PropertyFinder** — Headless stealth, `__NEXT_DATA__` JSON extraction. No bot protection.
2. **Dubizzle** — Headless first, escalates to headed if Incapsula WAF blocks (content < 100 chars).
3. **Bayut** — Headless first, escalates to headed if CAPTCHA. Auto-solves via Gemini VLM (free).

Search pipeline: `Scrape all sources concurrently → Post-filter (bedrooms, price, type) → Auto-paginate (up to 3 pages) → Deduplicate cross-source`

## Key Conventions

- **Torch MUST NOT be imported at module level** — segfaults with Playwright. The captcha-solver handles this with lazy imports.
- `captcha.py` adds `../captcha-solver` to `sys.path` — it's NOT pip-installed
- `_solver_available()` uses `importlib.util.find_spec()` not a full import (avoids loading torch)
- CAPTCHA solving has a 90-second timeout to prevent hanging
- All prices in AED (1 USD ~ 3.67 AED)
- Bedrooms: `0` = studio, `-1` = any
- Session cookies persist in `.sessions/` — once CAPTCHA solved, reused until expiry

## URL Patterns

- **Bayut**: `/{for-sale|to-rent}/{type}/dubai/{location-slug}/` + query params
- **Dubizzle**: `/en/property-for-{sale|rent}/residential/{type}/in/{slug}/{id}/` + query params
  - Location slugs MUST include numeric ID: `/in/dubai-marina/63/`
- **PropertyFinder**: `/en/search?c={1|2}&q={location}&t={type-id}` (query-based only, `.html` returns 404)

## Environment Variables

```
GEMINI_API_KEY       — Free Gemini VLM for CAPTCHA solving (recommended)
CAPSOLVER_API_KEY    — Paid CAPTCHA API fallback
BAYUT_RAPIDAPI_KEY   — Bayut RapidAPI fallback (free tier: 750/month)
```

## Claude Desktop Config

Path: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "uae-realestate": {
      "command": "python",
      "args": ["C:\\Prasad\\Projects\\claude_workspace\\BlackHole\\mcp-servers\\uae-realestate\\server.py"],
      "env": { "GEMINI_API_KEY": "..." }
    }
  }
}
```

## Run

```bash
python server.py                    # MCP server (stdio transport)
python slug_discovery.py            # Discover new location slugs
```

## Dependencies

Core: `mcp[cli]`, `httpx`
Scraping: `playwright`, `playwright-stealth`
CAPTCHA: Uses `../captcha-solver` (sister project, not pip-installed)

## Parent Repo

This is a subproject of `BlackHole` (`../../`). Depends on `../captcha-solver` for CAPTCHA solving.
