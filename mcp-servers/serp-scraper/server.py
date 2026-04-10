"""
SERP Scraper MCP Server

Extract search engine results from Google and Bing — organic results,
ads, featured snippets, People Also Ask, and related searches.

Tools:
  - search_google: Google search with full SERP extraction
  - search_bing: Bing search with structured results
  - keyword_research: Multi-query analysis for SEO research
  - check_ranking: Check where a domain ranks for a keyword

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
from scraper import SerpScraper
from stealth_browser import StealthBrowser


@dataclass
class AppContext:
    scraper: SerpScraper
    browser: StealthBrowser


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    browser = StealthBrowser()
    scraper = SerpScraper(browser=browser)
    try:
        yield AppContext(scraper=scraper, browser=browser)
    finally:
        await scraper.cleanup()


mcp = FastMCP(
    "SERP Scraper",
    instructions=(
        "Search engine results scraper — extract organic results, ads, "
        "featured snippets, People Also Ask, and related searches from "
        "Google and Bing.\n\n"
        "Use cases:\n"
        "- SEO research: check rankings, analyze SERPs, find content gaps\n"
        "- Competitor analysis: see who ranks for target keywords\n"
        "- Content research: find topics via PAA and related searches\n"
        "- Ad intelligence: see who's bidding on keywords\n\n"
        "All data is scraped live from search engines — never cached."
    ),
    lifespan=app_lifespan,
)


@mcp.tool()
async def search_google(
    query: str,
    num_results: int = 10,
    page: int = 1,
    language: str = "en",
    country: str = "",
) -> str:
    """Search Google and extract full SERP data.

    Args:
        query: Search query
        num_results: Results per page (10, 20, 50, 100)
        page: Page number (1-based)
        language: Language code (e.g. "en", "ar", "fr")
        country: Country code for localization (e.g. "ae", "us", "uk")

    Returns:
        JSON with organic results, ads, featured snippet, PAA, related searches
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    result = await ctx.scraper.search_google(
        query=query,
        num_results=num_results,
        page=page,
        language=language,
        country=country,
    )

    return json.dumps(result.to_dict(), indent=2)


@mcp.tool()
async def search_bing(
    query: str,
    num_results: int = 10,
    page: int = 1,
) -> str:
    """Search Bing and extract structured results.

    Args:
        query: Search query
        num_results: Results per page (default 10)
        page: Page number (1-based)

    Returns:
        JSON with organic results and related searches
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    result = await ctx.scraper.search_bing(
        query=query,
        num_results=num_results,
        page=page,
    )

    return json.dumps(result.to_dict(), indent=2)


@mcp.tool()
async def keyword_research(
    keywords: list[str],
    country: str = "",
) -> str:
    """Analyze multiple keywords for SEO research.

    Searches each keyword on Google and returns aggregated data:
    organic results, PAA questions, and related searches.

    Args:
        keywords: List of keywords to research (max 10)
        country: Country code for localization (e.g. "ae", "us")

    Returns:
        JSON with per-keyword SERP data and aggregated insights
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context
    keywords = keywords[:10]  # Limit to avoid rate limiting

    results = {}
    all_paa = []
    all_related = []

    for kw in keywords:
        serp = await ctx.scraper.search_google(
            query=kw,
            num_results=10,
            country=country,
        )
        results[kw] = serp.to_dict()
        all_paa.extend([p.question for p in serp.people_also_ask])
        all_related.extend(serp.related_searches)

        # Small delay between requests to avoid rate limiting
        await asyncio.sleep(2)

    # Deduplicate aggregated data
    unique_paa = list(dict.fromkeys(all_paa))
    unique_related = list(dict.fromkeys(all_related))

    return json.dumps(
        {
            "keywords": results,
            "all_paa_questions": unique_paa,
            "all_related_searches": unique_related,
            "keyword_count": len(keywords),
        },
        indent=2,
    )


@mcp.tool()
async def check_ranking(
    keyword: str,
    domain: str,
    num_results: int = 50,
    country: str = "",
) -> str:
    """Check where a domain ranks for a specific keyword.

    Args:
        keyword: Search query to check
        domain: Domain to look for (e.g. "example.com")
        num_results: How many results to check (default 50)
        country: Country code (e.g. "ae", "us")

    Returns:
        JSON with ranking position, URL, and surrounding competitors
    """
    ctx: AppContext = mcp.get_context().request_context.lifespan_context

    serp = await ctx.scraper.search_google(
        query=keyword,
        num_results=num_results,
        country=country,
    )

    domain_lower = domain.lower().replace("www.", "")
    found = None
    competitors = []

    for result in serp.organic:
        result_domain = result.domain.lower().replace("www.", "")
        if domain_lower in result_domain:
            found = result
        else:
            competitors.append(
                {
                    "position": result.position,
                    "domain": result.domain,
                    "title": result.title,
                }
            )

    output = {
        "keyword": keyword,
        "domain": domain,
        "total_results": serp.total_results,
    }

    if found:
        output["ranking"] = {
            "position": found.position,
            "url": found.url,
            "title": found.title,
            "snippet": found.snippet,
        }
    else:
        output["ranking"] = {
            "position": None,
            "message": f"{domain} not found in top {num_results} results",
        }

    output["top_competitors"] = competitors[:10]

    return json.dumps(output, indent=2)


# --- Resources ---

@mcp.resource("serp://config")
def get_config() -> str:
    """Current server configuration."""
    return json.dumps(
        {
            "server": "SERP Scraper",
            "version": "0.1.0",
            "engines": ["google", "bing"],
            "captcha_solver": "available" if os.path.exists(
                os.path.join(os.path.dirname(__file__), "..", "captcha-solver")
            ) else "not_available",
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
