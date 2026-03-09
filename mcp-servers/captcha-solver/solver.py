"""
Backward-compatible shim — imports from new module structure.

Existing code that does `from solver import solve_hcaptcha_challenge` continues to work.
"""

import os
import sys

# Ensure the package root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Re-export everything from old API
from solvers.clip_grid import CLIPGridSolver, enhance_task_text, TASK_REWRITES
from solvers.clip_canvas import (
    _decode_canvas, _solve_bucket, _solve_silhouette, _solve_line,
    CLIPCanvasSolver,
)
from vision.clip import (
    load_image, classify_image, classify_images_batch,
    get_image_embeddings, match_image_to_text,
)

import asyncio


# Old API functions
async def solve_hcaptcha_challenge(task_text, image_data, threshold=0.55):
    from core.types import CaptchaChallenge, SolverConfig, HCAPTCHA_GRID
    solver = CLIPGridSolver()
    challenge = CaptchaChallenge(type=HCAPTCHA_GRID, task_text=task_text, images=image_data)
    config = SolverConfig(clip_threshold=threshold)
    result = await solver.solve(challenge, config)
    return {
        "task": task_text,
        "target": enhance_task_text(task_text),
        "selections": result.selections,
        "details": result.details.get("results", []),
    }


async def solve_recaptcha_challenge(task_text, image_data, threshold=0.55):
    return await solve_hcaptcha_challenge(task_text, image_data, threshold)


async def solve_canvas_challenge(canvas_data_url, task_text=""):
    from core.types import CaptchaChallenge, SolverConfig
    from router import classify_challenge
    challenge_type = classify_challenge(task_text, [canvas_data_url], True, "hcaptcha")
    challenge = CaptchaChallenge(
        type=challenge_type, task_text=task_text,
        images=[canvas_data_url], is_canvas=True,
    )
    solver = CLIPCanvasSolver()
    result = await solver.solve(challenge, SolverConfig())
    if not result.success:
        return None
    return {
        "canvas_x": result.click_x,
        "canvas_y": result.click_y,
        "canvas_width": result.canvas_width,
        "canvas_height": result.canvas_height,
        "confidence": result.confidence,
    }


async def solve_silhouette_challenge(canvas_data_url, task_text=""):
    return await solve_canvas_challenge(canvas_data_url, task_text)


async def classify_single_image(image_data, labels):
    img = load_image(image_data)
    result = await asyncio.to_thread(classify_image, img, labels)
    return result
