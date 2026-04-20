"""Google Maps lead-gen fulfillment script.

Sellable product: "N verified business leads in {niche} + {city} — $99"

CLI:
    python leads_maps.py --niche "dentist" --location "Dubai" --count 100
    python leads_maps.py --niche "plumber" --location "Miami, FL" --count 50 \
        --min-rating 4.0 --no-enrich

Output: orders/order-<timestamp>-google-maps-leads-<slug>.zip
        containing the CSV + README-buyer.txt.
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from common import OrderContext, mcp_path, print_done

# Inject the MCP server directory onto sys.path so we can import its modules directly
sys.path.insert(0, str(mcp_path("google-maps")))

from scraper import GoogleMapsScraper  # noqa: E402
from enrichment import WebsiteEnricher  # noqa: E402
from stealth_browser import StealthBrowser  # noqa: E402
from models import Business  # noqa: E402


CSV_COLUMNS = [
    "name", "category", "address", "phone", "website",
    "emails", "phones", "social_links", "rating", "review_count",
    "lead_score", "tech_stack", "meta_description",
    "latitude", "longitude", "maps_url",
]


async def fulfill(niche: str, location: str, count: int, min_rating: float, enrich: bool) -> list[dict]:
    browser = StealthBrowser()
    scraper = GoogleMapsScraper(browser=browser)
    enricher = WebsiteEnricher(browser=browser)
    try:
        businesses = await scraper.search(query=niche, location=location, max_results=count)
        if not businesses:
            return []

        # Backfill missing phone/website from detail page for any lead that's thin
        missing = [(i, b.maps_url) for i, b in enumerate(businesses) if b.maps_url and (not b.phone or not b.website)]
        for start in range(0, len(missing), 3):
            batch = missing[start:start + 3]
            results = await asyncio.gather(
                *(scraper.get_details(maps_url=u) for _, u in batch),
                return_exceptions=True,
            )
            for (idx, _), r in zip(batch, results):
                if isinstance(r, Business) and r.name:
                    businesses[idx] = r

        if enrich:
            urls = [b.website for b in businesses if b.website]
            if urls:
                enriched = await enricher.enrich_batch(urls, max_concurrent=3)
                for b in businesses:
                    if b.website and b.website in enriched:
                        d = enriched[b.website]
                        b.emails = d.get("emails", [])
                        b.phones = d.get("phones", [])
                        b.social_links = d.get("social_links", {})
                        b.tech_stack = d.get("tech_stack", [])
                        b.meta_description = d.get("meta_description", "")

        for b in businesses:
            b.calculate_lead_score()

        if min_rating > 0:
            businesses = [b for b in businesses if b.rating >= min_rating]

        businesses.sort(key=lambda b: b.lead_score, reverse=True)
        return [b.to_dict() for b in businesses]
    finally:
        await scraper.cleanup()


def main() -> None:
    ap = argparse.ArgumentParser(description="Google Maps lead-gen fulfillment")
    ap.add_argument("--niche", required=True, help='Business type (e.g. "dentist", "restaurant")')
    ap.add_argument("--location", required=True, help='City / area (e.g. "Dubai Marina")')
    ap.add_argument("--count", type=int, default=50, help="Number of leads (default 50, max 60)")
    ap.add_argument("--min-rating", type=float, default=0.0, help="Minimum Google rating filter (default 0 = no filter)")
    ap.add_argument("--no-enrich", action="store_true", help="Skip website enrichment (much faster, fewer emails)")
    args = ap.parse_args()

    order = OrderContext(
        product="google-maps-leads",
        order_label=f"{args.niche}-{args.location}-{args.count}",
        params={
            "niche": args.niche,
            "location": args.location,
            "count": args.count,
            "min_rating": args.min_rating,
            "enrichment": not args.no_enrich,
        },
    )

    print(f"[start] {order.order_id}")
    print(f"        searching '{args.niche}' in '{args.location}' (up to {args.count} results)...")

    rows = asyncio.run(fulfill(
        niche=args.niche,
        location=args.location,
        count=min(args.count, 60),
        min_rating=args.min_rating,
        enrich=not args.no_enrich,
    ))

    if not rows:
        print("[warn] no results returned — delivering empty CSV with note.")

    order.write_csv(rows, columns=CSV_COLUMNS)

    # Summary stats
    total = len(rows)
    with_email = sum(1 for r in rows if r.get("emails"))
    with_phone = sum(1 for r in rows if r.get("phone") or r.get("phones"))
    with_website = sum(1 for r in rows if r.get("website"))
    avg_score = round(sum(r.get("lead_score", 0) for r in rows) / max(total, 1), 1)
    high_quality = sum(1 for r in rows if r.get("lead_score", 0) >= 60)

    summary = (
        f"Niche:        {args.niche}\n"
        f"Location:     {args.location}\n"
        f"Leads:        {total}\n"
        f"With email:   {with_email} ({round(100 * with_email / max(total, 1))}%)\n"
        f"With phone:   {with_phone} ({round(100 * with_phone / max(total, 1))}%)\n"
        f"With website: {with_website} ({round(100 * with_website / max(total, 1))}%)\n"
        f"Avg score:    {avg_score}/100\n"
        f"High quality (>= 60): {high_quality}\n\n"
        "Rows are sorted by lead score (highest first). Score weights email\n"
        "presence, phone, website, social links, and Google rating. Open the\n"
        "CSV in Excel, Google Sheets, or your CRM — it's UTF-8 with BOM so\n"
        "Excel handles it natively."
    )

    disclaimers = [
        "Data scraped from public Google Maps listings on delivery date.",
        "Emails are harvested from public website pages — not guaranteed valid.",
        "Always comply with local laws (GDPR, CAN-SPAM, UAE consent) before outreach.",
        "If a lead opts out or bounces, remove them from future campaigns.",
    ]

    order.write_readme(
        product_title=f"Google Maps Lead List — {args.niche.title()} in {args.location}",
        summary=summary,
        disclaimers=disclaimers,
    )
    zip_path = order.finalize()
    print_done(order, zip_path)


if __name__ == "__main__":
    main()
