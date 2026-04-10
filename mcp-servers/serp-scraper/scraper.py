"""
SERP scraper — extracts search results from Google and Bing.

Strategy:
  1. Load search engine with query via stealth browser
  2. Handle consent screens / CAPTCHA
  3. Parse organic results, ads, featured snippets, PAA, related searches
  4. Support pagination for deeper results

Uses browser rendering to bypass JS-based protections.
Can integrate with ../captcha-solver for Google CAPTCHA challenges.
"""

import asyncio
import json
import re
import logging
import os
import sys
from urllib.parse import quote_plus, urlencode, urlparse

from models import (
    OrganicResult,
    AdResult,
    FeaturedSnippet,
    PeopleAlsoAsk,
    SerpResult,
)
from stealth_browser import StealthBrowser

logger = logging.getLogger(__name__)

# Google search URL patterns
GOOGLE_SEARCH_URL = "https://www.google.com/search"
BING_SEARCH_URL = "https://www.bing.com/search"


class SerpScraper:
    """Scrapes search engine results pages."""

    def __init__(self, browser: StealthBrowser | None = None):
        self._browser = browser or StealthBrowser()
        self._own_browser = browser is None
        self._captcha_solver = None

    async def _get_captcha_solver(self):
        """Lazily load captcha solver from sister project."""
        if self._captcha_solver:
            return self._captcha_solver

        solver_path = os.path.join(
            os.path.dirname(__file__), "..", "captcha-solver"
        )
        if os.path.exists(solver_path):
            sys.path.insert(0, solver_path)
            try:
                from router import CaptchaRouter
                self._captcha_solver = CaptchaRouter
                return self._captcha_solver
            except ImportError:
                pass
        return None

    async def search_google(
        self,
        query: str,
        num_results: int = 10,
        page: int = 1,
        language: str = "en",
        country: str = "",
        headed: bool = False,
    ) -> SerpResult:
        """Search Google and extract structured results.

        Args:
            query: Search query
            num_results: Results per page (10, 20, 50, 100)
            page: Page number (1-based)
            language: Language code (e.g. "en", "ar")
            country: Country code for localization (e.g. "ae", "us")
            headed: Use visible browser
        """
        params = {
            "q": query,
            "num": min(num_results, 100),
            "hl": language,
            "start": (page - 1) * num_results,
        }
        if country:
            params["gl"] = country
            params["cr"] = f"country{country.upper()}"

        url = f"{GOOGLE_SEARCH_URL}?{urlencode(params)}"

        context = await self._browser.new_context(
            headed=headed, session_name="google_serp"
        )
        browser_page = await context.new_page()

        try:
            await browser_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await self._dismiss_consent(browser_page)

            # Check for CAPTCHA
            if await self._detect_captcha(browser_page):
                logger.warning("Google CAPTCHA detected — attempting solve")
                solved = await self._handle_captcha(browser_page)
                if not solved:
                    return SerpResult(
                        query=query,
                        organic=[],
                    )

            await asyncio.sleep(1)  # Let dynamic content render

            result = await self._parse_google_serp(browser_page, query)
            await self._browser.save_session(context, "google_serp")
            return result

        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return SerpResult(query=query)
        finally:
            await browser_page.close()
            await context.close()

    async def search_bing(
        self,
        query: str,
        num_results: int = 10,
        page: int = 1,
        headed: bool = False,
    ) -> SerpResult:
        """Search Bing and extract structured results.

        Args:
            query: Search query
            num_results: Results per page
            page: Page number (1-based)
            headed: Use visible browser
        """
        params = {
            "q": query,
            "count": min(num_results, 50),
            "first": (page - 1) * num_results + 1,
        }

        url = f"{BING_SEARCH_URL}?{urlencode(params)}"

        context = await self._browser.new_context(
            headed=headed, session_name="bing_serp"
        )
        browser_page = await context.new_page()

        try:
            await browser_page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Dismiss Bing cookie consent
            try:
                accept = browser_page.locator("#bnp_btn_accept, button:has-text('Accept')").first
                await accept.click(timeout=3000)
                await asyncio.sleep(0.5)
            except Exception:
                pass

            await asyncio.sleep(1)
            result = await self._parse_bing_serp(browser_page, query)
            await self._browser.save_session(context, "bing_serp")
            return result

        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return SerpResult(query=query)
        finally:
            await browser_page.close()
            await context.close()

    # --- Google Parsing ---

    async def _parse_google_serp(self, page, query: str) -> SerpResult:
        """Parse a Google SERP page into structured data."""
        result = SerpResult(query=query)

        # Total results count
        try:
            stats = page.locator("#result-stats").first
            result.total_results = (await stats.inner_text()).strip()
        except Exception:
            pass

        # Featured snippet
        result.featured_snippet = await self._extract_featured_snippet(page)

        # Organic results
        result.organic = await self._extract_google_organic(page)

        # Ads
        result.ads = await self._extract_google_ads(page)

        # People Also Ask
        result.people_also_ask = await self._extract_paa(page)

        # Related searches
        result.related_searches = await self._extract_related_searches(page)

        return result

    async def _extract_google_organic(self, page) -> list[OrganicResult]:
        """Extract organic search results from Google."""
        results = []
        # Main organic results container
        items = page.locator("#search div.g, #rso div.g")
        count = await items.count()

        for i in range(count):
            item = items.nth(i)
            try:
                organic = OrganicResult(position=i + 1)

                # Title + URL
                link = item.locator("a").first
                organic.url = await link.get_attribute("href") or ""
                title_el = item.locator("h3").first
                organic.title = (await title_el.inner_text()).strip()

                # Domain
                if organic.url:
                    parsed = urlparse(organic.url)
                    organic.domain = parsed.netloc

                # Snippet
                try:
                    # Google uses various classes for snippets
                    snippet_el = item.locator(
                        'div[data-sncf], div[style*="-webkit-line-clamp"], '
                        'div.VwiC3b, span.aCOpRe'
                    ).first
                    organic.snippet = (await snippet_el.inner_text()).strip()
                except Exception:
                    pass

                # Date (if present in snippet)
                try:
                    date_el = item.locator("span.LEwnzc").first
                    organic.date = (await date_el.inner_text()).strip()
                except Exception:
                    pass

                if organic.title and organic.url:
                    results.append(organic)

            except Exception:
                continue

        return results

    async def _extract_google_ads(self, page) -> list[AdResult]:
        """Extract ad results from Google."""
        ads = []

        # Top ads
        top_ads = page.locator('#tads div[data-text-ad], #tads .uEierd')
        count = await top_ads.count()
        for i in range(count):
            ad = await self._parse_google_ad(top_ads.nth(i), i + 1, is_top=True)
            if ad:
                ads.append(ad)

        # Bottom ads
        bottom_ads = page.locator('#bottomads div[data-text-ad], #bottomads .uEierd')
        count = await bottom_ads.count()
        for i in range(count):
            ad = await self._parse_google_ad(
                bottom_ads.nth(i), len(ads) + i + 1, is_top=False
            )
            if ad:
                ads.append(ad)

        return ads

    async def _parse_google_ad(self, el, position: int, is_top: bool) -> AdResult | None:
        try:
            ad = AdResult(position=position, is_top=is_top)

            link = el.locator("a").first
            ad.url = await link.get_attribute("href") or ""

            title_el = el.locator('div[role="heading"], h3').first
            ad.title = (await title_el.inner_text()).strip()

            if ad.url:
                ad.domain = urlparse(ad.url).netloc

            try:
                desc_el = el.locator("div.MUxGbd, div.yDYNvb").first
                ad.description = (await desc_el.inner_text()).strip()
            except Exception:
                pass

            return ad if ad.title else None
        except Exception:
            return None

    async def _extract_featured_snippet(self, page) -> FeaturedSnippet | None:
        """Extract featured snippet / answer box."""
        try:
            snippet_el = page.locator(
                'div.xpdopen div[data-md], block-component div[data-attrid="wa:/description"], '
                'div.IZ6rdc, div[data-tts="answers"]'
            ).first
            await snippet_el.wait_for(timeout=2000)

            fs = FeaturedSnippet()
            fs.text = (await snippet_el.inner_text()).strip()

            # Source link
            try:
                src_link = snippet_el.locator(".. a").first
                fs.source_url = await src_link.get_attribute("href") or ""
                fs.source_title = (await src_link.inner_text()).strip()
            except Exception:
                pass

            # Detect type
            if await snippet_el.locator("ol, ul").count() > 0:
                fs.snippet_type = "list"
            elif await snippet_el.locator("table").count() > 0:
                fs.snippet_type = "table"
            else:
                fs.snippet_type = "paragraph"

            return fs if fs.text else None
        except Exception:
            return None

    async def _extract_paa(self, page) -> list[PeopleAlsoAsk]:
        """Extract People Also Ask questions."""
        paa_list = []
        try:
            questions = page.locator(
                'div[jsname="Cpkphb"] div[role="button"], '
                'div.related-question-pair div[role="button"]'
            )
            count = await questions.count()

            for i in range(min(count, 8)):
                try:
                    q_el = questions.nth(i)
                    question = (await q_el.inner_text()).strip()
                    if question:
                        paa = PeopleAlsoAsk(question=question)

                        # Click to expand and get answer
                        try:
                            await q_el.click(timeout=2000)
                            await asyncio.sleep(0.5)

                            # Find the expanded answer
                            parent = q_el.locator("..")
                            answer_el = parent.locator(
                                'div[data-md], div.wDYxhc, span.hgKElc'
                            ).first
                            paa.answer = (await answer_el.inner_text()).strip()

                            link = parent.locator("a").first
                            paa.source_url = await link.get_attribute("href") or ""
                        except Exception:
                            pass

                        paa_list.append(paa)
                except Exception:
                    continue

        except Exception:
            pass

        return paa_list

    async def _extract_related_searches(self, page) -> list[str]:
        """Extract related searches from the bottom of the SERP."""
        related = []
        try:
            items = page.locator(
                '#botstuff a div.BNeawe, '
                'div[data-sncf] a, '
                'a.k8XOCe div.s75CSd, '
                'div.oatEtb a'
            )
            count = await items.count()
            for i in range(count):
                text = (await items.nth(i).inner_text()).strip()
                if text and text not in related:
                    related.append(text)
        except Exception:
            pass
        return related

    # --- Bing Parsing ---

    async def _parse_bing_serp(self, page, query: str) -> SerpResult:
        """Parse a Bing SERP page into structured data."""
        result = SerpResult(query=query)

        # Total results
        try:
            stats = page.locator(".sb_count").first
            result.total_results = (await stats.inner_text()).strip()
        except Exception:
            pass

        # Organic results
        items = page.locator("#b_results > li.b_algo")
        count = await items.count()

        for i in range(count):
            item = items.nth(i)
            try:
                organic = OrganicResult(position=i + 1)

                link = item.locator("h2 a").first
                organic.title = (await link.inner_text()).strip()
                organic.url = await link.get_attribute("href") or ""

                if organic.url:
                    organic.domain = urlparse(organic.url).netloc

                try:
                    snippet_el = item.locator("p, .b_caption p").first
                    organic.snippet = (await snippet_el.inner_text()).strip()
                except Exception:
                    pass

                if organic.title and organic.url:
                    result.organic.append(organic)
            except Exception:
                continue

        # Related searches
        try:
            related = page.locator(".b_rs a, #b_results .b_rs a")
            rcount = await related.count()
            for i in range(rcount):
                text = (await related.nth(i).inner_text()).strip()
                if text:
                    result.related_searches.append(text)
        except Exception:
            pass

        return result

    # --- CAPTCHA handling ---

    async def _dismiss_consent(self, page):
        """Dismiss Google consent dialog."""
        try:
            consent_btn = page.locator(
                'button:has-text("Accept all"), '
                'button:has-text("Reject all"), '
                'button:has-text("I agree"), '
                'form[action*="consent"] button'
            ).first
            await consent_btn.click(timeout=3000)
            await asyncio.sleep(0.5)
        except Exception:
            pass

    async def _detect_captcha(self, page) -> bool:
        """Check if Google is showing a CAPTCHA."""
        try:
            captcha_indicators = [
                "#captcha-form",
                'iframe[src*="recaptcha"]',
                'div[id="recaptcha"]',
                'form[action*="sorry"]',
                'div:has-text("unusual traffic")',
            ]
            for selector in captcha_indicators:
                if await page.locator(selector).count() > 0:
                    return True
        except Exception:
            pass
        return False

    async def _handle_captcha(self, page) -> bool:
        """Attempt to solve Google CAPTCHA using the captcha-solver."""
        solver_cls = await self._get_captcha_solver()
        if not solver_cls:
            logger.warning("No captcha solver available")
            return False

        try:
            # Take screenshot and send to solver
            screenshot = await page.screenshot()
            # Integration point: use CaptchaRouter to solve
            # This would need the full solving pipeline
            logger.info("CAPTCHA solving integration point — needs implementation")
            return False
        except Exception as e:
            logger.error(f"CAPTCHA handling failed: {e}")
            return False

    async def cleanup(self):
        if self._own_browser:
            await self._browser.cleanup()
