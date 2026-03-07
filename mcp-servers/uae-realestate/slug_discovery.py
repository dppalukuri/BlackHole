"""
Slug discovery - scrapes UAE real estate sites to discover and update location/property type slugs.

Reads from and writes to slugs.json. Run periodically to keep slugs current as
sites add new communities, rename areas, etc.

Usage:
  python slug_discovery.py              # Update all sites
  python slug_discovery.py dubizzle     # Update one site
  python slug_discovery.py --dry-run    # Show what would change without saving
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone

SLUGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "slugs.json")


def load_slugs() -> dict:
    """Load current slugs from JSON file."""
    if os.path.exists(SLUGS_FILE):
        with open(SLUGS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_slugs(data: dict):
    """Save slugs to JSON file."""
    data["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(SLUGS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


async def _get_browser():
    """Create a stealth browser for slug discovery."""
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--window-position=-32000,-32000"],
    )
    ctx = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="en-AE",
        timezone_id="Asia/Dubai",
    )
    stealth = Stealth()
    await stealth.apply_stealth_async(ctx)
    page = await ctx.new_page()
    return pw, browser, ctx, page


def _slug_to_display(slug: str) -> str:
    """Convert URL slug to display name: 'dubai-marina' -> 'dubai marina'."""
    return slug.replace("-", " ")


def _merge_locations(existing: dict, discovered: dict) -> tuple[dict, list[str]]:
    """
    Merge discovered slugs into existing, preserving manual aliases.
    Returns (merged dict, list of new entries).
    """
    merged = dict(existing)
    new_entries = []

    # Get all existing slug values to avoid duplicating
    existing_values = set(existing.values())

    for display, slug in discovered.items():
        if display not in merged:
            merged[display] = slug
            new_entries.append(f"  + {display} -> {slug}")

    return merged, new_entries


async def discover_dubizzle(page) -> dict:
    """
    Discover Dubizzle location slugs from their property listing pages.

    Dubizzle exposes location data in their filter/navigation elements and
    in the links on category pages.
    """
    discovered = {}

    # Strategy 1: Visit the main property page and extract location links
    await page.goto(
        "https://dubai.dubizzle.com/en/property-for-sale/residential/",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(5)

    # Extract location slugs from all internal links
    slugs = await page.evaluate("""() => {
        const locations = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            // Match /in/<slug>/ pattern in URLs
            const match = href.match(/\\/in\\/([a-z][a-z0-9-]+)\\//);
            if (match) {
                const slug = match[1];
                // Skip very short or generic slugs
                if (slug.length > 2 && slug !== 'dubai') {
                    const display = slug.replace(/-/g, ' ');
                    locations[display] = slug;
                }
            }
        }
        return locations;
    }""")
    discovered.update(slugs)

    # Strategy 2: Visit a popular area page to find "nearby" or "similar" area links
    await page.goto(
        "https://dubai.dubizzle.com/en/property-for-sale/residential/in/dubai-marina/",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(5)

    # Scroll to bottom to load footer/related links
    for _ in range(8):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2)

    more_slugs = await page.evaluate("""() => {
        const locations = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            const match = href.match(/\\/in\\/([a-z][a-z0-9-]+)\\//);
            if (match) {
                const slug = match[1];
                if (slug.length > 2 && slug !== 'dubai') {
                    const display = slug.replace(/-/g, ' ');
                    locations[display] = slug;
                }
            }
        }
        return locations;
    }""")
    discovered.update(more_slugs)

    # Strategy 3: Check the rent side too for any locations only listed there
    await page.goto(
        "https://dubai.dubizzle.com/en/property-for-rent/residential/",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(5)

    for _ in range(8):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2)

    rent_slugs = await page.evaluate("""() => {
        const locations = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            const match = href.match(/\\/in\\/([a-z][a-z0-9-]+)\\//);
            if (match) {
                const slug = match[1];
                if (slug.length > 2 && slug !== 'dubai') {
                    const display = slug.replace(/-/g, ' ');
                    locations[display] = slug;
                }
            }
        }
        return locations;
    }""")
    discovered.update(rent_slugs)

    # Also extract property type slugs
    prop_types = await page.evaluate("""() => {
        const types = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            // Match /residential/<type>/in/ pattern
            const match = href.match(/\\/residential\\/([a-z][a-z-]+)\\/in\\//);
            if (match) {
                const slug = match[1];
                const display = slug.replace(/-/g, ' ');
                types[display] = slug;
            }
        }
        return types;
    }""")

    return {"locations": discovered, "property_types": prop_types}


async def discover_bayut(page) -> dict:
    """
    Discover Bayut location slugs from their search pages.

    Bayut uses Next.js with __NEXT_DATA__ which often contains location lists,
    plus footer/navigation links to popular areas.
    """
    discovered = {}

    # Strategy 1: Main property page - extract from links and __NEXT_DATA__
    await page.goto(
        "https://www.bayut.com/for-sale/property/dubai/",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(5)

    # Scroll to load all content
    for _ in range(10):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2)

    # Extract location slugs from property links
    slugs = await page.evaluate("""() => {
        const locations = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            // Match /for-sale/{type}/dubai/{location}/ or /to-rent/{type}/dubai/{location}/
            const match = href.match(/\\/(for-sale|to-rent)\\/\\w+\\/dubai\\/([a-z][a-z0-9-]+)\\//);
            if (match) {
                const slug = match[2];
                if (slug.length > 2) {
                    const display = slug.replace(/-/g, ' ');
                    locations[display] = slug;
                }
            }
        }
        return locations;
    }""")
    discovered.update(slugs)

    # Strategy 2: Try __NEXT_DATA__ for location data
    next_data_locations = await page.evaluate("""() => {
        const el = document.getElementById('__NEXT_DATA__');
        if (!el) return {};
        try {
            const d = JSON.parse(el.textContent);
            const locations = {};

            // Look for location data in various spots
            const pageProps = d.props?.pageProps || {};
            const candidates = [
                pageProps.locations,
                pageProps.popularLocations,
                pageProps.trendingLocations,
                pageProps.searchFilters?.locations,
            ];

            for (const arr of candidates) {
                if (!Array.isArray(arr)) continue;
                for (const loc of arr) {
                    if (loc.slug && loc.name) {
                        locations[loc.name.toLowerCase()] = loc.slug;
                    }
                    if (loc.externalID && loc.name) {
                        locations[loc.name.toLowerCase()] = loc.externalID;
                    }
                }
            }

            // Also check apolloState for Location entries
            const apolloState = d.props?.apolloState || pageProps.apolloState;
            if (apolloState) {
                for (const [key, val] of Object.entries(apolloState)) {
                    if (key.startsWith('Location:') && val.name && val.externalID) {
                        locations[val.name.toLowerCase()] = val.externalID;
                    }
                }
            }

            return locations;
        } catch { return {}; }
    }""")
    discovered.update(next_data_locations)

    # Strategy 3: Popular areas from footer/sidebar links
    await page.goto(
        "https://www.bayut.com/for-sale/apartments/dubai/",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(5)

    for _ in range(10):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2)

    more_slugs = await page.evaluate("""() => {
        const locations = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            const match = href.match(/\\/(for-sale|to-rent)\\/\\w+\\/dubai\\/([a-z][a-z0-9-]+)\\//);
            if (match) {
                const slug = match[2];
                if (slug.length > 2) {
                    const display = slug.replace(/-/g, ' ');
                    locations[display] = slug;
                }
            }
        }
        return locations;
    }""")
    discovered.update(more_slugs)

    return {"location_slugs": discovered}


async def discover_propertyfinder(page) -> dict:
    """
    Discover PropertyFinder location slugs from their search pages.

    PropertyFinder uses Next.js SSR with location data in __NEXT_DATA__
    and has slug-based URLs for SEO pages.
    """
    discovered = {}

    # Strategy 1: Visit the buy page and extract location links
    await page.goto(
        "https://www.propertyfinder.ae/en/buy/properties-for-sale.html",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(5)

    for _ in range(10):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2)

    # Extract from page links (slug-based URLs)
    slugs = await page.evaluate("""() => {
        const locations = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            // Match /buy/apartments-for-sale-in-<location>.html or similar
            const match = href.match(/\\/(buy|rent)\\/\\w+-for-(?:sale|rent)-in-([a-z][a-z0-9-]+)\\.html/);
            if (match) {
                const slug = match[2];
                if (slug.length > 2) {
                    const display = slug.replace(/-/g, ' ');
                    locations[display] = slug;
                }
            }
        }
        return locations;
    }""")
    discovered.update(slugs)

    # Strategy 2: __NEXT_DATA__ for location lists
    next_data_locations = await page.evaluate("""() => {
        const el = document.getElementById('__NEXT_DATA__');
        if (!el) return {};
        try {
            const d = JSON.parse(el.textContent);
            const locations = {};

            const pageProps = d.props?.pageProps || {};
            const candidates = [
                pageProps.locations,
                pageProps.popularLocations,
                pageProps.trendingSearches,
                pageProps.locationSuggestions,
            ];

            for (const arr of candidates) {
                if (!Array.isArray(arr)) continue;
                for (const loc of arr) {
                    const name = (loc.name || loc.title || loc.label || '').toLowerCase();
                    const slug = loc.slug || loc.path || loc.id || '';
                    if (name && slug) {
                        locations[name] = String(slug);
                    }
                }
            }

            return locations;
        } catch { return {}; }
    }""")
    discovered.update(next_data_locations)

    # Strategy 3: Rent page for additional locations
    await page.goto(
        "https://www.propertyfinder.ae/en/rent/properties-for-rent.html",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    await asyncio.sleep(5)

    for _ in range(10):
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(0.5)
    await asyncio.sleep(2)

    rent_slugs = await page.evaluate("""() => {
        const locations = {};
        for (const a of document.querySelectorAll('a[href]')) {
            const href = a.href;
            const match = href.match(/\\/(buy|rent)\\/\\w+-for-(?:sale|rent)-in-([a-z][a-z0-9-]+)\\.html/);
            if (match) {
                const slug = match[2];
                if (slug.length > 2) {
                    const display = slug.replace(/-/g, ' ');
                    locations[display] = slug;
                }
            }
        }
        return locations;
    }""")
    discovered.update(rent_slugs)

    return {"locations": discovered}


async def run_discovery(sites: list[str] | None = None, dry_run: bool = False):
    """
    Run slug discovery for specified sites (or all).

    Args:
        sites: List of site names to discover, or None for all
        dry_run: If True, show changes without saving
    """
    all_sites = ["dubizzle", "bayut", "propertyfinder"]
    if sites is None:
        sites = all_sites

    slugs_data = load_slugs()
    if not slugs_data.get("_meta"):
        slugs_data["_meta"] = {"description": "Auto-discovered slugs", "last_updated": None}

    pw, browser, ctx, page = await _get_browser()
    total_new = 0

    try:
        for site in sites:
            if site not in all_sites:
                print(f"Unknown site: {site}")
                continue

            print(f"\n{'='*60}")
            print(f"Discovering slugs for: {site}")
            print(f"{'='*60}")

            try:
                if site == "dubizzle":
                    result = await discover_dubizzle(page)
                    site_data = slugs_data.setdefault("dubizzle", {})

                    # Merge locations
                    existing = site_data.get("locations", {})
                    merged, new_entries = _merge_locations(existing, result.get("locations", {}))
                    site_data["locations"] = merged

                    if new_entries:
                        print(f"\nNew locations found ({len(new_entries)}):")
                        for entry in new_entries:
                            print(entry)
                        total_new += len(new_entries)
                    else:
                        print(f"\nNo new locations (existing: {len(existing)})")

                    # Merge property types
                    if result.get("property_types"):
                        existing_pt = site_data.get("property_types", {})
                        merged_pt, new_pt = _merge_locations(existing_pt, result["property_types"])
                        site_data["property_types"] = merged_pt
                        if new_pt:
                            print(f"\nNew property types ({len(new_pt)}):")
                            for entry in new_pt:
                                print(entry)
                            total_new += len(new_pt)

                elif site == "bayut":
                    result = await discover_bayut(page)
                    site_data = slugs_data.setdefault("bayut", {})

                    existing = site_data.get("location_slugs", {})
                    merged, new_entries = _merge_locations(existing, result.get("location_slugs", {}))
                    site_data["location_slugs"] = merged

                    if new_entries:
                        print(f"\nNew location slugs found ({len(new_entries)}):")
                        for entry in new_entries:
                            print(entry)
                        total_new += len(new_entries)
                    else:
                        print(f"\nNo new location slugs (existing: {len(existing)})")

                elif site == "propertyfinder":
                    result = await discover_propertyfinder(page)
                    site_data = slugs_data.setdefault("propertyfinder", {})

                    existing = site_data.get("locations", {})
                    merged, new_entries = _merge_locations(existing, result.get("locations", {}))
                    site_data["locations"] = merged

                    if new_entries:
                        print(f"\nNew locations found ({len(new_entries)}):")
                        for entry in new_entries:
                            print(entry)
                        total_new += len(new_entries)
                    else:
                        print(f"\nNo new locations (existing: {len(existing)})")

            except Exception as e:
                print(f"\nError discovering {site}: {e}")

        print(f"\n{'='*60}")
        print(f"Total new entries: {total_new}")

        if not dry_run and total_new > 0:
            save_slugs(slugs_data)
            print(f"Saved to {SLUGS_FILE}")
        elif dry_run and total_new > 0:
            print("Dry run - changes NOT saved")
        else:
            # Still update the timestamp even if nothing new
            if not dry_run:
                save_slugs(slugs_data)
                print(f"Updated timestamp in {SLUGS_FILE}")

    finally:
        await browser.close()
        await pw.stop()


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    sites = [a for a in args if not a.startswith("--")]

    asyncio.run(run_discovery(sites or None, dry_run=dry_run))
