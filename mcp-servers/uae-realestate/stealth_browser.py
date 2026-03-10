"""
Stealth browser manager - shared Playwright browser with anti-detection.

Uses playwright-stealth for fingerprint evasion and persistent sessions
to minimize CAPTCHA triggers. Supports headless and headed modes.
"""

import asyncio
import os
import json
from pathlib import Path

# Session storage directory for cookies/state persistence
SESSION_DIR = Path(__file__).parent / ".sessions"


class StealthBrowser:
    """Manages stealth Playwright browsers with session persistence."""

    def __init__(self):
        self._browsers = {}  # key: "headless" or "headed"
        self._playwright = None
        self._stealth = None

    async def _ensure_playwright(self):
        if self._playwright:
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Stealth browser requires Playwright. Install with:\n"
                "  pip install playwright && playwright install chromium"
            )

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
        await self._ensure_playwright()
        key = "headed" if headed else "headless"

        if key not in self._browsers or not self._browsers[key].is_connected():
            args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ]
            if headed:
                args.extend([
                    "--window-position=-32000,-32000",  # off-screen
                ])

            self._browsers[key] = await self._playwright.chromium.launch(
                headless=not headed,
                args=args,
            )
        return self._browsers[key]

    async def new_context(self, site_name: str = "default", headed: bool = False):
        """Create a new browser context with stealth and optional session persistence."""
        browser = await self._get_browser(headed=headed)

        SESSION_DIR.mkdir(exist_ok=True)
        state_file = SESSION_DIR / f"{site_name}_state.json"

        ctx_options = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "viewport": {"width": 1920, "height": 1080},
            "locale": "en-AE",
            "timezone_id": "Asia/Dubai",
            "geolocation": {"latitude": 25.2048, "longitude": 55.2708},
            "permissions": ["geolocation"],
        }

        # Restore previous session state if available
        if state_file.exists():
            try:
                ctx_options["storage_state"] = str(state_file)
            except Exception:
                pass

        context = await browser.new_context(**ctx_options)

        # Apply stealth scripts
        if self._stealth:
            await self._stealth.apply_stealth_async(context)

        # Additional manual stealth patches
        await context.add_init_script("""
            // Override webdriver
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

            // Chrome object
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; },
                    app: { isInstalled: false },
                };
            }

            // Plugin array
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    const plugins = [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' },
                    ];
                    plugins.item = (i) => plugins[i];
                    plugins.namedItem = (n) => plugins.find(p => p.name === n);
                    plugins.refresh = () => {};
                    return plugins;
                }
            });

            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'ar']
            });

            // Connection
            if (!navigator.connection) {
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({ effectiveType: '4g', rtt: 50, downlink: 10, saveData: false })
                });
            }

            // Permissions override
            const originalQuery = window.Permissions?.prototype?.query;
            if (originalQuery) {
                window.Permissions.prototype.query = (params) => {
                    if (params.name === 'notifications') {
                        return Promise.resolve({ state: Notification.permission });
                    }
                    return originalQuery.call(window.Permissions.prototype, params);
                };
            }
        """)

        # Store context metadata for session saving
        context._state_file = state_file
        context._site_name = site_name

        context._is_headed = headed
        return context

    async def save_session(self, context):
        """Save browser context state (cookies, localStorage) for reuse."""
        try:
            state_file = getattr(context, "_state_file", None)
            if state_file:
                state = await context.storage_state()
                state_file.write_text(json.dumps(state))
        except Exception:
            pass

    async def cleanup(self):
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ResourceWarning)
            for key, browser in list(self._browsers.items()):
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


# Shared singleton instance
_browser = StealthBrowser()


async def get_stealth_browser() -> StealthBrowser:
    """Get the shared stealth browser instance."""
    return _browser
