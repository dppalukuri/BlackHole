"""
Slug registry - loads location and property type mappings from slugs.json.

All scrapers import from here instead of hardcoding their own dicts.
Data is loaded once on import and can be refreshed at runtime.
"""

import json
import os

_SLUGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slugs.json")
_data: dict = {}


def _load():
    """Load slugs from JSON file."""
    global _data
    if os.path.exists(_SLUGS_FILE):
        with open(_SLUGS_FILE, "r") as f:
            _data = json.load(f)
    else:
        _data = {}


def reload():
    """Force reload slugs from disk (e.g., after discovery)."""
    _load()


def get(site: str, key: str) -> dict:
    """
    Get a slug mapping for a site.

    Args:
        site: "dubizzle", "bayut", or "propertyfinder"
        key: "locations", "property_types", "location_slugs", etc.

    Returns:
        Dict mapping display names to slugs/IDs.
    """
    if not _data:
        _load()
    return _data.get(site, {}).get(key, {})


def resolve_location(site: str, location: str) -> str | None:
    """
    Resolve a user-provided location name to a site-specific slug.

    Tries exact match first, then partial/fuzzy matching.

    Args:
        site: "dubizzle", "bayut", or "propertyfinder"
        location: User-provided location name

    Returns:
        The slug/ID for the site, or None if not found.
    """
    key = "locations"
    if site == "bayut":
        # Bayut has both location IDs (for API) and location slugs (for URLs)
        key = "locations"
    locations = get(site, key)
    if not locations:
        # Fallback to location_slugs for bayut
        if site == "bayut":
            locations = get(site, "location_slugs")

    normalized = location.lower().strip()

    # Exact match
    if normalized in locations:
        return locations[normalized]

    # Partial match - user input contained in key or vice versa
    for loc_key, slug in locations.items():
        if normalized in loc_key or loc_key in normalized:
            return slug

    return None


def resolve_property_type(site: str, prop_type: str) -> str | None:
    """Resolve a property type name to a site-specific slug."""
    types = get(site, "property_types")
    if not types:
        types = get(site, "property_type_slugs")

    normalized = prop_type.lower().strip()
    if normalized in types:
        return types[normalized]

    for key, slug in types.items():
        if normalized in key or key in normalized:
            return slug

    return None


def resolve_location_id(site: str, location: str) -> str | None:
    """
    Resolve a location to its numeric ID (for sites that need it, e.g. Dubizzle).

    Args:
        site: "dubizzle", "bayut", etc.
        location: User-provided location name or slug

    Returns:
        Numeric ID string, or None if not found.
    """
    ids = get(site, "location_ids")
    if not ids:
        return None

    normalized = location.lower().strip()

    # Try by location name → slug → ID
    slug = resolve_location(site, normalized)
    if slug and slug in ids:
        return ids[slug]

    # Try direct slug match
    if normalized in ids:
        return ids[normalized]

    # Try partial
    for key, lid in ids.items():
        if normalized in key or key in normalized:
            return lid

    return None


def all_locations(site: str) -> list[str]:
    """Get all known location names for a site."""
    locations = get(site, "locations")
    if site == "bayut" and not locations:
        locations = get(site, "location_slugs")
    return sorted(set(locations.keys()))


def last_updated() -> str | None:
    """Get the timestamp of the last slug update."""
    if not _data:
        _load()
    return _data.get("_meta", {}).get("last_updated")


# Load on import
_load()
