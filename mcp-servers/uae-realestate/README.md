# UAE Real Estate MCP Server

An MCP (Model Context Protocol) server that gives AI assistants access to UAE property data from **Bayut**, **Dubizzle**, and **PropertyFinder**.

Search properties, analyze rental yields, compare areas, and get market insights across Dubai, Abu Dhabi, Sharjah, and all UAE emirates.

## Features

- **Unified Search** - Search across all 3 major UAE property platforms simultaneously
- **Rental Yield Calculator** - UAE-specific ROI analysis including DLD fees (4%), agency fees (2%), service charges
- **Market Snapshots** - Area-level statistics: average prices, price/sqft, breakdown by bedroom type
- **Area Comparison** - Compare multiple areas side-by-side
- **Property Details** - Detailed listing info including amenities, agent details, location

## Quick Start

### Install

```bash
# Clone the repo
git clone https://github.com/dppalukuri/BlackHole.git
cd BlackHole/mcp-servers/uae-realestate

# Install dependencies
pip install "mcp[cli]" httpx

# For Dubizzle and PropertyFinder (requires browser automation)
pip install playwright
playwright install chromium
```

### Set up Bayut API Key (free)

1. Go to https://rapidapi.com/apidojo/api/bayut
2. Sign up and get a free API key (750 calls/month)
3. Set the environment variable:

```bash
# Linux/Mac
export BAYUT_RAPIDAPI_KEY=your_key_here

# Windows
set BAYUT_RAPIDAPI_KEY=your_key_here
```

### Configure with Claude Desktop

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "uae-realestate": {
      "command": "python",
      "args": ["C:\\FULL\\PATH\\TO\\BlackHole\\mcp-servers\\uae-realestate\\server.py"],
      "env": {
        "BAYUT_RAPIDAPI_KEY": "your_key_here"
      }
    }
  }
}
```

Restart Claude Desktop after saving.

### Run Standalone (for testing)

```bash
python server.py
```

## Tools

### search_properties
Search for properties across UAE platforms.

```
location: "Dubai Marina"
purpose: "for-sale" | "for-rent"
property_type: "apartment" | "villa" | "townhouse" | "penthouse"
min_price: 0 (AED)
max_price: 0 (AED)
bedrooms: -1 (any) | 0 (studio) | 1-5
source: "all" | "bayut" | "dubizzle" | "propertyfinder"
```

### calculate_rental_yield
Calculate ROI with UAE-specific costs.

```
purchase_price: 1500000 (AED)
annual_rent: 85000 (AED)
service_charge: 15000 (AED/year)
vacancy_pct: 5 (%)
```

### get_market_snapshot
Get area-level market statistics.

### compare_areas
Compare multiple areas side-by-side.

## Supported Locations

**Emirates:** Dubai, Abu Dhabi, Sharjah, Ajman, RAK, Fujairah, UAQ

**Dubai Communities:** Dubai Marina, Downtown Dubai, Business Bay, JBR, Palm Jumeirah, Dubai Hills, Arabian Ranches, JVC, Dubai Creek Harbour, Emirates Hills, Al Barsha, DIFC, JLT, City Walk, Meydan, Damac Hills, Motor City, Sports City, Silicon Oasis, and more.

## Data Sources

| Source | Method | Requirements |
|--------|--------|-------------|
| Bayut | RapidAPI | Free API key (750 calls/month) |
| Dubizzle | Playwright | `pip install playwright` |
| PropertyFinder | Playwright | `pip install playwright` |

## License

MIT

mcp-name: io.github.dppalukuri/uae-realestate-mcp
