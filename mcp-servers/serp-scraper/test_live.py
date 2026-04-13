"""Live test for SERP scraper — runs against real Google/Bing."""

import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import SerpScraper


async def test_google():
    print("=" * 60)
    print("TEST 1: Google search for 'what is python programming'")
    print("=" * 60)

    scraper = SerpScraper()
    try:
        result = await scraper.search_google(
            query="what is python programming",
            num_results=10,
        )
        print(f"\nQuery: {result.query}")
        print(f"Total results: {result.total_results}")
        print(f"Organic: {len(result.organic)}")
        print(f"Ads: {len(result.ads)}")
        print(f"Featured snippet: {'Yes' if result.featured_snippet else 'No'}")
        print(f"PAA: {len(result.people_also_ask)}")
        print(f"Related searches: {len(result.related_searches)}")

        if result.organic:
            print("\nTop 3 organic:")
            for r in result.organic[:3]:
                print(f"  #{r.position}: {r.title[:60]}")
                print(f"          {r.domain}")
                print(f"          {r.snippet[:80]}..." if r.snippet else "")

        if result.people_also_ask:
            print("\nPAA questions:")
            for p in result.people_also_ask[:3]:
                print(f"  Q: {p.question}")

        if result.related_searches:
            print("\nRelated searches:")
            for rs in result.related_searches[:5]:
                print(f"  - {rs}")

        return len(result.organic) > 0
    finally:
        await scraper.cleanup()


async def test_bing():
    print("\n" + "=" * 60)
    print("TEST 2: Bing search for 'python developer jobs'")
    print("=" * 60)

    scraper = SerpScraper()
    try:
        result = await scraper.search_bing(
            query="python developer jobs",
            num_results=10,
        )
        print(f"\nQuery: {result.query}")
        print(f"Total results: {result.total_results}")
        print(f"Organic: {len(result.organic)}")
        print(f"Related: {len(result.related_searches)}")

        if result.organic:
            print("\nTop 3 organic:")
            for r in result.organic[:3]:
                print(f"  #{r.position}: {r.title[:60]}")
                print(f"          {r.domain}")

        return len(result.organic) > 0
    finally:
        await scraper.cleanup()


async def main():
    results = {}
    results["google"] = await test_google()
    results["bing"] = await test_bing()

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")

    print(f"\nOverall: {'ALL PASSED' if all(results.values()) else 'SOME FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())
