# SERP Scraper MCP

Extract structured search results from Google and Bing for AI agents. Organic results, ads, featured snippets, People Also Ask, related searches -- all parsed and structured.

**Free alternative to SerpApi ($50/mo), DataForSEO ($50/mo), and Serper.dev ($50/mo).**

## Why This Tool?

| Feature | This Tool | SerpApi | DataForSEO | Serper.dev |
|---------|-----------|---------|------------|------------|
| Free to use | Yes | $50/mo | $50/mo | $50/mo |
| MCP server (for AI agents) | Yes | No | No | No |
| Organic results | Yes | Yes | Yes | Yes |
| Ads extraction | Yes | Yes | Yes | No |
| Featured snippets | Yes | Yes | Yes | Yes |
| People Also Ask | Yes | Yes | Yes | Yes |
| Related searches | Yes | Yes | Yes | Yes |
| Keyword research | Yes | No | Yes | No |
| Rank checking | Yes | No | Yes | No |
| Google + Bing | Yes | Yes | Yes | Google only |
| No API key needed | Yes | No | No | No |

## How It Works

Stealth browser loads the search page, parses the DOM, and returns structured data. No API keys, no rate limits (beyond Google's natural limits), no monthly fees.

Can integrate with the CAPTCHA Solver MCP (sibling project) when Google shows CAPTCHAs.

## Quick Start

### As MCP Server (Claude Desktop, Cursor, etc.)

```json
{
  "mcpServers": {
    "serp-scraper": {
      "command": "python",
      "args": ["/path/to/mcp-servers/serp-scraper/server.py"]
    }
  }
}
```

Install dependencies:

```bash
pip install "mcp[cli]" playwright playwright-stealth
playwright install chromium
```

## Tools

### `search_google`

Full Google SERP extraction.

```json
{"query": "best crm software 2025", "num_results": 20, "country": "us"}
```

Example output:
```json
{
  "query": "best crm software 2025",
  "total_results": "About 234,000,000 results",
  "organic": [
    {
      "position": 1,
      "title": "The 10 Best CRM Software of 2025",
      "url": "https://www.forbes.com/advisor/crm/best-crm-software/",
      "domain": "www.forbes.com",
      "snippet": "Compare the best CRM software solutions..."
    }
  ],
  "ads": [
    {
      "position": 1,
      "title": "HubSpot CRM - Free Forever",
      "url": "https://www.hubspot.com/crm",
      "domain": "www.hubspot.com",
      "is_top": true
    }
  ],
  "featured_snippet": {
    "text": "The best CRM software includes Salesforce, HubSpot...",
    "source_url": "https://www.forbes.com/...",
    "snippet_type": "paragraph"
  },
  "people_also_ask": [
    {"question": "What is the #1 CRM software?", "answer": "..."},
    {"question": "Is HubSpot CRM really free?", "answer": "..."}
  ],
  "related_searches": [
    "best free crm software",
    "crm software for small business",
    "salesforce vs hubspot"
  ]
}
```

### `search_bing`

Bing search with structured results.

```json
{"query": "python developer jobs remote", "num_results": 20}
```

### `keyword_research`

Analyze multiple keywords at once. Returns per-keyword SERP data plus aggregated PAA questions and related searches -- great for content planning.

```json
{"keywords": ["crm software", "crm tools", "best crm"], "country": "us"}
```

### `check_ranking`

Check where a specific domain ranks for a keyword.

```json
{"keyword": "best crm software", "domain": "hubspot.com", "num_results": 50}
```

Output:
```json
{
  "keyword": "best crm software",
  "domain": "hubspot.com",
  "ranking": {
    "position": 3,
    "url": "https://www.hubspot.com/products/crm",
    "title": "Free CRM Software & Tools for Your Whole Team | HubSpot"
  },
  "top_competitors": [
    {"position": 1, "domain": "forbes.com"},
    {"position": 2, "domain": "pcmag.com"}
  ]
}
```

## Use Cases

- **SEO auditing**: Check where your site ranks for target keywords
- **Competitor analysis**: See who ranks above you and what ads they run
- **Content research**: Mine PAA questions and related searches for content ideas
- **Ad intelligence**: See who's bidding on your keywords
- **Market research**: Understand search landscape for any niche

## CAPTCHA Handling

Google occasionally shows CAPTCHAs for automated requests. When the sibling `captcha-solver` MCP server is installed (`../captcha-solver`), it will attempt to solve them automatically.

## Performance

- Session persistence reduces consent dialogs
- 2-second delay between multi-keyword requests (avoids rate limiting)
- Stealth browser with anti-detection

## License

MIT
