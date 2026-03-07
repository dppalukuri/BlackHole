"""
Dubizzle.com scraper - Uses Playwright with scroll-triggered lazy loading.

NOTE: Dubizzle has aggressive anti-bot protection (reCAPTCHA).
Headless scraping may return zero results. This scraper attempts
multiple strategies but may fail silently. PropertyFinder and Bayut
are more reliable sources.

Requires: pip install playwright && playwright install chromium
"""

import asyncio
import json
import re
from models import Property

BASE_URL = "https://dubai.dubizzle.com"

LOCATION_SLUGS = {
    "dubai marina": "dubai-marina",
    "downtown dubai": "downtown-dubai",
    "business bay": "business-bay",
    "jbr": "jumeirah-beach-residence-jbr",
    "jumeirah beach residence": "jumeirah-beach-residence-jbr",
    "palm jumeirah": "palm-jumeirah",
    "dubai hills": "dubai-hills-estate",
    "dubai hills estate": "dubai-hills-estate",
    "arabian ranches": "arabian-ranches",
    "jvc": "jumeirah-village-circle-jvc",
    "jumeirah village circle": "jumeirah-village-circle-jvc",
    "dubai creek harbour": "dubai-creek-harbour",
    "al barsha": "al-barsha",
    "deira": "deira",
    "motor city": "motor-city",
    "sports city": "dubai-sports-city",
    "damac hills": "damac-hills-akoya-by-damac",
    "jlt": "jumeirah-lake-towers-jlt",
    "jumeirah lake towers": "jumeirah-lake-towers-jlt",
    "difc": "difc",
    "city walk": "city-walk",
    "meydan": "meydan-city",
    "silicon oasis": "dubai-silicon-oasis",
    "dubai silicon oasis": "dubai-silicon-oasis",
    "emirates hills": "emirates-hills",
    "discovery gardens": "discovery-gardens",
    "international city": "international-city",
    "dubai south": "dubai-south-dubai-world-central",
    "mirdif": "mirdif",
    "dubailand": "dubailand",
    "al furjan": "al-furjan",
    "town square": "town-square",
    "mudon": "mudon",
    "al nahda": "al-nahda",
    "jumeirah": "jumeirah",
    "production city": "international-media-production-zone-impz",
}

PROPERTY_TYPE_SLUGS = {
    "apartment": "apartmentflat",
    "villa": "villa",
    "townhouse": "townhouse",
    "penthouse": "penthouse",
    "duplex": "duplex",
}


class DubizzleScraper:
    def __init__(self):
        self._browser = None
        self._playwright = None

    async def _get_browser(self):
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                raise ImportError(
                    "Dubizzle scraper requires Playwright. Install with:\n"
                    "  pip install playwright && playwright install chromium"
                )
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
        return self._browser

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
        """Search Dubizzle listings using Playwright with scroll loading."""
        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-AE",
            timezone_id="Asia/Dubai",
        )

        page_obj = await context.new_page()
        await page_obj.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        properties = []
        api_listings = []

        try:
            # Intercept API responses containing listings
            async def handle_response(response):
                try:
                    if response.status == 200 and "json" in response.headers.get("content-type", ""):
                        resp_url = response.url
                        if any(kw in resp_url for kw in ["/search", "/listing", "/properties", "/api/", "graphql"]):
                            body = await response.json()
                            if isinstance(body, dict):
                                # Look for arrays of listings
                                for key in ["results", "listings", "hits", "items", "data"]:
                                    val = body.get(key)
                                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                                        if any(k in val[0] for k in ["price", "title", "name", "bedrooms"]):
                                            api_listings.extend(val)
                except Exception:
                    pass

            page_obj.on("response", handle_response)

            url = self._build_url(location, purpose, property_type, min_price, max_price, bedrooms, page)
            await page_obj.goto(url, wait_until="networkidle", timeout=40000)

            # Scroll down to trigger lazy loading
            for _ in range(3):
                await page_obj.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1.5)

            # Wait for content
            await asyncio.sleep(2)

            # Strategy 1: Use intercepted API data
            if api_listings:
                for item in api_listings:
                    prop = self._parse_api_listing(item)
                    if prop:
                        properties.append(prop)

            # Strategy 2: Parse DOM
            if not properties:
                properties = await self._parse_dom(page_obj)

        except Exception as e:
            raise RuntimeError(f"Dubizzle scraping failed: {e}")
        finally:
            await context.close()

        return properties

    async def get_details(self, property_id: str) -> Property:
        """Get details for a specific Dubizzle listing."""
        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page_obj = await context.new_page()
        await page_obj.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        try:
            url = f"{BASE_URL}/en/property-for-sale/residential/details-{property_id}/"
            await page_obj.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            title = await page_obj.text_content("h1") or ""
            price_el = await page_obj.text_content("[class*='price'], [class*='Price']") or "0"
            price = float(re.sub(r"[^\d.]", "", price_el) or 0)

            return Property(
                id=property_id,
                source="dubizzle",
                title=title.strip(),
                price=price,
                url=url,
            )
        finally:
            await context.close()

    def _build_url(self, location, purpose, property_type, min_price, max_price, bedrooms, page):
        """Build Dubizzle search URL."""
        purpose_path = "property-for-sale" if purpose == "for-sale" else "property-for-rent"
        path = f"/en/{purpose_path}/residential/"

        if property_type and property_type.lower() in PROPERTY_TYPE_SLUGS:
            path += PROPERTY_TYPE_SLUGS[property_type.lower()] + "/"

        url = f"{BASE_URL}{path}"

        params = []
        loc_slug = LOCATION_SLUGS.get(location.lower().strip())
        if loc_slug:
            params.append(f"locations={loc_slug}")
        if min_price > 0:
            params.append(f"price__gte={min_price}")
        if max_price > 0:
            params.append(f"price__lte={max_price}")
        if bedrooms >= 0:
            params.append(f"bedrooms={bedrooms}")
        if page > 1:
            params.append(f"page={page}")

        if params:
            url += "?" + "&".join(params)

        return url

    def _parse_api_listing(self, data: dict) -> Property | None:
        """Parse listing from intercepted API data."""
        try:
            price = data.get("price", 0)
            if isinstance(price, dict):
                price = price.get("value", price.get("amount", 0))
            price = float(price or 0)

            location = data.get("location", "")
            if isinstance(location, dict):
                location = location.get("name", location.get("full_name", ""))

            return Property(
                id=str(data.get("id", data.get("externalId", ""))),
                source="dubizzle",
                title=data.get("title", data.get("name", "")),
                price=price,
                property_type=data.get("category", {}).get("name", "") if isinstance(data.get("category"), dict) else str(data.get("category", "")),
                bedrooms=int(data.get("bedrooms", data.get("rooms", 0)) or 0),
                bathrooms=int(data.get("bathrooms", data.get("baths", 0)) or 0),
                area_sqft=float(data.get("size", data.get("area", 0)) or 0),
                location=str(location),
                url=data.get("url", data.get("absolute_url", "")),
                image_url=data.get("photo", data.get("image", "")),
                agent_name=data.get("agent", {}).get("name", "") if isinstance(data.get("agent"), dict) else "",
            )
        except Exception:
            return None

    async def _parse_dom(self, page_obj) -> list[Property]:
        """Parse visible listing cards from the page DOM."""
        properties = []

        # Dubizzle uses various card layouts - try multiple selectors
        listings = await page_obj.evaluate("""() => {
            // Try to find listing links with prices
            const allLinks = document.querySelectorAll('a[href*="/property-for"]');
            const seen = new Set();
            const results = [];

            for (const link of allLinks) {
                const href = link.href;
                if (seen.has(href) || !href.includes('details') && !href.includes('/residential/')) continue;
                seen.add(href);

                // Walk up to find the card container
                let card = link.closest('li, article, [class*="card"], [class*="Card"], [class*="listing"]') || link;
                const text = card.textContent.trim();

                // Only include if it looks like a listing (has price-like text)
                if (text.match(/\\d{3,}/)) {
                    results.push({
                        href: href,
                        text: text.substring(0, 500),
                    });
                }
            }

            // If no links found, try a broader approach
            if (results.length === 0) {
                const elements = document.querySelectorAll('[data-testid], [class*="listing-item"], [class*="ListingItem"]');
                for (const el of elements) {
                    const link = el.querySelector('a');
                    const text = el.textContent.trim();
                    if (link && text.match(/\\d{3,}/) && text.length > 20) {
                        results.push({
                            href: link.href,
                            text: text.substring(0, 500),
                        });
                    }
                }
            }

            return results.slice(0, 25);
        }""")

        for item in listings:
            text = item.get("text", "")
            href = item.get("href", "")

            # Extract price (AED format or plain numbers)
            price_match = re.search(r"(?:AED|aed)?\s*([\d,]+(?:\.\d+)?)\s*(?:AED)?", text)
            price = 0
            if price_match:
                try:
                    price = float(price_match.group(1).replace(",", ""))
                except ValueError:
                    pass

            # Skip if price seems too low (probably not a property price)
            if price < 10000:
                continue

            # Specs
            beds_match = re.search(r"(\d+)\s*(?:bed|BR|Bed)", text, re.I)
            studio = bool(re.search(r"studio", text, re.I))
            baths_match = re.search(r"(\d+)\s*(?:bath|Bath)", text, re.I)
            area_match = re.search(r"([\d,]+)\s*(?:sqft|sq\.?\s*ft)", text, re.I)

            # Title - try to extract from text
            title_parts = text.split("\n")
            title = ""
            for part in title_parts:
                part = part.strip()
                if len(part) > 15 and not part.startswith("AED") and not re.match(r"^\d", part):
                    title = part[:100]
                    break

            # ID from URL
            id_match = re.search(r"details?-?(\d+)", href) or re.search(r"/(\d+)/?$", href)
            prop_id = id_match.group(1) if id_match else ""

            properties.append(Property(
                id=prop_id,
                source="dubizzle",
                title=title or f"Property listing",
                price=price,
                bedrooms=int(beds_match.group(1)) if beds_match else (0 if studio else 0),
                bathrooms=int(baths_match.group(1)) if baths_match else 0,
                area_sqft=float(area_match.group(1).replace(",", "")) if area_match else 0,
                url=href if href.startswith("http") else f"{BASE_URL}{href}",
            ))

        return properties

    async def cleanup(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
