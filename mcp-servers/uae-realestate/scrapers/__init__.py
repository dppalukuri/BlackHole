"""
UAE Real Estate Scrapers - Aggregates data from Bayut, Dubizzle, and PropertyFinder.
"""

import asyncio
from scrapers.bayut import BayutScraper
from scrapers.dubizzle import DubizzleScraper
from scrapers.propertyfinder import PropertyFinderScraper


def _post_filter(properties: list, bedrooms: int, min_price: int, max_price: int,
                  property_type: str) -> list:
    """Enforce filters that sites may ignore (promoted/similar listings leak through)."""
    filtered = []
    for p in properties:
        if bedrooms >= 0 and p.bedrooms != bedrooms:
            continue
        if min_price > 0 and p.price < min_price:
            continue
        if max_price > 0 and p.price > max_price:
            continue
        if property_type:
            pt = property_type.lower()
            pp = p.property_type.lower()
            if pt and pp and pt not in pp and pp not in pt:
                continue
        filtered.append(p)
    return filtered


def _deduplicate(properties: list) -> list:
    """Remove duplicate listings (same price + beds + area from different sources)."""
    seen = set()
    unique = []
    for p in properties:
        # Key: price + bedrooms + area (rounded) — catches cross-platform duplicates
        key = (int(p.price), p.bedrooms, int(p.area_sqft / 10) * 10)
        # Also deduplicate exact same listing from same source
        source_key = (p.source, p.id)
        if source_key not in seen and key not in seen:
            seen.add(source_key)
            seen.add(key)
            unique.append(p)
    return unique


class UAEPropertyAggregator:
    """Unified interface to search across all UAE property platforms."""

    def __init__(self):
        self.bayut = BayutScraper()
        self.dubizzle = DubizzleScraper()
        self.propertyfinder = PropertyFinderScraper()

    async def search(
        self,
        location: str,
        purpose: str = "for-sale",
        property_type: str = "",
        min_price: int = 0,
        max_price: int = 0,
        bedrooms: int = -1,
        source: str = "all",
        page: int = 1,
        min_results: int = 15,
    ):
        """
        Search properties across all platforms concurrently.

        Filters are applied at two levels:
          1. URL params (pre-fetch) — sites get the right query
          2. Post-filter — removes promoted/similar listings that leak through

        If post-filtering drops too many results, automatically fetches more
        pages until min_results is reached or pages are exhausted (max 3 pages).
        """
        sources_map = {
            "bayut": self.bayut,
            "dubizzle": self.dubizzle,
            "propertyfinder": self.propertyfinder,
        }

        if source != "all" and source in sources_map:
            sources_map = {source: sources_map[source]}

        all_results = []
        errors = []
        max_pages = 3  # Fetch up to 3 pages per source to fill min_results

        for current_page in range(page, page + max_pages):
            async def _run_scraper(name, scraper, pg):
                try:
                    return name, await scraper.search(
                        location=location,
                        purpose=purpose,
                        property_type=property_type,
                        min_price=min_price,
                        max_price=max_price,
                        bedrooms=bedrooms,
                        page=pg,
                    ), None
                except Exception as e:
                    return name, [], str(e)

            # First page: run all scrapers concurrently
            # Subsequent pages: only re-fetch scrapers that had results (not errored)
            if current_page == page:
                tasks = [_run_scraper(n, s, current_page) for n, s in sources_map.items()]
            else:
                tasks = [_run_scraper(n, s, current_page) for n, s in active_sources.items()]

            completed = await asyncio.gather(*tasks)

            page_results = []
            active_sources = {}
            for name, props, error in completed:
                if error:
                    if current_page == page:  # Only report errors from first page
                        errors.append(f"{name}: {error}")
                elif props:
                    page_results.extend(props)
                    active_sources[name] = sources_map[name]

            if not page_results:
                break  # No more results from any source

            # Post-filter this page
            filtered = _post_filter(page_results, bedrooms, min_price, max_price, property_type)
            all_results.extend(filtered)

            # Stop if we have enough or no sources left to paginate
            if len(all_results) >= min_results or not active_sources:
                break

        # Deduplicate cross-source matches
        all_results = _deduplicate(all_results)

        return all_results, errors

    async def get_details(self, property_id: str, source: str):
        """Get detailed info for a specific listing."""
        scrapers = {
            "bayut": self.bayut,
            "dubizzle": self.dubizzle,
            "propertyfinder": self.propertyfinder,
        }
        scraper = scrapers.get(source)
        if not scraper:
            raise ValueError(f"Unknown source: {source}")
        return await scraper.get_details(property_id)

    async def cleanup(self):
        """Close the shared stealth browser."""
        from stealth_browser import _browser
        await _browser.cleanup()
