"""UAE Real Estate fulfillment script.

Sellable product: "Live property listings for {location} + filters — $49–$199"
Buyers: UAE investors, agents, foreign relocators scouting Dubai/Abu Dhabi.

CLI:
    python uae_properties.py --location "Dubai Marina" --purpose for-sale --min-results 50
    python uae_properties.py --location "Downtown Dubai" --purpose to-rent \
        --bedrooms 2 --max-price 180000 --min-results 30

Output: orders/order-<timestamp>-uae-properties-<slug>.zip
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from common import OrderContext, mcp_path, print_done

sys.path.insert(0, str(mcp_path("uae-realestate")))

from scrapers import UAEPropertyAggregator  # noqa: E402


CSV_COLUMNS = [
    "source", "id", "title", "purpose", "property_type",
    "price", "currency", "price_per_sqft",
    "bedrooms", "bathrooms", "area_sqft",
    "location", "emirate", "community", "sub_community",
    "latitude", "longitude",
    "furnishing", "completion_status",
    "agent_name", "agent_phone", "agency_name",
    "url", "image_url", "listed_date", "reference",
    "amenities", "description",
]


async def fulfill(
    location: str, purpose: str, property_type: str,
    min_price: int, max_price: int, bedrooms: int,
    source: str, min_results: int,
) -> tuple[list[dict], list[str]]:
    agg = UAEPropertyAggregator()
    try:
        results, errors = await agg.search(
            location=location,
            purpose=purpose,
            property_type=property_type,
            min_price=min_price,
            max_price=max_price,
            bedrooms=bedrooms,
            source=source,
            min_results=min_results,
        )
        # Property dataclass → dict
        rows = [p.__dict__ if not hasattr(p, "to_dict") else p.to_dict() for p in results]
        return rows, errors
    finally:
        try:
            await agg.cleanup()
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description="UAE Real Estate fulfillment")
    ap.add_argument("--location", required=True, help='Area (e.g. "Dubai Marina", "Downtown Dubai")')
    ap.add_argument("--purpose", choices=["for-sale", "to-rent"], default="for-sale")
    ap.add_argument("--property-type", default="", help='apartment, villa, townhouse, etc.')
    ap.add_argument("--bedrooms", type=int, default=-1, help="-1 = any, 0 = studio, 1..n")
    ap.add_argument("--min-price", type=int, default=0, help="AED")
    ap.add_argument("--max-price", type=int, default=0, help="AED")
    ap.add_argument("--source", choices=["all", "bayut", "dubizzle", "propertyfinder"], default="all")
    ap.add_argument("--min-results", type=int, default=30)
    args = ap.parse_args()

    label = f"{args.location}-{args.purpose}"
    if args.bedrooms >= 0:
        label += f"-{args.bedrooms}br"
    order = OrderContext(
        product="uae-properties",
        order_label=label,
        params={
            "location": args.location, "purpose": args.purpose,
            "property_type": args.property_type or "(any)",
            "bedrooms": "any" if args.bedrooms < 0 else ("studio" if args.bedrooms == 0 else args.bedrooms),
            "min_price_aed": args.min_price or "(none)", "max_price_aed": args.max_price or "(none)",
            "source": args.source, "min_results": args.min_results,
        },
    )

    print(f"[start] {order.order_id}")
    print(f"        scanning {args.source} for '{args.location}' ({args.purpose})...")

    rows, errors = asyncio.run(fulfill(
        location=args.location, purpose=args.purpose,
        property_type=args.property_type,
        min_price=args.min_price, max_price=args.max_price,
        bedrooms=args.bedrooms, source=args.source,
        min_results=args.min_results,
    ))

    order.write_csv(rows, columns=CSV_COLUMNS)

    total = len(rows)
    by_source = {}
    prices = []
    for r in rows:
        s = r.get("source", "?")
        by_source[s] = by_source.get(s, 0) + 1
        if r.get("price"):
            prices.append(r["price"])
    prices.sort()
    median = prices[len(prices) // 2] if prices else 0
    avg = int(sum(prices) / len(prices)) if prices else 0

    summary_lines = [
        f"Location:     {args.location}",
        f"Purpose:      {args.purpose}",
        f"Total rows:   {total}",
        f"By source:    " + ", ".join(f"{s}={n}" for s, n in sorted(by_source.items())),
        f"Median price: AED {median:,}" if prices else "Median price: n/a",
        f"Avg price:    AED {avg:,}" if prices else "Avg price: n/a",
        "",
        "Rows are deduplicated across Bayut, Dubizzle, and PropertyFinder on",
        "price + bedrooms + area. Open the CSV in Excel or Google Sheets —",
        "UTF-8 with BOM for native Excel compatibility.",
    ]
    if errors:
        summary_lines += ["", "Scraper errors (partial data may still be usable):"]
        summary_lines += [f"  - {e}" for e in errors]

    disclaimers = [
        "Data scraped live on delivery date from public listing pages.",
        "Prices/availability change daily — re-order weekly for fresh data.",
        "Listings may be duplicated across portals; we dedupe by price+beds+area but some may slip through.",
        "Agent contact details are as published — always verify before transacting.",
    ]

    order.write_readme(
        product_title=f"UAE Property Listings — {args.location} ({args.purpose})",
        summary="\n".join(summary_lines),
        disclaimers=disclaimers,
    )
    zip_path = order.finalize()
    print_done(order, zip_path)


if __name__ == "__main__":
    main()
