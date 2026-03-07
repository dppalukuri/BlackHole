"""
PropertyFinder.ae scraper - Stealth Playwright (headless).

No bot protection on search pages. Extracts data from __NEXT_DATA__ (Next.js SSR)
with DOM article parsing as fallback.

URL pattern: /en/search?c={1|2}&q={location}&t={type}&pf={min}&pt={max}&bf={beds}&bt={beds}&fu={furnishing}&ob=nd
Filters: c=category, q=location, t=type, pf/pt=price, bf/bt=beds, fu=furnishing, ob=sort, page=page
"""

import asyncio
import json
import re
from models import Property
import slug_registry

BASE_URL = "https://www.propertyfinder.ae"

CATEGORY_MAP = {
    "for-sale": "1",
    "for-rent": "2",
}


class PropertyFinderScraper:
    def __init__(self):
        self._stealth_browser = None

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
        """Search PropertyFinder listings."""
        sb = await self._get_stealth_browser()
        context = await sb.new_context(site_name="propertyfinder")
        page_obj = await context.new_page()
        properties = []

        try:
            url = self._build_url(location, purpose, property_type, min_price, max_price, bedrooms, page)
            await page_obj.goto(url, wait_until="networkidle", timeout=40000)
            await asyncio.sleep(3)

            # Check for CAPTCHA and solve if present
            from captcha import handle_captcha_if_present
            await handle_captcha_if_present(page_obj)

            # Strategy 1: Extract from __NEXT_DATA__
            properties = await self._extract_next_data(page_obj)

            # Strategy 2: Parse DOM articles (scroll first to load all)
            if not properties:
                for _ in range(5):
                    await page_obj.evaluate("window.scrollBy(0, window.innerHeight)")
                    await asyncio.sleep(1)
                await asyncio.sleep(2)
                properties = await self._parse_dom(page_obj)

            await sb.save_session(context)

        except Exception as e:
            raise RuntimeError(f"PropertyFinder scraping failed: {e}")
        finally:
            await context.close()

        return properties

    async def get_details(self, property_id: str) -> Property:
        """Get detailed info for a PropertyFinder listing."""
        sb = await self._get_stealth_browser()
        context = await sb.new_context(site_name="propertyfinder")
        page_obj = await context.new_page()

        try:
            url = f"{BASE_URL}/en/plp/buy/property-{property_id}.html"
            await page_obj.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Try __NEXT_DATA__
            prop_data = await page_obj.evaluate("""() => {
                const el = document.getElementById('__NEXT_DATA__');
                if (!el) return null;
                try {
                    const d = JSON.parse(el.textContent);
                    return d.props?.pageProps?.property || d.props?.pageProps?.listing || null;
                } catch { return null; }
            }""")

            if prop_data:
                prop = self._parse_listing(prop_data)
                if prop:
                    return prop

            # Fallback DOM
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

    def _build_url(self, location, purpose, property_type, min_price, max_price, bedrooms, page):
        """Build PropertyFinder search URL using query-based search endpoint."""
        params = []

        # Category (buy/rent)
        category = CATEGORY_MAP.get(purpose, "1")
        params.append(f"c={category}")

        # Location as free-text query
        params.append(f"q={location.replace(' ', '%20')}")

        # Property type
        type_id = slug_registry.resolve_property_type("propertyfinder", property_type) if property_type else None
        if type_id:
            params.append(f"t={type_id}")

        # Price range
        if min_price > 0:
            params.append(f"pf={min_price}")
        if max_price > 0:
            params.append(f"pt={max_price}")

        # Bedrooms
        if bedrooms >= 0:
            params.append(f"bf={bedrooms}")
            params.append(f"bt={bedrooms}")

        # Sorting and pagination
        params.append("ob=nd")  # newest first
        if page > 1:
            params.append(f"page={page}")

        return f"{BASE_URL}/en/search?{'&'.join(params)}"

    async def _extract_next_data(self, page_obj) -> list[Property]:
        """Extract listings from __NEXT_DATA__."""
        raw = await page_obj.evaluate("""() => {
            const el = document.getElementById('__NEXT_DATA__');
            if (!el) return null;
            try {
                const d = JSON.parse(el.textContent);
                const sr = d.props?.pageProps?.searchResult;
                if (!sr) return null;

                // Collect from all arrays that have listings
                const all = [];
                for (const key of ['properties', 'listings', 'similar_properties', 'similar_listings']) {
                    const arr = sr[key];
                    if (Array.isArray(arr)) {
                        for (const item of arr) {
                            // Items can be direct property objects or wrapper objects
                            if (item.property) {
                                all.push(item.property);
                            } else if (item.price || item.id) {
                                all.push(item);
                            }
                        }
                    }
                }
                return all;
            } catch { return null; }
        }""")

        if not raw:
            return []

        properties = []
        for item in raw:
            prop = self._parse_listing(item)
            if prop:
                properties.append(prop)
        return properties

    def _parse_listing(self, data: dict) -> Property | None:
        """Parse a PropertyFinder listing object."""
        try:
            # Price
            price = 0
            price_data = data.get("price", {})
            if isinstance(price_data, dict):
                price = float(price_data.get("value", 0))
            elif isinstance(price_data, (int, float)):
                price = float(price_data)

            # Location
            loc = data.get("location", {})
            location_name = ""
            if isinstance(loc, dict):
                location_name = loc.get("full_name", loc.get("name", loc.get("path_name", "")))
                # Try building from path if full_name is empty
                if not location_name:
                    slug = loc.get("slug", loc.get("path", ""))
                    if slug:
                        location_name = slug.replace("-", " ").replace("/", ", ").title()
            elif isinstance(loc, str):
                location_name = loc

            # Also try extracting location from details_path URL
            if not location_name:
                details = data.get("details_path", data.get("share_url", ""))
                if details:
                    # URL format: apartment-for-sale-dubai-area-subarea-building-ID.html
                    loc_match = re.search(r"(?:sale|rent)-([a-z][a-z-]+?)-[A-Za-z0-9]{8,}\.html", details)
                    if loc_match:
                        location_name = loc_match.group(1).replace("-", " ").title()

            # Location tree
            loc_tree = data.get("location_tree", [])
            emirate = ""
            community = ""
            sub_community = ""
            if isinstance(loc_tree, list):
                if len(loc_tree) >= 1:
                    emirate = loc_tree[0].get("name", "") if isinstance(loc_tree[0], dict) else str(loc_tree[0])
                if len(loc_tree) >= 2:
                    community = loc_tree[1].get("name", "") if isinstance(loc_tree[1], dict) else str(loc_tree[1])
                if len(loc_tree) >= 3:
                    sub_community = loc_tree[2].get("name", "") if isinstance(loc_tree[2], dict) else str(loc_tree[2])

            # Area
            size_data = data.get("size", 0)
            if isinstance(size_data, dict):
                area = float(size_data.get("value", 0))
            else:
                area = float(size_data or 0)

            # Images
            images = data.get("images", [])
            image_url = ""
            if isinstance(images, list) and images:
                img = images[0]
                if isinstance(img, dict):
                    image_url = img.get("url", img.get("source", ""))
                elif isinstance(img, str):
                    image_url = img

            # Agent
            agent = data.get("agent", {})
            agent_name = agent.get("name", "") if isinstance(agent, dict) else ""

            # Broker
            broker = data.get("broker", {})
            agency_name = broker.get("name", "") if isinstance(broker, dict) else ""

            # URL
            details_path = data.get("details_path", data.get("share_url", ""))
            prop_url = details_path if details_path.startswith("http") else f"{BASE_URL}{details_path}" if details_path else ""

            prop_id = str(data.get("id", data.get("listing_id", "")))
            title = data.get("title", "")
            if not title and location_name:
                beds_label = f"{int(data.get('bedrooms_value', 0) or 0)}BR" if data.get("bedrooms_value") else "Studio"
                title = f"{beds_label} {data.get('property_type', 'Property')} in {location_name}"

            return Property(
                id=prop_id,
                source="propertyfinder",
                title=title,
                price=price,
                purpose=data.get("offering_type", ""),
                property_type=data.get("property_type", ""),
                bedrooms=int(data.get("bedrooms_value", data.get("bedrooms", 0)) or 0),
                bathrooms=int(data.get("bathrooms_value", data.get("bathrooms", 0)) or 0),
                area_sqft=area,
                location=location_name,
                emirate=emirate,
                community=community,
                sub_community=sub_community,
                furnishing=data.get("furnished", ""),
                completion_status=data.get("completion_status", ""),
                agent_name=agent_name,
                agency_name=agency_name,
                url=prop_url,
                image_url=image_url,
                reference=str(data.get("reference", "")),
                listed_date=data.get("listed_date", ""),
            )
        except Exception:
            return None

    async def _parse_dom(self, page_obj) -> list[Property]:
        """Parse listing cards from DOM articles."""
        properties = []

        listings = await page_obj.evaluate("""() => {
            const articles = document.querySelectorAll('article');
            return Array.from(articles).map(article => {
                const link = article.querySelector('a[href*="/plp/"]');
                if (!link) return null;

                const text = article.textContent.trim();
                const href = link.href || '';

                return { text, href };
            }).filter(x => x && x.href);
        }""")

        for item in listings:
            text = item.get("text", "")
            href = item.get("href", "")

            # Extract price
            price_match = re.search(r"([\d,]+)\s*AED", text)
            if not price_match:
                price_match = re.search(r"AED\s*([\d,]+)", text)
            price = float(price_match.group(1).replace(",", "")) if price_match else 0

            # Extract title - usually after price
            title_match = re.search(r"AED(.+?)(?:\d+\s*(?:bed|bath|studio)|[A-Z][a-z]+\s*(?:Road|Street|Tower))", text)
            title = title_match.group(1).strip() if title_match else ""

            # Specs
            beds_match = re.search(r"(\d+)\s*(?:bed|Bed|BR)", text)
            studio = "studio" in text.lower()
            baths_match = re.search(r"(\d+)\s*(?:bath|Bath)", text)
            area_match = re.search(r"([\d,]+)\s*sqft", text, re.I)

            # Location from URL
            location = ""
            loc_match = re.search(r"in-([\w-]+)-\d+\.html", href)
            if loc_match:
                location = loc_match.group(1).replace("-", " ").title()

            # ID from URL
            id_match = re.search(r"-(\d+)\.html", href)
            prop_id = id_match.group(1) if id_match else ""

            if price > 0:
                properties.append(Property(
                    id=prop_id,
                    source="propertyfinder",
                    title=title or f"Property in {location}",
                    price=price,
                    bedrooms=int(beds_match.group(1)) if beds_match else (0 if studio else 0),
                    bathrooms=int(baths_match.group(1)) if baths_match else 0,
                    area_sqft=float(area_match.group(1).replace(",", "")) if area_match else 0,
                    location=location,
                    url=href,
                ))

        return properties

    async def cleanup(self):
        if self._stealth_browser:
            await self._stealth_browser.cleanup()
            self._stealth_browser = None
