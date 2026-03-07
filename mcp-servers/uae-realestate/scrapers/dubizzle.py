"""
Dubizzle.com scraper - Stealth Playwright in headed mode.

Dubizzle uses Incapsula (Imperva) WAF which blocks headless browsers entirely.
Uses headed (non-headless) browser with stealth to bypass Incapsula detection.
The browser window is positioned off-screen so it doesn't interfere.

URL pattern: /en/property-for-{sale|rent}/residential/{type}/in/{location-slug}/
Filters: price__gte, price__lte, bedrooms, furnishing, page (as query params)
"""

import asyncio
import re
from models import Property

BASE_URL = "https://dubai.dubizzle.com"

# Location slugs discovered from the site's own navigation/filter data
LOCATION_SLUGS = {
    "dubai marina": "dubai-marina",
    "downtown dubai": "downtown-dubai",
    "downtown": "downtown-dubai",
    "business bay": "business-bay",
    "jbr": "jumeirah-beach-residence-jbr",
    "jumeirah beach residence": "jumeirah-beach-residence-jbr",
    "palm jumeirah": "the-palm-jumeirah",
    "the palm jumeirah": "the-palm-jumeirah",
    "dubai hills": "dubai-hills-estate",
    "dubai hills estate": "dubai-hills-estate",
    "arabian ranches": "arabian-ranches",
    "arabian ranches 2": "arabian-ranches-2",
    "arabian ranches 3": "arabian-ranches-3",
    "jvc": "jumeirah-village-circle-jvc",
    "jumeirah village circle": "jumeirah-village-circle-jvc",
    "jvt": "jumeirah-village-triangle-jvt",
    "jumeirah village triangle": "jumeirah-village-triangle-jvt",
    "dubai creek harbour": "dubai-creek-harbour",
    "creek harbour": "dubai-creek-harbour",
    "al barsha": "al-barsha",
    "deira": "deira",
    "motor city": "motor-city",
    "sports city": "dubai-sports-city",
    "dubai sports city": "dubai-sports-city",
    "damac hills": "damac-hills-akoya-by-damac",
    "damac hills 2": "damac-hills-2-akoya-oxygen",
    "jlt": "jlt-jumeirah-lake-towers",
    "jumeirah lake towers": "jlt-jumeirah-lake-towers",
    "difc": "difc",
    "city walk": "city-walk",
    "meydan": "meydan-city",
    "meydan city": "meydan-city",
    "silicon oasis": "dubai-silicon-oasis",
    "dubai silicon oasis": "dubai-silicon-oasis",
    "dso": "dubai-silicon-oasis",
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
    "impz": "international-media-production-zone-impz",
    "sobha hartland": "sobha-hartland",
    "dubai land": "dubailand",
    "al quoz": "al-quoz",
    "dubai investment park": "dubai-investment-park-dip",
    "dip": "dubai-investment-park-dip",
    "bluewaters island": "bluewaters-island",
    "dubai harbour": "dubai-harbour",
    "emaar beachfront": "emaar-beachfront",
    "dubai creek": "dubai-creek-harbour",
    "tilal al ghaf": "tilal-al-ghaf",
    "madinat jumeirah living": "madinat-jumeirah-living",
    "mohammed bin rashid city": "mohammed-bin-rashid-city",
    "mbr city": "mohammed-bin-rashid-city",
    "rashid yachts marina": "rashid-yachts-and-marina",
    "yas island": "yas-island",
    "saadiyat island": "saadiyat-island",
    "al reem island": "al-reem-island",
    "reem island": "al-reem-island",
    "khalifa city": "khalifa-city",
    "al reef": "al-reef",
    "masdar city": "masdar-city",
}

# Property type slugs - these go in the URL path
PROPERTY_TYPE_SLUGS = {
    "apartment": "apartment",
    "flat": "apartment",
    "villa": "villahouse",
    "house": "villahouse",
    "townhouse": "townhouse",
    "penthouse": "penthouse",
    "duplex": "duplex",
    "hotel apartment": "hotel-apartment",
    "residential building": "residential-building",
    "villa compound": "villa-compound",
    "residential floor": "residential-floor",
}


class DubizzleScraper:
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
        """Search Dubizzle listings using headed stealth browser."""
        sb = await self._get_stealth_browser()
        context = await sb.new_context(site_name="dubizzle", headed=True)
        page_obj = await context.new_page()

        properties = []
        api_listings = []

        try:
            # Intercept API responses containing listings
            async def handle_response(response):
                nonlocal api_listings
                try:
                    ct = response.headers.get("content-type", "")
                    if response.status == 200 and "json" in ct:
                        resp_url = response.url
                        if any(kw in resp_url for kw in ["/search", "/listing", "/properties", "/api/", "graphql"]):
                            body = await response.json()
                            if isinstance(body, dict):
                                for key in ["results", "listings", "hits", "items", "data"]:
                                    val = body.get(key)
                                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                                        if any(k in val[0] for k in ["price", "title", "name", "bedrooms"]):
                                            api_listings.extend(val)
                except Exception:
                    pass  # Context destroyed during navigation is expected

            page_obj.on("response", handle_response)

            url = self._build_url(location, purpose, property_type, min_price, max_price, bedrooms, page)
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=40000)

            # Wait for Incapsula JS to finish any redirects
            await asyncio.sleep(5)
            try:
                await page_obj.wait_for_load_state("load", timeout=10000)
            except Exception:
                pass

            # Check for CAPTCHA and solve if present
            try:
                from captcha import handle_captcha_if_present
                captcha_solved = await handle_captcha_if_present(page_obj)
                if not captcha_solved:
                    return []
            except Exception:
                pass  # Page may have navigated, continue

            # Scroll to trigger lazy loading
            for _ in range(5):
                try:
                    await page_obj.evaluate("window.scrollBy(0, window.innerHeight)")
                except Exception:
                    break
                await asyncio.sleep(1)
            await asyncio.sleep(2)

            # Strategy 1: Use intercepted API data
            if api_listings:
                for item in api_listings:
                    prop = self._parse_api_listing(item)
                    if prop:
                        properties.append(prop)

            # Strategy 2: Parse DOM using detail link pattern
            if not properties:
                properties = await self._parse_dom(page_obj, location)

            # Save session state
            await sb.save_session(context)

        except Exception as e:
            raise RuntimeError(f"Dubizzle scraping failed: {e}")
        finally:
            await context.close()

        return properties

    async def get_details(self, url: str) -> Property | None:
        """Get details for a specific Dubizzle listing by URL."""
        sb = await self._get_stealth_browser()
        context = await sb.new_context(site_name="dubizzle", headed=True)
        page_obj = await context.new_page()

        try:
            await page_obj.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)

            from captcha import handle_captcha_if_present
            await handle_captcha_if_present(page_obj)

            data = await page_obj.evaluate("""() => {
                const title = document.querySelector('h1')?.textContent?.trim() || '';
                const bodyText = document.body.innerText;

                const priceMatch = bodyText.match(/AED[\\s\\xa0]*\\n?([\\d,]+)/);
                const bedsMatch = bodyText.match(/(\\d+)\\s*Bed/i);
                const bathsMatch = bodyText.match(/(\\d+)\\s*Bath/i);
                const areaMatch = bodyText.match(/([\\d,]+)\\s*sqft/i);
                const studioMatch = /Studio/i.test(bodyText);
                const typeMatch = bodyText.match(/Type:\\s*(.+?)\\n/i) || bodyText.match(/Property Type:\\s*(.+?)\\n/i);
                const furnMatch = bodyText.match(/Furnishing:\\s*(.+?)\\n/i) || bodyText.match(/Furnished/i);
                const refMatch = bodyText.match(/Reference\\s*(?:no\\.?)?:?\\s*([A-Za-z0-9-]+)/i);

                // Find description
                let description = '';
                const descEl = document.querySelector('[class*="description"], [class*="Description"]');
                if (descEl) description = descEl.textContent.trim().substring(0, 500);

                // Find images
                const images = [];
                for (const img of document.querySelectorAll('img[src*="dubizzle"], img[src*="beehive"]')) {
                    if (img.src && img.naturalWidth > 100) images.push(img.src);
                }

                return {
                    title,
                    price: priceMatch ? parseInt(priceMatch[1].replace(/,/g, '')) : 0,
                    bedrooms: bedsMatch ? parseInt(bedsMatch[1]) : (studioMatch ? 0 : -1),
                    bathrooms: bathsMatch ? parseInt(bathsMatch[1]) : 0,
                    area: areaMatch ? parseInt(areaMatch[1].replace(/,/g, '')) : 0,
                    propertyType: typeMatch ? typeMatch[1].trim() : '',
                    furnishing: furnMatch ? (typeof furnMatch === 'object' && furnMatch[1] ? furnMatch[1].trim() : 'Furnished') : '',
                    reference: refMatch ? refMatch[1] : '',
                    description,
                    image: images[0] || '',
                };
            }""")

            await sb.save_session(context)

            if not data or data["price"] == 0:
                return None

            return Property(
                id=data.get("reference", ""),
                source="dubizzle",
                title=data["title"],
                price=float(data["price"]),
                property_type=data.get("propertyType", ""),
                bedrooms=data["bedrooms"],
                bathrooms=data["bathrooms"],
                area_sqft=float(data["area"]),
                furnishing=data.get("furnishing", ""),
                description=data.get("description", ""),
                url=url,
                image_url=data.get("image", ""),
            )
        except Exception:
            return None
        finally:
            await context.close()

    def _build_url(self, location, purpose, property_type, min_price, max_price, bedrooms, page):
        """
        Build Dubizzle search URL using path-based location pattern.

        Pattern: /en/property-for-{sale|rent}/residential/{type}/in/{location}/
        Filters go as query params: price__gte, price__lte, bedrooms, page
        """
        purpose_path = "property-for-sale" if purpose == "for-sale" else "property-for-rent"
        path = f"/en/{purpose_path}/residential/"

        # Property type goes in path (before /in/)
        if property_type and property_type.lower() in PROPERTY_TYPE_SLUGS:
            path += PROPERTY_TYPE_SLUGS[property_type.lower()] + "/"

        # Location goes in path using /in/<slug>/ pattern
        loc_slug = LOCATION_SLUGS.get(location.lower().strip())
        if loc_slug:
            path += f"in/{loc_slug}/"

        url = f"{BASE_URL}{path}"

        # Price, bedrooms, page go as query params
        params = []
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

    async def _parse_dom(self, page_obj, search_location: str = "") -> list[Property]:
        """
        Parse listing cards from the DOM using detail link date pattern.

        Listing detail URLs follow: /property-for-{sale|rent}/residential/{type}/YYYY/MM/DD/slug/
        We find these links, walk up to the parent card, and extract data from card text.
        """
        listings = await page_obj.evaluate("""() => {
            const results = [];
            const seen = new Set();

            for (const a of document.querySelectorAll('a[href]')) {
                const href = a.href;
                if (seen.has(href)) continue;
                // Match detail pages: /property-for-{sale|rent}/residential/{type}/YYYY/MM/DD/slug/
                if (!href.match(/property-for-(sale|rent)\\/residential\\/\\w+\\/\\d{4}\\/\\d+\\/\\d+/)) continue;
                seen.add(href);

                // Walk up to find the card container
                let card = a;
                for (let i = 0; i < 15; i++) {
                    if (!card.parentElement) break;
                    card = card.parentElement;
                    if (card.textContent.length > 50 && card.textContent.includes('AED')) break;
                }

                const text = card.innerText || card.textContent;

                // Extract price
                const priceMatch = text.match(/AED[\\s\\xa0]*\\n?([\\d,]+)/);

                // Extract beds/baths/area
                const bedsMatch = text.match(/(\\d+)\\s*Bed/i);
                const bathsMatch = text.match(/(\\d+)\\s*Bath/i);
                const areaMatch = text.match(/([\\d,]+)\\s*sqft/i);
                const studioMatch = /Studio/i.test(text);

                // Extract title from the link text or first substantial line
                let title = '';
                // Try the link's own text first
                const linkText = a.textContent.trim();
                if (linkText.length > 15 && !linkText.startsWith('AED') && !linkText.match(/^\\d/)) {
                    title = linkText.substring(0, 150);
                }
                // Fallback: find title from text lines
                if (!title) {
                    const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 15);
                    for (const line of lines) {
                        if (!line.startsWith('AED') && !line.match(/^\\d+\\s*(Bed|Bath|sqft)/i)
                            && !line.includes('Photo') && !line.includes('Verified')
                            && !line.includes('Premium') && line.length > 15) {
                            title = line.substring(0, 150);
                            break;
                        }
                    }
                }

                // Extract title from URL slug as last fallback
                if (!title) {
                    const slugMatch = href.match(/\\/\\d+\\/\\d+\\/\\d+\\/(.+?)\\/?$/);
                    if (slugMatch) {
                        title = slugMatch[1].replace(/-/g, ' ').replace(/\\d+$/, '').trim();
                        title = title.charAt(0).toUpperCase() + title.slice(1);
                    }
                }

                // Find image
                let image = '';
                const img = card.querySelector('img[src*="dubizzle"], img[src*="beehive"], img[src*="dnhvps"]');
                if (img) image = img.src;

                if (priceMatch) {
                    results.push({
                        url: href,
                        title: title,
                        price: parseInt(priceMatch[1].replace(/,/g, '')),
                        bedrooms: bedsMatch ? parseInt(bedsMatch[1]) : (studioMatch ? 0 : -1),
                        bathrooms: bathsMatch ? parseInt(bathsMatch[1]) : 0,
                        area: areaMatch ? parseInt(areaMatch[1].replace(/,/g, '')) : 0,
                        image: image,
                    });
                }
            }
            return results;
        }""")

        properties = []
        for item in listings:
            # Extract ID from URL slug
            id_match = re.search(r"/(\d+/\d+/\d+/.+?)/?$", item["url"])
            prop_id = id_match.group(1).replace("/", "-") if id_match else ""

            properties.append(Property(
                id=prop_id,
                source="dubizzle",
                title=item.get("title") or "Property listing",
                price=float(item["price"]),
                bedrooms=item.get("bedrooms", -1),
                bathrooms=item.get("bathrooms", 0),
                area_sqft=float(item.get("area", 0)),
                location=search_location,
                url=item["url"],
                image_url=item.get("image", ""),
            ))

        return properties

    async def cleanup(self):
        if self._stealth_browser:
            await self._stealth_browser.cleanup()
            self._stealth_browser = None
