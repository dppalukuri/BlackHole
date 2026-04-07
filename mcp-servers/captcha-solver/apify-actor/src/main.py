"""
Apify Actor wrapper for CAPTCHA Solver.

Accepts CAPTCHA challenge input, solves using CLIP/VLM/API chain,
returns solution via Apify dataset. Charges per successful solve.
"""

import os
import sys

# Add the captcha-solver root to path so we can import core/router/vision
SOLVER_ROOT = os.path.join(os.path.dirname(__file__), "..", "captcha-solver")
sys.path.insert(0, SOLVER_ROOT)

from apify import Actor

from core.types import SolverConfig
from router import CaptchaRouter, classify_challenge


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}

        task_text = actor_input.get("taskText", "")
        images = actor_input.get("images", [])
        captcha_type = actor_input.get("captchaType", "hcaptcha")
        is_canvas = actor_input.get("isCanvas", False)
        sitekey = actor_input.get("sitekey")
        page_url = actor_input.get("pageUrl")
        gemini_key = actor_input.get("geminiApiKey", "")

        # Allow Gemini key from input or environment
        gemini_key = gemini_key or os.environ.get("GEMINI_API_KEY", "")

        if not images and not sitekey:
            Actor.log.error("Provide either 'images' (for visual challenges) or "
                            "'sitekey' + 'pageUrl' (for token-based challenges)")
            await Actor.fail(exit_code=1)
            return

        # Configure solver
        config = SolverConfig(
            enable_vlm=bool(gemini_key),
            vlm_provider="gemini" if gemini_key else "",
            vlm_api_key=gemini_key,
            prefer_local=not bool(gemini_key),
            enable_external_api=False,
        )

        router = CaptchaRouter(config)
        Actor.log.info("Solving %s challenge (images=%d, canvas=%s)",
                       captcha_type, len(images), is_canvas)

        result = await router.solve_raw(
            task_text=task_text,
            images=images,
            is_canvas=is_canvas,
            captcha_type=captcha_type,
            sitekey=sitekey,
            page_url=page_url,
        )

        output = {
            "success": result.success,
            "solver": result.solver_used,
            "selections": result.selections if result.selections else None,
            "clickX": result.click_x,
            "clickY": result.click_y,
            "canvasWidth": result.canvas_width,
            "canvasHeight": result.canvas_height,
            "token": result.token,
            "confidence": round(result.confidence, 4),
            "costUsd": round(result.cost_usd, 6),
            "solveTimeMs": result.solve_time_ms,
            "error": result.error,
        }

        if result.success:
            # Charge per successful solve
            await Actor.push_data(output, "captcha-solved")
            await Actor.set_status_message(
                f"Solved via {result.solver_used} in {result.solve_time_ms}ms"
            )
            Actor.log.info("Solved: solver=%s conf=%.2f time=%dms",
                           result.solver_used, result.confidence, result.solve_time_ms)
        else:
            await Actor.push_data(output)
            await Actor.set_status_message(f"Failed: {result.error}")
            Actor.log.warning("Failed: %s", result.error)
