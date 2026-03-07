"""
Dubizzle.com scraper - Uses Playwright for browser automation.

Dubizzle is a JS-heavy SPA protected by Incapsula/Imperva.
Requires: pip install playwright && playwright install chromium
"""

import asyncio
import json
import re
from models import Property

# URL patterns
BASE_URL = "https://dubai.dubizzle.com"
SEARCH_PATHS = {
    "for-sale": "/en/property-for-sale/residential/",
    "for-rent": "/en/property-for-rent/residential/",
}

# Dubizzle location slugs
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
}

PROPERTY_TYPE_SLUGS = {
    "apartment": "apartmentflat",
    "villa": "villa",
    "townhouse": "townhouse",
    "penthouse": "penthouse",
    "duplex": "duplex",
    "studio": "apartmentflat",
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
        """Search Dubizzle listings using Playwright."""
        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )

        page_obj = await context.new_page()
        properties = []

        try:
            # Build URL
            path = SEARCH_PATHS.get(purpose, SEARCH_PATHS["for-sale"])

            # Add property type
            if property_type and property_type.lower() in PROPERTY_TYPE_SLUGS:
                path += PROPERTY_TYPE_SLUGS[property_type.lower()] + "/"

            url = f"{BASE_URL}{path}"

            # Add query params
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

            # Intercept API responses
            api_data = []

            async def handle_response(response):
                try:
                    if "/api/" in response.url and response.status == 200:
                        content_type = response.headers.get("content-type", "")
                        if "json" in content_type:
                            body = await response.json()
                            if isinstance(body, dict) and ("results" in body or "listings" in body):
                                api_data.append(body)
                except Exception:
                    pass

            page_obj.on("response", handle_response)

            await page_obj.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)  # Wait for dynamic content

            # Try parsing from intercepted API data first
            if api_data:
                for data in api_data:
                    listings = data.get("results", data.get("listings", []))
                    for item in listings:
                        prop = self._parse_api_listing(item)
                        if prop:
                            properties.append(prop)
            else:
                # Fallback: parse DOM
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

        try:
            url = f"{BASE_URL}/property/details-{property_id}"
            await page_obj.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Try to extract JSON-LD
            json_ld = await page_obj.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const s of scripts) {
                        try {
                            const data = JSON.parse(s.textContent);
                            if (data['@type'] === 'Product' || data['@type'] === 'RealEstateListing') {
                                return data;
                            }
                        } catch {}
                    }
                    return null;
                }
            """)

            if json_ld:
                return self._parse_json_ld(json_ld, property_id)

            # Fallback: scrape visible content
            title = await page_obj.text_content("h1") or ""
            price_text = await page_obj.text_content("[class*='price']") or "0"
            price = float(re.sub(r"[^\d.]", "", price_text) or 0)

            return Property(
                id=property_id,
                source="dubizzle",
                title=title.strip(),
                price=price,
                url=url,
            )
        finally:
            await context.close()

    async def _parse_dom(self, page_obj) -> list[Property]:
        """Parse listing cards from the DOM."""
        properties = []

        listings = await page_obj.evaluate("""
            () => {
                const cards = document.querySelectorAll('[class*="listing-card"], [class*="ListingCard"], article[data-testid]');
                return Array.from(cards).slice(0, 25).map(card => {
                    const getText = (sel) => {
                        const el = card.querySelector(sel);
                        return el ? el.textContent.trim() : '';
                    };
                    const getAttr = (sel, attr) => {
                        const el = card.querySelector(sel);
                        return el ? el.getAttribute(attr) : '';
                    };

                    const link = card.querySelector('a[href*="/property"]');
                    const href = link ? link.getAttribute('href') : '';
                    const title = getText('h2, h3, [class*="title"]');
                    const price = getText('[class*="price"], [class*="Price"]');
                    const details = getText('[class*="detail"], [class*="specs"], [class*="info"]');
                    const location = getText('[class*="location"], [class*="Location"]');
                    const img = getAttr('img', 'src') || getAttr('img', 'data-src');

                    return { href, title, price, details, location, img };
                });
            }
        """)

        for item in listings:
            if not item.get("title"):
                continue

            price = float(re.sub(r"[^\d.]", "", item.get("price", "0")) or 0)
            details = item.get("details", "")

            beds_match = re.search(r"(\d+)\s*(?:bed|BR)", details, re.I)
            baths_match = re.search(r"(\d+)\s*(?:bath)", details, re.I)
            area_match = re.search(r"([\d,]+)\s*(?:sqft|sq\.?\s*ft)", details, re.I)

            href = item.get("href", "")
            prop_id_match = re.search(r"details?-?(\d+)", href)
            prop_id = prop_id_match.group(1) if prop_id_match else href

            prop_url = href if href.startswith("http") else f"{BASE_URL}{href}"

            properties.append(Property(
                id=str(prop_id),
                source="dubizzle",
                title=item["title"],
                price=price,
                bedrooms=int(beds_match.group(1)) if beds_match else 0,
                bathrooms=int(baths_match.group(1)) if baths_match else 0,
                area_sqft=float(area_match.group(1).replace(",", "")) if area_match else 0,
                location=item.get("location", ""),
                url=prop_url,
                image_url=item.get("img", ""),
            ))

        return properties

    def _parse_api_listing(self, data: dict) -> Property | None:
        """Parse a listing from Dubizzle's internal API."""
        try:
            price = float(data.get("price", {}).get("value", 0) if isinstance(data.get("price"), dict) else data.get("price", 0))

            return Property(
                id=str(data.get("id", data.get("externalId", ""))),
                source="dubizzle",
                title=data.get("title", data.get("name", "")),
                price=price,
                purpose=data.get("purpose", ""),
                property_type=data.get("category", {}).get("name", "") if isinstance(data.get("category"), dict) else "",
                bedrooms=int(data.get("bedrooms", data.get("rooms", 0))),
                bathrooms=int(data.get("bathrooms", data.get("baths", 0))),
                area_sqft=float(data.get("size", data.get("area", 0))),
                location=data.get("location", {}).get("name", "") if isinstance(data.get("location"), dict) else str(data.get("location", "")),
                url=data.get("url", data.get("absolute_url", "")),
                image_url=data.get("photo", data.get("image", "")),
                agent_name=data.get("agent", {}).get("name", "") if isinstance(data.get("agent"), dict) else "",
            )
        except Exception:
            return None

    def _parse_json_ld(self, data: dict, property_id: str) -> Property:
        """Parse JSON-LD structured data."""
        price = 0
        offers = data.get("offers", {})
        if isinstance(offers, dict):
            price = float(offers.get("price", 0))

        return Property(
            id=property_id,
            source="dubizzle",
            title=data.get("name", ""),
            price=price,
            description=data.get("description", "")[:500],
            url=data.get("url", f"{BASE_URL}/property/details-{property_id}"),
            image_url=data.get("image", ""),
        )

    async def cleanup(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
