"""
CAPTCHA detection and solving for UAE real estate scrapers.

Solving priority:
  1. Local CLIP vision model (free, no API key) via captcha-solver
  2. CapSolver API (paid fallback) if CAPSOLVER_API_KEY is set

Supports:
  - hCaptcha (Bayut) - image grid challenges (multiple rounds)
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


def _solver_available() -> bool:
    """Check if the local CLIP solver is importable."""
    try:
        from solver import solve_hcaptcha_challenge
        return True
    except ImportError:
        return False


async def detect_captcha(page) -> dict | None:
    """Detect if current page has a CAPTCHA challenge. Returns captcha info or None."""
    try:
        info = await page.evaluate("""() => {
            // Check for CAPTCHA challenge page (Bayut redirects to /captchaChallenge)
            if (location.pathname.includes('captcha')) {
                const hcDiv = document.querySelector('[data-sitekey].h-captcha, .h-captcha[data-sitekey]');
                if (hcDiv) {
                    return {
                        type: 'hcaptcha',
                        sitekey: hcDiv.getAttribute('data-sitekey'),
                        url: location.href,
                    };
                }
            }

            // hCaptcha iframe
            const hcIframe = document.querySelector('iframe[src*="hcaptcha"]');
            if (hcIframe) {
                const srcMatch = hcIframe.src.match(/sitekey=([a-f0-9-]+)/);
                return {
                    type: 'hcaptcha',
                    sitekey: srcMatch ? srcMatch[1] : null,
                    url: location.href,
                };
            }
            // hCaptcha div
            const hcDiv = document.querySelector('[data-sitekey].h-captcha, .h-captcha[data-sitekey]');
            if (hcDiv) {
                return {
                    type: 'hcaptcha',
                    sitekey: hcDiv.getAttribute('data-sitekey'),
                    url: location.href,
                };
            }

            // reCAPTCHA iframe
            const rcIframe = document.querySelector('iframe[src*="recaptcha"]');
            if (rcIframe) {
                const srcMatch = rcIframe.src.match(/[?&]k=([a-zA-Z0-9_-]+)/);
                return {
                    type: 'recaptcha',
                    sitekey: srcMatch ? srcMatch[1] : null,
                    url: location.href,
                };
            }
            // reCAPTCHA div
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
    except Exception:
        return None


async def _find_challenge_frame(page, captcha_type: str):
    """Find the CAPTCHA challenge iframe."""
    keyword = "hcaptcha" if captcha_type == "hcaptcha" else "recaptcha"
    for frame in page.frames:
        if keyword in frame.url:
            return frame
    return None


async def _click_checkbox(page, captcha_type: str) -> bool:
    """Click the CAPTCHA checkbox to trigger the image challenge."""
    frame = await _find_challenge_frame(page, captcha_type)
    if not frame:
        return False

    try:
        if captcha_type == "hcaptcha":
            checkbox = await frame.wait_for_selector("#checkbox", timeout=5000)
        else:
            checkbox = await frame.wait_for_selector(".recaptcha-checkbox-border, #recaptcha-anchor", timeout=5000)

        if checkbox:
            await checkbox.click()
            await asyncio.sleep(2)
            return True
    except Exception:
        pass
    return False


async def _extract_challenge_data(page, captcha_type: str) -> dict:
    """Extract task text and images from the active CAPTCHA challenge frame."""
    keyword = "hcaptcha" if captcha_type == "hcaptcha" else "recaptcha"

    # Find the challenge frame (may differ from checkbox frame)
    challenge_frame = None
    for frame in page.frames:
        url = frame.url.lower()
        if keyword in url and ("challenge" in url or "bframe" in url or "api2" in url):
            challenge_frame = frame
            break

    # Fallback: any frame with the keyword
    if not challenge_frame:
        for frame in page.frames:
            if keyword in frame.url:
                challenge_frame = frame
                break

    if not challenge_frame:
        return {"task": "", "images": []}

    try:
        data = await challenge_frame.evaluate("""() => {
            // Extract task text
            let task = '';
            const taskSelectors = [
                '.prompt-text',
                '.rc-imageselect-desc-wrapper',
                '.rc-imageselect-desc',
                '[class*="prompt"]',
                '.display-language .prompt-text',
            ];
            for (const sel of taskSelectors) {
                const el = document.querySelector(sel);
                if (el && el.textContent.trim()) {
                    task = el.textContent.trim();
                    break;
                }
            }

            // Extract images
            const images = [];

            // Strategy 1: img elements in challenge cells
            const imgSelectors = [
                '.task-image img',
                '.challenge-image img',
                '.rc-image-tile-wrapper img',
                '.rc-imageselect-tile img',
                '[class*="image"] img',
                '.image img',
            ];
            for (const sel of imgSelectors) {
                const imgs = document.querySelectorAll(sel);
                for (const img of imgs) {
                    if (img.src && (img.src.startsWith('http') || img.src.startsWith('data:'))) {
                        images.push(img.src);
                    }
                }
                if (images.length > 0) break;
            }

            // Strategy 2: background images on cells
            if (images.length === 0) {
                const cellSelectors = [
                    '.task-image',
                    '.challenge-image',
                    '.rc-image-tile-wrapper',
                    '[class*="image"]',
                    '[class*="cell"]',
                ];
                for (const sel of cellSelectors) {
                    const divs = document.querySelectorAll(sel);
                    for (const div of divs) {
                        const bg = getComputedStyle(div).backgroundImage;
                        const match = bg.match(/url\\("?(.+?)"?\\)/);
                        if (match && (match[1].startsWith('http') || match[1].startsWith('data:'))) {
                            images.push(match[1]);
                        }
                    }
                    if (images.length > 0) break;
                }
            }

            // Strategy 3: canvas elements (convert to data URL)
            if (images.length === 0) {
                const canvases = document.querySelectorAll('canvas');
                for (const c of canvases) {
                    try {
                        images.push(c.toDataURL('image/png'));
                    } catch(e) {}
                }
            }

            return { task, images };
        }""")
        return data
    except Exception:
        return {"task": "", "images": []}


async def _click_challenge_cells(page, captcha_type: str, indices: list[int]):
    """Click specific cells in the CAPTCHA challenge grid."""
    keyword = "hcaptcha" if captcha_type == "hcaptcha" else "recaptcha"

    challenge_frame = None
    for frame in page.frames:
        url = frame.url.lower()
        if keyword in url and ("challenge" in url or "bframe" in url or "api2" in url):
            challenge_frame = frame
            break
    if not challenge_frame:
        for frame in page.frames:
            if keyword in frame.url:
                challenge_frame = frame
                break
    if not challenge_frame:
        return

    for idx in indices:
        try:
            await challenge_frame.evaluate(f"""() => {{
                const selectors = [
                    '.task-image',
                    '.challenge-image',
                    '.rc-image-tile-wrapper',
                    '[class*="image"]',
                    '[class*="cell"]',
                ];
                for (const sel of selectors) {{
                    const cells = document.querySelectorAll(sel);
                    if (cells.length > 0 && cells[{idx}]) {{
                        cells[{idx}].click();
                        break;
                    }}
                }}
            }}""")
            await asyncio.sleep(0.3)
        except Exception:
            pass


async def _click_submit(page, captcha_type: str):
    """Click the verify/submit button in the challenge frame."""
    keyword = "hcaptcha" if captcha_type == "hcaptcha" else "recaptcha"

    challenge_frame = None
    for frame in page.frames:
        url = frame.url.lower()
        if keyword in url and ("challenge" in url or "bframe" in url or "api2" in url):
            challenge_frame = frame
            break
    if not challenge_frame:
        for frame in page.frames:
            if keyword in frame.url:
                challenge_frame = frame
                break
    if not challenge_frame:
        return

    try:
        await challenge_frame.evaluate("""() => {
            const selectors = [
                '.button-submit',
                '.verify-button-holder button',
                '#submit',
                '[class*="submit"]',
                '.rc-button-default',
                'button[type="submit"]',
                'button',
            ];
            for (const sel of selectors) {
                const btn = document.querySelector(sel);
                if (btn && btn.textContent.match(/verify|submit|check|next/i)) {
                    btn.click();
                    return;
                }
            }
            // Fallback: click any submit-like button
            const btn = document.querySelector('.button-submit, .verify-button-holder button, .rc-button-default');
            if (btn) btn.click();
        }""")
    except Exception:
        pass


async def solve_captcha_locally(page, captcha_info: dict) -> bool:
    """
    Solve CAPTCHA using local CLIP vision model from captcha-solver.

    Handles multiple challenge rounds (hCaptcha often requires 2-3 rounds).
    Supports both hCaptcha and reCAPTCHA v2.

    Returns True if solved successfully, False otherwise.
    """
    if not _solver_available():
        return False

    from solver import solve_hcaptcha_challenge

    captcha_type = captcha_info.get("type", "hcaptcha")
    max_rounds = 5  # hCaptcha can require multiple rounds

    # Click the checkbox to trigger the challenge
    await _click_checkbox(page, captcha_type)
    await asyncio.sleep(1)

    for round_num in range(max_rounds):
        # Check if already solved (no more CAPTCHA)
        remaining = await detect_captcha(page)
        if not remaining:
            return True

        # Extract challenge data
        challenge = await _extract_challenge_data(page, captcha_type)
        task = challenge.get("task", "")
        images = challenge.get("images", [])

        if not task or not images:
            # No challenge visible — might be solved or transition
            await asyncio.sleep(2)
            remaining = await detect_captcha(page)
            if not remaining:
                return True
            continue

        # Solve with CLIP
        result = await solve_hcaptcha_challenge(task, images, threshold=0.5)
        selections = result.get("selections", [])

        if not selections:
            # CLIP couldn't match anything — try lower threshold
            result = await solve_hcaptcha_challenge(task, images, threshold=0.35)
            selections = result.get("selections", [])

        if not selections:
            # Still nothing — skip this round (will retry at outer level)
            return False

        # Click the matching images
        await _click_challenge_cells(page, captcha_type, selections)
        await asyncio.sleep(0.5)

        # Click verify/submit
        await _click_submit(page, captcha_type)
        await asyncio.sleep(3)

        # Check result — CAPTCHA might present another round
        remaining = await detect_captcha(page)
        if not remaining:
            return True

        # Still have CAPTCHA — might be a new round, loop back
        await asyncio.sleep(1)

    return False


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

    try:
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

            // Try hCaptcha callback
            if (type === 'hcaptcha' && typeof hcaptcha !== 'undefined') {
                try { hcaptcha.execute(); } catch(e) {}
            }

            // Try reCAPTCHA callback
            if (type === 'recaptcha' && typeof grecaptcha !== 'undefined') {
                try {
                    const callback = grecaptcha.getResponse ? null : null;
                    // Find the callback from the widget
                    const widgets = document.querySelectorAll('[data-callback]');
                    for (const w of widgets) {
                        const cbName = w.getAttribute('data-callback');
                        if (cbName && typeof window[cbName] === 'function') {
                            window[cbName](token);
                            return true;
                        }
                    }
                } catch(e) {}
            }

            // Submit the form
            const form = document.querySelector('form');
            if (form) { form.submit(); return true; }

            const btn = document.querySelector('button[type="submit"], input[type="submit"]');
            if (btn) { btn.click(); return true; }

            return false;
        }""", [token, captcha_type])
        return bool(result)
    except Exception:
        return False


async def handle_captcha_if_present(page, max_retries: int = 3) -> bool:
    """
    Detect and solve CAPTCHA on current page if present.

    Solving priority:
      1. Local CLIP solver (free, handles multiple rounds)
      2. CapSolver API (if CAPSOLVER_API_KEY is set)

    Returns True if page is now CAPTCHA-free, False if unsolvable.
    """
    for attempt in range(max_retries):
        captcha = await detect_captcha(page)
        if not captcha:
            return True  # No CAPTCHA

        # Strategy 1: Local CLIP solver (handles multi-round challenges)
        solved = await solve_captcha_locally(page, captcha)
        if solved:
            # Wait for page to settle after CAPTCHA solve
            await asyncio.sleep(2)
            try:
                await page.wait_for_load_state("load", timeout=10000)
            except Exception:
                pass
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

        # Wait before retry
        await asyncio.sleep(2)

    return False
