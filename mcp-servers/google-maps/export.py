"""
Export leads to CSV and Excel formats.
"""

import csv
import io
import json
import os
from pathlib import Path
from datetime import datetime

from models import Business

# Default export directory
EXPORT_DIR = Path(__file__).parent / "exports"


def leads_to_csv(businesses: list[Business], filepath: str = "") -> str:
    """Export businesses to CSV.

    Args:
        businesses: List of Business objects
        filepath: Output file path. If empty, auto-generates in exports/

    Returns:
        Path to the created CSV file
    """
    if not filepath:
        EXPORT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(EXPORT_DIR / f"leads_{timestamp}.csv")

    columns = [
        "lead_score", "name", "category", "rating", "review_count",
        "phone", "email", "website", "address",
        "linkedin", "facebook", "instagram", "twitter",
        "tech_stack", "maps_url",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()

        for biz in businesses:
            row = {
                "lead_score": biz.lead_score,
                "name": biz.name,
                "category": biz.category,
                "rating": biz.rating or "",
                "review_count": biz.review_count or "",
                "phone": biz.phone or (biz.phones[0] if biz.phones else ""),
                "email": biz.emails[0] if biz.emails else "",
                "website": biz.website,
                "address": biz.address,
                "linkedin": biz.social_links.get("linkedin", ""),
                "facebook": biz.social_links.get("facebook", ""),
                "instagram": biz.social_links.get("instagram", ""),
                "twitter": biz.social_links.get("twitter", ""),
                "tech_stack": ", ".join(biz.tech_stack) if biz.tech_stack else "",
                "maps_url": biz.maps_url,
            }
            writer.writerow(row)

    return filepath


def leads_to_csv_string(businesses: list[Business]) -> str:
    """Export businesses to CSV string (for returning via MCP tool)."""
    output = io.StringIO()

    columns = [
        "lead_score", "name", "category", "rating", "review_count",
        "phone", "email", "website", "address",
        "linkedin", "facebook", "instagram", "twitter",
    ]

    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()

    for biz in businesses:
        row = {
            "lead_score": biz.lead_score,
            "name": biz.name,
            "category": biz.category,
            "rating": biz.rating or "",
            "review_count": biz.review_count or "",
            "phone": biz.phone or (biz.phones[0] if biz.phones else ""),
            "email": biz.emails[0] if biz.emails else "",
            "website": biz.website,
            "address": biz.address,
            "linkedin": biz.social_links.get("linkedin", ""),
            "facebook": biz.social_links.get("facebook", ""),
            "instagram": biz.social_links.get("instagram", ""),
            "twitter": biz.social_links.get("twitter", ""),
        }
        writer.writerow(row)

    return output.getvalue()


def leads_to_json(businesses: list[Business], filepath: str = "") -> str:
    """Export businesses to JSON file.

    Args:
        businesses: List of Business objects
        filepath: Output file path. If empty, auto-generates in exports/

    Returns:
        Path to the created JSON file
    """
    if not filepath:
        EXPORT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(EXPORT_DIR / f"leads_{timestamp}.json")

    data = {
        "exported_at": datetime.now().isoformat(),
        "count": len(businesses),
        "leads": [biz.to_dict() for biz in businesses],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath
