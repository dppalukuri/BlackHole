"""
Real estate analytics - yield calculations, area stats, comparisons.
"""

from models import Property


def calculate_rental_yield(
    purchase_price: float,
    annual_rent: float,
    service_charge: float = 0,
    maintenance_pct: float = 0,
    vacancy_pct: float = 5,
) -> dict:
    """
    Calculate gross and net rental yield.

    Args:
        purchase_price: Purchase price in AED
        annual_rent: Annual rental income in AED
        service_charge: Annual service charge in AED
        maintenance_pct: Maintenance cost as % of rent (default 0)
        vacancy_pct: Expected vacancy rate % (default 5)
    """
    if purchase_price <= 0:
        return {"error": "Purchase price must be positive"}

    gross_yield = (annual_rent / purchase_price) * 100

    # Deductions
    vacancy_loss = annual_rent * (vacancy_pct / 100)
    maintenance = annual_rent * (maintenance_pct / 100)
    effective_rent = annual_rent - vacancy_loss - maintenance
    net_income = effective_rent - service_charge
    net_yield = (net_income / purchase_price) * 100

    # DLD fee (4% of purchase price, one-time)
    dld_fee = purchase_price * 0.04
    # Agency fee (2% of purchase price, one-time)
    agency_fee = purchase_price * 0.02
    total_acquisition = purchase_price + dld_fee + agency_fee

    # Yield including acquisition costs
    true_yield = (net_income / total_acquisition) * 100

    # Break-even
    if net_income > 0:
        breakeven_years = total_acquisition / net_income
    else:
        breakeven_years = float("inf")

    return {
        "purchase_price": purchase_price,
        "annual_rent": annual_rent,
        "gross_yield_pct": round(gross_yield, 2),
        "net_income": round(net_income, 2),
        "net_yield_pct": round(net_yield, 2),
        "true_yield_pct": round(true_yield, 2),
        "deductions": {
            "service_charge": service_charge,
            "vacancy_loss": round(vacancy_loss, 2),
            "maintenance": round(maintenance, 2),
        },
        "acquisition_costs": {
            "dld_fee_4pct": round(dld_fee, 2),
            "agency_fee_2pct": round(agency_fee, 2),
            "total_cost": round(total_acquisition, 2),
        },
        "breakeven_years": round(breakeven_years, 1),
        "monthly_net_income": round(net_income / 12, 2),
    }


def calculate_area_stats(properties: list[Property]) -> dict:
    """Calculate aggregate statistics for a list of properties."""
    if not properties:
        return {"error": "No properties to analyze"}

    prices = [p.price for p in properties]
    areas = [p.area_sqft for p in properties if p.area_sqft > 0]
    price_per_sqft = [p.price_per_sqft for p in properties if p.price_per_sqft > 0]

    by_beds = {}
    for p in properties:
        key = f"{p.bedrooms}BR" if p.bedrooms else "Studio"
        if key not in by_beds:
            by_beds[key] = []
        by_beds[key].append(p.price)

    bed_stats = {}
    for bed_type, bed_prices in sorted(by_beds.items()):
        bed_stats[bed_type] = {
            "count": len(bed_prices),
            "avg_price": round(sum(bed_prices) / len(bed_prices), 0),
            "min_price": min(bed_prices),
            "max_price": max(bed_prices),
        }

    by_source = {}
    for p in properties:
        by_source[p.source] = by_source.get(p.source, 0) + 1

    return {
        "total_listings": len(properties),
        "price": {
            "average": round(sum(prices) / len(prices), 0),
            "median": round(sorted(prices)[len(prices) // 2], 0),
            "min": min(prices),
            "max": max(prices),
        },
        "area_sqft": {
            "average": round(sum(areas) / len(areas), 0) if areas else 0,
            "min": min(areas) if areas else 0,
            "max": max(areas) if areas else 0,
        },
        "price_per_sqft": {
            "average": round(sum(price_per_sqft) / len(price_per_sqft), 0) if price_per_sqft else 0,
            "min": round(min(price_per_sqft), 0) if price_per_sqft else 0,
            "max": round(max(price_per_sqft), 0) if price_per_sqft else 0,
        },
        "by_bedroom": bed_stats,
        "by_source": by_source,
    }


def compare_properties(properties: list[Property]) -> str:
    """Generate a comparison table for multiple properties."""
    if len(properties) < 2:
        return "Need at least 2 properties to compare."

    headers = ["", *[f"Property {i+1}" for i in range(len(properties))]]
    rows = [
        ["Source", *[p.source for p in properties]],
        ["Price (AED)", *[f"{p.price:,.0f}" for p in properties]],
        ["Beds", *[str(p.bedrooms) if p.bedrooms else "Studio" for p in properties]],
        ["Baths", *[str(p.bathrooms) for p in properties]],
        ["Area (sqft)", *[f"{p.area_sqft:,.0f}" for p in properties]],
        ["AED/sqft", *[f"{p.price_per_sqft:,.0f}" for p in properties]],
        ["Location", *[p.community or p.location for p in properties]],
        ["Type", *[p.property_type for p in properties]],
        ["Furnishing", *[p.furnishing or "-" for p in properties]],
        ["Status", *[p.completion_status or "-" for p in properties]],
    ]

    # Calculate column widths
    col_widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

    lines = []
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    lines.append(header_line)
    lines.append("-+-".join("-" * w for w in col_widths))

    for row in rows:
        lines.append(" | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths)))

    return "\n".join(lines)


def format_yield_report(yield_data: dict) -> str:
    """Format yield calculation into readable text."""
    if "error" in yield_data:
        return f"Error: {yield_data['error']}"

    return f"""
RENTAL YIELD ANALYSIS
=====================

Purchase Price:     AED {yield_data['purchase_price']:>14,.0f}
Annual Rent:        AED {yield_data['annual_rent']:>14,.0f}

YIELD
  Gross Yield:      {yield_data['gross_yield_pct']:>13.2f}%
  Net Yield:        {yield_data['net_yield_pct']:>13.2f}%
  True Yield*:      {yield_data['true_yield_pct']:>13.2f}%

MONTHLY NET INCOME: AED {yield_data['monthly_net_income']:>14,.0f}

DEDUCTIONS (Annual)
  Service Charge:   AED {yield_data['deductions']['service_charge']:>14,.0f}
  Vacancy Loss:     AED {yield_data['deductions']['vacancy_loss']:>14,.0f}
  Maintenance:      AED {yield_data['deductions']['maintenance']:>14,.0f}

ACQUISITION COSTS (One-time)
  DLD Fee (4%):     AED {yield_data['acquisition_costs']['dld_fee_4pct']:>14,.0f}
  Agency Fee (2%):  AED {yield_data['acquisition_costs']['agency_fee_2pct']:>14,.0f}
  Total Cost:       AED {yield_data['acquisition_costs']['total_cost']:>14,.0f}

BREAK-EVEN:         {yield_data['breakeven_years']:>13.1f} years

* True yield includes DLD (4%) and agency (2%) fees in total cost basis.
""".strip()


def format_area_report(stats: dict, area_name: str = "") -> str:
    """Format area statistics into readable text."""
    if "error" in stats:
        return f"Error: {stats['error']}"

    header = f"MARKET SNAPSHOT: {area_name}" if area_name else "MARKET SNAPSHOT"

    lines = [
        header,
        "=" * len(header),
        "",
        f"Total Listings: {stats['total_listings']}",
        "",
        "PRICES (AED)",
        f"  Average:    {stats['price']['average']:>14,.0f}",
        f"  Median:     {stats['price']['median']:>14,.0f}",
        f"  Range:      {stats['price']['min']:>14,.0f} - {stats['price']['max']:,.0f}",
        "",
        "PRICE PER SQFT (AED)",
        f"  Average:    {stats['price_per_sqft']['average']:>14,.0f}",
        f"  Range:      {stats['price_per_sqft']['min']:>14,.0f} - {stats['price_per_sqft']['max']:,.0f}",
        "",
        "BY BEDROOM TYPE",
    ]

    for bed_type, bed_data in stats.get("by_bedroom", {}).items():
        lines.append(f"  {bed_type}: {bed_data['count']} listings | Avg AED {bed_data['avg_price']:,.0f} | Range AED {bed_data['min_price']:,.0f} - {bed_data['max_price']:,.0f}")

    if stats.get("by_source"):
        lines.append("")
        lines.append("BY SOURCE")
        for source, count in stats["by_source"].items():
            lines.append(f"  {source}: {count} listings")

    return "\n".join(lines)
