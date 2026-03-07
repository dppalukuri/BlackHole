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
        "Access UAE property listings from Bayut, Dubizzle, and PropertyFinder. "
        "Search properties, analyze yields, compare areas, and get market insights "
        "across Dubai, Abu Dhabi, Sharjah, and all UAE emirates."
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
    Search for properties across UAE real estate platforms.

    Args:
        location: Area or community name (e.g., "Dubai Marina", "Downtown Dubai", "Palm Jumeirah", "JVC", "Business Bay")
        purpose: "for-sale" or "for-rent"
        property_type: "apartment", "villa", "townhouse", "penthouse", "duplex", or "" for all types
        min_price: Minimum price in AED (0 for no minimum)
        max_price: Maximum price in AED (0 for no maximum)
        bedrooms: Number of bedrooms (-1 for any, 0 for studio, 1-5 for specific)
        source: "bayut", "dubizzle", "propertyfinder", or "all" to search all platforms
        page: Page number for results (starts at 1)

    Returns:
        Property listings with price, specs, location, and source details.
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


# ─── RESOURCES ─────────────────────────────────────────────────────────────────


@mcp.resource("uae-realestate://locations")
def list_locations() -> str:
    """List all searchable locations with their IDs."""
    from scrapers.bayut import LOCATION_IDS as bayut_locs

    lines = ["Available UAE Locations:", ""]
    lines.append("EMIRATES:")
    emirates = ["dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "fujairah", "umm al quwain"]
    for e in emirates:
        lines.append(f"  - {e.title()}")

    lines.append("\nDUBAI COMMUNITIES:")
    communities = sorted(k for k in bayut_locs.keys() if k not in [e.lower() for e in emirates])
    for c in communities:
        lines.append(f"  - {c.title()}")

    return "\n".join(lines)


@mcp.resource("uae-realestate://help")
def help_text() -> str:
    """Usage guide for the UAE Real Estate MCP server."""
    return """
UAE REAL ESTATE MCP SERVER - USAGE GUIDE

SEARCH PROPERTIES:
  Search for apartments in Dubai Marina under 2M AED:
    search_properties(location="Dubai Marina", purpose="for-sale", property_type="apartment", max_price=2000000)

  Find 2-bedroom rentals in JVC:
    search_properties(location="JVC", purpose="for-rent", bedrooms=2)

  Search only Bayut:
    search_properties(location="Downtown Dubai", source="bayut")

YIELD CALCULATOR:
  calculate_rental_yield(purchase_price=1500000, annual_rent=85000, service_charge=15000)

MARKET ANALYSIS:
  get_market_snapshot(location="Business Bay", purpose="for-sale", property_type="apartment")

COMPARE AREAS:
  compare_areas(areas=["Dubai Marina", "JVC", "Business Bay"], purpose="for-rent")

SOURCES:
  - bayut: Requires BAYUT_RAPIDAPI_KEY env var (free at rapidapi.com)
  - dubizzle: Requires Playwright (pip install playwright && playwright install chromium)
  - propertyfinder: Requires Playwright

NOTES:
  - All prices in AED (1 USD = ~3.67 AED)
  - Yield calculations include UAE-specific costs (4% DLD fee, 2% agency fee)
  - Use "all" as source to search across all platforms
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
