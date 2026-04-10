# Google Maps Extractor MCP

AI-powered lead generation from Google Maps. Search businesses, enrich with emails/phones/socials, score leads, and export to CSV -- all from your AI agent.

**Not just a scraper. A complete lead gen pipeline that replaces $200/month tools like Apollo and Hunter.io.**

## Why This Tool?

| Feature | This Tool | Apollo.io | Hunter.io | Outscraper |
|---------|-----------|-----------|-----------|------------|
| Free to use | Yes | $49/mo | $49/mo | Pay-per-row |
| MCP server (for AI agents) | Yes | No | No | No |
| Email discovery | Yes | Yes | Yes | No |
| Social links | Yes | Limited | No | No |
| Tech stack detection | Yes | No | No | No |
| Lead scoring | Yes | Yes | No | No |
| Google Maps search | Yes | No | No | Yes |
| Cross-platform (SERP + LinkedIn) | Yes | Partial | No | No |
| CSV/JSON export | Yes | Yes | Yes | Yes |
| No API key needed | Yes | No | No | No |

## How It Works

```
Google Maps search
  --> Detail extraction (phone, website, address, rating)
    --> Website enrichment (emails, socials, tech stack)
      --> SERP ranking check (optional)
        --> LinkedIn company lookup (optional)
          --> Lead scoring (0-100)
            --> Export CSV/JSON
```

One command to your AI agent:

> "Find me 20 dental clinics in Dubai with their emails and phone numbers, export as CSV"

## Quick Start

### As MCP Server (Claude Desktop, Cursor, etc.)

Add to your MCP client config:

```json
{
  "mcpServers": {
    "google-maps": {
      "command": "python",
      "args": ["/path/to/mcp-servers/google-maps/server.py"]
    }
  }
}
```

No API keys needed. Install dependencies:

```bash
pip install "mcp[cli]" playwright playwright-stealth
playwright install chromium
```

### With Docker

```bash
docker build -t google-maps-mcp .
docker run google-maps-mcp
```

## Tools

### `search_businesses`
Quick Google Maps search. Returns name, rating, address, category.

```json
{"query": "restaurants", "location": "Dubai Marina", "max_results": 20}
```

### `find_leads` (the main tool)
Search + enrich + score. Returns emails, phones, socials, tech stack, lead score.

```json
{"query": "real estate agencies", "location": "Miami", "max_results": 20, "enrich": true}
```

Example output:
```json
{
  "leads": [
    {
      "name": "Sunshine Realty Group",
      "lead_score": 85,
      "rating": 4.8,
      "review_count": 127,
      "phone": "+1 (305) 555-0123",
      "website": "https://sunshinerealty.com",
      "emails": ["john.smith@sunshinerealty.com", "info@sunshinerealty.com"],
      "social_links": {
        "linkedin": "https://linkedin.com/company/sunshine-realty",
        "instagram": "https://instagram.com/sunshinerealty",
        "facebook": "https://facebook.com/SunshineRealtyMiami"
      },
      "tech_stack": ["WordPress", "Google Analytics", "HubSpot"],
      "address": "1234 Brickell Ave, Miami, FL 33131",
      "maps_url": "https://maps.google.com/..."
    }
  ],
  "count": 20,
  "avg_score": 62.4,
  "enriched": true
}
```

### `generate_lead_report`
Full pipeline with optional SERP ranking + LinkedIn company data.

```json
{
  "query": "plumbers",
  "location": "London",
  "max_results": 15,
  "check_seo": true,
  "check_linkedin": false
}
```

### `get_business_details`
Deep-dive on a single business.

```json
{"maps_url": "https://maps.google.com/maps/place/..."}
```

### `get_reviews`
Customer reviews for sentiment analysis.

```json
{"maps_url": "...", "max_reviews": 50, "sort_by": "newest"}
```

### `export_leads`
Export last results to CSV or JSON file.

```json
{"format": "csv"}
```

CSV columns: `lead_score, name, category, rating, review_count, phone, email, website, address, linkedin, facebook, instagram, twitter, tech_stack`

## Lead Scoring

Every lead gets a score from 0-100:

| Signal | Points |
|--------|--------|
| Personal email (john.doe@...) | 25 |
| Any email | 15 |
| Phone number | 15 |
| Website | 10 |
| Social media links (5 each) | max 15 |
| Rating >= 4.0 | 10 |
| 50+ reviews | 10 |
| Has address | 5 |

Leads are sorted by score -- highest quality first.

## Website Enrichment

When `enrich=true`, the tool visits each business website and extracts:

- **Emails**: From homepage + /contact + /about pages. Ranked by quality (personal > role-based > generic). Filters out noreply@, postmaster@, etc.
- **Social links**: LinkedIn, Facebook, Instagram, Twitter/X, YouTube, TikTok
- **Phone numbers**: From `tel:` links and visible text
- **Tech stack**: WordPress, Shopify, Wix, React, HubSpot, Intercom, Zendesk, Google Analytics, and more

Results are cached for 24 hours to avoid re-scraping.

## Cross-Server Integration

When sibling MCP servers from the BlackHole suite are installed:

- **SERP Scraper**: Checks if leads rank on Google for the search query
- **LinkedIn Scraper**: Pulls company data (size, industry, specialties)

Both are optional -- works standalone without them.

## Performance

- Browser geolocation auto-matched to 30+ cities worldwide
- Concurrent enrichment (3 parallel websites)
- Retry with exponential backoff on failures
- 24-hour result cache to avoid redundant scraping
- Headless browser with stealth anti-detection

## License

MIT
