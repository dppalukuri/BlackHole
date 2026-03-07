"""
PropertyFinder.ae scraper - Uses Playwright for browser automation.

PropertyFinder is a JS-heavy SPA requiring headless browser.
Requires: pip install playwright && playwright install chromium
"""

import asyncio
import json
import re
from models import Property

BASE_URL = "https://www.propertyfinder.ae"

# PropertyFinder location IDs (mapped from their search)
LOCATION_IDS = {
    "dubai": "1",
    "abu dhabi": "2",
    "sharjah": "3",
    "ajman": "4",
    "ras al khaimah": "5",
    "fujairah": "6",
    "umm al quwain": "7",
    "dubai marina": "11",
    "downtown dubai": "18",
    "business bay": "21",
    "jbr": "31",
    "jumeirah beach residence": "31",
    "palm jumeirah": "22",
    "dubai hills": "262",
    "dubai hills estate": "262",
    "arabian ranches": "35",
    "jvc": "50",
    "jumeirah village circle": "50",
    "dubai creek harbour": "316",
    "al barsha": "58",
    "motor city": "66",
    "sports city": "67",
    "damac hills": "274",
    "jlt": "42",
    "jumeirah lake towers": "42",
    "difc": "63",
    "city walk": "259",
    "meydan": "243",
    "silicon oasis": "69",
    "dubai silicon oasis": "69",
    "emirates hills": "36",
    "discovery gardens": "57",
    "international city": "68",
    "mirdif": "73",
}

CATEGORY_MAP = {
    "for-sale": "1",
    "for-rent": "2",
}

PROPERTY_TYPE_MAP = {
    "apartment": "1",
    "villa": "2",
    "townhouse": "18",
    "penthouse": "3",
    "duplex": "25",
    "studio": "1",  # apartment category
}


class PropertyFinderScraper:
    def __init__(self):
        self._browser = None
        self._playwright = None

    async def _get_browser(self):
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                raise ImportError(
                    "PropertyFinder scraper requires Playwright. Install with:\n"
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
        """Search PropertyFinder listings."""
        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-AE",
        )

        page_obj = await context.new_page()
        properties = []

        try:
            # Build search URL
            params = []

            category = CATEGORY_MAP.get(purpose, "1")
            params.append(f"c={category}")

            loc_id = LOCATION_IDS.get(location.lower().strip())
            if loc_id:
                params.append(f"l={loc_id}")

            if property_type and property_type.lower() in PROPERTY_TYPE_MAP:
                params.append(f"t={PROPERTY_TYPE_MAP[property_type.lower()]}")

            if min_price > 0:
                params.append(f"pf={min_price}")
            if max_price > 0:
                params.append(f"pt={max_price}")
            if bedrooms >= 0:
                params.append(f"bf={bedrooms}")
                params.append(f"bt={bedrooms}")

            params.append(f"page={page}")
            params.append("ob=nd")  # newest first

            url = f"{BASE_URL}/en/search?{'&'.join(params)}"

            # Intercept search API responses
            api_data = []

            async def handle_response(response):
                try:
                    resp_url = response.url
                    if ("/search" in resp_url or "/api/" in resp_url or "/graphql" in resp_url) and response.status == 200:
                        content_type = response.headers.get("content-type", "")
                        if "json" in content_type:
                            body = await response.json()
                            if isinstance(body, dict):
                                # Look for listing data in response
                                if "properties" in body or "listings" in body or "results" in body or "data" in body:
                                    api_data.append(body)
                except Exception:
                    pass

            page_obj.on("response", handle_response)

            await page_obj.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Try __NEXT_DATA__ (PropertyFinder may use Next.js)
            next_data = await page_obj.evaluate("""
                () => {
                    const el = document.getElementById('__NEXT_DATA__');
                    if (el) {
                        try { return JSON.parse(el.textContent); } catch {}
                    }
                    return null;
                }
            """)

            if next_data:
                properties = self._parse_next_data(next_data)
            elif api_data:
                for data in api_data:
                    for item in self._extract_listings_from_api(data):
                        prop = self._parse_api_listing(item)
                        if prop:
                            properties.append(prop)
            else:
                properties = await self._parse_dom(page_obj)

        except Exception as e:
            raise RuntimeError(f"PropertyFinder scraping failed: {e}")
        finally:
            await context.close()

        return properties

    async def get_details(self, property_id: str) -> Property:
        """Get detailed info for a PropertyFinder listing."""
        browser = await self._get_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page_obj = await context.new_page()

        try:
            # PropertyFinder listing URLs contain the ID at the end
            url = f"{BASE_URL}/en/plp/buy/property-{property_id}.html"
            await page_obj.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Try JSON-LD
            json_ld = await page_obj.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const s of scripts) {
                        try {
                            const data = JSON.parse(s.textContent);
                            if (data['@type'] && data['@type'].includes('Real')) return data;
                            if (data['@type'] === 'Product') return data;
                        } catch {}
                    }
                    return null;
                }
            """)

            if json_ld:
                return self._parse_json_ld(json_ld, property_id)

            title = await page_obj.text_content("h1") or ""
            price_el = await page_obj.text_content("[class*='price'], [class*='Price']") or "0"
            price = float(re.sub(r"[^\d.]", "", price_el) or 0)

            return Property(
                id=property_id,
                source="propertyfinder",
                title=title.strip(),
                price=price,
                url=url,
            )
        finally:
            await context.close()

    def _parse_next_data(self, data: dict) -> list[Property]:
        """Parse listings from Next.js __NEXT_DATA__."""
        properties = []
        try:
            props = data.get("props", {}).get("pageProps", {})
            listings = (
                props.get("searchResult", {}).get("properties", [])
                or props.get("properties", [])
                or props.get("listings", [])
            )
            for item in listings:
                prop = self._parse_api_listing(item)
                if prop:
                    properties.append(prop)
        except Exception:
            pass
        return properties

    def _extract_listings_from_api(self, data: dict) -> list:
        """Recursively find listing arrays in API response."""
        listings = []
        if isinstance(data, dict):
            for key in ("properties", "listings", "results", "items", "hits"):
                if key in data and isinstance(data[key], list):
                    listings.extend(data[key])
            if "data" in data and isinstance(data["data"], dict):
                listings.extend(self._extract_listings_from_api(data["data"]))
        return listings

    def _parse_api_listing(self, data: dict) -> Property | None:
        """Parse a listing from PropertyFinder's internal data."""
        try:
            price = 0
            if isinstance(data.get("price"), dict):
                price = float(data["price"].get("value", data["price"].get("amount", 0)))
            else:
                price = float(data.get("price", 0))

            location_name = ""
            if isinstance(data.get("location"), dict):
                parts = []
                for key in ("community", "subCommunity", "city"):
                    val = data["location"].get(key, {})
                    if isinstance(val, dict):
                        parts.append(val.get("name", ""))
                    elif isinstance(val, str):
                        parts.append(val)
                location_name = ", ".join(p for p in parts if p)
            elif isinstance(data.get("location"), str):
                location_name = data["location"]

            area = float(data.get("area", data.get("size", 0)))

            prop_url = data.get("url", data.get("links", {}).get("detail", "")) if isinstance(data.get("links"), dict) else data.get("url", "")
            if prop_url and not prop_url.startswith("http"):
                prop_url = f"{BASE_URL}{prop_url}"

            return Property(
                id=str(data.get("id", data.get("referenceNumber", ""))),
                source="propertyfinder",
                title=data.get("title", data.get("name", "")),
                price=price,
                purpose=data.get("purpose", ""),
                property_type=data.get("type", data.get("propertyType", "")),
                bedrooms=int(data.get("bedrooms", data.get("beds", 0))),
                bathrooms=int(data.get("bathrooms", data.get("baths", 0))),
                area_sqft=area,
                location=location_name,
                latitude=float(data.get("latitude", data.get("lat", 0))),
                longitude=float(data.get("longitude", data.get("lng", 0))),
                furnishing=data.get("furnishing", data.get("furnishingStatus", "")),
                completion_status=data.get("completionStatus", ""),
                agent_name=data.get("agent", {}).get("name", "") if isinstance(data.get("agent"), dict) else "",
                agency_name=data.get("agency", {}).get("name", "") if isinstance(data.get("agency"), dict) else "",
                url=prop_url,
                image_url=data.get("image", data.get("coverImage", {}).get("url", "")) if isinstance(data.get("coverImage"), dict) else data.get("image", ""),
                reference=str(data.get("referenceNumber", data.get("reference", ""))),
            )
        except Exception:
            return None

    async def _parse_dom(self, page_obj) -> list[Property]:
        """Fallback: parse listing cards from DOM."""
        properties = []

        listings = await page_obj.evaluate("""
            () => {
                const cards = document.querySelectorAll('[class*="card"], [class*="Card"], [class*="listing"], article');
                return Array.from(cards).slice(0, 25).map(card => {
                    const getText = (sel) => {
                        const el = card.querySelector(sel);
                        return el ? el.textContent.trim() : '';
                    };
                    const getAttr = (sel, attr) => {
                        const el = card.querySelector(sel);
                        return el ? el.getAttribute(attr) : '';
                    };

                    const link = card.querySelector('a[href*="/plp/"], a[href*="/property"], a[href*="/buy/"], a[href*="/rent/"]');
                    const href = link ? link.getAttribute('href') : '';
                    const title = getText('h2, h3, [class*="title"], [class*="Title"]');
                    const price = getText('[class*="price"], [class*="Price"]');
                    const location = getText('[class*="location"], [class*="Location"], [class*="address"]');
                    const specs = getText('[class*="spec"], [class*="Spec"], [class*="detail"], [class*="info"]');
                    const img = getAttr('img', 'src') || getAttr('img', 'data-src');

                    return { href, title, price, location, specs, img };
                }).filter(x => x.title && x.title.length > 3);
            }
        """)

        for item in listings:
            if not item.get("title"):
                continue

            price = float(re.sub(r"[^\d.]", "", item.get("price", "0")) or 0)
            specs = item.get("specs", "")

            beds_match = re.search(r"(\d+)\s*(?:bed|BR)", specs, re.I)
            baths_match = re.search(r"(\d+)\s*(?:bath)", specs, re.I)
            area_match = re.search(r"([\d,]+)\s*(?:sqft|sq\.?\s*ft)", specs, re.I)

            href = item.get("href", "")
            id_match = re.search(r"-(\d+)\.html", href)
            prop_id = id_match.group(1) if id_match else href

            prop_url = href if href.startswith("http") else f"{BASE_URL}{href}"

            properties.append(Property(
                id=str(prop_id),
                source="propertyfinder",
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

    def _parse_json_ld(self, data: dict, property_id: str) -> Property:
        """Parse JSON-LD structured data."""
        price = 0
        offers = data.get("offers", {})
        if isinstance(offers, dict):
            price = float(offers.get("price", 0))

        return Property(
            id=property_id,
            source="propertyfinder",
            title=data.get("name", ""),
            price=price,
            description=data.get("description", "")[:500],
            url=data.get("url", ""),
            image_url=data.get("image", ""),
        )

    async def cleanup(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
