"""
Backward-compatible shim — routes through CaptchaRouter (CLIP → Gemini VLM → API).

Existing code that does `from solver import solve_hcaptcha_challenge` continues to work,
but now benefits from the full v2.0 solver chain with free Gemini VLM fallback.
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


def _get_router():
    """Get a CaptchaRouter with config loaded from env vars (cached)."""
    if not hasattr(_get_router, "_instance"):
        from server import _load_config
        from router import CaptchaRouter
        _get_router._instance = CaptchaRouter(_load_config())
    return _get_router._instance


# Old API functions — now route through full CLIP → Gemini → API chain
async def solve_hcaptcha_challenge(task_text, image_data, threshold=0.55):
    router = _get_router()
    result = await router.solve_raw(
        task_text=task_text, images=image_data,
        is_canvas=False, captcha_type="hcaptcha",
    )
    return {
        "task": task_text,
        "target": enhance_task_text(task_text),
        "selections": result.selections,
        "details": result.details.get("results", []),
    }


async def solve_recaptcha_challenge(task_text, image_data, threshold=0.55):
    return await solve_hcaptcha_challenge(task_text, image_data, threshold)


async def solve_canvas_challenge(canvas_data_url, task_text=""):
    router = _get_router()
    result = await router.solve_raw(
        task_text=task_text, images=[canvas_data_url],
        is_canvas=True, captcha_type="hcaptcha",
    )
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
