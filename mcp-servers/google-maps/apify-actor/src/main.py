"""
Apify Actor wrapper for Google Maps Lead Extractor.

Searches Google Maps, enriches with emails/phones/socials, scores leads,
and pushes structured results to Apify dataset.
"""

import os
import sys

APP_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, APP_ROOT)

from apify import Actor

from scraper import GoogleMapsScraper
from enrichment import WebsiteEnricher
from stealth_browser import StealthBrowser


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}

        query = actor_input.get("query", "")
        location = actor_input.get("location", "")
        max_results = actor_input.get("maxResults", 20)
        enrich = actor_input.get("enrichWebsites", True)
        min_rating = actor_input.get("minRating", 0)

        if not query:
            Actor.log.error("'query' is required (e.g. 'restaurants', 'plumbers')")
            await Actor.fail(exit_code=1)
            return

        if not location:
            Actor.log.error("'location' is required (e.g. 'Dubai', 'Miami')")
            await Actor.fail(exit_code=1)
            return

        Actor.log.info(
            "Searching Google Maps: '%s' in '%s' (max=%d, enrich=%s)",
            query, location, max_results, enrich,
        )

        browser = StealthBrowser()
        scraper = GoogleMapsScraper(browser=browser)
        enricher = WebsiteEnricher(browser=browser)

        try:
            # Step 1: Search Google Maps
            Actor.log.info("Step 1/3: Searching Google Maps...")
            businesses = await scraper.search(
                query=query,
                location=location,
                max_results=max_results,
            )

            if not businesses:
                Actor.log.warning("No businesses found")
                await Actor.push_data({"results": [], "count": 0})
                return

            Actor.log.info("Found %d businesses", len(businesses))

            # Step 2: Get details for businesses missing phone/website
            Actor.log.info("Step 2/3: Getting business details...")
            for i, biz in enumerate(businesses):
                if biz.maps_url and (not biz.phone or not biz.website):
                    try:
                        detailed = await scraper.get_details(maps_url=biz.maps_url)
                        if detailed and detailed.name:
                            businesses[i] = detailed
                    except Exception as e:
                        Actor.log.debug("Detail fetch failed for %s: %s", biz.name, e)

            # Step 3: Enrich websites
            if enrich:
                Actor.log.info("Step 3/3: Enriching websites for emails/socials...")
                website_urls = [b.website for b in businesses if b.website]
                if website_urls:
                    enrichment_data = await enricher.enrich_batch(
                        website_urls, max_concurrent=3,
                    )
                    for biz in businesses:
                        if biz.website and biz.website in enrichment_data:
                            data = enrichment_data[biz.website]
                            biz.emails = data.get("emails", [])
                            biz.phones = data.get("phones", [])
                            biz.social_links = data.get("social_links", {})
                            biz.tech_stack = data.get("tech_stack", [])

            # Score and filter
            for biz in businesses:
                biz.calculate_lead_score()

            if min_rating > 0:
                businesses = [b for b in businesses if b.rating >= min_rating]

            businesses.sort(key=lambda b: b.lead_score, reverse=True)

            # Push to Apify dataset
            results = [biz.to_dict() for biz in businesses]
            await Actor.push_data(results)

            Actor.log.info(
                "Done! Extracted %d leads (avg score: %.1f)",
                len(results),
                sum(b.lead_score for b in businesses) / max(len(businesses), 1),
            )

        finally:
            await scraper.cleanup()
