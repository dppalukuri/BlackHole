"""
Unified property data model for all UAE real estate sources.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Property:
    id: str
    source: str  # bayut, dubizzle, propertyfinder
    title: str
    price: float
    currency: str = "AED"
    purpose: str = ""  # for-sale, for-rent
    property_type: str = ""  # apartment, villa, townhouse, penthouse, etc.
    bedrooms: int = 0
    bathrooms: int = 0
    area_sqft: float = 0
    location: str = ""
    emirate: str = ""
    community: str = ""
    sub_community: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    price_per_sqft: float = 0.0
    furnishing: str = ""
    completion_status: str = ""  # ready, off-plan
    description: str = ""
    agent_name: str = ""
    agent_phone: str = ""
    agency_name: str = ""
    url: str = ""
    image_url: str = ""
    listed_date: str = ""
    reference: str = ""
    amenities: list = field(default_factory=list)

    def __post_init__(self):
        if self.area_sqft and self.price and not self.price_per_sqft:
            self.price_per_sqft = round(self.price / self.area_sqft, 2)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}

    def summary(self) -> str:
        beds = f"{self.bedrooms}BR" if self.bedrooms else "Studio"
        price_sqft = f" (AED {self.price_per_sqft:,.0f}/sqft)" if self.price_per_sqft else ""
        lines = [
            f"{self.title}",
            f"  Price: {self.currency} {self.price:,.0f}{price_sqft}",
            f"  Type: {beds} {self.property_type} | {self.area_sqft:,.0f} sqft",
            f"  Location: {self.location}",
        ]
        if self.furnishing:
            lines.append(f"  Furnishing: {self.furnishing}")
        if self.completion_status:
            lines.append(f"  Status: {self.completion_status}")
        lines.append(f"  Source: {self.source} | {self.url}")
        return "\n".join(lines)

    def compact(self) -> str:
        """One-line summary for list views."""
        beds = f"{self.bedrooms}BR" if self.bedrooms else "Studio"
        return (
            f"[{self.source}] {beds} {self.property_type} in {self.community or self.location} - "
            f"AED {self.price:,.0f} | {self.area_sqft:,.0f}sqft | "
            f"AED {self.price_per_sqft:,.0f}/sqft"
        )
