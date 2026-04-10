# BlackHole - Zero-Capital Wealth Engine

Monorepo for MCP servers, autonomous agents, and AI-native data products.

## Subprojects

| Project | Path | Status |
|---------|------|--------|
| CAPTCHA Solver MCP | `mcp-servers/captcha-solver/` | Active (v2.0) |
| UAE Real Estate MCP | `mcp-servers/uae-realestate/` | Active (v0.1) |
| Google Maps Extractor MCP | `mcp-servers/google-maps/` | Active (v0.1) |
| SERP Scraper MCP | `mcp-servers/serp-scraper/` | Active (v0.1) |
| LinkedIn Scraper MCP | `mcp-servers/linkedin/` | Active (v0.1) |
| Autonomous Agents | `autonomous-agents/` | Queued |
| Data Products | `data-products/` | Queued |

## Environment

- Python 3.14, Windows 10 (bash shell via Git Bash)
- Inline `python -c` breaks on `\!` escape sequences — always use .py temp files
- GitHub: `https://github.com/dppalukuri/BlackHole.git`

## Working on Subprojects

Each active subproject has its own `CLAUDE.md` with architecture, key files, and conventions. Open them independently:

```bash
cd mcp-servers/captcha-solver && claude
cd mcp-servers/uae-realestate && claude
cd mcp-servers/google-maps && claude
cd mcp-servers/serp-scraper && claude
cd mcp-servers/linkedin && claude
```

## Cross-Project Dependencies

- `uae-realestate` imports from `captcha-solver` via `sys.path` (not pip install)
- Path: `../captcha-solver` relative to uae-realestate
- Changes to captcha-solver's `solver.py`, `router.py`, or `vision/` affect uae-realestate

## Git

Single repo, single branch (`main`). Commit messages should prefix with the subproject:
- `captcha-solver: ...`
- `uae-realestate: ...`
- `google-maps: ...`
- `serp-scraper: ...`
- `linkedin: ...`
