"""
UAE Real Estate MCP Server

Provides AI assistants with access to UAE property data from
Bayut, Dubizzle, and PropertyFinder.

Tools:
  - search_properties: Search listings across all platforms
  - get_property_details: Get detailed info for a specific listing
  - calculate_rental_yield: Calculate ROI and yield metrics
  - get_market_snapshot: Area-level statistics and analytics
  - compare_properties: Side-by-side property comparison

Run:
  uv run server.py
  # or
  python server.py
"""

import os
import sys
import json
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from scrapers import UAEPropertyAggregator
from analytics import (
    calculate_rental_yield as calc_yield,
    calculate_area_stats,
    format_yield_report,
    format_area_report,
    compare_properties as compare_props,
)


@dataclass
class AppContext:
    aggregator: UAEPropertyAggregator


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    aggregator = UAEPropertyAggregator()
    try:
        yield AppContext(aggregator=aggregator)
    finally:
        await aggregator.cleanup()


mcp = FastMCP(
    "UAE Real Estate",
    instructions=(
        "Live UAE property search across Bayut, Dubizzle, and PropertyFinder. "
        "Data is fetched on-the-fly from real listings — never cached or pre-scraped.\n\n"
        "IMPORTANT WORKFLOW: When a user asks a property question, DO NOT search immediately. "
        "First clarify their requirements by asking about:\n"
        "  - Purpose: Are they looking to buy or rent?\n"
        "  - Property type: Apartment, villa, townhouse, penthouse, studio?\n"
        "  - Bedrooms: Studio, 1BHK, 2BHK, 3BHK, etc.?\n"
        "  - Budget range: What's their min/max price in AED?\n"
        "  - Location: Which area/community? (Dubai Marina, JVC, Downtown, etc.)\n"
        "Only ask about filters that weren't already specified in the question. "
        "Once filters are confirmed, call search_properties with the exact parameters.\n\n"
        "Example: If user asks 'houses in JVC under 55000 AED' — clarify if they mean "
        "for-rent or for-sale, what type (villa/townhouse/apartment), and how many bedrooms. "
        "Then search with those specific filters applied.\n\n"
        "Supported locations include: Dubai Marina, Downtown Dubai, Business Bay, JBR, "
        "Palm Jumeirah, Dubai Hills Estate, Arabian Ranches, JVC, JVT, JLT, DIFC, "
        "Dubai Creek Harbour, Al Barsha, Motor City, Sports City, Damac Hills, "
        "Silicon Oasis, Mirdif, Al Furjan, Town Square, Emaar Beachfront, and 50+ more."
    ),
    lifespan=app_lifespan,
)


# ─── TOOLS ─────────────────────────────────────────────────────────────────────


@mcp.tool()
async def search_properties(
    location: str,
    purpose: str = "for-sale",
    property_type: str = "",
    min_price: int = 0,
    max_price: int = 0,
    bedrooms: int = -1,
    source: str = "all",
    page: int = 1,
) -> str:
    """
    Search for properties across UAE real estate platforms (live, on-the-fly).

    Scrapes real listings from Bayut, Dubizzle, and PropertyFinder in real time.
    Always confirm filters with the user before calling this tool.

    Args:
        location: Area or community name (e.g., "Dubai Marina", "Downtown Dubai",
                  "Palm Jumeirah", "JVC", "Business Bay", "JLT", "Dubai Hills",
                  "Arabian Ranches", "Silicon Oasis", "DIFC", "Creek Harbour")
        purpose: "for-sale" or "for-rent"
        property_type: "apartment", "villa", "townhouse", "penthouse", "duplex",
                       or "" for all types
        min_price: Minimum price in AED (0 for no minimum)
        max_price: Maximum price in AED (0 for no maximum)
        bedrooms: Number of bedrooms (-1 for any, 0 for studio, 1-5 for specific)
        source: "bayut", "dubizzle", "propertyfinder", or "all"
        page: Page number for pagination (starts at 1)

    Returns:
        Live property listings with price, specs, location, and source details.
    """
    ctx = mcp.get_context()
    aggregator = ctx.request_context.lifespan_context.aggregator

    results, errors = await aggregator.search(
        location=location,
        purpose=purpose,
        property_type=property_type,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        source=source,
        page=page,
    )

    if not results and errors:
        return f"No results found. Errors:\n" + "\n".join(errors)

    if not results:
        return f"No properties found matching your criteria in {location}."

    # Format results
    lines = [f"Found {len(results)} properties in {location} ({purpose}):\n"]

    for i, prop in enumerate(results, 1):
        lines.append(f"--- Property {i} ---")
        lines.append(prop.summary())
        lines.append("")

    if errors:
        lines.append("Note - some sources had errors:")
        for e in errors:
            lines.append(f"  - {e}")

    return "\n".join(lines)


@mcp.tool()
async def get_property_details(
    property_id: str,
    source: str,
) -> str:
    """
    Get detailed information about a specific property listing.

    Args:
        property_id: The property ID (from search results)
        source: Which platform - "bayut", "dubizzle", or "propertyfinder"

    Returns:
        Detailed property information including description, amenities, and agent details.
    """
    ctx = mcp.get_context()
    aggregator = ctx.request_context.lifespan_context.aggregator

    try:
        prop = await aggregator.get_details(property_id, source)
        if not prop:
            return f"Property {property_id} not found on {source}."

        details = prop.to_dict()
        lines = [f"PROPERTY DETAILS ({source})", "=" * 40, ""]

        field_labels = {
            "title": "Title",
            "price": "Price (AED)",
            "property_type": "Type",
            "bedrooms": "Bedrooms",
            "bathrooms": "Bathrooms",
            "area_sqft": "Area (sqft)",
            "price_per_sqft": "Price/sqft (AED)",
            "location": "Location",
            "emirate": "Emirate",
            "community": "Community",
            "sub_community": "Sub-community",
            "furnishing": "Furnishing",
            "completion_status": "Completion",
            "agent_name": "Agent",
            "agency_name": "Agency",
            "reference": "Reference",
            "url": "URL",
        }

        for key, label in field_labels.items():
            val = details.get(key)
            if val:
                if isinstance(val, float):
                    lines.append(f"  {label}: {val:,.0f}")
                else:
                    lines.append(f"  {label}: {val}")

        if details.get("amenities"):
            lines.append(f"\n  Amenities: {', '.join(details['amenities'][:15])}")

        if details.get("description"):
            lines.append(f"\n  Description:\n  {details['description']}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error fetching details: {e}"


@mcp.tool()
async def calculate_rental_yield(
    purchase_price: float,
    annual_rent: float,
    service_charge: float = 0,
    maintenance_pct: float = 0,
    vacancy_pct: float = 5,
) -> str:
    """
    Calculate rental yield and ROI for a UAE property investment.

    Includes UAE-specific costs: DLD fee (4%), agency fee (2%), service charges.

    Args:
        purchase_price: Purchase price in AED
        annual_rent: Expected annual rental income in AED
        service_charge: Annual service charge in AED (0 if unknown)
        maintenance_pct: Maintenance cost as percentage of rent (default 0)
        vacancy_pct: Expected vacancy rate percentage (default 5%)

    Returns:
        Comprehensive yield analysis including gross yield, net yield, true yield
        (including acquisition costs), monthly net income, and break-even period.
    """
    result = calc_yield(
        purchase_price=purchase_price,
        annual_rent=annual_rent,
        service_charge=service_charge,
        maintenance_pct=maintenance_pct,
        vacancy_pct=vacancy_pct,
    )
    return format_yield_report(result)


@mcp.tool()
async def get_market_snapshot(
    location: str,
    purpose: str = "for-sale",
    property_type: str = "apartment",
    source: str = "all",
) -> str:
    """
    Get market statistics for a specific area - average prices, price per sqft,
    breakdown by bedroom type, and listing volume.

    Args:
        location: Area name (e.g., "Dubai Marina", "Downtown Dubai", "JVC")
        purpose: "for-sale" or "for-rent"
        property_type: "apartment", "villa", "townhouse", or "" for all
        source: "bayut", "dubizzle", "propertyfinder", or "all"

    Returns:
        Market statistics including average prices, price ranges, price per sqft,
        and breakdown by bedroom count.
    """
    ctx = mcp.get_context()
    aggregator = ctx.request_context.lifespan_context.aggregator

    results, errors = await aggregator.search(
        location=location,
        purpose=purpose,
        property_type=property_type,
        source=source,
    )

    if not results:
        msg = f"No data available for {location}."
        if errors:
            msg += " Errors: " + "; ".join(errors)
        return msg

    stats = calculate_area_stats(results)
    report = format_area_report(stats, f"{location} - {purpose} {property_type}s")

    if errors:
        report += "\n\nNote: " + "; ".join(errors)

    return report


@mcp.tool()
async def compare_areas(
    areas: list[str],
    purpose: str = "for-sale",
    property_type: str = "apartment",
    source: str = "all",
) -> str:
    """
    Compare multiple areas by price, price per sqft, and listing volume.

    Args:
        areas: List of area names to compare (e.g., ["Dubai Marina", "JVC", "Business Bay"])
        purpose: "for-sale" or "for-rent"
        property_type: "apartment", "villa", or "" for all
        source: "bayut", "dubizzle", "propertyfinder", or "all"

    Returns:
        Comparison table showing average prices, price per sqft, and volume for each area.
    """
    ctx = mcp.get_context()
    aggregator = ctx.request_context.lifespan_context.aggregator

    area_stats = {}
    for area in areas:
        results, _ = await aggregator.search(
            location=area,
            purpose=purpose,
            property_type=property_type,
            source=source,
        )
        if results:
            area_stats[area] = calculate_area_stats(results)

    if not area_stats:
        return "No data available for any of the specified areas."

    # Build comparison table
    lines = [
        f"AREA COMPARISON - {purpose} {property_type}s",
        "=" * 80,
        "",
        f"{'Area':<25} {'Listings':>8} {'Avg Price':>14} {'Avg/sqft':>12} {'Price Range':>25}",
        "-" * 80,
    ]

    for area, stats in area_stats.items():
        lines.append(
            f"{area:<25} {stats['total_listings']:>8} "
            f"AED {stats['price']['average']:>10,.0f} "
            f"AED {stats['price_per_sqft']['average']:>8,.0f} "
            f"AED {stats['price']['min']:,.0f} - {stats['price']['max']:,.0f}"
        )

    # Add bedroom breakdown
    lines.append("")
    lines.append("BY BEDROOM TYPE (Average Price)")
    lines.append("-" * 80)

    all_bed_types = set()
    for stats in area_stats.values():
        all_bed_types.update(stats.get("by_bedroom", {}).keys())

    header = f"{'Area':<25}" + "".join(f"{bt:>14}" for bt in sorted(all_bed_types))
    lines.append(header)

    for area, stats in area_stats.items():
        beds = stats.get("by_bedroom", {})
        row = f"{area:<25}"
        for bt in sorted(all_bed_types):
            if bt in beds:
                row += f"AED {beds[bt]['avg_price']:>10,.0f}"
            else:
                row += f"{'N/A':>14}"
        lines.append(row)

    return "\n".join(lines)


@mcp.tool()
async def warm_up_bayut() -> str:
    """
    Solve Bayut CAPTCHA interactively to enable Bayut searches.

    Opens a headed browser window where the user can solve the hCaptcha.
    After solving, session cookies and Algolia keys are cached so that
    subsequent Bayut searches work without CAPTCHA.

    Only needed once per session — call this if Bayut searches fail with
    CAPTCHA errors.

    Returns:
        Status message indicating whether the warm-up was successful.
    """
    ctx = mcp.get_context()
    aggregator = ctx.request_context.lifespan_context.aggregator
    return await aggregator.bayut.warm_up()


@mcp.tool()
async def refresh_locations(
    site: str = "all",
) -> str:
    """
    Discover and update location slugs from real estate sites.

    Scrapes the sites to find new communities and areas that may have been
    added since the last update. Run this periodically to keep location
    data current.

    Args:
        site: "dubizzle", "bayut", "propertyfinder", or "all"

    Returns:
        Summary of discovered locations and any new additions.
    """
    from slug_discovery import run_discovery
    import slug_registry
    import io
    from contextlib import redirect_stdout

    sites = None if site == "all" else [site]

    # Capture output from discovery
    output = io.StringIO()
    with redirect_stdout(output):
        await run_discovery(sites=sites)

    # Reload the registry so scrapers pick up new slugs
    slug_registry.reload()

    return output.getvalue()


# ─── RESOURCES ─────────────────────────────────────────────────────────────────


@mcp.resource("uae-realestate://locations")
def list_locations() -> str:
    """List all searchable locations across all platforms."""
    import slug_registry

    lines = ["Available UAE Locations:", ""]
    lines.append("EMIRATES:")
    emirates = ["dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "fujairah", "umm al quwain"]
    for e in emirates:
        lines.append(f"  - {e.title()}")

    lines.append("\nDUBAI COMMUNITIES (all platforms):")
    # Merge locations from all sites
    all_locs = set()
    for site in ["dubizzle", "bayut", "propertyfinder"]:
        all_locs.update(slug_registry.all_locations(site))
    # Remove emirate-level entries
    communities = sorted(loc for loc in all_locs if loc not in [e.lower() for e in emirates])
    for c in communities:
        lines.append(f"  - {c.title()}")

    updated = slug_registry.last_updated()
    if updated:
        lines.append(f"\nSlugs last updated: {updated}")

    return "\n".join(lines)


@mcp.resource("uae-realestate://help")
def help_text() -> str:
    """Usage guide for the UAE Real Estate MCP server."""
    return """
UAE REAL ESTATE MCP SERVER - USAGE GUIDE

HOW IT WORKS:
  All data is scraped LIVE from real estate platforms when you ask.
  No pre-cached data — results reflect current market listings.

  When a user asks a property question:
  1. Clarify any missing filters (buy/rent, type, bedrooms, budget, area)
  2. Search with the confirmed filters
  3. Present results and offer follow-up analysis

EXAMPLE CONVERSATIONS:
  User: "How many apartments are available in JVC under 500K?"
  → Clarify: buy or rent? any bedroom preference?
  → Then search with confirmed filters

  User: "I want to rent a 2BHK in Dubai Marina, budget 80-120K/year"
  → All filters are clear, search directly

AVAILABLE TOOLS:
  search_properties   - Live search across Bayut, Dubizzle, PropertyFinder
  get_property_details - Detailed info for a specific listing
  calculate_rental_yield - ROI calculator with UAE-specific costs
  get_market_snapshot  - Area-level price statistics
  compare_areas        - Side-by-side area comparison

SUPPORTED PROPERTY TYPES:
  apartment, villa, townhouse, penthouse, duplex, hotel apartment

SUPPORTED LOCATIONS (50+):
  Dubai Marina, Downtown Dubai, Business Bay, JBR, Palm Jumeirah,
  Dubai Hills Estate, Arabian Ranches, JVC, JVT, JLT, DIFC,
  Dubai Creek Harbour, Al Barsha, Motor City, Sports City,
  Damac Hills, Silicon Oasis, Mirdif, Al Furjan, Town Square,
  Emaar Beachfront, Bluewaters, Sobha Hartland, MBR City, and more.

SOURCES:
  - propertyfinder: Most reliable (headless stealth)
  - dubizzle: Headed browser (Incapsula WAF bypass)
  - bayut: Headed browser + session persistence (use warm_up_bayut if CAPTCHA blocks)

NOTES:
  - All prices in AED (1 USD ≈ 3.67 AED)
  - Yield calculations include DLD fee (4%), agency fee (2%)
  - Bedrooms: 0 = studio, -1 = any
""".strip()


# ─── PROMPTS ───────────────────────────────────────────────────────────────────


@mcp.prompt()
def investment_analysis(location: str, budget: str) -> str:
    """Analyze a property investment opportunity in a specific UAE area."""
    return f"""Please help me analyze property investment opportunities in {location} with a budget of AED {budget}.

Steps:
1. Search for properties in {location} within the budget using search_properties
2. Get the market snapshot for the area using get_market_snapshot
3. For the most promising properties, calculate rental yield using calculate_rental_yield
4. Compare with neighboring areas using compare_areas
5. Provide a recommendation with:
   - Best value properties found
   - Expected rental yield
   - Area growth potential
   - Risk factors
   - Final verdict: invest or pass
"""


@mcp.prompt()
def area_comparison(area1: str, area2: str) -> str:
    """Compare two UAE areas for property investment."""
    return f"""Compare {area1} vs {area2} for property investment.

Steps:
1. Get market snapshots for both areas
2. Compare prices, yields, and availability
3. Search for best deals in each area
4. Calculate typical rental yields for each
5. Provide verdict: which area is better for investment and why
"""


# ─── ENTRY POINT ───────────────────────────────────────────────────────────────


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
