"""
CAPTCHA detection and solving for UAE real estate scrapers.

Solving priority:
  1. reCAPTCHA v3 (Bayut): CapSolver/2Captcha API (token-based, no images)
  2. hCaptcha / reCAPTCHA v2: Local CLIP/VLM (free) → CapSolver API (paid)

Supports:
  - reCAPTCHA v3 (Bayut) - invisible score-based, solved via token API
  - hCaptcha - image grid challenges (multiple rounds)
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
    """Check if the local CLIP solver is importable (lightweight check)."""
    import importlib.util
    return importlib.util.find_spec("solver") is not None or os.path.isfile(
        os.path.join(_SOLVER_PATH, "solver.py")
    )


async def detect_captcha(page) -> dict | None:
    """Detect if current page has a CAPTCHA challenge. Returns captcha info or None."""
    try:
        info = await page.evaluate("""() => {
            const isCaptchaPage = location.pathname.includes('captcha');

            // --- reCAPTCHA v3 detection (Bayut's current system) ---
            const badge = document.querySelector('.grecaptcha-badge');
            const rcScript = document.querySelector(
                'script[src*="recaptcha/api.js"], script[src*="recaptcha/enterprise.js"]'
            );

            let v3Sitekey = null;
            // Try Next.js runtime config (Bayut stores STRAT_RECAPTCHA_KEY here)
            try {
                const nd = window.__NEXT_DATA__;
                if (nd) {
                    const rc = nd.runtimeConfig || nd.props?.pageProps || {};
                    v3Sitekey = rc.STRAT_RECAPTCHA_KEY || rc.recaptchaKey || null;
                }
            } catch(e) {}
            // Try script src render= param
            if (!v3Sitekey && rcScript) {
                const match = (rcScript.getAttribute('src') || '').match(/render=([a-zA-Z0-9_-]+)/);
                if (match && match[1] !== 'explicit') v3Sitekey = match[1];
            }
            // Try data-sitekey on any element (but not hCaptcha)
            if (!v3Sitekey && !document.querySelector('.h-captcha')) {
                const el = document.querySelector('[data-sitekey]');
                if (el) v3Sitekey = el.getAttribute('data-sitekey');
            }

            // If we have v3 indicators and we're on a captcha page, it's reCAPTCHA v3
            if (isCaptchaPage && (badge || rcScript || v3Sitekey)) {
                return {
                    type: 'recaptcha_v3',
                    sitekey: v3Sitekey,
                    url: location.href,
                };
            }

            // --- hCaptcha detection ---
            if (isCaptchaPage) {
                const hcDiv = document.querySelector('[data-sitekey].h-captcha, .h-captcha[data-sitekey]');
                if (hcDiv) {
                    return {
                        type: 'hcaptcha',
                        sitekey: hcDiv.getAttribute('data-sitekey'),
                        url: location.href,
                    };
                }
            }
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

            // --- reCAPTCHA v2 detection ---
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
    except Exception:
        return None


def _find_checkbox_frame(page, captcha_type: str):
    """Find the CAPTCHA checkbox iframe (separate from challenge frame)."""
    keyword = "hcaptcha" if captcha_type == "hcaptcha" else "recaptcha"
    for frame in page.frames:
        url = frame.url.lower()
        if keyword in url and "checkbox" in url:
            return frame
    # Fallback: any frame with the keyword (for reCAPTCHA which may not have checkbox in URL)
    for frame in page.frames:
        if keyword in frame.url.lower():
            return frame
    return None


def _find_challenge_frame(page, captcha_type: str):
    """Find the CAPTCHA challenge iframe (where images are shown)."""
    keyword = "hcaptcha" if captcha_type == "hcaptcha" else "recaptcha"
    for frame in page.frames:
        url = frame.url.lower()
        if keyword in url and ("challenge" in url or "bframe" in url or "api2" in url):
            return frame
    return None


async def _click_checkbox(page, captcha_type: str) -> bool:
    """Click the CAPTCHA checkbox to trigger the image challenge."""
    # Use the checkbox-specific frame, not the challenge frame
    frame = _find_checkbox_frame(page, captcha_type)
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
    challenge_frame = _find_challenge_frame(page, captcha_type)

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
            let is_canvas = false;
            if (images.length === 0) {
                const canvases = document.querySelectorAll('canvas');
                for (const c of canvases) {
                    try {
                        images.push(c.toDataURL('image/png'));
                        is_canvas = true;
                    } catch(e) {}
                }
            }

            return { task, images, is_canvas };
        }""")
        return data
    except Exception:
        return {"task": "", "images": []}


async def _click_challenge_cells(page, captcha_type: str, indices: list[int]):
    """Click specific cells in the CAPTCHA challenge grid."""
    challenge_frame = _find_challenge_frame(page, captcha_type)
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
    challenge_frame = _find_challenge_frame(page, captcha_type)
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


async def _solve_canvas_round(page, captcha_type: str, image_data: str, task_text: str = "") -> bool:
    """
    Solve one round of an hCaptcha single-image challenge.

    Handles both canvas-based and img-based challenges.
    Routes to VLM (Gemini) or CLIP based on the solver chain.
    """
    try:
        from solver import solve_canvas_challenge

        result = await solve_canvas_challenge(image_data, task_text)
        if not result:
            return False

        # Find the clickable element in the challenge frame (canvas or img)
        challenge_frame = _find_challenge_frame(page, captcha_type)
        if not challenge_frame:
            return False

        # Try canvas first, then img
        element = None
        for selector in ["canvas", ".task-image img", ".challenge-image img", "img[src]"]:
            try:
                element = await challenge_frame.wait_for_selector(selector, timeout=2000)
                if element:
                    break
            except Exception:
                continue

        if not element:
            return False

        box = await element.bounding_box()
        if not box:
            return False

        # Scale solver coords to display coords
        scale_x = box["width"] / result["canvas_width"]
        scale_y = box["height"] / result["canvas_height"]
        click_x = box["x"] + result["canvas_x"] * scale_x
        click_y = box["y"] + result["canvas_y"] * scale_y

        await page.mouse.click(click_x, click_y)
        await asyncio.sleep(1)

        # Click submit
        await _click_submit(page, captcha_type)
        return True
    except Exception as e:
        return False


async def _try_recaptcha_v3_browser(page, timeout: int = 10) -> bool:
    """
    Wait for reCAPTCHA v3 to auto-resolve in the browser.

    reCAPTCHA v3 is invisible and score-based. If the browser has good stealth,
    the page will auto-execute grecaptcha and redirect on its own.
    """
    original_url = page.url
    for _ in range(timeout):
        await asyncio.sleep(1)
        if "captcha" not in page.url.lower():
            return True  # Page navigated away from captcha
        if page.url != original_url and "captcha" not in page.url.lower():
            return True
    return False


async def solve_recaptcha_v3(page, captcha_info: dict) -> bool:
    """
    Solve reCAPTCHA v3 challenge.

    reCAPTCHA v3 is invisible/score-based — no images to classify.
    Strategy:
      1. Wait for browser auto-resolve (stealth might score high enough)
      2. CapSolver/2Captcha API to get a valid token
      3. Inject token and submit the form
    """
    # Strategy 1: Wait for browser to auto-resolve (free)
    if await _try_recaptcha_v3_browser(page, timeout=8):
        return True

    # Strategy 2: CapSolver API (paid)
    if not CAPSOLVER_API_KEY:
        return False

    sitekey = captcha_info.get("sitekey")
    page_url = captcha_info.get("url")
    if not sitekey or not page_url:
        return False

    token = await _solve_recaptcha_v3_api(sitekey, page_url)
    if not token:
        return False

    # Inject token and submit
    injected = await inject_captcha_token(page, captcha_info, token)
    if injected:
        await asyncio.sleep(3)
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        # Check if we left the captcha page
        if "captcha" not in page.url.lower():
            return True

    return False


async def _solve_recaptcha_v3_api(sitekey: str, page_url: str) -> str | None:
    """Get reCAPTCHA v3 token from CapSolver API."""
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": CAPSOLVER_API_KEY,
            "task": {
                "type": "ReCaptchaV3TaskProxyLess",
                "websiteURL": page_url,
                "websiteKey": sitekey,
                "pageAction": "captchaChallenge",
                "minScore": 0.7,
            }
        })
        data = resp.json()
        if data.get("errorId", 0) != 0:
            return None

        task_id = data.get("taskId")
        if not task_id:
            return None

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


async def solve_captcha_locally(page, captcha_info: dict, timeout: int = 90) -> bool:
    """
    Solve CAPTCHA using captcha-solver (Gemini VLM → CLIP → API chain).

    Handles multiple challenge rounds (hCaptcha often requires 2-3 rounds).
    Supports both hCaptcha and reCAPTCHA v2.
    Has a timeout to prevent hanging on slow model downloads.

    Returns True if solved successfully, False otherwise.
    """
    if not _solver_available():
        return False

    try:
        return await asyncio.wait_for(
            _solve_captcha_rounds(page, captcha_info), timeout=timeout
        )
    except asyncio.TimeoutError:
        return False


async def _solve_captcha_rounds(page, captcha_info: dict) -> bool:
    """Inner CAPTCHA solving loop — multiple rounds."""
    captcha_type = captcha_info.get("type", "hcaptcha")
    max_rounds = 5  # hCaptcha can require multiple rounds

    # Click the checkbox to trigger the challenge
    await _click_checkbox(page, captcha_type)
    await asyncio.sleep(3)  # hCaptcha needs time to render the challenge canvas

    for round_num in range(max_rounds):
        # Check if already solved (no more CAPTCHA)
        remaining = await detect_captcha(page)
        if not remaining:
            return True

        # Extract challenge data
        challenge = await _extract_challenge_data(page, captcha_type)
        task = challenge.get("task", "")
        images = challenge.get("images", [])
        is_canvas = challenge.get("is_canvas", False)

        if not images:
            # No challenge visible — might be solved or transition
            await asyncio.sleep(2)
            remaining = await detect_captcha(page)
            if not remaining:
                return True
            continue

        # Single-image challenge: canvas click OR image-based "tap on" challenge
        # hCaptcha serves these as both <canvas> and <img> — handle both
        if len(images) == 1:
            solved = await _solve_canvas_round(page, captcha_type, images[0], task)
            if solved:
                await asyncio.sleep(3)
                remaining = await detect_captcha(page)
                if not remaining:
                    return True
                continue  # More rounds possible

        # Regular grid challenge: text-to-image classification
        if not task:
            await asyncio.sleep(2)
            remaining = await detect_captcha(page)
            if not remaining:
                return True
            continue

        from solver import solve_hcaptcha_challenge

        result = await solve_hcaptcha_challenge(task, images, threshold=0.5)
        selections = result.get("selections", [])

        if not selections:
            # Couldn't match anything — try lower threshold
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
                // Find existing element or create one
                let el = document.querySelector(`[name="${name}"]`);
                if (!el) {
                    el = document.createElement('textarea');
                    el.name = name;
                    el.style.display = 'none';
                    document.body.appendChild(el);
                }
                el.value = token;
            }

            // Try hCaptcha callback
            if (type === 'hcaptcha' && typeof hcaptcha !== 'undefined') {
                try { hcaptcha.execute(); } catch(e) {}
            }

            // Try reCAPTCHA v3 callback (grecaptcha.execute resolves to token)
            if ((type === 'recaptcha_v3' || type === 'recaptcha') && typeof grecaptcha !== 'undefined') {
                try {
                    // Try enterprise callback
                    if (typeof grecaptcha.enterprise !== 'undefined') {
                        const widgets = grecaptcha.enterprise.getResponse;
                    }
                    // Find callback from data-callback attributes
                    const widgets = document.querySelectorAll('[data-callback]');
                    for (const w of widgets) {
                        const cbName = w.getAttribute('data-callback');
                        if (cbName && typeof window[cbName] === 'function') {
                            window[cbName](token);
                            return true;
                        }
                    }
                    // Try ___grecaptcha_cfg callbacks
                    if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {
                        for (const clientId in window.___grecaptcha_cfg.clients) {
                            const client = window.___grecaptcha_cfg.clients[clientId];
                            // Walk the client object tree looking for callback functions
                            const findCallback = (obj, depth) => {
                                if (depth > 5 || !obj) return null;
                                for (const key in obj) {
                                    if (typeof obj[key] === 'function') return obj[key];
                                    if (typeof obj[key] === 'object') {
                                        const cb = findCallback(obj[key], depth + 1);
                                        if (cb) return cb;
                                    }
                                }
                                return null;
                            };
                            const cb = findCallback(client, 0);
                            if (cb) { cb(token); return true; }
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
      - reCAPTCHA v3: browser auto-resolve → CapSolver API (token-based)
      - hCaptcha/reCAPTCHA v2: Local CLIP/VLM → CapSolver API

    Returns True if page is now CAPTCHA-free, False if unsolvable.
    """
    for attempt in range(max_retries):
        captcha = await detect_captcha(page)
        if not captcha:
            return True  # No CAPTCHA

        captcha_type = captcha.get("type", "")

        # --- reCAPTCHA v3: invisible, score-based (no images to classify) ---
        if captcha_type == "recaptcha_v3":
            solved = await solve_recaptcha_v3(page, captcha)
            if solved:
                await asyncio.sleep(2)
                try:
                    await page.wait_for_load_state("load", timeout=10000)
                except Exception:
                    pass
                return True
            # v3 failed — wait and retry (score may improve)
            await asyncio.sleep(3)
            continue

        # --- hCaptcha / reCAPTCHA v2: image-based challenges ---
        # Strategy 1: Local CLIP/VLM solver (handles multi-round challenges)
        solved = await solve_captcha_locally(page, captcha)
        if solved:
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

                remaining = await detect_captcha(page)
                if not remaining:
                    return True

        await asyncio.sleep(2)

    return False
