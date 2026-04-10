"""
Stealth browser manager for SERP scraping.

Same pattern as google-maps and uae-realestate.
"""

import asyncio
import json
from pathlib import Path

SESSION_DIR = Path(__file__).parent / ".sessions"


class StealthBrowser:
    """Manages stealth Playwright browsers with session persistence."""

    def __init__(self):
        self._browsers = {}
        self._playwright = None
        self._stealth = None

    async def _ensure_playwright(self):
        if self._playwright:
            return

        from playwright.async_api import async_playwright

        try:
            from playwright_stealth import Stealth
            self._stealth = Stealth(
                navigator_webdriver=True,
                navigator_plugins=True,
                navigator_permissions=True,
                navigator_languages=True,
                navigator_platform=True,
                navigator_vendor=True,
                navigator_user_agent=True,
                webgl_vendor=True,
                chrome_app=True,
                chrome_runtime=False,
                iframe_content_window=True,
                media_codecs=True,
                hairline=True,
                sec_ch_ua=True,
            )
        except ImportError:
            self._stealth = None

        self._playwright = await async_playwright().start()

    async def _get_browser(self, headed: bool = False):
        key = "headed" if headed else "headless"
        if key in self._browsers:
            return self._browsers[key]

        await self._ensure_playwright()
        browser = await self._playwright.chromium.launch(
            headless=not headed,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        self._browsers[key] = browser
        return browser

    async def new_context(self, headed: bool = False, session_name: str = "default"):
        """Create a new browser context with optional session persistence."""
        browser = await self._get_browser(headed=headed)

        SESSION_DIR.mkdir(exist_ok=True)
        state_file = SESSION_DIR / f"{session_name}.json"

        kwargs = {
            "viewport": {"width": 1366, "height": 768},
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "locale": "en-US",
        }

        if state_file.exists():
            try:
                kwargs["storage_state"] = str(state_file)
            except Exception:
                pass

        context = await browser.new_context(**kwargs)

        if self._stealth:
            await self._stealth.apply_stealth_async(context)

        return context

    async def save_session(self, context, session_name: str = "default"):
        SESSION_DIR.mkdir(exist_ok=True)
        state_file = SESSION_DIR / f"{session_name}.json"
        state = await context.storage_state()
        state_file.write_text(json.dumps(state))

    async def cleanup(self):
        for browser in self._browsers.values():
            try:
                await browser.close()
            except Exception:
                pass
        self._browsers.clear()
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
