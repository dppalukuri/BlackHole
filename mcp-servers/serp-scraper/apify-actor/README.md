# SERP Scraper

Extract structured search results from Google and Bing.

## What it does

Scrapes search engine results pages and returns structured data:
- **Organic results**: title, URL, domain, snippet, position
- **Ads**: title, URL, domain, top/bottom placement
- **Featured snippets**: text, source, type
- **People Also Ask**: questions and answers
- **Related searches**: alternative query suggestions

## Input

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `queries` | string[] | Yes | Search queries (max 20) |
| `engine` | string | No | "google", "bing", or "both" (default "google") |
| `numResults` | integer | No | Results per query (default 10) |
| `country` | string | No | Country code for Google (e.g. "us", "ae") |
| `language` | string | No | Language code (default "en") |

## Output

```json
{
  "engine": "google",
  "query": "best crm software",
  "total_results": "About 234,000,000 results",
  "organic": [
    {
      "position": 1,
      "title": "The 10 Best CRM Software of 2025",
      "url": "https://www.forbes.com/...",
      "domain": "www.forbes.com",
      "snippet": "Compare the best CRM..."
    }
  ],
  "ads": [...],
  "featured_snippet": {...},
  "people_also_ask": [...],
  "related_searches": [...]
}
```

## Cost

Free to use. No API keys required.
