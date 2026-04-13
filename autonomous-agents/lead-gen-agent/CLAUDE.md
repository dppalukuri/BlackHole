# Autonomous Lead Generation Agent

Scheduled agent that scrapes Google Maps for configured niches/cities, enriches with emails/socials, scores leads, and outputs packaged lead lists.

## Architecture

```
agent.py               — Main agent: search → enrich → score → export
config.json            — Niches, cities, and schedule configuration
output/                — Generated lead list CSVs/JSONs (gitignored)
```

## How It Works

1. Reads `config.json` for list of niches and cities
2. For each niche/city pair: searches Google Maps → gets details → enriches websites → scores leads
3. Outputs CSV/JSON files to `output/` directory
4. Can run once or on a schedule (hourly/daily/weekly)

## Usage

```bash
# Run once with all configured jobs
python agent.py

# Run a single job
python agent.py --niche "plumbers" --city "Miami" --max 30

# Run on a schedule
python agent.py --schedule daily

# Skip enrichment (faster, fewer details)
python agent.py --niche "restaurants" --city "London" --no-enrich
```

## Config

Edit `config.json` to add niches and cities:

```json
{
  "jobs": [
    {
      "niche": "restaurants",
      "cities": ["Dubai Marina", "Downtown Dubai"],
      "max_results": 20,
      "min_rating": 4.0,
      "enrich": true
    }
  ],
  "schedule": "daily",
  "output_format": "csv"
}
```

## Revenue Model

- **Sell lead lists**: Package CSVs by niche/city on Gumroad ($10-50 per list)
- **Email subscription**: Weekly fresh leads delivered to subscribers
- **Your own outreach**: Use the leads for your own sales campaigns

## Dependencies

Uses `../../mcp-servers/google-maps/` for scraping and enrichment.

```bash
pip install playwright playwright-stealth
playwright install chromium
```
