"""
Autonomous Lead Generation Agent

Runs on a schedule (daily/weekly), scrapes Google Maps for a configured niche,
enriches with emails/socials, scores leads, and outputs packaged lead lists.

Revenue model:
  - Sell lead lists per niche/city on Gumroad ($10-50 per list)
  - Or deliver via email subscription
  - Or use for your own outreach

Usage:
  python agent.py                          # Run once
  python agent.py --schedule daily         # Run daily at configured time
  python agent.py --niche restaurants --city "Dubai Marina" --max 30
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add sibling projects to path
AGENT_DIR = Path(__file__).parent
REPO_ROOT = AGENT_DIR.parent.parent
GOOGLE_MAPS = REPO_ROOT / "mcp-servers" / "google-maps"
SERP_SCRAPER = REPO_ROOT / "mcp-servers" / "serp-scraper"

# Google Maps must be first so its scraper.py wins over serp-scraper's
sys.path.insert(0, str(SERP_SCRAPER))
sys.path.insert(0, str(GOOGLE_MAPS))

from scraper import GoogleMapsScraper
from enrichment import WebsiteEnricher
from export import leads_to_csv, leads_to_json
from stealth_browser import StealthBrowser
from models import Business

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("lead-gen-agent")

# Output directory for lead lists
OUTPUT_DIR = AGENT_DIR / "output"
CONFIG_FILE = AGENT_DIR / "config.json"

# Default niches to scrape
DEFAULT_CONFIG = {
    "jobs": [
        {
            "niche": "restaurants",
            "cities": ["Dubai Marina", "Downtown Dubai"],
            "max_results": 20,
            "min_rating": 3.5,
            "enrich": True,
        },
        {
            "niche": "dental clinics",
            "cities": ["Dubai", "Abu Dhabi"],
            "max_results": 15,
            "min_rating": 4.0,
            "enrich": True,
        },
    ],
    "schedule": "daily",
    "output_format": "csv",
}


def load_config() -> dict:
    """Load agent config from config.json, or create default."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    else:
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
        logger.info(f"Created default config at {CONFIG_FILE}")
        return DEFAULT_CONFIG


async def run_job(
    niche: str,
    city: str,
    max_results: int = 20,
    min_rating: float = 0,
    enrich: bool = True,
) -> list[Business]:
    """Run a single lead gen job: search + enrich + score."""
    logger.info(f"--- Job: '{niche}' in '{city}' (max={max_results}) ---")

    browser = StealthBrowser()
    scraper = GoogleMapsScraper(browser=browser)
    enricher = WebsiteEnricher(browser=browser)

    try:
        # Step 1: Search
        logger.info("Searching Google Maps...")
        businesses = await scraper.search(
            query=niche,
            location=city,
            max_results=max_results,
        )

        if not businesses:
            logger.warning("No results found")
            return []

        logger.info(f"Found {len(businesses)} businesses")

        # Step 2: Get details for ones missing phone/website
        logger.info("Getting business details...")
        for i, biz in enumerate(businesses):
            if biz.maps_url and (not biz.phone or not biz.website):
                try:
                    detailed = await scraper.get_details(maps_url=biz.maps_url)
                    if detailed and detailed.name:
                        businesses[i] = detailed
                except Exception:
                    pass

        # Step 3: Enrich
        if enrich:
            logger.info("Enriching websites for emails/socials...")
            urls = [b.website for b in businesses if b.website]
            if urls:
                enrichment = await enricher.enrich_batch(urls, max_concurrent=3)
                for biz in businesses:
                    if biz.website and biz.website in enrichment:
                        data = enrichment[biz.website]
                        biz.emails = data.get("emails", [])
                        biz.phones = data.get("phones", [])
                        biz.social_links = data.get("social_links", {})
                        biz.tech_stack = data.get("tech_stack", [])

        # Step 4: Score and filter
        for biz in businesses:
            biz.calculate_lead_score()

        if min_rating > 0:
            businesses = [b for b in businesses if b.rating >= min_rating]

        businesses.sort(key=lambda b: b.lead_score, reverse=True)

        with_email = sum(1 for b in businesses if b.emails)
        with_phone = sum(1 for b in businesses if b.phone or b.phones)
        avg_score = sum(b.lead_score for b in businesses) / max(len(businesses), 1)

        logger.info(
            f"Results: {len(businesses)} leads, "
            f"{with_email} with email, {with_phone} with phone, "
            f"avg score {avg_score:.0f}"
        )

        return businesses

    finally:
        await scraper.cleanup()


async def run_all_jobs(config: dict) -> dict[str, list[Business]]:
    """Run all configured jobs."""
    all_results = {}

    for job in config.get("jobs", []):
        niche = job["niche"]
        cities = job.get("cities", [])
        max_results = job.get("max_results", 20)
        min_rating = job.get("min_rating", 0)
        enrich = job.get("enrich", True)

        for city in cities:
            key = f"{niche}_{city}".replace(" ", "_").lower()
            leads = await run_job(
                niche=niche,
                city=city,
                max_results=max_results,
                min_rating=min_rating,
                enrich=enrich,
            )
            all_results[key] = leads

            # Delay between jobs to avoid detection
            await asyncio.sleep(5)

    return all_results


def save_results(
    results: dict[str, list[Business]],
    output_format: str = "csv",
) -> list[str]:
    """Save lead lists to output directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d")
    saved_files = []

    for key, leads in results.items():
        if not leads:
            continue

        filename = f"{key}_{timestamp}"

        if output_format == "csv":
            filepath = str(OUTPUT_DIR / f"{filename}.csv")
            leads_to_csv(leads, filepath)
        else:
            filepath = str(OUTPUT_DIR / f"{filename}.json")
            leads_to_json(leads, filepath)

        saved_files.append(filepath)
        logger.info(f"Saved {len(leads)} leads to {filepath}")

    return saved_files


def generate_summary(results: dict[str, list[Business]]) -> str:
    """Generate a text summary of the run."""
    lines = [
        f"Lead Generation Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
    ]

    total_leads = 0
    total_with_email = 0
    total_with_phone = 0

    for key, leads in results.items():
        if not leads:
            continue

        total_leads += len(leads)
        with_email = sum(1 for b in leads if b.emails)
        with_phone = sum(1 for b in leads if b.phone or b.phones)
        total_with_email += with_email
        total_with_phone += with_phone
        avg_score = sum(b.lead_score for b in leads) / len(leads)

        lines.append(f"  {key}:")
        lines.append(f"    Leads: {len(leads)}")
        lines.append(f"    With email: {with_email}")
        lines.append(f"    With phone: {with_phone}")
        lines.append(f"    Avg score: {avg_score:.0f}")
        lines.append(f"    Top lead: {leads[0].name} (score {leads[0].lead_score})")
        lines.append("")

    lines.append("-" * 60)
    lines.append(f"  TOTAL: {total_leads} leads, {total_with_email} with email, {total_with_phone} with phone")

    return "\n".join(lines)


async def run_once(args):
    """Run the agent once."""
    if args.niche and args.city:
        # Single job from CLI args
        leads = await run_job(
            niche=args.niche,
            city=args.city,
            max_results=args.max,
            min_rating=args.min_rating,
            enrich=not args.no_enrich,
        )
        results = {f"{args.niche}_{args.city}".replace(" ", "_").lower(): leads}
    else:
        # Run all configured jobs
        config = load_config()
        results = await run_all_jobs(config)

    # Save and summarize
    config = load_config()
    saved = save_results(results, config.get("output_format", "csv"))
    summary = generate_summary(results)
    print(summary)

    if saved:
        print(f"\nFiles saved:")
        for f in saved:
            print(f"  {f}")


async def run_scheduled(args):
    """Run the agent on a schedule."""
    import time

    schedule = args.schedule
    intervals = {
        "hourly": 3600,
        "daily": 86400,
        "weekly": 604800,
    }

    interval = intervals.get(schedule, 86400)
    logger.info(f"Starting scheduled agent (interval: {schedule})")

    while True:
        try:
            await run_once(args)
        except Exception as e:
            logger.error(f"Run failed: {e}")

        logger.info(f"Next run in {interval // 3600} hours")
        await asyncio.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Lead Generation Agent")
    parser.add_argument("--niche", help="Business type (e.g. 'restaurants')")
    parser.add_argument("--city", help="City to search (e.g. 'Dubai Marina')")
    parser.add_argument("--max", type=int, default=20, help="Max results")
    parser.add_argument("--min-rating", type=float, default=0, help="Min Google rating")
    parser.add_argument("--no-enrich", action="store_true", help="Skip website enrichment")
    parser.add_argument(
        "--schedule",
        choices=["hourly", "daily", "weekly"],
        help="Run on a schedule",
    )

    args = parser.parse_args()

    if args.schedule:
        asyncio.run(run_scheduled(args))
    else:
        asyncio.run(run_once(args))


if __name__ == "__main__":
    main()
