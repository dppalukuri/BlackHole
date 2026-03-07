"""
UAE Real Estate Scrapers - Aggregates data from Bayut, Dubizzle, and PropertyFinder.
"""

from scrapers.bayut import BayutScraper
from scrapers.dubizzle import DubizzleScraper
from scrapers.propertyfinder import PropertyFinderScraper


class UAEPropertyAggregator:
    """Unified interface to search across all UAE property platforms."""

    def __init__(self, bayut_api_key: str = "", use_playwright: bool = True):
        self.bayut = BayutScraper(api_key=bayut_api_key)
        self.dubizzle = DubizzleScraper()
        self.propertyfinder = PropertyFinderScraper()
        self.use_playwright = use_playwright

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

        Args:
            location: Area name (e.g., "Dubai Marina", "JBR", "Downtown Dubai")
            purpose: "for-sale" or "for-rent"
            property_type: "apartment", "villa", "townhouse", etc. (empty = all)
            min_price: Minimum price in AED (0 = no min)
            max_price: Maximum price in AED (0 = no max)
            bedrooms: Number of bedrooms (-1 = any, 0 = studio)
            source: "bayut", "dubizzle", "propertyfinder", or "all"
            page: Page number for pagination
        """
        results = []
        errors = []

        sources = {
            "bayut": self.bayut,
            "dubizzle": self.dubizzle,
            "propertyfinder": self.propertyfinder,
        }

        if source != "all":
            sources = {source: sources[source]} if source in sources else {}

        for name, scraper in sources.items():
            try:
                props = await scraper.search(
                    location=location,
                    purpose=purpose,
                    property_type=property_type,
                    min_price=min_price,
                    max_price=max_price,
                    bedrooms=bedrooms,
                    page=page,
                )
                results.extend(props)
            except Exception as e:
                errors.append(f"{name}: {str(e)}")

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
        """Close browser instances."""
        await self.dubizzle.cleanup()
        await self.propertyfinder.cleanup()
