"""
CAPTCHA Solver MCP Server

AI-powered CAPTCHA solving using CLIP vision model.
No API keys needed - runs entirely locally on CPU.

Tools:
  - solve_hcaptcha: Solve hCaptcha image grid challenges
  - solve_recaptcha: Solve reCAPTCHA v2 image challenges
  - classify_image: General-purpose image classification
  - extract_and_solve: Extract CAPTCHA from a live page and solve it

Run:
  python server.py
"""

import os
import sys
import json
import asyncio
import base64
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from solver import solve_hcaptcha_challenge, solve_recaptcha_challenge, classify_single_image


@dataclass
class AppContext:
    model_loaded: bool


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    # Pre-load the CLIP model on startup
    from vision import _load_model
    await asyncio.to_thread(_load_model)
    yield AppContext(model_loaded=True)


mcp = FastMCP(
    "CAPTCHA Solver",
    instructions=(
        "AI-powered CAPTCHA solver using CLIP vision model. "
        "Solves hCaptcha and reCAPTCHA image challenges locally without API keys. "
        "Pass challenge images and task description to get solutions."
    ),
    lifespan=app_lifespan,
)


@mcp.tool()
async def solve_hcaptcha(
    task_text: str,
    image_urls: list[str],
    threshold: float = 0.55,
) -> str:
    """
    Solve an hCaptcha image grid challenge using CLIP vision AI.

    Args:
        task_text: The challenge instruction (e.g., "Please click each image containing a motorbus")
        image_urls: List of image URLs or base64 data URIs for the grid images
        threshold: Confidence threshold (0-1, default 0.55). Lower = more selections.

    Returns:
        JSON with matched image indices and confidence scores.
    """
    result = await solve_hcaptcha_challenge(task_text, image_urls, threshold)
    return json.dumps(result, indent=2)


@mcp.tool()
async def solve_recaptcha(
    task_text: str,
    image_urls: list[str],
    threshold: float = 0.55,
) -> str:
    """
    Solve a reCAPTCHA v2 image challenge using CLIP vision AI.

    Args:
        task_text: The challenge instruction (e.g., "Select all images with crosswalks")
        image_urls: List of image URLs or base64 data URIs
        threshold: Confidence threshold (0-1, default 0.55)

    Returns:
        JSON with matched image indices and confidence scores.
    """
    result = await solve_recaptcha_challenge(task_text, image_urls, threshold)
    return json.dumps(result, indent=2)


@mcp.tool()
async def classify_image(
    image_url: str,
    labels: list[str],
) -> str:
    """
    Classify an image against a list of text descriptions using CLIP.

    Useful for general image understanding beyond just CAPTCHA solving.

    Args:
        image_url: URL or base64 data URI of the image
        labels: List of text descriptions to match against (e.g., ["a cat", "a dog", "a bird"])

    Returns:
        JSON with {label: probability} sorted by probability.
    """
    result = await classify_single_image(image_url, labels)
    return json.dumps(result, indent=2)


@mcp.tool()
async def extract_and_solve_hcaptcha(
    page_url: str,
    sitekey: str,
) -> str:
    """
    Extract hCaptcha challenge from a page and solve it.

    Launches a browser, triggers the hCaptcha, extracts challenge images,
    solves with CLIP, and returns the token.

    Args:
        page_url: The URL of the page with hCaptcha
        sitekey: The hCaptcha sitekey (from data-sitekey attribute or iframe URL)

    Returns:
        JSON with solution token (if successful) or error details.
    """
    try:
        return json.dumps(await _browser_solve_hcaptcha(page_url, sitekey), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


async def _browser_solve_hcaptcha(page_url: str, sitekey: str) -> dict:
    """Full browser-based hCaptcha solving pipeline."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"error": "Playwright required for browser-based solving. pip install playwright"}

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )
    page = await context.new_page()

    try:
        await page.goto(page_url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)

        # Find the hCaptcha iframe
        hcaptcha_frame = None
        for frame in page.frames:
            if "hcaptcha" in frame.url:
                hcaptcha_frame = frame
                break

        if not hcaptcha_frame:
            return {"error": "No hCaptcha iframe found on page"}

        # Try to click the checkbox to trigger the challenge
        try:
            checkbox = await hcaptcha_frame.wait_for_selector("#checkbox", timeout=5000)
            if checkbox:
                await checkbox.click()
                await asyncio.sleep(2)
        except Exception:
            pass

        # Find the challenge frame (opens after clicking checkbox)
        challenge_frame = None
        for frame in page.frames:
            if "hcaptcha" in frame.url and "challenge" in frame.url:
                challenge_frame = frame
                break

        if not challenge_frame:
            challenge_frame = hcaptcha_frame

        # Extract task text and images
        challenge_data = await challenge_frame.evaluate("""() => {
            // Get task text
            const taskEl = document.querySelector('.prompt-text, [class*="prompt"]');
            const task = taskEl ? taskEl.textContent.trim() : '';

            // Get grid images
            const images = [];
            const cells = document.querySelectorAll('.task-image img, .challenge-image img, [class*="image"] img');
            for (const img of cells) {
                if (img.src) images.push(img.src);
            }

            // If no img tags, try background images
            if (images.length === 0) {
                const divs = document.querySelectorAll('.task-image, [class*="image"]');
                for (const div of divs) {
                    const bg = getComputedStyle(div).backgroundImage;
                    const match = bg.match(/url\\("?(.+?)"?\\)/);
                    if (match) images.push(match[1]);
                }
            }

            return { task, images, imageCount: images.length };
        }""")

        if not challenge_data.get("images"):
            return {"error": "Could not extract challenge images", "data": challenge_data}

        # Solve with CLIP
        result = await solve_hcaptcha_challenge(
            challenge_data["task"],
            challenge_data["images"],
        )

        # Click the matching images
        selections = result.get("selections", [])
        if selections:
            for idx in selections:
                try:
                    await challenge_frame.evaluate(f"""() => {{
                        const cells = document.querySelectorAll('.task-image, [class*="image"]');
                        if (cells[{idx}]) cells[{idx}].click();
                    }}""")
                    await asyncio.sleep(0.3)
                except Exception:
                    pass

            # Click verify/submit
            await asyncio.sleep(0.5)
            try:
                submit = await challenge_frame.wait_for_selector(
                    '.button-submit, [class*="submit"], button[type="submit"]',
                    timeout=3000
                )
                if submit:
                    await submit.click()
                    await asyncio.sleep(3)
            except Exception:
                pass

        # Check if we got a token
        token = await page.evaluate("""() => {
            const textarea = document.querySelector('[name="h-captcha-response"], [name="g-recaptcha-response"]');
            return textarea ? textarea.value : null;
        }""")

        result["token"] = token
        result["success"] = bool(token)
        return result

    finally:
        await browser.close()
        await pw.stop()


# ─── RESOURCES ─────────────────────────────────────────────────────────────────

@mcp.resource("captcha-solver://help")
def help_text() -> str:
    """Usage guide for the CAPTCHA Solver MCP server."""
    return """
CAPTCHA SOLVER MCP SERVER - USAGE GUIDE

This server uses CLIP (OpenAI's vision model) to solve image-based CAPTCHAs locally.
No API keys or external services needed.

SOLVE HCAPTCHA:
  solve_hcaptcha(
      task_text="Please click each image containing a motorbus",
      image_urls=["https://...", "https://...", ...],
      threshold=0.55
  )

SOLVE RECAPTCHA:
  solve_recaptcha(
      task_text="Select all images with crosswalks",
      image_urls=["https://...", ...],
      threshold=0.55
  )

CLASSIFY ANY IMAGE:
  classify_image(
      image_url="https://example.com/photo.jpg",
      labels=["a cat", "a dog", "a bird", "a car"]
  )

FULL BROWSER SOLVE:
  extract_and_solve_hcaptcha(
      page_url="https://example.com/page-with-captcha",
      sitekey="the-hcaptcha-sitekey"
  )

SUPPORTED CAPTCHA TYPES:
  - hCaptcha image grid (3x3, 4x4)
  - reCAPTCHA v2 image selection

HOW IT WORKS:
  1. CLIP model matches images to text descriptions
  2. Challenge task text is parsed and enhanced for better accuracy
  3. Each grid image is classified as matching or not matching
  4. Indices of matching images are returned

ACCURACY:
  - Common objects (vehicles, animals, traffic signs): ~85-90%
  - Complex scenes (crosswalks, specific areas): ~70-80%
  - Multiple attempts may be needed for difficult challenges

MODEL:
  - openai/clip-vit-base-patch32 (~350MB, downloaded on first use)
  - Runs on CPU, no GPU required
  - First request takes ~5-10s (model loading), subsequent ~1-2s
""".strip()


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
