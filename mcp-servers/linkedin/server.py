"""
LinkedIn Scraper MCP Server

Extract profiles, job postings, and company data from LinkedIn.

Tools:
  - login: Open browser for manual LinkedIn login (saves session)
  - get_profile: Get a LinkedIn profile by URL or username
  - search_people: Search for people (requires login session)
  - search_jobs: Search for job postings (works without login)
  - get_company: Get company page data

Run:
  python server.py
"""

import os
import sys
import json
import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from scraper import LinkedInScraper
from stealth_browser import StealthBrowser

SESSION_DIR = Path(__file__).parent / ".sessions"


@dataclass
class AppContext:
    scraper: LinkedInScraper
    browser: StealthBrowser


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    browser = StealthBrowser()
    scraper = LinkedInScraper(browser=browser)
    try:
        yield AppContext(scraper=scraper, browser=browser)
    finally:
        await scraper.cleanup()


mcp = FastMCP(
    "LinkedIn Scraper",
    instructions=(
        "Extract data from LinkedIn — profiles, jobs, and companies.\n\n"
        "IMPORTANT: Some features require a logged-in session:\n"
        "- Job search: works WITHOUT login\n"
        "- Public profiles: partial data without login\n"
        "- People search: REQUIRES login\n"
        "- Full profiles: REQUIRES login\n\n"
        "If the user needs login-required features, use the `login` tool first.\n"
        "This opens a browser for them to log in manually. The session is saved\n"
        "and reused for subsequent requests.\n\n"
        "Rate limiting: LinkedIn is aggressive — avoid rapid-fire requests.\n"
        "All data is scraped live from LinkedIn pages."
    ),
    lifespan=app_lifespan,
)


def _has_session() -> bool:
    """Check if a LinkedIn session exists."""
    return (SESSION_DIR / "linkedin.json").exists()


@mcp.tool()
async def login() -> str:
    """Open a browser window for manual LinkedIn login.

    This opens a visible browser where you can log in to LinkedIn.
    The session cookies are saved for subsequent headless scraping.
    You only need to do this once — the session persists across restarts.

    Returns:
        JSON with login status
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    success = await ctx.scraper.login()

    if success:
        return json.dumps({
            "status": "success",
            "message": "LinkedIn session saved. You can now use all tools.",
        })
    else:
        return json.dumps({
            "status": "failed",
            "message": "Login was not completed. Try again with the login tool.",
        })


@mcp.tool()
async def get_profile(
    profile_url: str = "",
    username: str = "",
) -> str:
    """Get a LinkedIn profile.

    Provide either a full profile URL or a username.
    Full profiles require a login session.

    Args:
        profile_url: Full LinkedIn URL (e.g. "https://www.linkedin.com/in/johndoe/")
        username: LinkedIn username (e.g. "johndoe")

    Returns:
        JSON with profile data: name, headline, location, experience, skills
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    if not profile_url and not username:
        return json.dumps({"error": "Provide either profile_url or username"})

    profile = await ctx.scraper.get_profile(
        profile_url=profile_url,
        username=username,
    )

    if not profile:
        msg = "Could not fetch profile."
        if not _has_session():
            msg += " Try logging in first with the login tool for full access."
        return json.dumps({"error": msg})

    return json.dumps(profile.to_dict(), indent=2)


@mcp.tool()
async def search_people(
    query: str,
    location: str = "",
    company: str = "",
    title: str = "",
    max_results: int = 20,
) -> str:
    """Search for people on LinkedIn.

    REQUIRES login session. Use the login tool first if not logged in.

    Args:
        query: Search keywords (e.g. "software engineer")
        location: Filter by location
        company: Filter by current company
        title: Filter by current title
        max_results: Maximum results (default 20)

    Returns:
        JSON array of people with name, headline, location, profile URL
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    if not _has_session():
        return json.dumps({
            "error": "Login required for people search. Use the login tool first.",
        })

    result = await ctx.scraper.search_people(
        query=query,
        location=location,
        company=company,
        title=title,
        max_results=min(max_results, 50),
    )

    return json.dumps(result.to_dict(), indent=2)


@mcp.tool()
async def search_jobs(
    query: str,
    location: str = "",
    remote: str = "",
    job_type: str = "",
    experience: str = "",
    max_results: int = 25,
) -> str:
    """Search for jobs on LinkedIn. Works without login.

    Args:
        query: Job title or keywords (e.g. "python developer")
        location: Location filter (e.g. "Dubai", "Remote")
        remote: "remote", "onsite", or "hybrid"
        job_type: "full-time", "part-time", "contract", "internship"
        experience: "entry", "mid-senior", "director", "executive"
        max_results: Maximum results (default 25)

    Returns:
        JSON array of jobs with title, company, location, posted date
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    result = await ctx.scraper.search_jobs(
        query=query,
        location=location,
        remote=remote,
        job_type=job_type,
        experience=experience,
        max_results=min(max_results, 50),
    )

    return json.dumps(result.to_dict(), indent=2)


@mcp.tool()
async def get_company(
    company_url: str = "",
    company_slug: str = "",
) -> str:
    """Get LinkedIn company page data.

    Args:
        company_url: Full company URL (e.g. "https://www.linkedin.com/company/google/")
        company_slug: Company slug (e.g. "google")

    Returns:
        JSON with company data: name, industry, size, website, about
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    if not company_url and not company_slug:
        return json.dumps({"error": "Provide either company_url or company_slug"})

    company = await ctx.scraper.get_company(
        company_url=company_url,
        company_slug=company_slug,
    )

    if not company:
        return json.dumps({"error": "Could not fetch company data"})

    return json.dumps(company.to_dict(), indent=2)


# --- Resources ---

@mcp.resource("linkedin://config")
def get_config() -> str:
    """Current server configuration and login status."""
    return json.dumps(
        {
            "server": "LinkedIn Scraper",
            "version": "0.1.0",
            "logged_in": _has_session(),
            "capabilities": {
                "without_login": ["search_jobs", "get_company", "get_profile (partial)"],
                "with_login": ["search_people", "get_profile (full)"],
            },
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
