# Google Maps Lead Extractor

Extract business leads from Google Maps with email/phone enrichment and lead scoring.

## What it does

1. **Searches** Google Maps for businesses by type and location
2. **Extracts** phone, website, address, rating, review count
3. **Enriches** by visiting each website for emails, social links, tech stack
4. **Scores** each lead 0-100 based on data completeness
5. **Exports** structured data to Apify dataset

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Business type (e.g. "restaurants", "plumbers") |
| `location` | string | Yes | Location (e.g. "Dubai", "Miami") |
| `maxResults` | integer | No | Max results (default 20, max 60) |
| `enrichWebsites` | boolean | No | Visit websites for emails/socials (default true) |
| `minRating` | number | No | Minimum Google rating filter (default 0) |

## Output

Each result includes:

```json
{
  "name": "Business Name",
  "lead_score": 85,
  "rating": 4.8,
  "review_count": 127,
  "phone": "+1 (305) 555-0123",
  "website": "https://example.com",
  "emails": ["owner@example.com", "info@example.com"],
  "social_links": {
    "linkedin": "https://linkedin.com/company/example",
    "facebook": "https://facebook.com/example"
  },
  "tech_stack": ["WordPress", "Google Analytics"],
  "address": "123 Main St, Miami, FL",
  "maps_url": "https://maps.google.com/..."
}
```

## Lead Scoring

| Signal | Points |
|--------|--------|
| Personal email | 25 |
| Any email | 15 |
| Phone | 15 |
| Website | 10 |
| Social links | 5 each (max 15) |
| Rating 4.0+ | 10 |
| 50+ reviews | 10 |
| Address | 5 |

## Cost

Free to use. No API keys required. Uses browser-based scraping.
