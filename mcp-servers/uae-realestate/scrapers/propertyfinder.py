"""
PropertyFinder.ae scraper - Stealth Playwright (headless).

No bot protection on search pages. Extracts data from __NEXT_DATA__ (Next.js SSR)
with data-testid DOM selectors as fallback.

URL pattern: /en/{buy|rent}/{city}/{type}-for-{sale|rent}.html
  With bedrooms: /en/buy/dubai/2-bedroom-apartments-for-sale.html
  With location: /en/buy/dubai/apartments-for-sale-dubai-marina.html
  Studio: /en/buy/dubai/studio-apartments-for-sale.html

Filter query params: pf/pt (price), bf/bt (beds), fu (furnished), cs (completion), ob (sort), page
Category IDs: buy=1, rent=2
City slugs: dubai, abu-dhabi, sharjah, ajman, ras-al-khaimah, umm-al-quwain, fujairah, al-ain
"""

import asyncio
import json
import re
from models import Property
import slug_registry

BASE_URL = "https://www.propertyfinder.ae"

# Property type URL slug mapping for path-based URLs
TYPE_URL_SLUGS = {
    "apartment": "apartments",
    "villa": "villas",
    "townhouse": "townhouses",
    "penthouse": "penthouses",
    "duplex": "duplexes",
    "land": "land",
    "hotel apartment": "hotels-hotel-apartments",
    "compound": "compounds",
    "full floor": "full-floors",
    "whole building": "whole-buildings",
}

# City slug mapping
CITY_SLUGS = {
    "dubai": "dubai",
    "abu dhabi": "abu-dhabi",
    "sharjah": "sharjah",
    "ajman": "ajman",
    "ras al khaimah": "ras-al-khaimah",
    "umm al quwain": "umm-al-quwain",
    "fujairah": "fujairah",
    "al ain": "al-ain",
}


def _infer_city(location: str) -> str:
    """Infer city slug from location name. Defaults to dubai."""
    loc = location.lower().strip()
    for city_name, slug in CITY_SLUGS.items():
        if city_name == loc:
            return slug
    # Most UAE property queries target Dubai
    return "dubai"


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
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=40000)
            await asyncio.sleep(5)

            # Check for CAPTCHA and solve if present
            from captcha import handle_captcha_if_present
            await handle_captcha_if_present(page_obj)

            # Strategy 1: Extract from __NEXT_DATA__
            properties = await self._extract_next_data(page_obj)

            # Strategy 2: Parse DOM with data-testid selectors (scroll first)
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
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

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
            price_el = await page_obj.text_content("[data-testid='property-card-price'], [class*='price']") or "0"
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
        """
        Build PropertyFinder path-based URL.

        Pattern: /en/{buy|rent}/{city}/{beds}-{type}-for-{sale|rent}-{location}.html
        Examples:
          /en/buy/dubai/apartments-for-sale.html
          /en/buy/dubai/2-bedroom-apartments-for-sale.html
          /en/buy/dubai/apartments-for-sale-dubai-marina.html
          /en/buy/dubai/studio-apartments-for-sale.html
        """
        category = "buy" if purpose == "for-sale" else "rent"
        sale_type = "sale" if purpose == "for-sale" else "rent"
        city = _infer_city(location)

        # Property type slug
        type_slug = "properties"
        if property_type:
            pt_lower = property_type.lower().strip()
            if pt_lower in TYPE_URL_SLUGS:
                type_slug = TYPE_URL_SLUGS[pt_lower]

        # Build the path slug: {beds}-{type}-for-{sale|rent}
        parts = []

        # Bedrooms prefix
        if bedrooms == 0:
            parts.append("studio")
        elif bedrooms > 0:
            parts.append(f"{bedrooms}-bedroom")

        parts.append(f"{type_slug}-for-{sale_type}")

        # Location suffix (if not just a city name)
        loc_lower = location.lower().strip()
        if loc_lower not in CITY_SLUGS:
            # Convert location to URL slug
            loc_slug = slug_registry.resolve_location("propertyfinder", location)
            if not loc_slug:
                loc_slug = loc_lower.replace(" ", "-")
            parts[-1] = f"{parts[-1]}-{loc_slug}"

        path_slug = "-".join(parts) if bedrooms >= 0 else parts[-1]
        url = f"{BASE_URL}/en/{category}/{city}/{path_slug}.html"

        # Query params for filters not expressible in the path
        params = []
        if min_price > 0:
            params.append(f"pf={min_price}")
        if max_price > 0:
            params.append(f"pt={max_price}")
        # Only add bed params if not already in the path
        if bedrooms < 0:
            pass  # "any" bedrooms, no param needed
        # Pagination
        if page > 1:
            params.append(f"page={page}")

        if params:
            url += "?" + "&".join(params)

        return url

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
        """Parse a PropertyFinder listing object from __NEXT_DATA__."""
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
                if not location_name:
                    slug = loc.get("slug", loc.get("path", ""))
                    if slug:
                        location_name = slug.replace("-", " ").replace("/", ", ").title()
            elif isinstance(loc, str):
                location_name = loc

            # Fallback: extract location from details_path URL
            if not location_name:
                details = data.get("details_path", data.get("share_url", ""))
                if details:
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
        """Parse listing cards using data-testid selectors."""
        listings = await page_obj.evaluate("""() => {
            const cards = document.querySelectorAll('[data-testid="property-card"]');
            if (cards.length === 0) {
                // Fallback: try article elements
                const articles = document.querySelectorAll('article');
                return Array.from(articles).map(el => {
                    const link = el.querySelector('a[href]');
                    if (!link) return null;
                    return { text: el.textContent.trim().substring(0, 500), href: link.href };
                }).filter(x => x && x.href);
            }

            return Array.from(cards).map(card => {
                const link = card.querySelector('a[href]');
                const href = link ? link.href : '';

                // Use data-testid selectors for reliable extraction
                const priceEl = card.querySelector('[data-testid="property-card-price"]');
                const typeEl = card.querySelector('[data-testid="property-card-type"]');
                const bedsEl = card.querySelector('[data-testid="property-card-spec-bedroom"]');
                const areaEl = card.querySelector('[data-testid="property-card-spec-area"]');

                // Get all text as fallback
                const text = card.textContent.trim();

                // Extract price
                let price = 0;
                if (priceEl) {
                    const priceText = priceEl.textContent.replace(/[^\\d]/g, '');
                    price = parseInt(priceText) || 0;
                }

                // Extract beds
                let beds = -1;
                if (bedsEl) {
                    const bedsText = bedsEl.textContent.trim();
                    if (/studio/i.test(bedsText)) beds = 0;
                    else {
                        const m = bedsText.match(/(\\d+)/);
                        if (m) beds = parseInt(m[1]);
                    }
                }

                // Extract area
                let area = 0;
                if (areaEl) {
                    const areaText = areaEl.textContent.replace(/[^\\d]/g, '');
                    area = parseInt(areaText) || 0;
                }

                // Extract baths from text
                const bathMatch = text.match(/(\\d+)\\s*Bath/i);
                const baths = bathMatch ? parseInt(bathMatch[1]) : 0;

                // Title - find first substantial link text
                let title = '';
                const titleLink = card.querySelector('a[title]');
                if (titleLink) {
                    title = titleLink.getAttribute('title') || titleLink.textContent.trim();
                }
                if (!title && link) {
                    title = link.textContent.trim().substring(0, 150);
                }

                // Property type
                const propType = typeEl ? typeEl.textContent.trim() : '';

                // Image
                let image = '';
                const img = card.querySelector('img[src]');
                if (img && img.src && !img.src.includes('data:')) image = img.src;

                return {
                    href, title, price, beds, baths, area, propType, image, text: text.substring(0, 300),
                };
            }).filter(x => x.href && x.price > 0);
        }""")

        properties = []
        for item in listings:
            href = item.get("href", "")

            # ID from URL
            id_match = re.search(r"-(\d+)\.html", href)
            prop_id = id_match.group(1) if id_match else ""

            # Location from URL
            location = ""
            loc_match = re.search(r"(?:sale|rent)-(.+?)-\d+\.html", href)
            if loc_match:
                location = loc_match.group(1).replace("-", " ").title()

            title = item.get("title", "")
            if not title:
                # Extract from text
                text = item.get("text", "")
                lines = text.split("\n")
                for line in lines:
                    line = line.strip()
                    if len(line) > 15 and not re.match(r"^[\d,]+$|^AED", line):
                        title = line[:120]
                        break

            properties.append(Property(
                id=prop_id,
                source="propertyfinder",
                title=title or f"Property in {location}",
                price=float(item.get("price", 0)),
                property_type=item.get("propType", ""),
                bedrooms=item.get("beds", -1),
                bathrooms=item.get("baths", 0),
                area_sqft=float(item.get("area", 0)),
                location=location,
                url=href,
                image_url=item.get("image", ""),
            ))

        return properties

    async def cleanup(self):
        if self._stealth_browser:
            await self._stealth_browser.cleanup()
            self._stealth_browser = None
