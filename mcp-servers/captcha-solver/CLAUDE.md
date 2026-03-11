# CAPTCHA Solver MCP Server v2.0

Multi-strategy CAPTCHA solver for AI agents. First-mover MCP CAPTCHA solver.

## Architecture

```
server.py          — FastMCP server (4 tools), config loader
router.py          — CaptchaRouter: routes by type, cost, confidence
solver.py          — Backward-compatible shim (routes through CaptchaRouter)
api.py             — REST API (2Captcha/CapSolver drop-in replacement)
core/types.py      — CaptchaChallenge, SolveResult, SolverConfig dataclasses
solvers/
  base.py          — BaseSolver ABC
  clip_grid.py     — CLIP zero-shot for image grids (hCaptcha/reCAPTCHA)
  clip_canvas.py   — CLIP for canvas challenges (bucket/silhouette/line)
  vlm.py           — VLM solver (Gemini/Claude/GPT-4o)
  token_api.py     — External API fallback (CapSolver/2Captcha)
vision/
  clip.py          — CLIP model loading + inference (torch lazy-loaded!)
  vlm_client.py    — Multi-provider VLM client (Gemini, Anthropic, OpenAI)
browser/           — Playwright browser automation for interactive solving
tests/             — Test suite
```

## Solving Chain

`CLIP (free, local) → Gemini VLM (free, 250/day) → External API (paid)`

When `GEMINI_API_KEY` is set, Gemini goes first (skips 350MB CLIP download).

## Key Conventions

- **Torch MUST be lazy-loaded** in `vision/clip.py` — importing at module level segfaults when Playwright Chromium runs in the same process. Keep `import torch` inside functions, never at top of file.
- `solver.py` is a shim for backward compat — real logic is in `router.py` + `solvers/`
- `_load_config()` in `server.py` reads env vars, sets `prefer_local=False` when Gemini available
- VLM providers: Gemini (`google-genai`), Anthropic, OpenAI. Gemini uses `client.aio.models.generate_content()`
- CLIP model: `openai/clip-vit-base-patch32` (~350MB, downloads on first use)
- hCaptcha challenges render on `<canvas>` not `<img>` — extract via `canvas.toDataURL()`

## Environment Variables

```
GEMINI_API_KEY      — Free Gemini Vision (recommended, 250 calls/day)
ANTHROPIC_API_KEY   — Claude Vision (~$0.004/solve)
OPENAI_API_KEY      — GPT-4o Vision (~$0.002/solve)
CAPSOLVER_API_KEY   — CapSolver API (paid fallback)
TWOCAPTCHA_API_KEY  — 2Captcha API (paid fallback)
```

## Run

```bash
python server.py                    # MCP server (stdio)
python api.py                       # REST API (port 8080)
python -m pytest tests/             # Tests
```

## Dependencies

Core: `mcp[cli]`, `torch`, `transformers`, `pillow`, `httpx`, `numpy`, `scipy`
VLM: `google-genai` (Gemini), `anthropic`, `openai`
Browser: `playwright`, `playwright-stealth`

## Parent Repo

This is a subproject of `BlackHole` (`../../`). The UAE Real Estate MCP server imports from here via `sys.path`.
