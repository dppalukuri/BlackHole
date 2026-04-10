"""
Data models for SERP Scraper.
"""

from dataclasses import dataclass, field, asdict


@dataclass
class OrganicResult:
    """A single organic search result."""

    position: int = 0
    title: str = ""
    url: str = ""
    domain: str = ""
    snippet: str = ""
    date: str = ""
    cached_url: str = ""
    sitelinks: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class AdResult:
    """A paid ad result."""

    position: int = 0
    title: str = ""
    url: str = ""
    domain: str = ""
    description: str = ""
    is_top: bool = True  # Top vs bottom ads

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class FeaturedSnippet:
    """A featured snippet / answer box."""

    text: str = ""
    source_url: str = ""
    source_title: str = ""
    snippet_type: str = ""  # paragraph, list, table

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class PeopleAlsoAsk:
    """A People Also Ask question."""

    question: str = ""
    answer: str = ""
    source_url: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class SerpResult:
    """Complete SERP result for a query."""

    query: str = ""
    total_results: str = ""  # "About 1,230,000 results"
    organic: list[OrganicResult] = field(default_factory=list)
    ads: list[AdResult] = field(default_factory=list)
    featured_snippet: FeaturedSnippet | None = None
    people_also_ask: list[PeopleAlsoAsk] = field(default_factory=list)
    related_searches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        result = {"query": self.query}
        if self.total_results:
            result["total_results"] = self.total_results
        if self.organic:
            result["organic"] = [r.to_dict() for r in self.organic]
        if self.ads:
            result["ads"] = [a.to_dict() for a in self.ads]
        if self.featured_snippet:
            result["featured_snippet"] = self.featured_snippet.to_dict()
        if self.people_also_ask:
            result["people_also_ask"] = [p.to_dict() for p in self.people_also_ask]
        if self.related_searches:
            result["related_searches"] = self.related_searches
        return result
