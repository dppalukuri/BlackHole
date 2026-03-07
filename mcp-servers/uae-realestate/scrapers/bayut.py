"""
Bayut.com scraper - Uses the unofficial RapidAPI (free tier: 750 calls/month).

Get a free API key at: https://rapidapi.com/apidojo/api/bayut
Set env var: BAYUT_RAPIDAPI_KEY=your_key
"""

import os
import httpx
from models import Property

RAPIDAPI_HOST = "bayut.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}"

# Bayut category slugs
PROPERTY_TYPES = {
    "apartment": 4,
    "villa": 3,
    "townhouse": 16,
    "penthouse": 18,
    "duplex": 21,
    "studio": 4,  # apartment with 0 beds
    "land": 14,
    "office": 5,
    "shop": 6,
    "warehouse": 7,
}

# Common location IDs (pre-mapped to avoid API calls)
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
    "jumeirah village circle": "6903",
    "jvc": "6903",
    "dubai creek harbour": "11238",
    "emirates hills": "6906",
    "dubai silicon oasis": "6911",
    "al barsha": "6814",
    "deira": "6815",
    "bur dubai": "6816",
    "motor city": "6918",
    "sports city": "6910",
    "dubailand": "6919",
    "meydan": "11075",
    "damac hills": "11587",
    "jumeirah lake towers": "6807",
    "jlt": "6807",
    "difc": "7166",
    "city walk": "11149",
    "al reem island": "5169",
    "saadiyat island": "5419",
    "yas island": "5541",
    "corniche": "5071",
}


class BayutScraper:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.environ.get("BAYUT_RAPIDAPI_KEY", "")
        self.headers = {
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": self.api_key,
        }

    async def _resolve_location(self, location: str) -> str:
        """Resolve a location name to a Bayut location ID."""
        normalized = location.lower().strip()
        if normalized in LOCATION_IDS:
            return LOCATION_IDS[normalized]

        if not self.api_key:
            raise ValueError(
                f"Location '{location}' not in cache and no API key set. "
                f"Set BAYUT_RAPIDAPI_KEY or use a known location: {', '.join(sorted(LOCATION_IDS.keys()))}"
            )

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/auto-complete",
                headers=self.headers,
                params={"query": location, "hitsPerPage": 5, "lang": "en"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("hits", [])
            if hits:
                return str(hits[0].get("externalID", ""))

        raise ValueError(f"Could not resolve location: {location}")

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
        """Search Bayut listings."""
        if not self.api_key:
            raise ValueError(
                "Bayut requires a RapidAPI key. Get one free at "
                "https://rapidapi.com/apidojo/api/bayut and set BAYUT_RAPIDAPI_KEY"
            )

        location_id = await self._resolve_location(location)

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

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/properties/list",
                headers=self.headers,
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
        """Get detailed info for a Bayut listing."""
        if not self.api_key:
            raise ValueError("Bayut requires a RapidAPI key.")

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BASE_URL}/properties/detail",
                headers=self.headers,
                params={"externalID": property_id},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

        return self._parse_listing(data)

    def _parse_listing(self, data: dict) -> Property | None:
        """Parse a Bayut API listing into a Property object."""
        try:
            # Extract location info
            location_parts = []
            for loc in data.get("location", []):
                name = loc.get("name", "")
                if name:
                    location_parts.append(name)

            community = ""
            sub_community = ""
            emirate = ""
            if len(location_parts) >= 1:
                emirate = location_parts[0]
            if len(location_parts) >= 2:
                community = location_parts[1]
            if len(location_parts) >= 3:
                sub_community = location_parts[2]

            # Extract amenities
            amenities = []
            for group in data.get("amenities", []):
                for a in group.get("amenities", []):
                    amenities.append(a.get("text", ""))

            photo = ""
            cover = data.get("coverPhoto")
            if cover:
                photo = cover.get("url", "")

            area = float(data.get("area", 0))
            # Bayut returns area in sqft

            return Property(
                id=str(data.get("externalID", "")),
                source="bayut",
                title=data.get("title", ""),
                price=float(data.get("price", 0)),
                purpose=data.get("purpose", ""),
                property_type=data.get("category", [{}])[0].get("nameSingular", "") if data.get("category") else "",
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
                description=data.get("description", "")[:500],
                agent_name=data.get("contactName", ""),
                agency_name=data.get("agency", {}).get("name", "") if data.get("agency") else "",
                url=f"https://www.bayut.com/property/details-{data.get('externalID', '')}.html",
                image_url=photo,
                reference=data.get("referenceNumber", ""),
                amenities=amenities,
            )
        except Exception:
            return None
