"""CLIP-based solver for image grid CAPTCHAs (hCaptcha/reCAPTCHA v2)."""

import asyncio
import re
from core.types import (
    CaptchaChallenge, SolveResult, SolverConfig,
    HCAPTCHA_GRID, RECAPTCHA_V2,
)
from solvers.base import BaseSolver


# Common hCaptcha task mappings to improve CLIP accuracy
TASK_REWRITES = {
    "motorbus": "a bus on a road",
    "bus": "a bus on a road",
    "airplane": "an airplane in the sky",
    "motorcycle": "a motorcycle",
    "bicycle": "a bicycle",
    "boat": "a boat on water",
    "traffic light": "a traffic light",
    "fire hydrant": "a fire hydrant on a street",
    "stop sign": "a stop sign",
    "parking meter": "a parking meter",
    "horse": "a horse",
    "elephant": "an elephant",
    "bear": "a bear",
    "zebra": "a zebra",
    "giraffe": "a giraffe",
    "dog": "a dog",
    "cat": "a cat",
    "bird": "a bird",
    "train": "a train on tracks",
    "truck": "a truck on a road",
    "car": "a car on a road",
    "bridge": "a bridge",
    "chimney": "a chimney on a roof",
    "crosswalk": "a crosswalk or pedestrian crossing",
    "staircase": "a staircase or stairs",
    "bedroom": "a bedroom with a bed",
    "living room": "a living room",
    "kitchen": "a kitchen with appliances",
    "bathroom": "a bathroom",
    "swimming pool": "a swimming pool",
    "seaplane": "a seaplane on water",
    "vertical river": "a river flowing vertically",
}


def enhance_task_text(raw_task: str) -> str:
    """Extract target object from task text and rewrite for better CLIP accuracy."""
    patterns = [
        r"containing (?:a |an )?(.+?)\.?$",
        r"with (?:a |an )?(.+?)\.?$",
        r"showing (?:a |an )?(.+?)\.?$",
        r"select (?:all )?(?:images? )?(?:of |with )?(?:a |an )?(.+?)\.?$",
        r"click (?:on )?(?:each |all )?(?:images? )?(?:containing |with |of )?(?:a |an )?(.+?)\.?$",
    ]

    target = raw_task.lower().strip()
    for pattern in patterns:
        match = re.search(pattern, target, re.I)
        if match:
            target = match.group(1).strip()
            break

    if target in TASK_REWRITES:
        return TASK_REWRITES[target]

    if not target.startswith(("a ", "an ", "the ")):
        target = f"a {target}"
    return target


class CLIPGridSolver(BaseSolver):
    """Solve image grid CAPTCHAs using CLIP zero-shot classification."""

    name = "clip_grid"
    cost_per_solve = 0.0  # Free, runs locally

    async def can_solve(self, challenge: CaptchaChallenge) -> bool:
        return challenge.type in (HCAPTCHA_GRID, RECAPTCHA_V2) and len(challenge.images) > 1

    async def solve(self, challenge: CaptchaChallenge, config: SolverConfig) -> SolveResult:
        import time
        from PIL import Image
        from vision.clip import load_image, classify_images_batch

        t0 = time.time()
        target = enhance_task_text(challenge.task_text)

        images = []
        for src in challenge.images:
            try:
                images.append(load_image(src))
            except Exception:
                images.append(Image.new("RGB", (100, 100), (128, 128, 128)))

        if not images:
            return SolveResult(success=False, solver_used=self.name, error="No images loaded")

        results = await asyncio.to_thread(
            classify_images_batch, images,
            target_label=target,
            threshold=config.clip_threshold,
        )

        selections = [r["index"] for r in results if r["match"]]

        # Fallback: if no matches, take the best above 0.35
        if not selections and results:
            best = max(results, key=lambda r: r["confidence"])
            if best["confidence"] > 0.35:
                selections = [best["index"]]

        confidence = max((r["confidence"] for r in results), default=0.0) if results else 0.0

        return SolveResult(
            success=len(selections) > 0,
            solver_used=self.name,
            selections=selections,
            confidence=confidence,
            solve_time_ms=int((time.time() - t0) * 1000),
            details={"target": target, "results": results},
        )
