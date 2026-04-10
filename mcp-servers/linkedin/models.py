"""
Data models for LinkedIn Scraper.
"""

from dataclasses import dataclass, field, asdict


@dataclass
class Profile:
    """A LinkedIn profile."""

    name: str = ""
    headline: str = ""
    location: str = ""
    profile_url: str = ""
    avatar_url: str = ""
    about: str = ""
    current_company: str = ""
    current_title: str = ""
    connections: str = ""  # "500+", "1K", etc.
    experience: list = field(default_factory=list)  # list of dicts
    education: list = field(default_factory=list)  # list of dicts
    skills: list = field(default_factory=list)  # list of strings
    certifications: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class Job:
    """A LinkedIn job posting."""

    title: str = ""
    company: str = ""
    location: str = ""
    job_url: str = ""
    job_id: str = ""
    posted_date: str = ""
    applicants: str = ""
    employment_type: str = ""  # Full-time, Part-time, Contract
    seniority: str = ""  # Entry, Mid-Senior, Director, etc.
    description: str = ""
    salary: str = ""
    remote: str = ""  # Remote, On-site, Hybrid
    company_logo: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class Company:
    """A LinkedIn company page."""

    name: str = ""
    tagline: str = ""
    industry: str = ""
    company_size: str = ""
    headquarters: str = ""
    website: str = ""
    founded: str = ""
    company_url: str = ""
    logo_url: str = ""
    about: str = ""
    specialties: list = field(default_factory=list)
    employee_count: str = ""

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class SearchResult:
    """A LinkedIn search result (people, jobs, or companies)."""

    query: str = ""
    result_type: str = ""  # "people", "jobs", "companies"
    total_count: str = ""
    results: list = field(default_factory=list)  # list of Profile/Job/Company dicts

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "type": self.result_type,
            "total_count": self.total_count,
            "results": self.results,
            "count": len(self.results),
        }
