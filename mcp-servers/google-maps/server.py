"""
Google Maps Extractor MCP Server

Extract business listings, details, reviews, and enriched leads from Google Maps.

Tools:
  - search_businesses: Search for businesses by query and location
  - get_business_details: Get full details for a specific business
  - get_reviews: Get reviews for a business
  - find_leads: Search + enrich with emails/socials/phone (lead generation)
  - generate_lead_report: Full pipeline — Maps + website enrichment + SERP + LinkedIn
  - export_leads: Export last results to CSV file

Run:
  python server.py
"""

import os
import sys
import json
import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from scraper import GoogleMapsScraper
from enrichment import WebsiteEnricher
from export import leads_to_csv, leads_to_csv_string, leads_to_json
from stealth_browser import StealthBrowser
from models import Business

logger = logging.getLogger(__name__)

# Cross-server imports (optional — graceful if not available)
_serp_available = False
_linkedin_available = False

SERP_PATH = os.path.join(os.path.dirname(__file__), "..", "serp-scraper")
LINKEDIN_PATH = os.path.join(os.path.dirname(__file__), "..", "linkedin")


@dataclass
class AppContext:
    scraper: GoogleMapsScraper
    enricher: WebsiteEnricher
    browser: StealthBrowser
    # Stores last find_leads/generate_lead_report results for export
    last_leads: list


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    browser = StealthBrowser()
    scraper = GoogleMapsScraper(browser=browser)
    enricher = WebsiteEnricher(browser=browser)
    try:
        yield AppContext(
            scraper=scraper,
            enricher=enricher,
            browser=browser,
            last_leads=[],
        )
    finally:
        await scraper.cleanup()


mcp = FastMCP(
    "Google Maps Extractor",
    instructions=(
        "Extract business data from Google Maps — listings, contact info, "
        "reviews, and ratings. Best-in-class lead generation with email "
        "enrichment, social links, and lead scoring.\n\n"
        "When the user asks to find businesses or generate leads:\n"
        "1. Ask what type of business and location if not specified\n"
        "2. Use find_leads for enriched results with emails + scoring\n"
        "3. Use generate_lead_report for the full pipeline (+ SERP + LinkedIn)\n"
        "4. Use export_leads to save results as CSV\n\n"
        "For basic lookups without enrichment:\n"
        "- search_businesses: quick listing scan\n"
        "- get_business_details: single business deep-dive\n"
        "- get_reviews: customer sentiment analysis\n\n"
        "All data is scraped live — never cached. Lead scores (0-100) "
        "rank results by data completeness and quality."
    ),
    lifespan=app_lifespan,
)


# ─── Basic tools (unchanged) ───


@mcp.tool()
async def search_businesses(
    query: str,
    location: str = "",
    max_results: int = 20,
) -> str:
    """Search Google Maps for businesses (no enrichment).

    Args:
        query: What to search for (e.g. "restaurants", "plumbers", "dentists")
        location: Location to search in (e.g. "Dubai Marina", "New York")
        max_results: Maximum number of results (default 20, max 60)

    Returns:
        JSON array of business listings with name, rating, address, category
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    max_results = min(max_results, 60)

    businesses = await ctx.scraper.search(
        query=query, location=location, max_results=max_results,
    )

    if not businesses:
        return json.dumps({"results": [], "message": "No businesses found"})

    return json.dumps(
        {
            "results": [b.to_dict() for b in businesses],
            "count": len(businesses),
            "query": f"{query} {location}".strip(),
        },
        indent=2,
    )


@mcp.tool()
async def get_business_details(
    maps_url: str = "",
    place_id: str = "",
) -> str:
    """Get detailed information about a specific business.

    Args:
        maps_url: Google Maps URL for the business
        place_id: Google Place ID

    Returns:
        JSON with full business details: name, address, phone, website,
        rating, reviews count, category, coordinates
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    business = await ctx.scraper.get_details(
        place_id=place_id, maps_url=maps_url,
    )

    if not business:
        return json.dumps({"error": "Could not fetch business details"})

    return json.dumps(business.to_dict(), indent=2)


@mcp.tool()
async def get_reviews(
    maps_url: str = "",
    place_id: str = "",
    max_reviews: int = 20,
    sort_by: str = "newest",
) -> str:
    """Get reviews for a business.

    Args:
        maps_url: Google Maps URL for the business
        place_id: Google Place ID
        max_reviews: Maximum reviews to fetch (default 20, max 100)
        sort_by: Sort order — "newest", "highest", "lowest", "relevant"

    Returns:
        JSON array of reviews with author, rating, text, date
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    max_reviews = min(max_reviews, 100)

    reviews = await ctx.scraper.get_reviews(
        place_id=place_id, maps_url=maps_url,
        max_reviews=max_reviews, sort_by=sort_by,
    )

    return json.dumps(
        {"reviews": [r.to_dict() for r in reviews], "count": len(reviews), "sort": sort_by},
        indent=2,
    )


# ─── Lead generation (the differentiator) ───


@mcp.tool()
async def find_leads(
    query: str,
    location: str = "",
    max_results: int = 20,
    enrich: bool = True,
    min_rating: float = 0.0,
) -> str:
    """Find business leads with enriched contact information.

    Pipeline: Google Maps search → detail extraction → website enrichment
    → email/phone/social discovery → lead scoring

    Args:
        query: Business type (e.g. "real estate agencies", "restaurants")
        location: Location (e.g. "Dubai", "New York")
        max_results: Maximum leads (default 20, max 40)
        enrich: Scrape websites for emails/socials (default True)
        min_rating: Minimum Google rating filter (0.0 = no filter)

    Returns:
        JSON array of scored leads with emails, phones, socials, lead_score
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    max_results = min(max_results, 40)

    # Step 1: Search Google Maps
    businesses = await ctx.scraper.search(
        query=query, location=location, max_results=max_results,
    )

    if not businesses:
        return json.dumps({"leads": [], "message": "No businesses found"})

    # Step 2: Get details for businesses missing phone/website
    details_tasks = []
    for i, biz in enumerate(businesses):
        if biz.maps_url and (not biz.phone or not biz.website):
            details_tasks.append((i, biz.maps_url))

    # Fetch details concurrently (batches of 3)
    for batch_start in range(0, len(details_tasks), 3):
        batch = details_tasks[batch_start:batch_start + 3]
        results = await asyncio.gather(*[
            ctx.scraper.get_details(maps_url=url) for _, url in batch
        ], return_exceptions=True)
        for (idx, _), result in zip(batch, results):
            if isinstance(result, Business) and result.name:
                businesses[idx] = result

    # Step 3: Enrich websites for emails/socials
    if enrich:
        website_urls = [biz.website for biz in businesses if biz.website]
        if website_urls:
            enrichment_data = await ctx.enricher.enrich_batch(
                website_urls, max_concurrent=3,
            )
            for biz in businesses:
                if biz.website and biz.website in enrichment_data:
                    data = enrichment_data[biz.website]
                    biz.emails = data.get("emails", [])
                    biz.phones = data.get("phones", [])
                    biz.social_links = data.get("social_links", {})
                    biz.tech_stack = data.get("tech_stack", [])
                    biz.meta_description = data.get("meta_description", "")

    # Step 4: Score and filter
    for biz in businesses:
        biz.calculate_lead_score()

    if min_rating > 0:
        businesses = [b for b in businesses if b.rating >= min_rating]

    # Sort by lead score (highest first)
    businesses.sort(key=lambda b: b.lead_score, reverse=True)

    # Store for export
    ctx.last_leads = businesses

    return json.dumps(
        {
            "leads": [b.to_dict() for b in businesses],
            "count": len(businesses),
            "query": f"{query} {location}".strip(),
            "enriched": enrich,
            "avg_score": round(
                sum(b.lead_score for b in businesses) / max(len(businesses), 1), 1
            ),
        },
        indent=2,
    )


@mcp.tool()
async def generate_lead_report(
    query: str,
    location: str = "",
    max_results: int = 15,
    check_seo: bool = True,
    check_linkedin: bool = False,
) -> str:
    """Full lead generation pipeline — the most comprehensive tool.

    Pipeline:
      1. Google Maps: search + details
      2. Website enrichment: emails, phones, socials, tech stack
      3. SERP check (optional): how well they rank on Google
      4. LinkedIn (optional): company info
      5. Lead scoring + ranking

    Args:
        query: Business type (e.g. "plumbers", "dental clinics")
        location: Location (e.g. "Miami", "London")
        max_results: Maximum leads (default 15, max 25 — more = slower)
        check_seo: Check their Google ranking (default True)
        check_linkedin: Look up LinkedIn company pages (default False)

    Returns:
        JSON lead report with scored, enriched leads + insights
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    max_results = min(max_results, 25)

    report = {
        "query": f"{query} {location}".strip(),
        "pipeline": ["google_maps", "website_enrichment"],
        "leads": [],
        "insights": {},
    }

    # Step 1: Google Maps search + details
    businesses = await ctx.scraper.search(
        query=query, location=location, max_results=max_results,
    )

    if not businesses:
        report["leads"] = []
        report["insights"]["message"] = "No businesses found"
        return json.dumps(report, indent=2)

    # Get details concurrently
    async def _get_detail(biz):
        if biz.maps_url and (not biz.phone or not biz.website):
            try:
                detailed = await ctx.scraper.get_details(maps_url=biz.maps_url)
                if detailed and detailed.name:
                    return detailed
            except Exception:
                pass
        return biz

    businesses = await asyncio.gather(*[_get_detail(b) for b in businesses])
    businesses = list(businesses)

    # Step 2: Website enrichment (concurrent)
    website_urls = [biz.website for biz in businesses if biz.website]
    if website_urls:
        enrichment_data = await ctx.enricher.enrich_batch(
            website_urls, max_concurrent=3,
        )
        for biz in businesses:
            if biz.website and biz.website in enrichment_data:
                data = enrichment_data[biz.website]
                biz.emails = data.get("emails", [])
                biz.phones = data.get("phones", [])
                biz.social_links = data.get("social_links", {})
                biz.tech_stack = data.get("tech_stack", [])
                biz.meta_description = data.get("meta_description", "")

    # Step 3: SERP check (optional)
    serp_data = {}
    if check_seo and os.path.exists(SERP_PATH):
        report["pipeline"].append("serp_check")
        try:
            sys.path.insert(0, SERP_PATH)
            from scraper import SerpScraper
            from stealth_browser import StealthBrowser as SerpBrowser

            serp_browser = SerpBrowser()
            serp_scraper = SerpScraper(browser=serp_browser)

            try:
                # Check how top leads rank for the search query
                serp_result = await serp_scraper.search_google(
                    query=f"{query} {location}".strip(),
                    num_results=20,
                )

                # Map domains to ranking positions
                for organic in serp_result.organic:
                    domain = organic.domain.lower().replace("www.", "")
                    serp_data[domain] = {
                        "position": organic.position,
                        "serp_title": organic.title,
                    }
            finally:
                await serp_scraper.cleanup()
        except Exception as e:
            logger.warning(f"SERP check failed: {e}")

    # Step 4: LinkedIn company lookup (optional)
    linkedin_data = {}
    if check_linkedin and os.path.exists(LINKEDIN_PATH):
        report["pipeline"].append("linkedin")
        try:
            sys.path.insert(0, LINKEDIN_PATH)
            from scraper import LinkedInScraper
            from stealth_browser import StealthBrowser as LiBrowser

            li_browser = LiBrowser()
            li_scraper = LinkedInScraper(browser=li_browser)

            try:
                for biz in businesses[:10]:  # Limit to top 10 to avoid rate limits
                    li_url = biz.social_links.get("linkedin", "")
                    if li_url and "/company/" in li_url:
                        try:
                            company = await li_scraper.get_company(company_url=li_url)
                            if company and company.name:
                                linkedin_data[biz.name] = company.to_dict()
                        except Exception:
                            pass
                        await asyncio.sleep(2)  # Rate limit
            finally:
                await li_scraper.cleanup()
        except Exception as e:
            logger.warning(f"LinkedIn check failed: {e}")

    # Step 5: Merge cross-server data + score
    for biz in businesses:
        # Add SERP ranking if found
        if biz.website and serp_data:
            biz_domain = urlparse_domain(biz.website)
            if biz_domain in serp_data:
                biz_dict = biz.to_dict()
                biz_dict["serp_ranking"] = serp_data[biz_domain]

        # Add LinkedIn data if found
        if biz.name in linkedin_data:
            biz_dict = biz.to_dict()
            biz_dict["linkedin_company"] = linkedin_data[biz.name]

        biz.calculate_lead_score()

    # Sort by score
    businesses.sort(key=lambda b: b.lead_score, reverse=True)

    # Store for export
    ctx.last_leads = businesses

    # Generate insights
    scored = [b.lead_score for b in businesses]
    with_email = sum(1 for b in businesses if b.emails)
    with_phone = sum(1 for b in businesses if b.phone or b.phones)
    with_website = sum(1 for b in businesses if b.website)

    report["leads"] = [b.to_dict() for b in businesses]
    report["count"] = len(businesses)
    report["insights"] = {
        "avg_lead_score": round(sum(scored) / max(len(scored), 1), 1),
        "top_score": max(scored) if scored else 0,
        "with_email": f"{with_email}/{len(businesses)}",
        "with_phone": f"{with_phone}/{len(businesses)}",
        "with_website": f"{with_website}/{len(businesses)}",
        "serp_matches": len(serp_data) if serp_data else "skipped",
        "linkedin_matches": len(linkedin_data) if linkedin_data else "skipped",
    }

    return json.dumps(report, indent=2)


@mcp.tool()
async def export_leads(
    format: str = "csv",
    filepath: str = "",
) -> str:
    """Export the most recent lead results to a file.

    Call find_leads or generate_lead_report first, then export.

    Args:
        format: "csv" or "json" (default "csv")
        filepath: Custom output path (optional, auto-generates if empty)

    Returns:
        Path to the exported file, or CSV content if no file path
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    if not ctx.last_leads:
        return json.dumps({
            "error": "No leads to export. Run find_leads or generate_lead_report first.",
        })

    if format == "json":
        path = leads_to_json(ctx.last_leads, filepath)
        return json.dumps({
            "exported": path,
            "format": "json",
            "count": len(ctx.last_leads),
        })
    else:
        if filepath:
            path = leads_to_csv(ctx.last_leads, filepath)
            return json.dumps({
                "exported": path,
                "format": "csv",
                "count": len(ctx.last_leads),
            })
        else:
            # Return CSV content + save to file
            path = leads_to_csv(ctx.last_leads)
            csv_content = leads_to_csv_string(ctx.last_leads)
            return json.dumps({
                "exported": path,
                "format": "csv",
                "count": len(ctx.last_leads),
                "preview": csv_content[:2000],
            })


# ─── Helpers ───


def urlparse_domain(url: str) -> str:
    """Extract clean domain from URL."""
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


# ─── Resources ───


@mcp.resource("maps://config")
def get_config() -> str:
    """Current server configuration."""
    serp_ok = os.path.exists(SERP_PATH)
    li_ok = os.path.exists(LINKEDIN_PATH)

    return json.dumps(
        {
            "server": "Google Maps Extractor",
            "version": "0.2.0",
            "capabilities": [
                "search_businesses",
                "get_business_details",
                "get_reviews",
                "find_leads (with enrichment)",
                "generate_lead_report (full pipeline)",
                "export_leads (CSV/JSON)",
            ],
            "cross_server": {
                "serp_scraper": "available" if serp_ok else "not_found",
                "linkedin": "available" if li_ok else "not_found",
            },
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
