"""
Data models for Google Maps Extractor.
"""

from dataclasses import dataclass, field, asdict


@dataclass
class Business:
    """A business listing from Google Maps."""

    name: str = ""
    place_id: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: float = 0.0
    review_count: int = 0
    category: str = ""
    price_level: str = ""  # $, $$, $$$, $$$$
    hours: dict = field(default_factory=dict)
    latitude: float = 0.0
    longitude: float = 0.0
    maps_url: str = ""
    thumbnail: str = ""
    # Enriched fields
    emails: list = field(default_factory=list)
    phones: list = field(default_factory=list)  # Additional phones from website
    social_links: dict = field(default_factory=dict)
    tech_stack: list = field(default_factory=list)
    meta_description: str = ""
    # Scoring
    lead_score: int = 0

    def to_dict(self) -> dict:
        d = {k: v for k, v in asdict(self).items() if v}
        d["lead_score"] = self.lead_score  # Always include score
        return d

    def calculate_lead_score(self) -> int:
        """Score 0-100 based on data completeness and quality.

        Scoring weights:
          - Has email (personal):     25 pts
          - Has email (any):          15 pts
          - Has phone:                15 pts
          - Has website:              10 pts
          - Has social links:          5 pts per platform (max 15)
          - Rating >= 4.0:            10 pts
          - Review count >= 10:        5 pts
          - Review count >= 50:        5 pts (bonus)
          - Has address:               5 pts
        """
        score = 0

        # Email — most valuable
        if self.emails:
            score += 15
            # Bonus for personal-looking emails (contain a dot in prefix)
            if any("." in e.split("@")[0] for e in self.emails):
                score += 10

        # Phone
        if self.phone or self.phones:
            score += 15

        # Website
        if self.website:
            score += 10

        # Social links (5 each, max 15)
        social_count = len(self.social_links)
        score += min(social_count * 5, 15)

        # Rating quality
        if self.rating >= 4.0:
            score += 10
        elif self.rating >= 3.0:
            score += 5

        # Review volume
        if self.review_count >= 50:
            score += 10
        elif self.review_count >= 10:
            score += 5

        # Address
        if self.address:
            score += 5

        self.lead_score = min(score, 100)
        return self.lead_score


@dataclass
class Review:
    """A single review for a business."""

    author: str = ""
    rating: int = 0
    text: str = ""
    date: str = ""
    response: str = ""  # Owner response
    photos: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v}
