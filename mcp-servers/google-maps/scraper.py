"""
Google Maps scraper — extracts business listings, details, and reviews.

Strategy:
  1. Search Google Maps with query
  2. Scroll results panel to load more listings
  3. Extract structured data from each listing
  4. Optionally drill into individual listings for full details + reviews

All extraction uses DOM selectors on the rendered page — no private APIs.
"""

import asyncio
import json
import re
import logging
from urllib.parse import quote_plus

from models import Business, Review
from stealth_browser import StealthBrowser

logger = logging.getLogger(__name__)

MAPS_SEARCH_URL = "https://www.google.com/maps/search/{query}"
MAPS_PLACE_URL = "https://www.google.com/maps/place/?q=place_id:{place_id}"

# Well-known city geocoordinates + timezones for browser context
KNOWN_LOCATIONS = {
    "dubai": (25.2048, 55.2708, "Asia/Dubai"),
    "abu dhabi": (24.4539, 54.3773, "Asia/Dubai"),
    "sharjah": (25.3463, 55.4209, "Asia/Dubai"),
    "new york": (40.7128, -74.0060, "America/New_York"),
    "los angeles": (34.0522, -118.2437, "America/Los_Angeles"),
    "san francisco": (37.7749, -122.4194, "America/Los_Angeles"),
    "chicago": (41.8781, -87.6298, "America/Chicago"),
    "london": (51.5074, -0.1278, "Europe/London"),
    "paris": (48.8566, 2.3522, "Europe/Paris"),
    "berlin": (52.5200, 13.4050, "Europe/Berlin"),
    "tokyo": (35.6762, 139.6503, "Asia/Tokyo"),
    "singapore": (1.3521, 103.8198, "Asia/Singapore"),
    "sydney": (-33.8688, 151.2093, "Australia/Sydney"),
    "mumbai": (19.0760, 72.8777, "Asia/Kolkata"),
    "bangalore": (12.9716, 77.5946, "Asia/Kolkata"),
    "delhi": (28.6139, 77.2090, "Asia/Kolkata"),
    "riyadh": (24.7136, 46.6753, "Asia/Riyadh"),
    "toronto": (43.6532, -79.3832, "America/Toronto"),
    "miami": (25.7617, -80.1918, "America/New_York"),
    "houston": (29.7604, -95.3698, "America/Chicago"),
    "seattle": (47.6062, -122.3321, "America/Los_Angeles"),
    "boston": (42.3601, -71.0589, "America/New_York"),
    "amsterdam": (52.3676, 4.9041, "Europe/Amsterdam"),
    "barcelona": (41.3874, 2.1686, "Europe/Madrid"),
    "rome": (41.9028, 12.4964, "Europe/Rome"),
    "hong kong": (22.3193, 114.1694, "Asia/Hong_Kong"),
    "bangkok": (13.7563, 100.5018, "Asia/Bangkok"),
    "cairo": (30.0444, 31.2357, "Africa/Cairo"),
    "doha": (25.2854, 51.5310, "Asia/Qatar"),
    "kuala lumpur": (3.1390, 101.6869, "Asia/Kuala_Lumpur"),
}


def _resolve_geolocation(location: str) -> tuple[dict | None, str]:
    """Resolve a location string to geolocation + timezone.

    Returns (geolocation_dict_or_None, timezone_str_or_empty).
    """
    if not location:
        return None, ""

    loc_lower = location.lower().strip()

    # Direct match
    if loc_lower in KNOWN_LOCATIONS:
        lat, lng, tz = KNOWN_LOCATIONS[loc_lower]
        return {"latitude": lat, "longitude": lng}, tz

    # Partial match (e.g. "Dubai Marina" matches "dubai")
    for city, (lat, lng, tz) in KNOWN_LOCATIONS.items():
        if city in loc_lower or loc_lower in city:
            return {"latitude": lat, "longitude": lng}, tz

    return None, ""


class GoogleMapsScraper:
    """Scrapes Google Maps for business data."""

    def __init__(self, browser: StealthBrowser | None = None):
        self._browser = browser or StealthBrowser()
        self._own_browser = browser is None

    async def search(
        self,
        query: str,
        location: str = "",
        max_results: int = 20,
        headed: bool = False,
    ) -> list[Business]:
        """Search Google Maps and return business listings.

        Args:
            query: Search term (e.g. "restaurants", "plumbers near me")
            location: Optional location to append (e.g. "Dubai Marina")
            max_results: Maximum results to return (default 20)
            headed: Use visible browser (for debugging)
        """
        search_term = f"{query} {location}".strip() if location else query
        url = MAPS_SEARCH_URL.format(query=quote_plus(search_term))

        geo, tz = _resolve_geolocation(location)
        context = await self._browser.new_context(
            headed=headed,
            session_name="google_maps",
            geolocation=geo,
            timezone_id=tz,
        )
        page = await context.new_page()
        businesses = []

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Accept cookies consent if shown
            await self._dismiss_consent(page)

            # Wait for results feed to appear
            feed_selector = 'div[role="feed"]'
            try:
                await page.wait_for_selector(feed_selector, timeout=10000)
            except Exception:
                # Might be a single result or no results
                single = await self._try_extract_single(page)
                if single:
                    return [single]
                return []

            # Scroll to load more results
            businesses = await self._scroll_and_extract(
                page, feed_selector, max_results
            )

            await self._browser.save_session(context, "google_maps")

        except Exception as e:
            logger.error(f"Search failed: {e}")
        finally:
            await page.close()
            await context.close()

        return businesses[:max_results]

    async def get_details(
        self,
        place_id: str = "",
        maps_url: str = "",
        headed: bool = False,
    ) -> Business | None:
        """Get detailed business info from a place ID or Maps URL.

        Args:
            place_id: Google place ID
            maps_url: Direct Google Maps URL
            headed: Use visible browser
        """
        if not place_id and not maps_url:
            return None

        url = maps_url or MAPS_PLACE_URL.format(place_id=place_id)

        context = await self._browser.new_context(
            headed=headed, session_name="google_maps"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._dismiss_consent(page)

            # Wait for the details panel (h1 with class DUwDvf or any h1)
            try:
                await page.wait_for_selector('h1.DUwDvf', timeout=8000)
            except Exception:
                await page.wait_for_selector('h1', timeout=5000)
            await asyncio.sleep(1.5)  # Let dynamic content load

            business = await self._extract_detail_page(page)
            await self._browser.save_session(context, "google_maps")
            return business

        except Exception as e:
            logger.error(f"Detail fetch failed: {e}")
            return None
        finally:
            await page.close()
            await context.close()

    async def get_reviews(
        self,
        place_id: str = "",
        maps_url: str = "",
        max_reviews: int = 20,
        sort_by: str = "newest",
        headed: bool = False,
    ) -> list[Review]:
        """Get reviews for a business.

        Args:
            place_id: Google place ID
            maps_url: Direct Google Maps URL
            max_reviews: Maximum reviews to fetch
            sort_by: "newest", "highest", "lowest", "relevant"
            headed: Use visible browser
        """
        if not place_id and not maps_url:
            return []

        url = maps_url or MAPS_PLACE_URL.format(place_id=place_id)

        context = await self._browser.new_context(
            headed=headed, session_name="google_maps"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._dismiss_consent(page)

            # Click reviews tab/button
            reviews_btn = page.locator('button[aria-label*="review" i]').first
            try:
                await reviews_btn.wait_for(timeout=5000)
                await reviews_btn.click()
                await asyncio.sleep(1)
            except Exception:
                # Try the reviews count link
                reviews_link = page.locator(
                    'button:has-text("review"), a:has-text("review")'
                ).first
                try:
                    await reviews_link.click()
                    await asyncio.sleep(1)
                except Exception:
                    logger.warning("Could not find reviews section")
                    return []

            # Sort reviews
            await self._sort_reviews(page, sort_by)

            # Scroll and extract reviews
            reviews = await self._scroll_and_extract_reviews(page, max_reviews)

            await self._browser.save_session(context, "google_maps")
            return reviews

        except Exception as e:
            logger.error(f"Reviews fetch failed: {e}")
            return []
        finally:
            await page.close()
            await context.close()

    # --- Private helpers ---

    async def _dismiss_consent(self, page):
        """Dismiss Google's consent/cookie dialog if present."""
        try:
            consent_btn = page.locator(
                'button:has-text("Accept all"), '
                'button:has-text("Reject all"), '
                'form[action*="consent"] button'
            ).first
            await consent_btn.click(timeout=3000)
            await asyncio.sleep(0.5)
        except Exception:
            pass

    async def _scroll_and_extract(
        self, page, feed_selector: str, max_results: int
    ) -> list[Business]:
        """Scroll the results feed and extract business cards."""
        businesses = []
        seen_names = set()
        scroll_attempts = 0
        max_scrolls = max_results // 4 + 5  # ~4 results per scroll

        feed = page.locator(feed_selector)

        while len(businesses) < max_results and scroll_attempts < max_scrolls:
            # Extract currently visible listings
            items = page.locator(f'{feed_selector} > div > div > a[href*="/maps/place/"]')
            count = await items.count()

            for i in range(count):
                if len(businesses) >= max_results:
                    break

                item = items.nth(i)
                try:
                    business = await self._extract_listing_card(item)
                    if business and business.name and business.name not in seen_names:
                        seen_names.add(business.name)
                        businesses.append(business)
                except Exception:
                    continue

            # Scroll down in the feed
            prev_count = len(businesses)
            await feed.evaluate(
                "el => el.scrollTo(0, el.scrollHeight)"
            )
            await asyncio.sleep(1.5)
            scroll_attempts += 1

            # Check if we've hit the end (no new results)
            if len(businesses) == prev_count and scroll_attempts > 3:
                # Check for "end of list" indicator
                end_marker = page.locator('span:has-text("end of list"), p:has-text("no more results")')
                try:
                    if await end_marker.count() > 0:
                        break
                except Exception:
                    pass

                # One more try
                if scroll_attempts > max_scrolls - 2:
                    break

        return businesses

    async def _extract_listing_card(self, item) -> Business | None:
        """Extract business data from a search result card.

        The <a> tag has the name in aria-label and the URL in href,
        but rating/category/address are in the parent container's text.
        """
        try:
            href = await item.get_attribute("href") or ""
            aria_label = await item.get_attribute("aria-label") or ""

            if not aria_label:
                return None

            business = Business(name=aria_label, maps_url=href)

            # Extract place_id from URL if present
            pid_match = re.search(r"place_id[=:]([A-Za-z0-9_-]+)", href)
            if pid_match:
                business.place_id = pid_match.group(1)

            # The card text is in the parent container, not the <a> tag
            # Go up to the nearest container div that holds all card info
            parent = item.locator("..").locator("..")
            try:
                text_content = await parent.inner_text()
            except Exception:
                text_content = ""

            lines = [l.strip() for l in text_content.split("\n") if l.strip()]

            for line in lines:
                # Rating pattern: "4.5(123)" or "4.5 (123)" or "4.5(1,234)"
                rating_match = re.match(r"^(\d+\.?\d*)\s*\((\d[\d,]*)\)", line)
                if rating_match:
                    business.rating = float(rating_match.group(1))
                    business.review_count = int(
                        rating_match.group(2).replace(",", "")
                    )
                    continue

                # Price level: "$", "$$", etc. (possibly with a separator)
                if re.match(r"^[\$€£]{1,4}(\s*·)?$", line):
                    business.price_level = line.rstrip(" ·")
                    continue

                # Category: usually a short phrase without numbers
                if (
                    not business.category
                    and len(line) < 50
                    and not re.search(r"\d", line)
                    and line != business.name
                    and line not in ("Directions", "Website", "Open", "Closed")
                ):
                    business.category = line

                # Address: usually contains numbers or common patterns
                if not business.address and (
                    re.search(r"\d+\s", line) or ", " in line
                ):
                    if line != business.name and line != business.category:
                        business.address = line

            return business

        except Exception as e:
            logger.debug(f"Card extraction failed: {e}")
            return None

    async def _try_extract_single(self, page) -> Business | None:
        """Try to extract a single business result (direct place page)."""
        try:
            h1 = page.locator("h1").first
            await h1.wait_for(timeout=5000)
            name = await h1.inner_text()
            if name:
                return await self._extract_detail_page(page)
        except Exception:
            pass
        return None

    async def _extract_detail_page(self, page) -> Business:
        """Extract full details from a business detail page."""
        business = Business()

        # Name
        try:
            h1 = page.locator("h1").first
            business.name = (await h1.inner_text()).strip()
        except Exception:
            pass

        # Current URL
        business.maps_url = page.url

        # Place ID from URL
        pid_match = re.search(r"place_id[=:]([A-Za-z0-9_-]+)", page.url)
        if pid_match:
            business.place_id = pid_match.group(1)

        # Rating + review count from aria-label like "4.6 stars 8,799 Reviews"
        try:
            rating_els = page.locator(
                'div[role="img"][aria-label*="star"], '
                'span[role="img"][aria-label*="star"]'
            )
            count = await rating_els.count()
            for i in range(count):
                label = await rating_els.nth(i).get_attribute("aria-label") or ""
                # Look for the one with both stars AND reviews
                rm = re.search(r"([\d.]+)\s*star", label, re.I)
                rev_m = re.search(r"([\d,]+)\s*review", label, re.I)
                if rm:
                    business.rating = float(rm.group(1))
                if rev_m:
                    business.review_count = int(rev_m.group(1).replace(",", ""))
                if rm and rev_m:
                    break  # Found the main one
        except Exception:
            pass

        # Category
        try:
            cat_btn = page.locator('button[jsaction*="category"]').first
            business.category = (await cat_btn.inner_text()).strip()
        except Exception:
            pass

        # Info items via data-item-id (most reliable selectors)
        # Address
        try:
            addr_el = page.locator('button[data-item-id="address"]').first
            text = (await addr_el.inner_text()).strip()
            # Remove leading icon characters
            business.address = re.sub(r'^[^\w\d]+', '', text).strip()
        except Exception:
            pass

        # Phone
        try:
            phone_el = page.locator('button[data-item-id^="phone:tel:"]').first
            text = (await phone_el.inner_text()).strip()
            business.phone = re.sub(r'^[^\d+]+', '', text).strip()
        except Exception:
            pass

        # Website
        try:
            web_el = page.locator(
                'a[data-item-id="authority"], button[data-item-id="authority"]'
            ).first
            aria = await web_el.get_attribute("aria-label") or ""
            # aria-label is like "Website: example.com"
            web_match = re.search(r"Website:\s*(.+?)(?:\s|$)", aria)
            if web_match:
                business.website = web_match.group(1).strip()
                if not business.website.startswith("http"):
                    business.website = f"https://{business.website}"
            else:
                href = await web_el.get_attribute("href")
                if href:
                    business.website = href
        except Exception:
            pass

        # Coordinates from URL
        coord_match = re.search(r"@(-?\d+\.?\d*),(-?\d+\.?\d*)", page.url)
        if coord_match:
            business.latitude = float(coord_match.group(1))
            business.longitude = float(coord_match.group(2))

        return business

    async def _sort_reviews(self, page, sort_by: str):
        """Click the sort dropdown and select sort order."""
        sort_map = {
            "relevant": 0,
            "newest": 1,
            "highest": 2,
            "lowest": 3,
        }
        idx = sort_map.get(sort_by, 1)

        try:
            sort_btn = page.locator(
                'button[aria-label*="Sort"], button[data-value="Sort"]'
            ).first
            await sort_btn.click(timeout=3000)
            await asyncio.sleep(0.5)

            menu_items = page.locator('div[role="menuitemradio"]')
            if await menu_items.count() > idx:
                await menu_items.nth(idx).click()
                await asyncio.sleep(1)
        except Exception:
            pass

    async def _scroll_and_extract_reviews(
        self, page, max_reviews: int
    ) -> list[Review]:
        """Scroll the reviews panel and extract review data."""
        reviews = []
        scroll_attempts = 0
        max_scrolls = max_reviews // 3 + 5

        # Find the scrollable reviews container
        scrollable = page.locator(
            'div[class*="review"] div[tabindex="-1"], '
            'div[role="main"] div[tabindex="-1"]'
        ).first

        while len(reviews) < max_reviews and scroll_attempts < max_scrolls:
            # Expand truncated reviews ("More" buttons)
            more_buttons = page.locator(
                'button:has-text("More"), button[aria-label*="more" i]'
            )
            btn_count = await more_buttons.count()
            for i in range(min(btn_count, 5)):
                try:
                    await more_buttons.nth(i).click(timeout=500)
                except Exception:
                    pass

            # Extract reviews
            review_els = page.locator(
                'div[data-review-id], div[class*="review"][data-id]'
            )
            count = await review_els.count()

            for i in range(count):
                if len(reviews) >= max_reviews:
                    break

                el = review_els.nth(i)
                try:
                    review = await self._extract_review(el)
                    if review and review.author:
                        # Dedup by author + date
                        key = f"{review.author}:{review.date}"
                        existing_keys = {
                            f"{r.author}:{r.date}" for r in reviews
                        }
                        if key not in existing_keys:
                            reviews.append(review)
                except Exception:
                    continue

            # Scroll
            prev_count = len(reviews)
            try:
                await scrollable.evaluate(
                    "el => el.scrollTo(0, el.scrollHeight)"
                )
            except Exception:
                break
            await asyncio.sleep(1.5)
            scroll_attempts += 1

            if len(reviews) == prev_count and scroll_attempts > 3:
                break

        return reviews

    async def _extract_review(self, el) -> Review:
        """Extract a single review from its DOM element."""
        review = Review()

        # Author
        try:
            author_el = el.locator('div[class*="name"], a[class*="name"]').first
            review.author = (await author_el.inner_text()).strip()
        except Exception:
            pass

        # Rating
        try:
            stars = el.locator('span[role="img"][aria-label*="star"]').first
            label = await stars.get_attribute("aria-label") or ""
            rm = re.search(r"(\d+)", label)
            if rm:
                review.rating = int(rm.group(1))
        except Exception:
            pass

        # Text
        try:
            text_el = el.locator(
                'span[class*="review-text"], div[class*="review-text"], '
                'span[class*="text"], div[class*="MyEned"]'
            ).first
            review.text = (await text_el.inner_text()).strip()
        except Exception:
            pass

        # Date
        try:
            date_el = el.locator('span[class*="date"], span:has-text("ago")').first
            review.date = (await date_el.inner_text()).strip()
        except Exception:
            pass

        # Owner response
        try:
            response_el = el.locator(
                'div[class*="owner-response"], div[class*="response"]'
            ).first
            resp_text = el.locator(
                'div[class*="owner-response"] span, div[class*="response"] span'
            ).first
            review.response = (await resp_text.inner_text()).strip()
        except Exception:
            pass

        return review

    async def cleanup(self):
        """Clean up browser resources."""
        if self._own_browser:
            await self._browser.cleanup()
