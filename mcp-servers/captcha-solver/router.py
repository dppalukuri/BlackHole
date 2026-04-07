"""Smart solver routing -- tries cheapest viable solver first, escalates on failure."""

import logging
import re
from core.types import (
    CaptchaChallenge, SolveResult, SolverConfig,
    HCAPTCHA_GRID, HCAPTCHA_CANVAS_BUCKET, HCAPTCHA_CANVAS_SILHOUETTE,
    HCAPTCHA_CANVAS_LINE, HCAPTCHA_CANVAS_UNKNOWN,
    RECAPTCHA_V2, RECAPTCHA_V3, TURNSTILE, FUNCAPTCHA,
)
from solvers.clip_grid import CLIPGridSolver
from solvers.clip_canvas import CLIPCanvasSolver
from solvers.vlm import VLMSolver
from solvers.token_api import ExternalAPISolver


# Solver chain per challenge type (cheapest first)
ROUTING_TABLE = {
    HCAPTCHA_GRID: ["clip_grid", "vlm", "token_api"],
    HCAPTCHA_CANVAS_BUCKET: ["clip_canvas", "vlm"],
    HCAPTCHA_CANVAS_SILHOUETTE: ["clip_canvas", "vlm"],
    HCAPTCHA_CANVAS_LINE: ["clip_canvas", "vlm"],
    HCAPTCHA_CANVAS_UNKNOWN: ["vlm", "clip_canvas"],
    RECAPTCHA_V2: ["clip_grid", "vlm", "token_api"],
    RECAPTCHA_V3: ["token_api"],
    TURNSTILE: ["token_api"],
    FUNCAPTCHA: ["vlm", "token_api"],
}

# Minimum confidence to accept a solver's result
CONFIDENCE_GATES = {
    "clip_grid": 0.45,
    "clip_canvas": 0.45,
    "vlm": 0.3,
    "token_api": 0.0,  # Always accept external API results
}


def classify_challenge(task_text: str, images: list[str], is_canvas: bool,
                       captcha_type: str = "hcaptcha") -> str:
    """Classify a raw challenge into a specific challenge type."""
    task_lower = task_text.lower()

    if captcha_type == "recaptcha_v3":
        return RECAPTCHA_V3

    if captcha_type == "recaptcha":
        if is_canvas:
            return RECAPTCHA_V2  # reCAPTCHA doesn't have canvas types
        return RECAPTCHA_V2

    if captcha_type == "turnstile":
        return TURNSTILE

    if captcha_type == "funcaptcha":
        return FUNCAPTCHA

    # hCaptcha classification
    if is_canvas and len(images) == 1:
        if "bucket" in task_lower or "catch the ball" in task_lower:
            return HCAPTCHA_CANVAS_BUCKET
        elif "silhouette" in task_lower or "character in the middle" in task_lower:
            return HCAPTCHA_CANVAS_SILHOUETTE
        elif "solid line" in task_lower or "connected" in task_lower:
            return HCAPTCHA_CANVAS_LINE
        else:
            return HCAPTCHA_CANVAS_UNKNOWN
    elif len(images) > 1:
        return HCAPTCHA_GRID

    return HCAPTCHA_CANVAS_UNKNOWN


logger = logging.getLogger("captcha_solver.router")


class CaptchaRouter:
    """Routes challenges to solvers based on type, cost, and confidence."""

    def __init__(self, config: SolverConfig | None = None):
        self.config = config or SolverConfig()
        self._solvers = {
            "clip_grid": CLIPGridSolver(),
            "clip_canvas": CLIPCanvasSolver(),
            "vlm": VLMSolver(),
            "token_api": ExternalAPISolver(),
        }

        # When VLM is available and prefer_local is False (e.g. free Gemini),
        # reorder chains to put VLM before CLIP (avoids 350MB model download)
        if self.config.enable_vlm and not self.config.prefer_local:
            self._routing = {}
            for ctype, chain in ROUTING_TABLE.items():
                if "vlm" in chain and any(s.startswith("clip") for s in chain):
                    # Move VLM before CLIP solvers
                    new_chain = ["vlm"] + [s for s in chain if s != "vlm"]
                    self._routing[ctype] = new_chain
                else:
                    self._routing[ctype] = chain
        else:
            self._routing = ROUTING_TABLE

    async def solve(self, challenge: CaptchaChallenge) -> SolveResult:
        """Try solvers in order until one succeeds above confidence threshold."""
        chain = self._routing.get(challenge.type, ["vlm", "clip_canvas", "token_api"])

        for solver_name in chain:
            solver = self._solvers.get(solver_name)
            if not solver:
                continue

            # Check cost budget
            if solver.cost_per_solve > self.config.max_cost_per_solve:
                continue

            # Check if solver can handle this challenge
            if not await solver.can_solve(challenge):
                continue

            result = await solver.solve(challenge, self.config)

            if result.success:
                gate = CONFIDENCE_GATES.get(solver_name, 0.3)
                # If CLIP result is below gate AND VLM is available, skip to VLM
                if result.confidence < gate and solver_name.startswith("clip") and self.config.enable_vlm:
                    logger.info("Solver %s below gate (%.2f < %.2f), escalating",
                                solver_name, result.confidence, gate)
                    continue
                logger.info("Solved via %s: success=%s conf=%.2f time=%dms",
                            solver_name, result.success, result.confidence, result.solve_time_ms)
                return result

        logger.warning("All solvers failed for challenge type=%s", challenge.type)
        return SolveResult(success=False, error="All solvers failed")

    async def solve_raw(
        self,
        task_text: str,
        images: list[str],
        is_canvas: bool = False,
        captcha_type: str = "hcaptcha",
        sitekey: str | None = None,
        page_url: str | None = None,
    ) -> SolveResult:
        """Convenience method — classify challenge type and solve."""
        challenge_type = classify_challenge(task_text, images, is_canvas, captcha_type)
        challenge = CaptchaChallenge(
            type=challenge_type,
            task_text=task_text,
            images=images,
            is_canvas=is_canvas,
            sitekey=sitekey,
            page_url=page_url,
        )
        return await self.solve(challenge)
