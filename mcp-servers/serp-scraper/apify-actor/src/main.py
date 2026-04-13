"""
Apify Actor wrapper for SERP Scraper.

Scrapes Google and/or Bing for search queries,
pushes structured SERP data to Apify dataset.
"""

import asyncio
import os
import sys

APP_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, APP_ROOT)

from apify import Actor

from scraper import SerpScraper
from stealth_browser import StealthBrowser


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}

        queries = actor_input.get("queries", [])
        engine = actor_input.get("engine", "google")
        num_results = actor_input.get("numResults", 10)
        country = actor_input.get("country", "")
        language = actor_input.get("language", "en")

        if not queries:
            Actor.log.error("'queries' is required — provide a list of search queries")
            await Actor.fail(exit_code=1)
            return

        queries = queries[:20]  # Limit to 20 queries

        Actor.log.info(
            "Scraping %d queries on %s (results=%d, country=%s)",
            len(queries), engine, num_results, country or "auto",
        )

        browser = StealthBrowser()
        scraper = SerpScraper(browser=browser)

        try:
            for i, query in enumerate(queries):
                Actor.log.info("[%d/%d] Searching: '%s'", i + 1, len(queries), query)

                results = []

                if engine in ("google", "both"):
                    serp = await scraper.search_google(
                        query=query,
                        num_results=num_results,
                        language=language,
                        country=country,
                    )
                    results.append({
                        "engine": "google",
                        **serp.to_dict(),
                    })

                if engine in ("bing", "both"):
                    serp = await scraper.search_bing(
                        query=query,
                        num_results=num_results,
                    )
                    results.append({
                        "engine": "bing",
                        **serp.to_dict(),
                    })

                await Actor.push_data(results)

                # Delay between queries to avoid rate limiting
                if i < len(queries) - 1:
                    await asyncio.sleep(3)

            Actor.log.info("Done! Scraped %d queries", len(queries))

        finally:
            await scraper.cleanup()
