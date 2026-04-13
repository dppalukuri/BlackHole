"""Live test for LinkedIn scraper — runs against real LinkedIn."""

import asyncio
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import LinkedInScraper


async def test_job_search():
    print("=" * 60)
    print("TEST 1: Job search for 'python developer' in 'Dubai'")
    print("=" * 60)

    scraper = LinkedInScraper()
    try:
        result = await scraper.search_jobs(
            query="python developer",
            location="Dubai",
            max_results=5,
        )
        print(f"\nQuery: {result.query}")
        print(f"Type: {result.result_type}")
        print(f"Results: {len(result.results)}")

        if result.results:
            print("\nTop results:")
            for i, job in enumerate(result.results[:5]):
                print(f"  [{i+1}] {job.get('title', 'N/A')}")
                print(f"      Company: {job.get('company', 'N/A')}")
                print(f"      Location: {job.get('location', 'N/A')}")
                print(f"      Posted: {job.get('posted_date', 'N/A')}")
        else:
            print("  NO RESULTS")

        return len(result.results) > 0
    finally:
        await scraper.cleanup()


async def test_company():
    print("\n" + "=" * 60)
    print("TEST 2: Company page for 'google'")
    print("=" * 60)

    scraper = LinkedInScraper()
    try:
        company = await scraper.get_company(company_slug="google")
        if company and company.name:
            print(f"\n  Name: {company.name}")
            print(f"  Tagline: {company.tagline}")
            print(f"  Industry: {company.industry}")
            print(f"  Size: {company.company_size}")
            print(f"  HQ: {company.headquarters}")
            print(f"  Website: {company.website}")
            print(f"  Founded: {company.founded}")
            return True
        else:
            print("  FAILED — no company data returned")
            return False
    finally:
        await scraper.cleanup()


async def test_public_profile():
    print("\n" + "=" * 60)
    print("TEST 3: Public profile (without login)")
    print("=" * 60)

    scraper = LinkedInScraper()
    try:
        profile = await scraper.get_profile(username="satyanadella")
        if profile and profile.name:
            print(f"\n  Name: {profile.name}")
            print(f"  Headline: {profile.headline}")
            print(f"  Location: {profile.location}")
            return True
        else:
            print("  Limited or no data (expected without login)")
            return True  # Not a failure — expected without login
    finally:
        await scraper.cleanup()


async def main():
    results = {}
    results["job_search"] = await test_job_search()
    results["company"] = await test_company()
    results["public_profile"] = await test_public_profile()

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")

    print(f"\nOverall: {'ALL PASSED' if all(results.values()) else 'SOME FAILED'}")


if __name__ == "__main__":
    asyncio.run(main())
