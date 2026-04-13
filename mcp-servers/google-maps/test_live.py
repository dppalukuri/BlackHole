"""Live test for Google Maps scraper — runs against real Google Maps."""

import asyncio
import json
import sys
import os

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import GoogleMapsScraper
from enrichment import WebsiteEnricher
from models import Business


async def test_search():
    print("=" * 60)
    print("TEST 1: Search Google Maps for 'restaurants' in 'Dubai Marina'")
    print("=" * 60)

    scraper = GoogleMapsScraper()
    try:
        results = await scraper.search(
            query="restaurants",
            location="Dubai Marina",
            max_results=5,
        )
        print(f"\nFound {len(results)} results:")
        for i, biz in enumerate(results):
            print(f"\n  [{i+1}] {biz.name}")
            print(f"      Rating: {biz.rating} ({biz.review_count} reviews)")
            print(f"      Category: {biz.category}")
            print(f"      Address: {biz.address}")
            print(f"      Maps URL: {biz.maps_url[:80]}..." if biz.maps_url else "      Maps URL: N/A")

        if not results:
            print("  NO RESULTS — selectors likely broken")
            return False

        return len(results) > 0
    finally:
        await scraper.cleanup()


async def test_details():
    print("\n" + "=" * 60)
    print("TEST 2: Get business details from search result")
    print("=" * 60)

    scraper = GoogleMapsScraper()
    try:
        # First search to get a URL
        results = await scraper.search(
            query="coffee shops",
            location="New York",
            max_results=3,
        )

        if not results or not results[0].maps_url:
            print("  SKIP — no search results to test details on")
            return False

        url = results[0].maps_url
        print(f"\nGetting details for: {results[0].name}")
        print(f"URL: {url[:80]}...")

        details = await scraper.get_details(maps_url=url)
        if details:
            print(f"\n  Name: {details.name}")
            print(f"  Phone: {details.phone}")
            print(f"  Website: {details.website}")
            print(f"  Address: {details.address}")
            print(f"  Rating: {details.rating}")
            print(f"  Coords: {details.latitude}, {details.longitude}")
            return bool(details.name)
        else:
            print("  FAILED — no details returned")
            return False
    finally:
        await scraper.cleanup()


async def test_enrichment():
    print("\n" + "=" * 60)
    print("TEST 3: Website enrichment")
    print("=" * 60)

    enricher = WebsiteEnricher()
    try:
        # Test with a known website
        url = "https://www.starbucks.com"
        print(f"\nEnriching: {url}")

        result = await enricher.enrich(url, deep=False)
        print(f"\n  Emails: {result['emails'][:3]}")
        print(f"  Phones: {result['phones'][:3]}")
        print(f"  Social links: {list(result['social_links'].keys())}")
        print(f"  Tech stack: {result['tech_stack']}")
        print(f"  Meta desc: {result['meta_description'][:80]}..." if result['meta_description'] else "  Meta desc: N/A")

        return True  # Enrichment ran without crashing
    finally:
        await enricher.cleanup()


async def test_lead_scoring():
    print("\n" + "=" * 60)
    print("TEST 4: Lead scoring")
    print("=" * 60)

    biz = Business(
        name="Test Business",
        phone="+1-555-0123",
        website="https://example.com",
        rating=4.5,
        review_count=75,
        address="123 Main St",
        emails=["john.doe@example.com", "info@example.com"],
        social_links={"linkedin": "https://linkedin.com/company/test", "facebook": "https://facebook.com/test"},
    )
    score = biz.calculate_lead_score()
    print(f"\n  Business: {biz.name}")
    print(f"  Score: {score}/100")
    print(f"  Expected: ~85 (email=25 + phone=15 + website=10 + socials=10 + rating=10 + reviews=10 + address=5)")

    return score > 50


async def main():
    results = {}

    results["search"] = await test_search()
    results["details"] = await test_details()
    results["enrichment"] = await test_enrichment()
    results["lead_scoring"] = await test_lead_scoring()

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")

    all_passed = all(results.values())
    print(f"\nOverall: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
