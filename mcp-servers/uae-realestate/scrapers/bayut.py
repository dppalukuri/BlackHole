"""
Bayut.com scraper - Multiple strategies to bypass hCaptcha.

Bayut uses hCaptcha on every request + Algolia as search backend.

Strategy order:
  1. Algolia direct API (if keys available from prior session)
  2. Playwright with stealth + CAPTCHA solving
  3. RapidAPI fallback (free tier: 750 calls/month)

URL pattern: /{for-sale|to-rent}/{type}/dubai/{location-slug}/
Filters: price_min, price_max, beds_min, beds_max, furnishing_status, completion_status, page
Data extraction: __NEXT_DATA__ (Next.js SSR), Apollo cache, DOM cards
Algolia index: bayut-production-ads-en

Env vars:
  CAPSOLVER_API_KEY  - For hCaptcha solving (capsolver.com)
  BAYUT_RAPIDAPI_KEY - Fallback API key (rapidapi.com/apidojo/api/bayut)
"""

import os
import asyncio
import re
import json
import httpx
from models import Property
import slug_registry

BASE_URL = "https://www.bayut.com"
RAPIDAPI_HOST = "bayut.p.rapidapi.com"
ALGOLIA_INDEX = "bayut-production-ads-en"

# Algolia credentials cache (extracted from page after CAPTCHA solve)
_algolia_cache = {"app_id": "", "api_key": ""}


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
        # Strategy 1: Algolia direct (if we have cached keys)
        if _algolia_cache["app_id"] and _algolia_cache["api_key"]:
            try:
                results = await self._search_algolia(
                    location, purpose, property_type, min_price, max_price, bedrooms, page
                )
                if results:
                    return results
            except Exception:
                pass

        # Strategy 2: Playwright with stealth + CAPTCHA solving
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
            "Bayut scraping blocked by CAPTCHA. Set CAPSOLVER_API_KEY for auto-solving, "
            "or BAYUT_RAPIDAPI_KEY for API fallback."
        )

    async def _search_playwright(
        self, location, purpose, property_type, min_price, max_price, bedrooms, page
    ) -> list[Property]:
        """Search using stealth Playwright with CAPTCHA solving."""
        sb = await self._get_stealth_browser()
        context = await sb.new_context(site_name="bayut")
        page_obj = await context.new_page()

        try:
            url = self._build_url(location, purpose, property_type, min_price, max_price, bedrooms, page)
            await page_obj.goto(url, wait_until="networkidle", timeout=40000)
            await asyncio.sleep(2)

            # Check for CAPTCHA and solve if present
            from captcha import handle_captcha_if_present
            captcha_solved = await handle_captcha_if_present(page_obj)

            if not captcha_solved:
                return []

            # Wait for content after CAPTCHA, then scroll
            await asyncio.sleep(2)
            for _ in range(5):
                await page_obj.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1)
            await asyncio.sleep(2)

            # Try to extract Algolia keys for future direct queries
            await self._extract_algolia_keys(page_obj)

            # Extract listings from page
            properties = await self._extract_listings(page_obj)

            # Save session state for future requests
            await sb.save_session(context)

            return properties
        finally:
            await context.close()

    async def _extract_algolia_keys(self, page_obj):
        """Extract Algolia API credentials from the page for direct queries."""
        global _algolia_cache
        try:
            keys = await page_obj.evaluate("""() => {
                // Check window.state (exposed on CAPTCHA page and listing pages)
                if (window.state) {
                    const s = window.state;
                    if (s.algoliaAppId && s.algoliaApiKey) {
                        return { app_id: s.algoliaAppId, api_key: s.algoliaApiKey };
                    }
                }

                // Check __NEXT_DATA__ for Algolia config
                const el = document.getElementById('__NEXT_DATA__');
                if (el) {
                    try {
                        const d = JSON.parse(el.textContent);
                        const rc = d.runtimeConfig || d.props?.runtimeConfig || {};
                        if (rc.algoliaAppId && rc.algoliaApiKey) {
                            return { app_id: rc.algoliaAppId, api_key: rc.algoliaApiKey };
                        }
                        const pp = d.props?.pageProps || {};
                        if (pp.algoliaAppId && pp.algoliaApiKey) {
                            return { app_id: pp.algoliaAppId, api_key: pp.algoliaApiKey };
                        }
                    } catch {}
                }

                // Scan script tags for Algolia config
                for (const script of document.scripts) {
                    const t = script.textContent;
                    if (t.includes('algolia') || t.includes('algoliasearch')) {
                        const appMatch = t.match(/(?:appId|applicationID|ALGOLIA_APP_ID)['":\\s]+([A-Z0-9]{10,})/i);
                        const keyMatch = t.match(/(?:apiKey|searchKey|ALGOLIA_API_KEY)['":\\s]+([a-f0-9]{20,})/i);
                        if (appMatch && keyMatch) {
                            return { app_id: appMatch[1], api_key: keyMatch[1] };
                        }
                    }
                }

                return null;
            }""")

            if keys and keys.get("app_id") and keys.get("api_key"):
                _algolia_cache["app_id"] = keys["app_id"]
                _algolia_cache["api_key"] = keys["api_key"]
        except Exception:
            pass

    async def _search_algolia(
        self, location, purpose, property_type, min_price, max_price, bedrooms, page
    ) -> list[Property]:
        """Search Bayut via Algolia API directly."""
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

        payload = {
            "requests": [{
                "indexName": ALGOLIA_INDEX,
                "params": {
                    "filters": " AND ".join(filters),
                    "hitsPerPage": 25,
                    "page": page - 1,
                },
            }],
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://{_algolia_cache['app_id']}-dsn.algolia.net/1/indexes/*/queries",
                headers={
                    "X-Algolia-Application-Id": _algolia_cache["app_id"],
                    "X-Algolia-API-Key": _algolia_cache["api_key"],
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

        properties = []
        results = data.get("results", [])
        if results:
            for hit in results[0].get("hits", []):
                prop = self._parse_listing(hit)
                if prop:
                    properties.append(prop)

        return properties

    async def _extract_listings(self, page_obj) -> list[Property]:
        """Extract property listings from Bayut search results page."""
        raw = await page_obj.evaluate("""() => {
            // Try __NEXT_DATA__ first (Bayut uses Next.js)
            const nextEl = document.getElementById('__NEXT_DATA__');
            if (nextEl) {
                try {
                    const d = JSON.parse(nextEl.textContent);
                    const pageProps = d.props?.pageProps;
                    if (!pageProps) return null;

                    // Look for listings in various locations
                    const candidates = [
                        pageProps.properties,
                        pageProps.listings,
                        pageProps.searchResult?.properties,
                        pageProps.searchResult?.hits,
                        pageProps.hits,
                    ];

                    for (const arr of candidates) {
                        if (Array.isArray(arr) && arr.length > 0) {
                            return { source: '__NEXT_DATA__', listings: arr };
                        }
                    }

                    // Try Apollo state cache
                    const apolloState = d.props?.apolloState || d.props?.pageProps?.apolloState;
                    if (apolloState) {
                        const listings = [];
                        for (const [key, val] of Object.entries(apolloState)) {
                            if (key.startsWith('Property:') && val.price && val.title) {
                                listings.push(val);
                            }
                        }
                        if (listings.length > 0) {
                            return { source: 'apollo', listings };
                        }
                    }
                } catch(e) {}
            }

            // Fallback: parse DOM cards
            const cards = document.querySelectorAll('[role="article"], article, [class*="property-card"], [data-testid*="listing"]');
            if (cards.length > 0) {
                const results = [];
                for (const card of cards) {
                    const link = card.querySelector('a[href*="/property/"]');
                    if (!link) continue;
                    results.push({
                        href: link.href,
                        text: card.textContent.trim().substring(0, 500),
                    });
                }
                if (results.length > 0) {
                    return { source: 'dom', listings: results };
                }
            }

            return null;
        }""")

        if not raw:
            return []

        properties = []
        source = raw.get("source", "")

        if source in ("__NEXT_DATA__", "apollo"):
            for item in raw.get("listings", []):
                prop = self._parse_listing(item)
                if prop:
                    properties.append(prop)
        elif source == "dom":
            for item in raw.get("listings", []):
                prop = self._parse_dom_card(item)
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
        # Try Playwright first
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

    def _parse_dom_card(self, item: dict) -> Property | None:
        """Parse a listing from DOM text."""
        try:
            text = item.get("text", "")
            href = item.get("href", "")

            price_match = re.search(r"AED\s*([\d,]+)", text)
            price = float(price_match.group(1).replace(",", "")) if price_match else 0
            if price < 10000:
                return None

            beds_match = re.search(r"(\d+)\s*(?:bed|BR|Bed)", text, re.I)
            studio = bool(re.search(r"studio", text, re.I))
            baths_match = re.search(r"(\d+)\s*(?:bath|Bath)", text, re.I)
            area_match = re.search(r"([\d,]+)\s*(?:sqft|sq\.?\s*ft)", text, re.I)

            id_match = re.search(r"details?-?(\d+)", href)
            prop_id = id_match.group(1) if id_match else ""

            title_parts = text.split("\n")
            title = ""
            for part in title_parts:
                part = part.strip()
                if len(part) > 15 and not part.startswith("AED") and not re.match(r"^\d", part):
                    title = part[:100]
                    break

            return Property(
                id=prop_id,
                source="bayut",
                title=title or "Property listing",
                price=price,
                bedrooms=int(beds_match.group(1)) if beds_match else (0 if studio else 0),
                bathrooms=int(baths_match.group(1)) if baths_match else 0,
                area_sqft=float(area_match.group(1).replace(",", "")) if area_match else 0,
                url=href if href.startswith("http") else f"{BASE_URL}{href}",
            )
        except Exception:
            return None

    async def cleanup(self):
        if self._stealth_browser:
            await self._stealth_browser.cleanup()
            self._stealth_browser = None
