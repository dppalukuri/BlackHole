"""
UAE Real Estate Scrapers - Aggregates data from Bayut, Dubizzle, and PropertyFinder.
"""

import os
import asyncio
from scrapers.bayut import BayutScraper
from scrapers.dubizzle import DubizzleScraper
from scrapers.propertyfinder import PropertyFinderScraper


# Bayut requires CAPTCHA solving — skip unless API keys are configured
def _bayut_available() -> bool:
    return bool(
        os.environ.get("CAPSOLVER_API_KEY")
        or os.environ.get("BAYUT_RAPIDAPI_KEY")
    )


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
        Search properties across all or specific platforms.
        Runs scrapers concurrently for faster results.
        Skips Bayut when source="all" and no API keys are configured.
        """
        results = []
        errors = []

        sources = {
            "dubizzle": self.dubizzle,
            "propertyfinder": self.propertyfinder,
        }

        if source == "all":
            if _bayut_available():
                sources["bayut"] = self.bayut
            else:
                errors.append("bayut: skipped (no CAPSOLVER_API_KEY or BAYUT_RAPIDAPI_KEY)")
        elif source == "bayut":
            sources = {"bayut": self.bayut}
        elif source in ("dubizzle", "propertyfinder"):
            sources = {source: sources.get(source, self.dubizzle)}

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
