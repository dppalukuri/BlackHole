"""
UAE Real Estate Scrapers - Aggregates data from Bayut, Dubizzle, and PropertyFinder.
"""

import asyncio
from scrapers.bayut import BayutScraper
from scrapers.dubizzle import DubizzleScraper
from scrapers.propertyfinder import PropertyFinderScraper


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
    ):
        """
        Search properties across all platforms concurrently.
        All three scrapers always run — errors are captured per-source.
        Results are deduplicated across sources.
        """
        results = []
        errors = []

        sources = {
            "bayut": self.bayut,
            "dubizzle": self.dubizzle,
            "propertyfinder": self.propertyfinder,
        }

        if source != "all" and source in sources:
            sources = {source: sources[source]}

        # Run all scrapers concurrently
        async def _run_scraper(name, scraper):
            try:
                return name, await scraper.search(
                    location=location,
                    purpose=purpose,
                    property_type=property_type,
                    min_price=min_price,
                    max_price=max_price,
                    bedrooms=bedrooms,
                    page=page,
                ), None
            except Exception as e:
                return name, [], str(e)

        tasks = [_run_scraper(name, scraper) for name, scraper in sources.items()]
        completed = await asyncio.gather(*tasks)

        for name, props, error in completed:
            if error:
                errors.append(f"{name}: {error}")
            else:
                results.extend(props)

        # Deduplicate cross-source matches
        results = _deduplicate(results)

        return results, errors

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
