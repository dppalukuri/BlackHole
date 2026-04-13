"""
Website enrichment — extract emails, social links, phone numbers from business websites.

Given a URL, this module:
  1. Fetches the homepage + contact/about pages
  2. Extracts emails via regex (skips generic ones like info@, noreply@)
  3. Finds social media links (LinkedIn, Facebook, Instagram, Twitter/X, YouTube)
  4. Extracts phone numbers
  5. Detects basic tech stack from meta tags and scripts

This turns a raw Google Maps listing into an actionable sales lead.
"""

import asyncio
import re
import logging
from urllib.parse import urljoin, urlparse

from stealth_browser import StealthBrowser
from retry import retry_async, ResultCache

logger = logging.getLogger(__name__)

# Cache enrichment results for 24 hours
_cache = ResultCache(ttl_seconds=86400)

# --- Regex patterns ---

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

PHONE_PATTERN = re.compile(
    r"(?:\+\d{1,3}[\s\-.]?)"  # country code (require + for intl)
    r"(?:\(?\d{1,4}\)?[\s\-.]?)"  # area code
    r"(?:\d[\d\s\-.]{4,10}\d)",  # number body
)

SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[a-zA-Z0-9\-_.%/]+", re.I),
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.\-_]+", re.I),
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/[a-zA-Z0-9.\-_]+", re.I),
    "twitter": re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[a-zA-Z0-9_]+", re.I),
    "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/(?:@|channel/|c/)[a-zA-Z0-9\-_]+", re.I),
    "tiktok": re.compile(r"https?://(?:www\.)?tiktok\.com/@[a-zA-Z0-9.\-_]+", re.I),
}

# Emails to skip (generic/useless for sales)
SKIP_EMAIL_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "mailer-daemon", "postmaster", "webmaster", "hostmaster",
    "abuse", "security", "privacy", "root", "admin",
    "example", "test", "demo", "sentry", "error",
}

# Common contact/about page paths to check
CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus",
    "/about", "/about-us", "/aboutus",
    "/team", "/our-team",
]


class WebsiteEnricher:
    """Extracts contact info and social links from business websites."""

    def __init__(self, browser: StealthBrowser | None = None):
        self._browser = browser or StealthBrowser()
        self._own_browser = browser is None

    async def enrich(
        self,
        website_url: str,
        deep: bool = True,
        timeout: int = 15000,
    ) -> dict:
        """Enrich a business by scraping its website.

        Uses caching (24h TTL) and retry with backoff.

        Args:
            website_url: The business website URL
            deep: If True, also check /contact and /about pages
            timeout: Page load timeout in ms

        Returns:
            Dict with emails, phones, social_links, tech_stack
        """
        result = {
            "emails": [],
            "phones": [],
            "social_links": {},
            "meta_description": "",
            "tech_stack": [],
        }

        if not website_url:
            return result

        # Normalize URL
        if not website_url.startswith("http"):
            website_url = f"https://{website_url}"

        # Check cache first
        cached = _cache.get(website_url)
        if cached:
            logger.debug(f"Cache hit for {website_url}")
            return cached

        context = await self._browser.new_context(session_name="enrichment")
        page = await context.new_page()

        try:
            # Block heavy resources to speed up loading
            await page.route(
                "**/*.{png,jpg,jpeg,gif,svg,webp,mp4,webm,woff,woff2,ttf}",
                lambda route: route.abort(),
            )

            # Scrape homepage with retry
            homepage_data = await retry_async(
                lambda: self._scrape_page(page, website_url, timeout),
                max_retries=1,
                backoff=2.0,
            ) or {}
            self._merge_results(result, homepage_data)

            # Scrape contact/about pages for more emails
            if deep:
                pages_to_try = self._find_contact_links(
                    homepage_data.get("links", []), website_url
                )

                for contact_url in pages_to_try[:3]:  # Max 3 subpages
                    try:
                        subpage_data = await self._scrape_page(
                            page, contact_url, timeout
                        )
                        self._merge_results(result, subpage_data)
                    except Exception:
                        continue
                    await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Enrichment failed for {website_url}: {e}")
        finally:
            await page.close()
            await context.close()

        # Deduplicate and clean
        result["emails"] = self._rank_emails(list(set(result["emails"])))
        result["phones"] = list(set(result["phones"]))[:5]

        # Cache the result
        _cache.set(website_url, result)

        return result

    async def enrich_batch(
        self,
        urls: list[str],
        max_concurrent: int = 3,
        deep: bool = True,
    ) -> dict[str, dict]:
        """Enrich multiple websites concurrently.

        Args:
            urls: List of website URLs
            max_concurrent: Max parallel enrichments
            deep: Check subpages

        Returns:
            Dict mapping URL to enrichment results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def _enrich_one(url: str):
            async with semaphore:
                results[url] = await self.enrich(url, deep=deep)

        tasks = [_enrich_one(url) for url in urls if url]
        await asyncio.gather(*tasks, return_exceptions=True)

        return results

    def _merge_results(self, target: dict, source: dict):
        """Merge scraped page data into the running result."""
        if not source:
            return
        target["emails"].extend(source.get("emails", []))
        target["phones"].extend(source.get("phones", []))
        # Social links: keep first found per platform
        for platform, url in source.get("social_links", {}).items():
            if platform not in target["social_links"]:
                target["social_links"][platform] = url
        # Tech stack: merge
        for tech in source.get("tech_stack", []):
            if tech not in target["tech_stack"]:
                target["tech_stack"].append(tech)
        # Meta description: keep first non-empty
        if not target["meta_description"] and source.get("meta_description"):
            target["meta_description"] = source["meta_description"]

    async def _scrape_page(self, page, url: str, timeout: int) -> dict:
        """Scrape a single page for contact info."""
        data = {"emails": [], "phones": [], "social_links": {}, "links": [], "tech_stack": []}

        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            if not response or response.status >= 400:
                return data

            await asyncio.sleep(1)  # Let JS render

            # Get page HTML
            html = await page.content()

            # Extract emails from HTML (catches mailto: and visible text)
            data["emails"] = self._extract_emails(html)

            # Extract phone numbers
            data["phones"] = self._extract_phones(html)

            # Extract social links
            data["social_links"] = self._extract_socials(html)

            # Extract all links (for finding contact pages)
            data["links"] = await self._extract_links(page)

            # Meta description
            try:
                meta = await page.locator('meta[name="description"]').first.get_attribute("content")
                data["meta_description"] = (meta or "").strip()
            except Exception:
                pass

            # Basic tech stack detection
            data["tech_stack"] = self._detect_tech_stack(html)

        except Exception as e:
            logger.debug(f"Page scrape failed for {url}: {e}")

        return data

    def _extract_emails(self, html: str) -> list[str]:
        """Extract email addresses from HTML, filtering out junk."""
        raw_emails = EMAIL_PATTERN.findall(html)
        valid = []

        for email in raw_emails:
            email = email.lower().strip()

            # Skip image filenames mistaken as emails
            if any(email.endswith(ext) for ext in (".png", ".jpg", ".gif", ".svg", ".webp")):
                continue

            # Skip generic/useless addresses
            prefix = email.split("@")[0]
            if prefix in SKIP_EMAIL_PREFIXES:
                continue

            # Skip very long addresses (usually encoded strings)
            if len(email) > 60:
                continue

            valid.append(email)

        return valid

    def _extract_phones(self, html: str) -> list[str]:
        """Extract phone numbers from HTML."""
        # Look in tel: links first (most reliable)
        tel_pattern = re.compile(r'href="tel:([^"]+)"', re.I)
        tel_numbers = tel_pattern.findall(html)

        # Also look for visible phone numbers
        visible = PHONE_PATTERN.findall(html)

        all_phones = []
        for phone in tel_numbers + visible:
            cleaned = re.sub(r"[^\d+\-() ]", "", phone).strip()
            # Must have at least 7 digits
            digits = re.sub(r"\D", "", cleaned)
            if 7 <= len(digits) <= 15:
                all_phones.append(cleaned)

        return list(set(all_phones))[:10]

    def _extract_socials(self, html: str) -> dict[str, str]:
        """Extract social media profile URLs."""
        socials = {}
        for platform, pattern in SOCIAL_PATTERNS.items():
            match = pattern.search(html)
            if match:
                url = match.group(0).rstrip("/")
                # Skip share/intent links
                if "/share" in url or "/intent" in url or "/sharer" in url:
                    continue
                socials[platform] = url
        return socials

    async def _extract_links(self, page) -> list[str]:
        """Extract all href links from the page."""
        try:
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(el => el.href).filter(h => h.startsWith('http'))",
            )
            return links[:200]
        except Exception:
            return []

    def _find_contact_links(self, links: list[str], base_url: str) -> list[str]:
        """Find contact/about page URLs from a list of links."""
        base_domain = urlparse(base_url).netloc
        contact_urls = []

        # Check existing links first
        for link in links:
            parsed = urlparse(link)
            if parsed.netloc != base_domain:
                continue
            path = parsed.path.lower().rstrip("/")
            if any(cp in path for cp in CONTACT_PATHS):
                contact_urls.append(link)

        # If none found, try common paths
        if not contact_urls:
            for path in CONTACT_PATHS[:4]:
                contact_urls.append(urljoin(base_url, path))

        return contact_urls[:3]

    def _detect_tech_stack(self, html: str) -> list[str]:
        """Detect technologies from HTML content."""
        stack = []
        checks = {
            "WordPress": ('wp-content', 'wp-includes'),
            "Shopify": ('cdn.shopify.com', 'Shopify.theme'),
            "Wix": ('wix.com', 'X-Wix'),
            "Squarespace": ('squarespace.com', 'squarespace-cdn'),
            "React": ('react', '_next/static', '__NEXT_DATA__'),
            "Vue": ('vue.js', 'vue.min.js', '__vue__'),
            "Angular": ('ng-version', 'angular'),
            "Bootstrap": ('bootstrap.min', 'bootstrap.css'),
            "Tailwind": ('tailwindcss',),
            "Google Analytics": ('google-analytics.com', 'gtag(', 'analytics.js'),
            "Google Tag Manager": ('googletagmanager.com',),
            "HubSpot": ('hubspot.com', 'hs-scripts'),
            "Intercom": ('intercom.io', 'intercomSettings'),
            "Zendesk": ('zendesk.com', 'zE('),
            "Mailchimp": ('mailchimp.com', 'mc.js'),
        }

        html_lower = html.lower()
        for tech, signatures in checks.items():
            if any(sig.lower() in html_lower for sig in signatures):
                stack.append(tech)

        return stack

    def _rank_emails(self, emails: list[str]) -> list[str]:
        """Rank emails by likely usefulness for sales outreach.

        Priority: personal names > role-based > generic
        """
        personal = []
        role_based = []
        generic = []

        role_prefixes = {
            "info", "contact", "hello", "hi", "support",
            "help", "sales", "enquiry", "inquiry", "office",
            "mail", "general", "team", "service",
        }

        for email in emails:
            prefix = email.split("@")[0]
            if prefix in role_prefixes:
                role_based.append(email)
            elif "." in prefix or any(c.isdigit() for c in prefix):
                # Likely personal (john.doe@, jane2@)
                personal.append(email)
            else:
                generic.append(email)

        # Personal first, then role-based, then generic
        return (personal + role_based + generic)[:10]

    async def cleanup(self):
        if self._own_browser:
            await self._browser.cleanup()
