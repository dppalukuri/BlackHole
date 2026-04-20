"""SERP scraper fulfillment script.

Sellable product: "SEO competitor report — top 100 results + PAA + ads — $29"
Buyers: freelance SEOs, marketing consultants, indie founders doing keyword research.

CLI:
    python serp_report.py --query "best crm software 2026" --depth 50
    python serp_report.py --query "indian mutual funds" --country in --language en --depth 100

Output: orders/order-<timestamp>-serp-report-<slug>.zip
        containing an organic-results CSV, an ads CSV, and a PAA/related JSON.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from common import OrderContext, mcp_path, print_done

sys.path.insert(0, str(mcp_path("serp-scraper")))

from scraper import SerpScraper  # noqa: E402


ORGANIC_COLS = ["position", "title", "url", "domain", "snippet", "date", "sitelinks"]
ADS_COLS = ["position", "title", "url", "domain", "description", "is_top"]


async def fulfill(query: str, depth: int, language: str, country: str) -> dict:
    scraper = SerpScraper()
    try:
        # depth > 10 → loop through pages; SERP returns up to ~10 organic per page
        organic: list = []
        ads: list = []
        featured = None
        paa: list = []
        related: list = []
        total_label = ""

        per_page = 10
        pages = max(1, (depth + per_page - 1) // per_page)
        for page in range(1, pages + 1):
            result = await scraper.search_google(
                query=query, num_results=per_page, page=page,
                language=language, country=country, headed=False,
            )
            if page == 1:
                featured = result.featured_snippet
                paa = result.people_also_ask or []
                related = result.related_searches or []
                total_label = result.total_results or ""
            organic.extend(result.organic or [])
            ads.extend(result.ads or [])
            if len(organic) >= depth:
                break

        organic = organic[:depth]
        return {
            "query": query, "total_results": total_label,
            "organic": [o.to_dict() for o in organic],
            "ads": [a.to_dict() for a in ads],
            "featured_snippet": featured.to_dict() if featured else None,
            "people_also_ask": [p.to_dict() for p in paa],
            "related_searches": related,
        }
    finally:
        try:
            await scraper.cleanup()  # type: ignore[attr-defined]
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Google SERP report fulfillment")
    ap.add_argument("--query", required=True, help='Search query')
    ap.add_argument("--depth", type=int, default=50, help="Max organic rows to collect (default 50)")
    ap.add_argument("--language", default="en")
    ap.add_argument("--country", default="", help='e.g. "us", "in", "ae"')
    args = ap.parse_args()

    order = OrderContext(
        product="serp-report",
        order_label=args.query,
        params={
            "query": args.query, "depth": args.depth,
            "language": args.language, "country": args.country or "(auto)",
        },
    )

    print(f"[start] {order.order_id}")
    print(f"        fetching top-{args.depth} Google results for '{args.query}'...")

    data = asyncio.run(fulfill(
        query=args.query, depth=args.depth,
        language=args.language, country=args.country,
    ))

    # Write organic CSV
    order.write_csv(
        data["organic"], columns=ORGANIC_COLS,
        filename=f"organic-{order.stamp}.csv",
    )

    # Ads CSV (if any) — write to work_dir manually
    if data["ads"]:
        import csv as _csv
        ads_path = order.work_dir / f"ads-{order.stamp}.csv"
        with open(ads_path, "w", encoding="utf-8-sig", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=ADS_COLS, extrasaction="ignore")
            w.writeheader()
            for r in data["ads"]:
                w.writerow(r)

    # Features (PAA, related, featured snippet) as JSON side file
    features_path = order.work_dir / "features.json"
    features_path.write_text(
        json.dumps(
            {
                "query": data["query"],
                "total_results_label": data["total_results"],
                "featured_snippet": data["featured_snippet"],
                "people_also_ask": data["people_also_ask"],
                "related_searches": data["related_searches"],
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Summary
    unique_domains = {r["domain"] for r in data["organic"] if r.get("domain")}
    summary = (
        f"Query:            {args.query}\n"
        f"Organic results:  {len(data['organic'])}\n"
        f"Unique domains:   {len(unique_domains)}\n"
        f"Ad placements:    {len(data['ads'])}\n"
        f"Featured snippet: {'yes' if data['featured_snippet'] else 'no'}\n"
        f"People Also Ask:  {len(data['people_also_ask'])}\n"
        f"Related searches: {len(data['related_searches'])}\n"
        f"Total-results lbl: {data['total_results'] or 'n/a'}\n\n"
        "Files in this delivery:\n"
        f"  - organic-{order.stamp}.csv    → ranked organic results\n"
        f"  - ads-{order.stamp}.csv        → paid ads on page 1 (if any)\n"
        "  - features.json              → featured snippet, PAA, related searches\n\n"
        "Use this for: competitor mapping, keyword intent clustering, PAA-driven\n"
        "content briefs, SERP-feature opportunity analysis."
    )
    disclaimers = [
        "Google SERP changes by geo, language, and personalisation — your view may differ.",
        "Ads shown only from the first page; Google shows ~0–4 top + 0–3 bottom depending on query.",
        "Organic positions include sitelinks — position counting follows Google's DOM order, not adjusted.",
    ]

    order.write_readme(
        product_title=f"SERP Report — '{args.query}'",
        summary=summary, disclaimers=disclaimers,
    )
    zip_path = order.finalize()
    print_done(order, zip_path)


if __name__ == "__main__":
    main()
