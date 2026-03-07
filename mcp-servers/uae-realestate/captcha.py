"""
CAPTCHA detection and solving for UAE real estate scrapers.

Supports:
  - hCaptcha (Bayut)
  - reCAPTCHA v2/v3 (Dubizzle)

Uses CapSolver API (capsolver.com) - sign up for free trial credits.
Set env var: CAPSOLVER_API_KEY=your_key

Alternative services can be added by implementing the solve_* methods.
"""

import os
import re
import asyncio
import httpx

CAPSOLVER_API_KEY = os.environ.get("CAPSOLVER_API_KEY", "")
CAPSOLVER_API = "https://api.capsolver.com"


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


async def solve_captcha(captcha_info: dict) -> str | None:
    """
    Solve a CAPTCHA using CapSolver API.

    Returns the solution token, or None if solving fails.
    """
    api_key = CAPSOLVER_API_KEY
    if not api_key:
        return None

    captcha_type = captcha_info.get("type")
    sitekey = captcha_info.get("sitekey")
    page_url = captcha_info.get("url")

    if not sitekey or not page_url:
        return None

    if captcha_type == "hcaptcha":
        return await _solve_hcaptcha(api_key, sitekey, page_url)
    elif captcha_type == "recaptcha":
        return await _solve_recaptcha(api_key, sitekey, page_url)

    return None


async def _solve_hcaptcha(api_key: str, sitekey: str, page_url: str) -> str | None:
    """Solve hCaptcha via CapSolver."""
    async with httpx.AsyncClient(timeout=180) as client:
        # Create task
        resp = await client.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": api_key,
            "task": {
                "type": "HCaptchaTaskProxyLess",
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
        return await _poll_result(client, api_key, task_id)


async def _solve_recaptcha(api_key: str, sitekey: str, page_url: str) -> str | None:
    """Solve reCAPTCHA v2 via CapSolver."""
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(f"{CAPSOLVER_API}/createTask", json={
            "clientKey": api_key,
            "task": {
                "type": "ReCaptchaV2TaskProxyLess",
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

        return await _poll_result(client, api_key, task_id)


async def _poll_result(client: httpx.AsyncClient, api_key: str, task_id: str, max_wait: int = 120) -> str | None:
    """Poll CapSolver for task result."""
    for _ in range(max_wait // 3):
        await asyncio.sleep(3)
        resp = await client.post(f"{CAPSOLVER_API}/getTaskResult", json={
            "clientKey": api_key,
            "taskId": task_id,
        })
        data = resp.json()
        status = data.get("status")
        if status == "ready":
            solution = data.get("solution", {})
            return solution.get("gRecaptchaResponse") or solution.get("token")
        elif status == "failed":
            return None
    return None


async def inject_captcha_token(page, captcha_info: dict, token: str) -> bool:
    """Inject solved CAPTCHA token into the page and submit."""
    captcha_type = captcha_info.get("type")

    if captcha_type == "hcaptcha":
        return await _inject_hcaptcha(page, token)
    elif captcha_type == "recaptcha":
        return await _inject_recaptcha(page, token)
    return False


async def _inject_hcaptcha(page, token: str) -> bool:
    """Inject hCaptcha token and trigger callback."""
    result = await page.evaluate(f"""(token) => {{
        // Set the response textarea
        const textarea = document.querySelector('[name="h-captcha-response"], textarea[name="h-captcha-response"]');
        if (textarea) textarea.value = token;

        // Also set g-recaptcha-response (hCaptcha compat mode)
        const gTextarea = document.querySelector('[name="g-recaptcha-response"]');
        if (gTextarea) gTextarea.value = token;

        // Try to trigger the callback
        if (typeof window.hcaptcha !== 'undefined') {{
            try {{
                // Get the widget ID
                const widgetIds = window.hcaptcha.getAllWidgetIds ? window.hcaptcha.getAllWidgetIds() : [0];
                for (const id of widgetIds) {{
                    window.hcaptcha.setData(id, {{ response: token }});
                }}
            }} catch(e) {{}}
        }}

        // Submit the form
        const form = document.querySelector('form');
        if (form) {{
            form.submit();
            return true;
        }}

        // Try clicking a submit button
        const btn = document.querySelector('button[type="submit"], input[type="submit"], .challenge-submit');
        if (btn) {{
            btn.click();
            return true;
        }}

        return false;
    }}""", token)
    return bool(result)


async def _inject_recaptcha(page, token: str) -> bool:
    """Inject reCAPTCHA token and trigger callback."""
    result = await page.evaluate(f"""(token) => {{
        const textarea = document.querySelector('#g-recaptcha-response, [name="g-recaptcha-response"]');
        if (textarea) {{
            textarea.style.display = 'block';
            textarea.value = token;
        }}

        // Trigger callback
        if (typeof ___grecaptcha_cfg !== 'undefined') {{
            try {{
                const clients = ___grecaptcha_cfg.clients;
                for (const key in clients) {{
                    const client = clients[key];
                    // Find callback in nested structure
                    const findCallback = (obj) => {{
                        for (const k in obj) {{
                            if (typeof obj[k] === 'function') return obj[k];
                            if (typeof obj[k] === 'object' && obj[k] !== null) {{
                                const cb = findCallback(obj[k]);
                                if (cb) return cb;
                            }}
                        }}
                        return null;
                    }};
                    const cb = findCallback(client);
                    if (cb) cb(token);
                }}
            }} catch(e) {{}}
        }}

        // Submit form
        const form = document.querySelector('form');
        if (form) {{
            form.submit();
            return true;
        }}
        return false;
    }}""", token)
    return bool(result)


async def handle_captcha_if_present(page, max_retries: int = 1) -> bool:
    """
    Detect and solve CAPTCHA on current page if present.

    Returns True if page is now CAPTCHA-free (either no CAPTCHA was present,
    or it was solved successfully). Returns False if CAPTCHA couldn't be solved.
    """
    for attempt in range(max_retries):
        captcha = await detect_captcha(page)
        if not captcha:
            return True  # No CAPTCHA, good to go

        if not CAPSOLVER_API_KEY:
            return False  # Can't solve without API key

        sitekey = captcha.get("sitekey")
        if not sitekey:
            return False

        token = await solve_captcha(captcha)
        if not token:
            return False

        await inject_captcha_token(page, captcha, token)
        await asyncio.sleep(3)

        # Wait for navigation after CAPTCHA solve
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

    # Final check - is CAPTCHA still there?
    final_captcha = await detect_captcha(page)
    return final_captcha is None
