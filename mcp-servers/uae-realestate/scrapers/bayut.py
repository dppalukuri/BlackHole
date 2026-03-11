"""
Bayut.com scraper - Headed stealth browser with session persistence.

Bayut uses reCAPTCHA v3 on every uncached request + Algolia as search backend.

Strategy order:
  1. Algolia direct API (if runtime keys cached from prior session)
  2. Headed Playwright with saved session (CAPTCHA-free if session valid)
  3. If CAPTCHA: auto-solve via CapSolver API or warm_up tool
  4. RapidAPI fallback (free tier: 750 calls/month)

URL pattern: /{for-sale|to-rent}/{type}/dubai/{location-slug}/
Filters: price_min, price_max, beds_min, beds_max, furnishing_status, completion_status, page
Data extraction: __NEXT_DATA__ (Next.js SSR), Apollo cache, DOM cards
Algolia index: bayut-production-ads-en

Env vars:
  CAPSOLVER_API_KEY  - For reCAPTCHA v3 solving (capsolver.com)
  BAYUT_RAPIDAPI_KEY - Fallback API key (rapidapi.com/apidojo/api/bayut)
"""

import os
import asyncio
import re
import json
from pathlib import Path
import httpx
from models import Property
import slug_registry

BASE_URL = "https://www.bayut.com"
RAPIDAPI_HOST = "bayut.p.rapidapi.com"
ALGOLIA_INDEX = "bayut-production-ads-en"

# Algolia runtime config cache file
_SESSIONS_DIR = Path(__file__).parent.parent / ".sessions"
_ALGOLIA_CACHE_FILE = _SESSIONS_DIR / "bayut_algolia.json"

# In-memory Algolia credentials (loaded from file or extracted at runtime)
_algolia_cache = {"app_id": "", "api_key": "", "browser_hosts": []}


def _load_algolia_cache():
    """Load cached Algolia config from file."""
    global _algolia_cache
    if _ALGOLIA_CACHE_FILE.exists():
        try:
            data = json.loads(_ALGOLIA_CACHE_FILE.read_text())
            if data.get("app_id") and data.get("api_key"):
                _algolia_cache.update(data)
        except Exception:
            pass


def _save_algolia_cache():
    """Save Algolia config to file for future sessions."""
    _SESSIONS_DIR.mkdir(exist_ok=True)
    try:
        _ALGOLIA_CACHE_FILE.write_text(json.dumps(_algolia_cache, indent=2))
    except Exception:
        pass


# Load cached keys on module import
_load_algolia_cache()


class BayutScraper:
    def __init__(self):
        self._stealth_browser = None
        self.api_key = os.environ.get("BAYUT_RAPIDAPI_KEY", "")

    async def _get_stealth_browser(self):
        if self._stealth_browser is None:
            from stealth_browser import get_stealth_browser
            self._stealth_browser = await get_stealth_browser()
        return self._stealth_browser

    async def search(
        self,
        location: str,
        purpose: str = "for-sale",
        property_type: str = "",
        min_price: int = 0,
        max_price: int = 0,
        bedrooms: int = -1,
        page: int = 1,
    ) -> list[Property]:
        """Search Bayut - tries Algolia, then Playwright, then RapidAPI."""
        # Strategy 1: Algolia direct (if we have cached runtime keys + hosts)
        if _algolia_cache["app_id"] and _algolia_cache["api_key"] and _algolia_cache.get("browser_hosts"):
            try:
                results = await self._search_algolia(
                    location, purpose, property_type, min_price, max_price, bedrooms, page
                )
                if results:
                    return results
            except Exception:
                pass

        # Strategy 2: Headed Playwright with saved session (may bypass CAPTCHA)
        try:
            results = await self._search_playwright(
                location, purpose, property_type, min_price, max_price, bedrooms, page
            )
            if results:
                return results
        except Exception:
            pass

        # Strategy 3: RapidAPI fallback
        if self.api_key:
            return await self._search_api(
                location, purpose, property_type, min_price, max_price, bedrooms, page
            )

        raise RuntimeError(
            "Bayut requires CAPTCHA solving. Set CAPSOLVER_API_KEY for automatic reCAPTCHA v3 "
            "solving, or use the warm_up_bayut tool to open a browser and solve manually. "
            "After solving, Bayut searches will work automatically using the saved session.\n"
            "Alternatively, set BAYUT_RAPIDAPI_KEY for API access (free at rapidapi.com)."
        )

    async def _search_playwright(
        self, location, purpose, property_type, min_price, max_price, bedrooms, page
    ) -> list[Property]:
        """Search using stealth Playwright with session persistence.

        Starts headless (invisible). If CAPTCHA is hit, escalates to headed
        mode to solve it, saves the session, then closes the window.
        """
        sb = await self._get_stealth_browser()
        url = self._build_url(location, purpose, property_type, min_price, max_price, bedrooms, page)

        # Try headless first (no visible window)
        for headed in (False, True):
            context = await sb.new_context(site_name="bayut", headed=headed)
            page_obj = await context.new_page()

            try:
                await page_obj.goto(url, wait_until="domcontentloaded", timeout=30000)
                try:
                    await page_obj.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass
                await asyncio.sleep(2)

                # CAPTCHA check
                if "captcha" in page_obj.url.lower():
                    if not headed:
                        await context.close()
                        continue  # Escalate to headed mode for CAPTCHA solving

                    from captcha import handle_captcha_if_present
                    solved = await handle_captcha_if_present(page_obj, max_retries=3)
                    if not solved:
                        return []
                    await asyncio.sleep(3)
                    try:
                        await page_obj.wait_for_load_state("networkidle", timeout=15000)
                    except Exception:
                        pass

                # Scroll to trigger lazy loading
                for _ in range(3):
                    await page_obj.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(0.5)
                await asyncio.sleep(1)

                await self._extract_algolia_keys(page_obj)
                properties = await self._extract_listings(page_obj)
                await sb.save_session(context)

                return properties
            finally:
                await context.close()

        return []

    async def warm_up(self, timeout: int = 120) -> str:
        """
        Interactive CAPTCHA solve: opens browser for user to solve hCaptcha.

        After solving, session cookies and Algolia keys are cached for future use.
        Returns status message.
        """
        sb = await self._get_stealth_browser()
        context = await sb.new_context(site_name="bayut", headed=True)
        page_obj = await context.new_page()

        try:
            # Move window on-screen for user interaction
            try:
                cdp = await context.new_cdp_session(page_obj)
                window = await cdp.send("Browser.getWindowForTarget")
                window_id = window.get("windowId")
                if window_id:
                    await cdp.send("Browser.setWindowBounds", {
                        "windowId": window_id,
                        "bounds": {"left": 100, "top": 100, "width": 1200, "height": 800, "windowState": "normal"}
                    })
            except Exception:
                pass

            await page_obj.goto(f"{BASE_URL}/to-rent/apartments/dubai/", wait_until="domcontentloaded", timeout=30000)
            try:
                await page_obj.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            await asyncio.sleep(3)

            if "captcha" not in page_obj.url.lower():
                # No CAPTCHA — session already valid
                await self._extract_algolia_keys(page_obj)
                await sb.save_session(context)
                return "Bayut session is already active — no CAPTCHA needed!"

            # Try automated CAPTCHA solving first
            from captcha import handle_captcha_if_present
            solved = await handle_captcha_if_present(page_obj, max_retries=3)

            # If automated solving failed, wait for user to solve manually
            if not solved:
                for i in range(timeout // 2):
                    await asyncio.sleep(2)
                    if "captcha" not in page_obj.url.lower():
                        solved = True
                        break

            if not solved:
                return (
                    "CAPTCHA was not solved within the timeout. "
                    "Please try again — a browser window will appear with the CAPTCHA."
                )

            # Wait for page to fully load after redirect
            await asyncio.sleep(3)
            try:
                await page_obj.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            # Extract and cache Algolia runtime keys
            await self._extract_algolia_keys(page_obj)
            await sb.save_session(context)

            return (
                "Bayut CAPTCHA solved successfully! Session saved. "
                "Bayut searches will now work without CAPTCHA until the session expires."
            )
        finally:
            await context.close()

    async def _extract_algolia_keys(self, page_obj):
        """Extract Algolia runtime config from the page (app ID, API key, browser hosts)."""
        global _algolia_cache
        try:
            config = await page_obj.evaluate("""() => {
                const result = {};

                // Extract from window.CONFIG.runtime (Bayut's runtime config)
                if (window.CONFIG && window.CONFIG.runtime) {
                    const rt = window.CONFIG.runtime;
                    for (const [k, v] of Object.entries(rt)) {
                        if (k.toLowerCase().includes('algolia')) {
                            result[k] = v;
                        }
                    }
                }

                // Extract from __NEXT_DATA__ runtimeConfig
                const el = document.getElementById('__NEXT_DATA__');
                if (el) {
                    try {
                        const d = JSON.parse(el.textContent);
                        const rc = d.runtimeConfig || d.props?.runtimeConfig || {};
                        for (const [k, v] of Object.entries(rc)) {
                            if (k.toLowerCase().includes('algolia')) {
                                result[k] = v;
                            }
                        }
                    } catch {}
                }

                // Try to extract the actual API key from the Redux/Algolia state
                // The key is computed at runtime by (0,Tn.A)() but stored in state
                try {
                    if (window.__NEXT_DATA__?.props?.pageProps?.algoliaApiKey) {
                        result.pageProps_apiKey = window.__NEXT_DATA__.props.pageProps.algoliaApiKey;
                    }
                } catch {}

                return Object.keys(result).length > 0 ? result : null;
            }""")

            if config:
                # Map known config keys to our cache format
                app_id = config.get("ALGOLIA_APP_ID", config.get("algoliaAppId", ""))
                api_key = config.get("ALGOLIA_API_KEY", config.get("algoliaApiKey", config.get("pageProps_apiKey", "")))
                hosts = config.get("ALGOLIA_BROWSER_HOST_NAMES", [])

                if app_id:
                    _algolia_cache["app_id"] = app_id
                if api_key:
                    _algolia_cache["api_key"] = api_key
                if hosts:
                    _algolia_cache["browser_hosts"] = hosts if isinstance(hosts, list) else [hosts]

                # Save to file for persistence across server restarts
                if _algolia_cache["app_id"] and (_algolia_cache["api_key"] or _algolia_cache.get("browser_hosts")):
                    _save_algolia_cache()
        except Exception:
            pass

    async def _search_algolia(
        self, location, purpose, property_type, min_price, max_price, bedrooms, page
    ) -> list[Property]:
        """Search Bayut via Algolia API directly (using cached runtime keys + proxy hosts)."""
        location_id = self._resolve_location_id(location)

        # Build Algolia filters
        filters = [f'purpose:"{purpose}"']
        filters.append(f'location.externalID:"{location_id}"')

        if property_type:
            type_ids = slug_registry.get("bayut", "property_types")
            type_id = type_ids.get(property_type.lower())
            if type_id:
                filters.append(f'category.externalID:"{type_id}"')

        if min_price > 0:
            filters.append(f"price >= {min_price}")
        if max_price > 0:
            filters.append(f"price <= {max_price}")
        if bedrooms >= 0:
            filters.append(f"rooms = {bedrooms}")

        filter_str = " AND ".join(filters)
        params_str = f"filters={filter_str}&hitsPerPage=25&page={page - 1}"

        payload = {
            "requests": [{
                "indexName": ALGOLIA_INDEX,
                "params": params_str,
            }],
        }

        algolia_headers = {
            "X-Algolia-Application-Id": _algolia_cache["app_id"],
            "X-Algolia-API-Key": _algolia_cache["api_key"],
            "Content-Type": "application/json",
            "Referer": "https://www.bayut.com/",
            "Origin": "https://www.bayut.com",
        }

        # Use browser hosts (Bayut proxy) if available, else standard Algolia
        hosts = _algolia_cache.get("browser_hosts", [])
        if not hosts:
            hosts = [f"{_algolia_cache['app_id']}-dsn.algolia.net"]

        async with httpx.AsyncClient(timeout=15) as client:
            for host in hosts:
                try:
                    url = f"https://{host}/1/indexes/*/queries"
                    resp = await client.post(url, headers=algolia_headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        properties = []
                        results = data.get("results", [])
                        if results:
                            for hit in results[0].get("hits", []):
                                prop = self._parse_listing(hit)
                                if prop:
                                    properties.append(prop)
                        return properties
                except Exception:
                    continue

        return []

    async def _extract_listings(self, page_obj) -> list[Property]:
        """Extract property listings from Bayut search results page.

        Uses aria-label selectors on <article> cards — Bayut labels every field
        (Title, Price, Beds, Baths, Area, Location, Type, Frequency, etc.).
        """
        raw = await page_obj.evaluate("""() => {
            const articles = document.querySelectorAll("article");
            const results = [];

            for (const card of articles) {
                // Get the listing link
                const link = card.querySelector('a[aria-label="Listing link"]');
                const href = link ? link.getAttribute("href") || "" : "";
                if (!href || !href.includes("/property/")) continue;

                // Helper: get text from first element with matching aria-label
                function aria(label) {
                    const el = card.querySelector('[aria-label="' + label + '"]');
                    return el ? el.textContent.trim() : "";
                }

                results.push({
                    href: href,
                    title: aria("Title"),
                    price: aria("Price"),
                    currency: aria("Currency") || "AED",
                    frequency: aria("Frequency"),
                    type: aria("Type"),
                    beds: aria("Beds"),
                    baths: aria("Baths"),
                    area: aria("Area"),
                    location: aria("Location"),
                });
            }
            return results;
        }""")

        if not raw:
            return []

        properties = []
        for item in raw:
            prop = self._parse_aria_card(item)
            if prop:
                properties.append(prop)
        return properties

    def _build_url(self, location, purpose, property_type, min_price, max_price, bedrooms, page):
        """Build Bayut search URL."""
        purpose_path = "for-sale" if purpose == "for-sale" else "to-rent"

        # Property type slug (for URL, need the slug form like "apartments", not the API ID)
        type_slug = self._resolve_type_slug(property_type) if property_type else None
        if not type_slug:
            type_slug = "property"

        # Location slug (for URL, need the slug form like "dubai-marina", not the API ID)
        loc_slug = self._resolve_location_slug(location)
        if not loc_slug:
            loc_slug = location.lower().strip().replace(" ", "-")

        url = f"{BASE_URL}/{purpose_path}/{type_slug}/dubai/{loc_slug}/"

        params = []
        if min_price > 0:
            params.append(f"price_min={min_price}")
        if max_price > 0:
            params.append(f"price_max={max_price}")
        if bedrooms >= 0:
            params.append(f"beds_min={bedrooms}")
            params.append(f"beds_max={bedrooms}")
        if page > 1:
            params.append(f"page={page}")

        if params:
            url += "?" + "&".join(params)

        return url

    async def _search_api(
        self, location, purpose, property_type, min_price, max_price, bedrooms, page
    ) -> list[Property]:
        """Search via RapidAPI (fallback)."""
        location_id = self._resolve_location_id(location)

        params = {
            "locationExternalIDs": location_id,
            "purpose": purpose,
            "hitsPerPage": 25,
            "page": page - 1,  # API is 0-indexed
            "lang": "en",
            "sort": "date-desc",
        }

        if property_type:
            type_ids = slug_registry.get("bayut", "property_types")
            type_id = type_ids.get(property_type.lower())
            if type_id:
                params["categoryExternalID"] = type_id
        if min_price > 0:
            params["priceMin"] = min_price
        if max_price > 0:
            params["priceMax"] = max_price
        if bedrooms >= 0:
            params["roomsMin"] = bedrooms
            params["roomsMax"] = bedrooms

        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{RAPIDAPI_HOST}/properties/list",
                headers=headers,
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

        properties = []
        for hit in data.get("hits", []):
            prop = self._parse_listing(hit)
            if prop:
                properties.append(prop)
        return properties

    async def get_details(self, property_id: str) -> Property:
        """Get details for a Bayut listing."""
        # Try Playwright first (headless, escalate if CAPTCHA)
        try:
            sb = await self._get_stealth_browser()
            context = await sb.new_context(site_name="bayut")
            page_obj = await context.new_page()
            try:
                url = f"{BASE_URL}/property/details-{property_id}.html"
                await page_obj.goto(url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)

                from captcha import handle_captcha_if_present
                await handle_captcha_if_present(page_obj)

                raw = await page_obj.evaluate("""() => {
                    const el = document.getElementById('__NEXT_DATA__');
                    if (!el) return null;
                    const d = JSON.parse(el.textContent);
                    return d.props?.pageProps?.property || d.props?.pageProps?.listing || null;
                }""")

                if raw:
                    prop = self._parse_listing(raw)
                    if prop:
                        await sb.save_session(context)
                        return prop
            finally:
                await context.close()
        except Exception:
            pass

        # Fallback to API
        if self.api_key:
            headers = {
                "x-rapidapi-host": RAPIDAPI_HOST,
                "x-rapidapi-key": self.api_key,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://{RAPIDAPI_HOST}/properties/detail",
                    headers=headers,
                    params={"externalID": property_id},
                    timeout=15,
                )
                resp.raise_for_status()
                return self._parse_listing(resp.json())

        raise RuntimeError("Cannot fetch Bayut details without CAPSOLVER_API_KEY or BAYUT_RAPIDAPI_KEY")

    def _resolve_location_id(self, location: str) -> str:
        """Resolve location to Bayut API external ID (numeric)."""
        loc_ids = slug_registry.get("bayut", "locations")
        normalized = location.lower().strip()
        if normalized in loc_ids:
            return loc_ids[normalized]
        for key, val in loc_ids.items():
            if normalized in key or key in normalized:
                return val
        available = sorted(loc_ids.keys())
        raise ValueError(
            f"Unknown location '{location}'. Available: {', '.join(available[:30])}"
        )

    def _resolve_location_slug(self, location: str) -> str | None:
        """Resolve location to Bayut URL slug (for Playwright URLs)."""
        loc_slugs = slug_registry.get("bayut", "location_slugs")
        normalized = location.lower().strip()
        if normalized in loc_slugs:
            return loc_slugs[normalized]
        for key, val in loc_slugs.items():
            if normalized in key or key in normalized:
                return val
        return None

    def _resolve_type_slug(self, property_type: str) -> str | None:
        """Resolve property type to Bayut URL slug (e.g. 'apartments')."""
        type_slugs = slug_registry.get("bayut", "property_type_slugs")
        normalized = property_type.lower().strip()
        if normalized in type_slugs:
            return type_slugs[normalized]
        for key, val in type_slugs.items():
            if normalized in key or key in normalized:
                return val
        return None

    def _parse_listing(self, data: dict) -> Property | None:
        try:
            location_parts = []
            for loc in data.get("location", []):
                if isinstance(loc, dict):
                    name = loc.get("name", "")
                    if name:
                        location_parts.append(name)

            emirate = location_parts[0] if len(location_parts) >= 1 else ""
            community = location_parts[1] if len(location_parts) >= 2 else ""
            sub_community = location_parts[2] if len(location_parts) >= 3 else ""

            amenities = []
            for group in data.get("amenities", []):
                if isinstance(group, dict):
                    for a in group.get("amenities", []):
                        if isinstance(a, dict):
                            amenities.append(a.get("text", ""))

            photo = ""
            cover = data.get("coverPhoto")
            if isinstance(cover, dict):
                photo = cover.get("url", "")

            area = float(data.get("area", 0))
            ext_id = str(data.get("externalID", data.get("id", "")))

            prop_type = ""
            category = data.get("category", [])
            if isinstance(category, list) and category:
                prop_type = category[0].get("nameSingular", "") if isinstance(category[0], dict) else ""
            elif isinstance(category, str):
                prop_type = category

            return Property(
                id=ext_id,
                source="bayut",
                title=data.get("title", ""),
                price=float(data.get("price", 0)),
                purpose=data.get("purpose", ""),
                property_type=prop_type,
                bedrooms=int(data.get("rooms", data.get("bedrooms", 0)) or 0),
                bathrooms=int(data.get("baths", data.get("bathrooms", 0)) or 0),
                area_sqft=area,
                location=", ".join(location_parts),
                emirate=emirate,
                community=community,
                sub_community=sub_community,
                latitude=float(data.get("geography", {}).get("lat", 0)),
                longitude=float(data.get("geography", {}).get("lng", 0)),
                furnishing=data.get("furnishingStatus", ""),
                completion_status=data.get("completionStatus", ""),
                description=str(data.get("description", ""))[:500],
                agent_name=data.get("contactName", ""),
                agency_name=data.get("agency", {}).get("name", "") if isinstance(data.get("agency"), dict) else "",
                url=f"{BASE_URL}/property/details-{ext_id}.html",
                image_url=photo,
                reference=data.get("referenceNumber", ""),
                amenities=amenities,
            )
        except Exception:
            return None

    def _parse_aria_card(self, item: dict) -> Property | None:
        """Parse a listing from aria-label extracted card data."""
        try:
            href = item.get("href", "")
            price_text = item.get("price", "").replace(",", "")
            price = float(price_text) if price_text else 0
            if price < 1000:
                return None

            # Extract ID from /property/details-12345678.html
            id_match = re.search(r"details-?(\d+)", href)
            prop_id = id_match.group(1) if id_match else ""

            # Beds: "2" or "Studio"
            beds_text = item.get("beds", "")
            if beds_text.lower() == "studio":
                bedrooms = 0
            else:
                beds_match = re.search(r"(\d+)", beds_text)
                bedrooms = int(beds_match.group(1)) if beds_match else 0

            # Baths
            baths_text = item.get("baths", "")
            baths_match = re.search(r"(\d+)", baths_text)
            bathrooms = int(baths_match.group(1)) if baths_match else 0

            # Area: "1,430 sqft" → 1430
            area_text = item.get("area", "").replace(",", "")
            area_match = re.search(r"([\d.]+)", area_text)
            area = float(area_match.group(1)) if area_match else 0

            # Location: "Trident Grand Residence, Dubai Marina, Dubai"
            location = item.get("location", "")
            loc_parts = [p.strip() for p in location.split(",")]
            emirate = loc_parts[-1] if len(loc_parts) >= 1 else ""
            community = loc_parts[-2] if len(loc_parts) >= 2 else ""
            sub_community = loc_parts[0] if len(loc_parts) >= 3 else ""

            # Frequency for purpose inference
            frequency = item.get("frequency", "").lower()
            purpose = "for-rent" if frequency in ("yearly", "monthly") else "for-sale"

            url = href if href.startswith("http") else f"{BASE_URL}{href}"

            return Property(
                id=prop_id,
                source="bayut",
                title=item.get("title", "") or "Property listing",
                price=price,
                purpose=purpose,
                property_type=item.get("type", ""),
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                area_sqft=area,
                location=location,
                emirate=emirate,
                community=community,
                sub_community=sub_community,
                url=url,
            )
        except Exception:
            return None

    async def cleanup(self):
        if self._stealth_browser:
            await self._stealth_browser.cleanup()
            self._stealth_browser = None
