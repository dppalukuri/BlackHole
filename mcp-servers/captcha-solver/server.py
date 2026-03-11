"""
CAPTCHA Solver MCP Server

Multi-strategy CAPTCHA solver with smart cost routing:
  1. CLIP (free, local) — image grids, simple canvas challenges
  2. VLM (Claude/GPT-4o) — hard canvas challenges, novel types
  3. External API (CapSolver/2Captcha) — last resort fallback

Supports: hCaptcha, reCAPTCHA v2/v3, Cloudflare Turnstile, FunCaptcha

Tools:
  - solve_captcha: Auto-detect and solve any CAPTCHA from images + task text
  - solve_image_grid: Solve image grid selection challenges
  - solve_canvas: Solve canvas/interactive challenges (click coordinates)
  - classify_image: General-purpose image classification

Run:
  python server.py
"""

import os
import sys
import json
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from core.types import CaptchaChallenge, SolverConfig
from router import CaptchaRouter, classify_challenge


def _load_config() -> SolverConfig:
    """Load solver config from environment variables.

    Priority: Gemini (free) > Anthropic > OpenAI
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    # Pick best available VLM provider (free first)
    if gemini_key:
        vlm_provider, vlm_key = "gemini", gemini_key
    elif anthropic_key:
        vlm_provider, vlm_key = "anthropic", anthropic_key
    elif openai_key:
        vlm_provider, vlm_key = "openai", openai_key
    else:
        vlm_provider, vlm_key = "gemini", ""

    return SolverConfig(
        enable_vlm=bool(vlm_key),
        vlm_provider=vlm_provider,
        vlm_api_key=vlm_key,
        enable_external_api=bool(os.environ.get("CAPSOLVER_API_KEY") or os.environ.get("TWOCAPTCHA_API_KEY")),
        external_api_key=os.environ.get("CAPSOLVER_API_KEY") or os.environ.get("TWOCAPTCHA_API_KEY") or "",
        external_api_provider="capsolver" if os.environ.get("CAPSOLVER_API_KEY") else "2captcha",
        # When free VLM (Gemini) is available, prefer it over CLIP (avoids 350MB model download)
        prefer_local=not bool(gemini_key),
    )


@dataclass
class AppContext:
    router: CaptchaRouter
    config: SolverConfig


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    config = _load_config()
    router = CaptchaRouter(config)

    # Pre-load CLIP model
    try:
        from vision.clip import _load_model
        await asyncio.to_thread(_load_model)
    except Exception:
        pass  # CLIP loading failure is non-fatal if VLM is available

    yield AppContext(router=router, config=config)


mcp = FastMCP(
    "CAPTCHA Solver",
    instructions=(
        "Multi-strategy CAPTCHA solver. Uses CLIP (free, local) for simple challenges, "
        "VLM (Gemini free / Claude / GPT-4o) for hard challenges, and external APIs as fallback. "
        "Supports hCaptcha, reCAPTCHA v2/v3, Cloudflare Turnstile, FunCaptcha."
    ),
    lifespan=app_lifespan,
)


@mcp.tool()
async def solve_captcha(
    task_text: str,
    images: list[str],
    captcha_type: str = "hcaptcha",
    is_canvas: bool = False,
    sitekey: str = "",
    page_url: str = "",
) -> str:
    """
    Auto-detect and solve any CAPTCHA challenge.

    Smart routing: tries cheapest solver first (CLIP → VLM → External API).

    Args:
        task_text: The challenge instruction (e.g., "Click each image containing a bus")
        images: List of image data (base64 data URIs, URLs, or single canvas data URI)
        captcha_type: "hcaptcha", "recaptcha", "turnstile", "funcaptcha" (default: hcaptcha)
        is_canvas: True if images contain a single canvas screenshot (interactive challenge)
        sitekey: Optional site key for token-based solving
        page_url: Optional page URL for token-based solving

    Returns:
        JSON with solution: selections (grid), click coordinates (canvas), or token.
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    result = await ctx.router.solve_raw(
        task_text=task_text,
        images=images,
        is_canvas=is_canvas,
        captcha_type=captcha_type,
        sitekey=sitekey or None,
        page_url=page_url or None,
    )

    return json.dumps({
        "success": result.success,
        "solver": result.solver_used,
        "selections": result.selections if result.selections else None,
        "click_x": result.click_x,
        "click_y": result.click_y,
        "canvas_width": result.canvas_width,
        "canvas_height": result.canvas_height,
        "token": result.token,
        "confidence": round(result.confidence, 4),
        "cost_usd": round(result.cost_usd, 6),
        "solve_time_ms": result.solve_time_ms,
        "error": result.error,
    }, indent=2)


@mcp.tool()
async def solve_image_grid(
    task_text: str,
    image_urls: list[str],
    threshold: float = 0.55,
) -> str:
    """
    Solve an image grid CAPTCHA (hCaptcha/reCAPTCHA style).

    Uses CLIP vision model locally (free). Falls back to VLM if confidence is low.

    Args:
        task_text: The challenge instruction (e.g., "Please click each image containing a motorbus")
        image_urls: List of image URLs or base64 data URIs for the grid images
        threshold: Confidence threshold (0-1, default 0.55). Lower = more selections.

    Returns:
        JSON with matched image indices and confidence scores.
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    result = await ctx.router.solve_raw(
        task_text=task_text,
        images=image_urls,
        is_canvas=False,
        captcha_type="hcaptcha",
    )

    return json.dumps({
        "success": result.success,
        "solver": result.solver_used,
        "selections": result.selections,
        "confidence": round(result.confidence, 4),
        "details": result.details,
    }, indent=2)


@mcp.tool()
async def solve_canvas(
    canvas_data: str,
    task_text: str,
) -> str:
    """
    Solve a canvas/interactive CAPTCHA challenge (returns click coordinates).

    Handles hCaptcha canvas challenges: silhouette matching, bucket/ball,
    line connection, and any unknown canvas challenge via VLM.

    Args:
        canvas_data: Canvas image as base64 data URI (from canvas.toDataURL())
        task_text: The challenge instruction text

    Returns:
        JSON with click coordinates (x, y) in canvas pixel space.
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    result = await ctx.router.solve_raw(
        task_text=task_text,
        images=[canvas_data],
        is_canvas=True,
        captcha_type="hcaptcha",
    )

    return json.dumps({
        "success": result.success,
        "solver": result.solver_used,
        "click_x": result.click_x,
        "click_y": result.click_y,
        "canvas_width": result.canvas_width,
        "canvas_height": result.canvas_height,
        "confidence": round(result.confidence, 4),
    }, indent=2)


@mcp.tool()
async def classify_image(
    image_url: str,
    labels: list[str],
) -> str:
    """
    Classify an image against text descriptions using CLIP.

    General-purpose zero-shot classification, not limited to CAPTCHAs.

    Args:
        image_url: URL or base64 data URI of the image
        labels: List of text descriptions to match against

    Returns:
        JSON with {label: probability} sorted by probability.
    """
    from vision.clip import load_image, classify_image as _classify

    img = load_image(image_url)
    result = await asyncio.to_thread(_classify, img, labels)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_solver_status() -> str:
    """Check which solvers are available and their status."""
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    config = ctx.config

    clip_ok = False
    try:
        from vision.clip import _model
        clip_ok = _model is not None
    except Exception:
        pass

    vlm_costs = {"gemini": "free (10 RPM / 250 RPD)", "anthropic": "~$0.004/solve", "openai": "~$0.002/solve"}
    return json.dumps({
        "clip": {"available": True, "loaded": clip_ok, "cost": "free"},
        "vlm": {
            "available": config.enable_vlm,
            "provider": config.vlm_provider if config.enable_vlm else None,
            "cost": vlm_costs.get(config.vlm_provider, "~$0.004/solve"),
        },
        "external_api": {
            "available": config.enable_external_api,
            "provider": config.external_api_provider if config.enable_external_api else None,
            "cost": "~$0.002/solve",
        },
        "supported_types": [
            "hcaptcha_grid", "hcaptcha_canvas (bucket, silhouette, line)",
            "recaptcha_v2", "recaptcha_v3 (token-only)",
            "turnstile (token-only)", "funcaptcha (vlm-only)",
        ],
    }, indent=2)


# ─── RESOURCES ─────────────────────────────────────────────────────────

@mcp.resource("captcha-solver://help")
def help_text() -> str:
    """Usage guide for the CAPTCHA Solver MCP server."""
    return """
CAPTCHA SOLVER MCP SERVER v2.0

Multi-strategy solver with smart cost routing:
  CLIP (free, local) → VLM (Gemini free / Claude / GPT-4o) → External API (~$0.002)

QUICK START:
  solve_captcha(task_text="...", images=["data:image/png;base64,...", ...])

SUPPORTED TYPES:
  - hCaptcha image grids (3x3, 4x4)
  - hCaptcha canvas: silhouette, bucket/ball, line connection
  - reCAPTCHA v2 image selection
  - reCAPTCHA v3 (token via external API)
  - Cloudflare Turnstile (token via external API)
  - FunCaptcha (VLM-powered)

CONFIGURATION (via environment variables):
  GEMINI_API_KEY     — Enable Gemini Vision (FREE, recommended)
  ANTHROPIC_API_KEY  — Enable Claude Vision
  OPENAI_API_KEY     — Enable GPT-4o Vision
  CAPSOLVER_API_KEY  — Enable CapSolver API fallback
  TWOCAPTCHA_API_KEY — Enable 2Captcha API fallback

Priority: Gemini (free) > Anthropic > OpenAI. Without API keys, only CLIP (free, local) is available.
""".strip()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
