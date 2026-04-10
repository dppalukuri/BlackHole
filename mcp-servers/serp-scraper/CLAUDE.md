# SERP Scraper MCP Server

Extract search engine results from Google and Bing for AI agents.

## Architecture

```
server.py              — FastMCP server (4 tools, 1 resource)
scraper.py             — SERP scraper (Google + Bing parsing)
models.py              — OrganicResult, AdResult, FeaturedSnippet, PeopleAlsoAsk, SerpResult
stealth_browser.py     — Shared Playwright browser with stealth
.sessions/             — Session state persistence (gitignored)
```

## Tools

| Tool | Description |
|------|-------------|
| `search_google` | Full Google SERP extraction (organic, ads, PAA, snippets) |
| `search_bing` | Bing search with structured results |
| `keyword_research` | Multi-keyword SEO analysis |
| `check_ranking` | Check domain ranking position for a keyword |

## Scraping Strategy

1. Stealth Playwright browser (headless)
2. Parse Google's DOM selectors for each SERP component
3. Bing as fallback / alternative data source
4. Session persistence to reduce consent dialogs
5. Optional CAPTCHA solving via `../captcha-solver` when Google blocks

## Key Conventions

- Google SERP selectors change frequently — selectors may need updates
- 2-second delay between requests in multi-keyword mode to avoid rate limiting
- CAPTCHA solver integration is a stub — needs wiring when Google blocks increase
- No API keys needed — fully browser-based

## Environment Variables

None required. Optional: `GEMINI_API_KEY` if wiring up CAPTCHA solver.

## Run

```bash
python server.py                    # MCP server (stdio)
```

## Dependencies

Core: `mcp[cli]`
Scraping: `playwright`, `playwright-stealth`
CAPTCHA (optional): `../captcha-solver`

## Parent Repo

This is a subproject of `BlackHole` (`../../`). Can use `../captcha-solver` for Google CAPTCHA challenges.
