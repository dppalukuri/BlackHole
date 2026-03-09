"""VLM-based solver for hard CAPTCHA challenges.

Uses Google Gemini (free), Claude Vision, or GPT-4o to solve challenges
that CLIP cannot: canvas challenges, complex spatial reasoning, novel types.
"""

import time
from core.types import (
    CaptchaChallenge, SolveResult, SolverConfig,
    HCAPTCHA_CANVAS_BUCKET, HCAPTCHA_CANVAS_SILHOUETTE,
    HCAPTCHA_CANVAS_LINE, HCAPTCHA_CANVAS_UNKNOWN,
    HCAPTCHA_GRID, RECAPTCHA_V2, FUNCAPTCHA,
)
from solvers.base import BaseSolver

CANVAS_TYPES = {HCAPTCHA_CANVAS_BUCKET, HCAPTCHA_CANVAS_SILHOUETTE,
                HCAPTCHA_CANVAS_LINE, HCAPTCHA_CANVAS_UNKNOWN}

GRID_TYPES = {HCAPTCHA_GRID, RECAPTCHA_V2}

SUPPORTED_TYPES = CANVAS_TYPES | GRID_TYPES | {FUNCAPTCHA}


class VLMSolver(BaseSolver):
    """Solve CAPTCHAs using Vision Language Models (Gemini/Claude/GPT-4o)."""

    name = "vlm"
    cost_per_solve = 0.0  # $0 with Gemini free tier, ~$0.004 with Claude

    async def can_solve(self, challenge: CaptchaChallenge) -> bool:
        return challenge.type in SUPPORTED_TYPES

    async def solve(self, challenge: CaptchaChallenge, config: SolverConfig) -> SolveResult:
        if not config.enable_vlm or not config.vlm_api_key:
            return SolveResult(success=False, solver_used=self.name,
                             error="VLM not configured")

        from vision.vlm_client import solve_canvas_vlm, solve_grid_vlm, COST_ESTIMATES

        t0 = time.time()
        provider = config.vlm_provider
        cost = COST_ESTIMATES.get(provider, 0.004)

        if challenge.type in CANVAS_TYPES and challenge.is_canvas and challenge.images:
            result = await solve_canvas_vlm(
                canvas_b64=challenge.images[0],
                task_text=challenge.task_text,
                provider=provider,
                api_key=config.vlm_api_key,
                model=config.vlm_model,
            )

            if result and "x" in result and "y" in result:
                return SolveResult(
                    success=True,
                    solver_used=self.name,
                    click_x=int(result["x"]),
                    click_y=int(result["y"]),
                    canvas_width=1000,  # Standard hCaptcha canvas
                    canvas_height=940,
                    confidence=0.7,
                    cost_usd=cost,
                    solve_time_ms=int((time.time() - t0) * 1000),
                    details={"reasoning": result.get("reasoning", ""),
                             "provider": provider},
                )

        elif challenge.type in GRID_TYPES and challenge.images:
            result = await solve_grid_vlm(
                images_b64=challenge.images,
                task_text=challenge.task_text,
                provider=provider,
                api_key=config.vlm_api_key,
                model=config.vlm_model,
            )

            if result and "selections" in result:
                selections = [int(s) for s in result["selections"]
                            if isinstance(s, (int, float)) and 0 <= s < len(challenge.images)]
                if selections:
                    return SolveResult(
                        success=True,
                        solver_used=self.name,
                        selections=selections,
                        confidence=0.75,
                        cost_usd=cost * len(challenge.images),
                        solve_time_ms=int((time.time() - t0) * 1000),
                        details={"reasoning": result.get("reasoning", ""),
                                 "provider": provider},
                    )

        return SolveResult(
            success=False,
            solver_used=self.name,
            cost_usd=cost,
            solve_time_ms=int((time.time() - t0) * 1000),
            error="VLM did not return a valid solution",
        )
