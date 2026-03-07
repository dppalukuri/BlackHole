"""
Bayut.com scraper - Dual mode: RapidAPI (recommended) or Playwright (may hit CAPTCHA).

Bayut uses hCaptcha which blocks headless browsers. The RapidAPI is the reliable
free option (750 calls/month).

Get a free key at: https://rapidapi.com/apidojo/api/bayut
Set env var: BAYUT_RAPIDAPI_KEY=your_key
"""

import os
import asyncio
import re
import httpx
from models import Property

BASE_URL = "https://www.bayut.com"
RAPIDAPI_HOST = "bayut.p.rapidapi.com"

LOCATION_IDS = {
    "dubai": "5002",
    "abu dhabi": "5001",
    "sharjah": "5003",
    "ajman": "5004",
    "ras al khaimah": "5005",
    "fujairah": "5006",
    "umm al quwain": "5007",
    "dubai marina": "6901",
    "downtown dubai": "6904",
    "business bay": "7165",
    "jbr": "6812",
    "jumeirah beach residence": "6812",
    "palm jumeirah": "6813",
    "dubai hills": "12663",
    "dubai hills estate": "12663",
    "arabian ranches": "6905",
    "jvc": "6903",
    "jumeirah village circle": "6903",
    "dubai creek harbour": "11238",
    "emirates hills": "6906",
    "dubai silicon oasis": "6911",
    "silicon oasis": "6911",
    "al barsha": "6814",
    "deira": "6815",
    "bur dubai": "6816",
    "motor city": "6918",
    "sports city": "6910",
    "dubailand": "6919",
    "meydan": "11075",
    "damac hills": "11587",
    "jlt": "6807",
    "jumeirah lake towers": "6807",
    "difc": "7166",
    "city walk": "11149",
    "al reem island": "5169",
    "saadiyat island": "5419",
    "yas island": "5541",
    "discovery gardens": "6912",
    "international city": "6913",
    "mirdif": "6914",
    "al furjan": "11078",
    "town square": "14238",
    "jumeirah": "6817",
    "mudon": "11076",
}

PROPERTY_TYPES = {
    "apartment": 4,
    "villa": 3,
    "townhouse": 16,
    "penthouse": 18,
    "duplex": 21,
    "land": 14,
    "office": 5,
}


class BayutScraper:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("BAYUT_RAPIDAPI_KEY", "")

    async def search(
        self,
        location: str,
        purpose: str = "for-sale",
        property_type: str = "",
        min_price: int = 0,
        max_price: int = 0,
        bedrooms: int = -1,
        page: int = 0,
    ) -> list[Property]:
        """Search Bayut listings via RapidAPI."""
        if not self.api_key:
            raise ValueError(
                "Bayut requires a RapidAPI key (free, 750 calls/month). "
                "Get one at https://rapidapi.com/apidojo/api/bayut "
                "and set BAYUT_RAPIDAPI_KEY environment variable."
            )

        location_id = self._resolve_location(location)

        params = {
            "locationExternalIDs": location_id,
            "purpose": purpose,
            "hitsPerPage": 25,
            "page": page,
            "lang": "en",
            "sort": "date-desc",
        }

        if property_type and property_type.lower() in PROPERTY_TYPES:
            params["categoryExternalID"] = PROPERTY_TYPES[property_type.lower()]
        if min_price > 0:
            params["priceMin"] = min_price
        if max_price > 0:
            params["priceMax"] = max_price
        if bedrooms >= 0:
            params["roomsMin"] = bedrooms
            params["roomsMax"] = bedrooms

        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{RAPIDAPI_HOST}/properties/list",
                headers=headers,
                params=params,
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()

        properties = []
        for hit in data.get("hits", []):
            prop = self._parse_listing(hit)
            if prop:
                properties.append(prop)
        return properties

    async def get_details(self, property_id: str) -> Property:
        """Get details for a Bayut listing via RapidAPI."""
        if not self.api_key:
            raise ValueError("Bayut requires BAYUT_RAPIDAPI_KEY.")

        headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://{RAPIDAPI_HOST}/properties/detail",
                headers=headers,
                params={"externalID": property_id},
                timeout=15,
            )
            resp.raise_for_status()
            return self._parse_listing(resp.json())

    def _resolve_location(self, location: str) -> str:
        normalized = location.lower().strip()
        if normalized in LOCATION_IDS:
            return LOCATION_IDS[normalized]
        # Try partial match
        for key, val in LOCATION_IDS.items():
            if normalized in key or key in normalized:
                return val
        raise ValueError(
            f"Unknown location '{location}'. Available: {', '.join(sorted(LOCATION_IDS.keys()))}"
        )

    def _parse_listing(self, data: dict) -> Property | None:
        try:
            location_parts = []
            for loc in data.get("location", []):
                if isinstance(loc, dict):
                    name = loc.get("name", "")
                    if name:
                        location_parts.append(name)

            emirate = location_parts[0] if len(location_parts) >= 1 else ""
            community = location_parts[1] if len(location_parts) >= 2 else ""
            sub_community = location_parts[2] if len(location_parts) >= 3 else ""

            amenities = []
            for group in data.get("amenities", []):
                if isinstance(group, dict):
                    for a in group.get("amenities", []):
                        if isinstance(a, dict):
                            amenities.append(a.get("text", ""))

            photo = ""
            cover = data.get("coverPhoto")
            if isinstance(cover, dict):
                photo = cover.get("url", "")

            area = float(data.get("area", 0))
            ext_id = str(data.get("externalID", ""))

            prop_type = ""
            category = data.get("category", [])
            if isinstance(category, list) and category:
                prop_type = category[0].get("nameSingular", "") if isinstance(category[0], dict) else ""

            return Property(
                id=ext_id,
                source="bayut",
                title=data.get("title", ""),
                price=float(data.get("price", 0)),
                purpose=data.get("purpose", ""),
                property_type=prop_type,
                bedrooms=int(data.get("rooms", 0)),
                bathrooms=int(data.get("baths", 0)),
                area_sqft=area,
                location=", ".join(location_parts),
                emirate=emirate,
                community=community,
                sub_community=sub_community,
                latitude=float(data.get("geography", {}).get("lat", 0)),
                longitude=float(data.get("geography", {}).get("lng", 0)),
                furnishing=data.get("furnishingStatus", ""),
                completion_status=data.get("completionStatus", ""),
                description=str(data.get("description", ""))[:500],
                agent_name=data.get("contactName", ""),
                agency_name=data.get("agency", {}).get("name", "") if isinstance(data.get("agency"), dict) else "",
                url=f"{BASE_URL}/property/details-{ext_id}.html",
                image_url=photo,
                reference=data.get("referenceNumber", ""),
                amenities=amenities,
            )
        except Exception:
            return None

    async def cleanup(self):
        pass  # No browser to clean up
