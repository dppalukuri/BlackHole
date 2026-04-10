"""
LinkedIn scraper — profiles, jobs, companies via public pages.

Strategy:
  - Public profiles: accessible without login at /in/{slug}
  - Job search: accessible at /jobs/search/?keywords=...
  - Company pages: accessible at /company/{slug}
  - People search: requires login session (stored in .sessions/)

LinkedIn is aggressive with bot detection:
  - Rate limit: ~50 pages/hour before soft blocks
  - Hard blocks show CAPTCHA or "unusual activity" page
  - Session cookies from manual login bypass most checks
  - Random delays between requests are essential

Login flow:
  1. User logs in manually via `login` tool (opens headed browser)
  2. Session cookies saved to .sessions/linkedin.json
  3. All subsequent scraping uses these cookies in headless mode
"""

import asyncio
import json
import re
import logging
from urllib.parse import quote_plus, urlencode

from models import Profile, Job, Company, SearchResult
from stealth_browser import StealthBrowser

logger = logging.getLogger(__name__)

BASE_URL = "https://www.linkedin.com"


class LinkedInScraper:
    """Scrapes LinkedIn for profiles, jobs, and company data."""

    def __init__(self, browser: StealthBrowser | None = None):
        self._browser = browser or StealthBrowser()
        self._own_browser = browser is None

    async def login(self) -> bool:
        """Open a headed browser for manual LinkedIn login.

        The user logs in manually, then we save the session cookies
        for headless use in subsequent scraping.

        Returns True if login session was saved.
        """
        context = await self._browser.new_context(
            headed=True, session_name="linkedin"
        )
        page = await context.new_page()

        try:
            await page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")

            # Wait for user to log in — detect the feed page
            logger.info("Waiting for manual login... (complete login in the browser)")
            try:
                await page.wait_for_url(
                    "**/feed/**", timeout=120000  # 2 minutes to log in
                )
            except Exception:
                # Check if we're on any authenticated page
                current_url = page.url
                if "/login" in current_url or "/checkpoint" in current_url:
                    logger.warning("Login not completed within timeout")
                    return False

            # Save session
            await self._browser.save_session(context, "linkedin")
            logger.info("LinkedIn session saved successfully")
            return True

        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
        finally:
            await page.close()
            await context.close()

    async def _is_logged_in(self, page) -> bool:
        """Check if current page indicates a logged-in state."""
        try:
            # Logged-in pages have the global nav
            nav = page.locator("#global-nav, nav.global-nav").first
            await nav.wait_for(timeout=3000)
            return True
        except Exception:
            return False

    async def get_profile(
        self,
        profile_url: str = "",
        username: str = "",
        headed: bool = False,
    ) -> Profile | None:
        """Get a LinkedIn profile.

        Args:
            profile_url: Full LinkedIn profile URL
            username: LinkedIn username/slug (e.g. "johndoe")
            headed: Use visible browser
        """
        if not profile_url and not username:
            return None

        url = profile_url or f"{BASE_URL}/in/{username}/"

        context = await self._browser.new_context(
            headed=headed, session_name="linkedin"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # Check for auth wall
            if await self._is_auth_wall(page):
                logger.warning("Auth wall detected — login required")
                # Try public view
                profile = await self._extract_public_profile(page)
                if profile and profile.name:
                    return profile
                return None

            profile = await self._extract_profile(page)
            await self._browser.save_session(context, "linkedin")
            return profile

        except Exception as e:
            logger.error(f"Profile fetch failed: {e}")
            return None
        finally:
            await page.close()
            await context.close()

    async def search_people(
        self,
        query: str,
        location: str = "",
        company: str = "",
        title: str = "",
        max_results: int = 20,
        headed: bool = False,
    ) -> SearchResult:
        """Search for people on LinkedIn.

        Requires login session for full results.

        Args:
            query: Search keywords
            location: Filter by location
            company: Filter by current company
            title: Filter by current title
            max_results: Maximum results (default 20)
            headed: Use visible browser
        """
        params = {"keywords": query, "origin": "GLOBAL_SEARCH_HEADER"}
        if location:
            params["geoUrn"] = location
        if company:
            params["company"] = company
        if title:
            params["title"] = title

        url = f"{BASE_URL}/search/results/people/?{urlencode(params)}"

        context = await self._browser.new_context(
            headed=headed, session_name="linkedin"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            if await self._is_auth_wall(page):
                return SearchResult(
                    query=query,
                    result_type="people",
                    results=[{"error": "Login required for people search"}],
                )

            result = await self._extract_people_search(page, query, max_results)
            await self._browser.save_session(context, "linkedin")
            return result

        except Exception as e:
            logger.error(f"People search failed: {e}")
            return SearchResult(query=query, result_type="people")
        finally:
            await page.close()
            await context.close()

    async def search_jobs(
        self,
        query: str,
        location: str = "",
        remote: str = "",
        job_type: str = "",
        experience: str = "",
        max_results: int = 25,
        headed: bool = False,
    ) -> SearchResult:
        """Search for jobs on LinkedIn (works without login).

        Args:
            query: Job title or keywords
            location: Location filter
            remote: "remote", "onsite", "hybrid"
            job_type: "full-time", "part-time", "contract", "internship"
            experience: "internship", "entry", "associate", "mid-senior", "director", "executive"
            max_results: Maximum results (default 25)
            headed: Use visible browser
        """
        params = {"keywords": quote_plus(query), "position": 1, "pageNum": 0}
        if location:
            params["location"] = location

        # Remote filter
        remote_map = {"remote": "2", "onsite": "1", "hybrid": "3"}
        if remote and remote.lower() in remote_map:
            params["f_WT"] = remote_map[remote.lower()]

        # Job type filter
        type_map = {
            "full-time": "F", "part-time": "P",
            "contract": "C", "internship": "I", "temporary": "T",
        }
        if job_type and job_type.lower() in type_map:
            params["f_JT"] = type_map[job_type.lower()]

        # Experience level
        exp_map = {
            "internship": "1", "entry": "2", "associate": "3",
            "mid-senior": "4", "director": "5", "executive": "6",
        }
        if experience and experience.lower() in exp_map:
            params["f_E"] = exp_map[experience.lower()]

        url = f"{BASE_URL}/jobs/search/?{urlencode(params)}"

        context = await self._browser.new_context(
            headed=headed, session_name="linkedin"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            result = await self._extract_job_search(page, query, max_results)
            await self._browser.save_session(context, "linkedin")
            return result

        except Exception as e:
            logger.error(f"Job search failed: {e}")
            return SearchResult(query=query, result_type="jobs")
        finally:
            await page.close()
            await context.close()

    async def get_company(
        self,
        company_url: str = "",
        company_slug: str = "",
        headed: bool = False,
    ) -> Company | None:
        """Get company page data.

        Args:
            company_url: Full LinkedIn company URL
            company_slug: Company slug (e.g. "google")
            headed: Use visible browser
        """
        if not company_url and not company_slug:
            return None

        url = company_url or f"{BASE_URL}/company/{company_slug}/"

        context = await self._browser.new_context(
            headed=headed, session_name="linkedin"
        )
        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            company = await self._extract_company(page)
            await self._browser.save_session(context, "linkedin")
            return company

        except Exception as e:
            logger.error(f"Company fetch failed: {e}")
            return None
        finally:
            await page.close()
            await context.close()

    # --- Extraction helpers ---

    async def _is_auth_wall(self, page) -> bool:
        """Check if LinkedIn is showing an auth wall."""
        try:
            indicators = [
                'a[href*="/login"]',
                'button:has-text("Sign in")',
                'div.authwall-join-form',
                'section.auth-wall',
            ]
            for selector in indicators:
                if await page.locator(selector).count() > 0:
                    # Might be a CTA on a public page, check if content is visible
                    main_content = page.locator("main, section.profile, .scaffold-layout")
                    if await main_content.count() == 0:
                        return True
        except Exception:
            pass
        return False

    async def _extract_profile(self, page) -> Profile:
        """Extract profile from an authenticated LinkedIn page."""
        profile = Profile()
        profile.profile_url = page.url

        # Name
        try:
            name_el = page.locator("h1").first
            profile.name = (await name_el.inner_text()).strip()
        except Exception:
            pass

        # Headline
        try:
            headline_el = page.locator(
                'div.text-body-medium, div[data-generated-suggestion-target]'
            ).first
            profile.headline = (await headline_el.inner_text()).strip()
        except Exception:
            pass

        # Location
        try:
            loc_el = page.locator(
                'span.text-body-small:has-text(","), '
                'span.text-body-small[class*="inline"]'
            ).first
            profile.location = (await loc_el.inner_text()).strip()
        except Exception:
            pass

        # About
        try:
            about_section = page.locator('#about ~ div, section:has(#about)').first
            about_text = page.locator(
                '#about ~ div span[aria-hidden="true"], '
                'section:has(#about) span[aria-hidden="true"]'
            ).first
            profile.about = (await about_text.inner_text()).strip()
        except Exception:
            pass

        # Current position
        try:
            exp_item = page.locator(
                '#experience ~ div li, section:has(#experience) li'
            ).first
            title_el = exp_item.locator(
                'span[aria-hidden="true"]'
            ).first
            profile.current_title = (await title_el.inner_text()).strip()

            company_el = exp_item.locator(
                'span[aria-hidden="true"]'
            ).nth(1)
            profile.current_company = (await company_el.inner_text()).strip()
        except Exception:
            pass

        # Connections
        try:
            conn_el = page.locator(
                'span:has-text("connection"), span:has-text("follower")'
            ).first
            profile.connections = (await conn_el.inner_text()).strip()
        except Exception:
            pass

        # Skills
        try:
            skills_section = page.locator(
                '#skills ~ div li span[aria-hidden="true"], '
                'section:has(#skills) li span[aria-hidden="true"]'
            )
            count = await skills_section.count()
            for i in range(min(count, 20)):
                skill = (await skills_section.nth(i).inner_text()).strip()
                if skill and skill not in profile.skills:
                    profile.skills.append(skill)
        except Exception:
            pass

        return profile

    async def _extract_public_profile(self, page) -> Profile:
        """Extract what's available from a public (non-logged-in) profile view."""
        profile = Profile()
        profile.profile_url = page.url

        try:
            name_el = page.locator("h1").first
            profile.name = (await name_el.inner_text()).strip()
        except Exception:
            pass

        try:
            headline_el = page.locator("h2, div.top-card-layout__headline").first
            profile.headline = (await headline_el.inner_text()).strip()
        except Exception:
            pass

        try:
            loc_el = page.locator(
                'span.top-card__subline-item, div.top-card-layout__first-subline span'
            ).first
            profile.location = (await loc_el.inner_text()).strip()
        except Exception:
            pass

        return profile

    async def _extract_people_search(
        self, page, query: str, max_results: int
    ) -> SearchResult:
        """Extract people search results."""
        result = SearchResult(query=query, result_type="people")

        # Result count
        try:
            count_el = page.locator("div.search-results-container h2").first
            result.total_count = (await count_el.inner_text()).strip()
        except Exception:
            pass

        # Result items
        items = page.locator(
            'li.reusable-search__result-container, '
            'div[data-view-name="search-entity-result-universal-template"]'
        )
        count = await items.count()

        for i in range(min(count, max_results)):
            item = items.nth(i)
            try:
                person = {}

                # Name + link
                link = item.locator('a[href*="/in/"]').first
                person["profile_url"] = await link.get_attribute("href") or ""
                name_el = item.locator('span[aria-hidden="true"]').first
                person["name"] = (await name_el.inner_text()).strip()

                # Headline
                try:
                    hl = item.locator('div.entity-result__primary-subtitle').first
                    person["headline"] = (await hl.inner_text()).strip()
                except Exception:
                    pass

                # Location
                try:
                    loc = item.locator('div.entity-result__secondary-subtitle').first
                    person["location"] = (await loc.inner_text()).strip()
                except Exception:
                    pass

                if person.get("name"):
                    result.results.append(person)

            except Exception:
                continue

        return result

    async def _extract_job_search(
        self, page, query: str, max_results: int
    ) -> SearchResult:
        """Extract job search results."""
        result = SearchResult(query=query, result_type="jobs")

        # Result count
        try:
            count_el = page.locator(
                'div.jobs-search-results-list__subtitle, '
                'small.jobs-search-results-list__text'
            ).first
            result.total_count = (await count_el.inner_text()).strip()
        except Exception:
            pass

        # Job cards
        items = page.locator(
            'li.jobs-search-results__list-item, '
            'div.job-search-card'
        )
        count = await items.count()

        for i in range(min(count, max_results)):
            item = items.nth(i)
            try:
                job = {}

                # Title
                title_el = item.locator(
                    'a.job-card-list__title, h3.base-search-card__title'
                ).first
                job["title"] = (await title_el.inner_text()).strip()
                href = await title_el.get_attribute("href") or ""
                job["job_url"] = href

                # Company
                try:
                    co = item.locator(
                        'a.job-card-container__company-name, '
                        'h4.base-search-card__subtitle a'
                    ).first
                    job["company"] = (await co.inner_text()).strip()
                except Exception:
                    pass

                # Location
                try:
                    loc = item.locator(
                        'li.job-card-container__metadata-item, '
                        'span.job-search-card__location'
                    ).first
                    job["location"] = (await loc.inner_text()).strip()
                except Exception:
                    pass

                # Posted date
                try:
                    date_el = item.locator('time, span:has-text("ago")').first
                    job["posted_date"] = (await date_el.inner_text()).strip()
                except Exception:
                    pass

                if job.get("title"):
                    result.results.append(job)

            except Exception:
                continue

        return result

    async def _extract_company(self, page) -> Company:
        """Extract company page data."""
        company = Company()
        company.company_url = page.url

        # Name
        try:
            name_el = page.locator("h1").first
            company.name = (await name_el.inner_text()).strip()
        except Exception:
            pass

        # Tagline
        try:
            tagline_el = page.locator(
                'p.org-top-card-summary__tagline, '
                'p.top-card-layout__headline'
            ).first
            company.tagline = (await tagline_el.inner_text()).strip()
        except Exception:
            pass

        # About section details
        detail_items = page.locator(
            'dl.overflow-hidden dt, '
            'div.org-page-details__definition-term'
        )
        detail_values = page.locator(
            'dl.overflow-hidden dd, '
            'div.org-page-details__definition-text'
        )

        dt_count = await detail_items.count()
        dd_count = await detail_values.count()

        for i in range(min(dt_count, dd_count)):
            try:
                label = (await detail_items.nth(i).inner_text()).strip().lower()
                value = (await detail_values.nth(i).inner_text()).strip()

                if "website" in label:
                    company.website = value
                elif "industry" in label:
                    company.industry = value
                elif "company size" in label or "size" in label:
                    company.company_size = value
                elif "headquarter" in label:
                    company.headquarters = value
                elif "founded" in label:
                    company.founded = value
                elif "specialties" in label or "specialities" in label:
                    company.specialties = [
                        s.strip() for s in value.split(",") if s.strip()
                    ]
            except Exception:
                continue

        # About text
        try:
            about_el = page.locator(
                'section.org-about-us-organization-description p, '
                'p[data-test-id="about-us__description"]'
            ).first
            company.about = (await about_el.inner_text()).strip()
        except Exception:
            pass

        return company

    async def cleanup(self):
        if self._own_browser:
            await self._browser.cleanup()
