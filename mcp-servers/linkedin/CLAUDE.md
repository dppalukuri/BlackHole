# LinkedIn Scraper MCP Server

Extract profiles, job postings, and company data from LinkedIn for AI agents.

## Architecture

```
server.py              — FastMCP server (5 tools, 1 resource)
scraper.py             — LinkedIn scraper (profiles, jobs, companies, people search)
models.py              — Profile, Job, Company, SearchResult dataclasses
stealth_browser.py     — Shared Playwright browser with stealth
.sessions/             — Login session persistence (gitignored, SENSITIVE)
```

## Tools

| Tool | Login Required | Description |
|------|---------------|-------------|
| `login` | N/A | Open browser for manual LinkedIn login |
| `search_jobs` | No | Search job postings with filters |
| `get_company` | No | Get company page data |
| `get_profile` | Partial | Full profile needs login, public view without |
| `search_people` | Yes | Search for people by keywords/filters |

## Authentication Strategy

LinkedIn blocks most headless scraping. Strategy:
1. User logs in manually via `login` tool (opens headed browser)
2. Session cookies saved to `.sessions/linkedin.json`
3. All subsequent requests use saved cookies in headless mode
4. Session typically lasts days/weeks before re-login needed

## Key Conventions

- LinkedIn is AGGRESSIVE with bot detection — respect rate limits
- ~50 pages/hour before soft blocks, then CAPTCHAs or "unusual activity"
- Random delays between requests are essential
- `.sessions/linkedin.json` contains auth cookies — NEVER commit this
- Job search works without login (public pages)
- People search REQUIRES login session
- Public profiles show limited data, logged-in shows full

## Environment Variables

None required. Authentication is via browser session cookies.

## Run

```bash
python server.py                    # MCP server (stdio)
```

## Dependencies

Core: `mcp[cli]`
Scraping: `playwright`, `playwright-stealth`

## Parent Repo

This is a subproject of `BlackHole` (`../../`).
