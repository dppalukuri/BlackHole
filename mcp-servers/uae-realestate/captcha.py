"""
CAPTCHA detection and solving for UAE real estate scrapers.

Solving priority:
  1. Local CLIP vision model (free, no API key) via captcha-solver
  2. CapSolver API (paid fallback) if CAPSOLVER_API_KEY is set

Supports:
  - hCaptcha (Bayut) - image grid challenges
  - reCAPTCHA v2 (Dubizzle) - image selection challenges
"""

import os
import sys
import re
import asyncio
import httpx

CAPSOLVER_API_KEY = os.environ.get("CAPSOLVER_API_KEY", "")
CAPSOLVER_API = "https://api.capsolver.com"

# Add captcha-solver to path for local CLIP solving
_SOLVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "captcha-solver")
if _SOLVER_PATH not in sys.path:
    sys.path.insert(0, _SOLVER_PATH)


async def detect_captcha(page) -> dict | None:
    """Detect if current page has a CAPTCHA challenge. Returns captcha info or None."""
    info = await page.evaluate("""() => {
        // hCaptcha
        const hcIframe = document.querySelector('iframe[src*="hcaptcha"]');
        if (hcIframe) {
            const srcMatch = hcIframe.src.match(/sitekey=([a-f0-9-]+)/);
            return {
                type: 'hcaptcha',
                sitekey: srcMatch ? srcMatch[1] : null,
                url: location.href,
            };
        }
        const hcDiv = document.querySelector('[data-sitekey].h-captcha, .h-captcha[data-sitekey]');
        if (hcDiv) {
            return {
                type: 'hcaptcha',
                sitekey: hcDiv.getAttribute('data-sitekey'),
                url: location.href,
            };
        }

        // reCAPTCHA
        const rcIframe = document.querySelector('iframe[src*="recaptcha"]');
        if (rcIframe) {
            const srcMatch = rcIframe.src.match(/[?&]k=([a-zA-Z0-9_-]+)/);
            return {
                type: 'recaptcha',
                sitekey: srcMatch ? srcMatch[1] : null,
                url: location.href,
            };
        }
        const rcDiv = document.querySelector('.g-recaptcha[data-sitekey], [data-sitekey]');
        if (rcDiv && !document.querySelector('.h-captcha')) {
            return {
                type: 'recaptcha',
                sitekey: rcDiv.getAttribute('data-sitekey'),
                url: location.href,
            };
        }

        return null;
    }""")
    return info


async def solve_captcha_locally(page, captcha_info: dict) -> bool:
    """
    Solve CAPTCHA using local CLIP vision model.

    Extracts challenge images from the page, classifies with CLIP,
    clicks matching images, and submits.

    Returns True if solved successfully, False otherwise.
    """
    try:
        from solver import solve_hcaptcha_challenge
    except ImportError:
        return False

    captcha_type = captcha_info.get("type")
    if captcha_type != "hcaptcha":
        return False  # Only hCaptcha has extractable image grids

    # Find the hCaptcha challenge frame
    challenge_frame = None
    for frame in page.frames:
        if "hcaptcha" in frame.url:
            challenge_frame = frame
            break

    if not challenge_frame:
        return False

    # Click the checkbox to trigger the challenge
    try:
        checkbox = await challenge_frame.wait_for_selector("#checkbox", timeout=3000)
        if checkbox:
            await checkbox.click()
            await asyncio.sleep(2)
    except Exception:
        pass

    # Re-find the challenge frame (may have changed after checkbox click)
    for frame in page.frames:
        if "hcaptcha" in frame.url and "challenge" in frame.url:
            challenge_frame = frame
            break

    # Extract task text and images from the challenge
    challenge_data = await challenge_frame.evaluate("""() => {
        const taskEl = document.querySelector('.prompt-text, [class*="prompt"]');
        const task = taskEl ? taskEl.textContent.trim() : '';

        const images = [];

        // Try img elements first
        const imgs = document.querySelectorAll('.task-image img, .challenge-image img, [class*="image"] img');
        for (const img of imgs) {
            if (img.src && img.src.startsWith('http')) images.push(img.src);
        }

        // Try background images
        if (images.length === 0) {
            const divs = document.querySelectorAll('.task-image, [class*="image"], [class*="cell"]');
            for (const div of divs) {
                const bg = getComputedStyle(div).backgroundImage;
                const match = bg.match(/url\\("?(.+?)"?\\)/);
                if (match && match[1].startsWith('http')) images.push(match[1]);
            }
        }

        // Try canvas elements (convert to data URL)
        if (images.length === 0) {
            const canvases = document.querySelectorAll('canvas');
            for (const c of canvases) {
                try { images.push(c.toDataURL('image/png')); } catch(e) {}
            }
        }

        return { task, images };
    }""")

    task = challenge_data.get("task", "")
    images = challenge_data.get("images", [])

    if not task or not images:
        return False

    # Solve with CLIP
    result = await solve_hcaptcha_challenge(task, images, threshold=0.4)
    selections = result.get("selections", [])

    if not selections:
        return False

    # Click matching images in the challenge
    for idx in selections:
        try:
            await challenge_frame.evaluate(f"""() => {{
                const cells = document.querySelectorAll('.task-image, [class*="image"], [class*="cell"]');
                if (cells[{idx}]) cells[{idx}].click();
            }}""")
            await asyncio.sleep(0.3)
        except Exception:
            pass

    # Click verify/submit button
    await asyncio.sleep(0.5)
    try:
        await challenge_frame.evaluate("""() => {
            const btn = document.querySelector('.button-submit, [class*="submit"], button');
            if (btn) btn.click();
        }""")
    except Exception:
        pass

    await asyncio.sleep(3)

    # Check if CAPTCHA is gone
    remaining = await detect_captcha(page)
    return remaining is None


async def solve_captcha_api(captcha_info: dict) -> str | None:
    """Solve CAPTCHA via CapSolver API (paid fallback)."""
    if not CAPSOLVER_API_KEY:
        return None

    captcha_type = captcha_info.get("type")
    sitekey = captcha_info.get("sitekey")
    page_url = captcha_info.get("url")

    if not sitekey or not page_url:
        return None

    task_type = "HCaptchaTaskProxyLess" if captcha_type == "hcaptcha" else "ReCaptchaV2TaskProxyLess"

    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": task_type,
                "websiteURL": page_url,
                "websiteKey": sitekey,
            }
        })
        data = resp.json()
        if data.get("errorId", 0) != 0:
            return None

        task_id = data.get("taskId")
        if not task_id:
            return None

        # Poll for result
        for _ in range(40):
            await asyncio.sleep(3)
            resp = await client.post(f"{CAPSOLVER_API}/getTaskResult", json={
                "clientKey": CAPSOLVER_API_KEY,
                "taskId": task_id,
            })
            result = resp.json()
            if result.get("status") == "ready":
                solution = result.get("solution", {})
                return solution.get("gRecaptchaResponse") or solution.get("token")
            elif result.get("status") == "failed":
                return None

    return None


async def inject_captcha_token(page, captcha_info: dict, token: str) -> bool:
    """Inject solved CAPTCHA token into the page and submit."""
    captcha_type = captcha_info.get("type")

    result = await page.evaluate("""(args) => {
        const [token, type] = args;

        // Set response textareas
        const names = type === 'hcaptcha'
            ? ['h-captcha-response', 'g-recaptcha-response']
            : ['g-recaptcha-response'];

        for (const name of names) {
            const el = document.querySelector(`[name="${name}"]`);
            if (el) { el.value = token; el.style.display = 'block'; }
        }

        // Submit the form
        const form = document.querySelector('form');
        if (form) { form.submit(); return true; }

        const btn = document.querySelector('button[type="submit"], input[type="submit"]');
        if (btn) { btn.click(); return true; }

        return false;
    }""", [token, captcha_type])

    return bool(result)


async def handle_captcha_if_present(page, max_retries: int = 2) -> bool:
    """
    Detect and solve CAPTCHA on current page if present.

    Solving priority:
      1. Local CLIP solver (free)
      2. CapSolver API (if CAPSOLVER_API_KEY is set)

    Returns True if page is now CAPTCHA-free, False if unsolvable.
    """
    for attempt in range(max_retries):
        captcha = await detect_captcha(page)
        if not captcha:
            return True  # No CAPTCHA

        # Strategy 1: Local CLIP solver
        solved = await solve_captcha_locally(page, captcha)
        if solved:
            return True

        # Strategy 2: CapSolver API fallback
        if CAPSOLVER_API_KEY:
            token = await solve_captcha_api(captcha)
            if token:
                await inject_captcha_token(page, captcha, token)
                await asyncio.sleep(3)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    pass

                # Check if solved
                remaining = await detect_captcha(page)
                if not remaining:
                    return True

    return False
