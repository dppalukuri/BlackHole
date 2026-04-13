---
title: I Built a Free AI-Powered Lead Generation Engine That Replaces $200/mo in SaaS Tools
published: false
description: 5 open-source MCP servers for AI agents — Google Maps lead gen, SERP scraping, LinkedIn, CAPTCHA solving. Zero capital, laptop-only.
tags: mcp, python, ai, opensource
cover_image: 
---

Every month, businesses pay $200+ for data tools:

- **Apollo.io**: $49/mo for business contacts
- **Hunter.io**: $49/mo for email finding
- **SerpApi**: $50/mo for Google search data
- **Proxycurl**: $50/mo for LinkedIn profiles

I built free, open-source replacements for all of them. They run as MCP servers — meaning AI agents like Claude, Cursor, and Copilot can use them directly. No API keys, no monthly fees, no hosting costs.

## What I Built

Five MCP servers that work as a suite:

| Server | Replaces | Saves |
|--------|----------|-------|
| Google Maps Extractor | Apollo, Hunter | $100/mo |
| SERP Scraper | SerpApi, DataForSEO | $50/mo |
| LinkedIn Scraper | Proxycurl, PhantomBuster | $50/mo |
| CAPTCHA Solver | 2Captcha, CapSolver | $20/mo |
| UAE Real Estate | Manual research | hours/week |

**Total saved: $200+/month**

## The Killer Feature: AI-Native Lead Generation

The Google Maps Extractor isn't just a scraper. It's a complete lead generation pipeline:

```
"Find me 20 dental clinics in Dubai with their emails"
```

One command to your AI agent. Here's what happens:

1. **Search** Google Maps for dental clinics in Dubai
2. **Extract** phone, website, address, rating from each listing
3. **Visit each website** to find emails, social links, tech stack
4. **Score** each lead 0-100 based on data completeness
5. **Export** to CSV, sorted by lead quality

The output looks like this:

```json
{
  "name": "Smile Dental Clinic",
  "lead_score": 85,
  "rating": 4.8,
  "review_count": 127,
  "phone": "+971 4 555 0123",
  "website": "https://smileclinic.ae",
  "emails": ["dr.ahmed@smileclinic.ae", "info@smileclinic.ae"],
  "social_links": {
    "instagram": "https://instagram.com/smileclinic",
    "facebook": "https://facebook.com/SmileClinicDubai"
  },
  "tech_stack": ["WordPress", "Google Analytics"],
  "address": "Marina Walk, Dubai Marina"
}
```

Notice: it found the **personal email** of the doctor (25 points), not just the generic info@ address. It detected they use **WordPress** — so if you're selling WordPress plugins or SEO services, you know this is a qualified lead.

## How Lead Scoring Works

Every lead gets scored 0-100:

| Signal | Points |
|--------|--------|
| Personal email (john.doe@...) | 25 |
| Any email | 15 |
| Phone number | 15 |
| Website | 10 |
| Social media links (5 each) | max 15 |
| Google rating >= 4.0 | 10 |
| 50+ reviews | 10 |
| Has address | 5 |

Leads with score 70+ are gold — they have verified contact info, good reputation, and online presence. Score 30-50 means the business exists but is harder to reach. Below 30 is low quality.

## The Tech Stack

Everything is built with:

- **Python 3.12** — the servers
- **Playwright** — headless browser for scraping
- **playwright-stealth** — anti-detection
- **FastMCP** — MCP server framework
- **No paid APIs** — everything is browser-based

### Why MCP?

MCP (Model Context Protocol) is the standard for giving AI agents access to tools. When you add an MCP server to Claude Desktop or Cursor, the AI can call your tools directly:

```json
{
  "mcpServers": {
    "google-maps": {
      "command": "python",
      "args": ["path/to/server.py"]
    }
  }
}
```

Now your AI agent can say "find leads" and it just works. No API calls, no manual scraping, no copy-pasting.

## SERP Scraper: Free SerpApi Alternative

The SERP scraper extracts everything from a Google/Bing search results page:

- **Organic results**: title, URL, domain, snippet, position
- **Ads**: who's bidding on this keyword?
- **Featured snippets**: what Google thinks is the answer
- **People Also Ask**: content ideas from real questions
- **Related searches**: long-tail keyword opportunities

Use case: "What keywords do my competitors rank for?"

```json
{"query": "best crm software", "num_results": 20, "country": "us"}
```

The `keyword_research` tool takes multiple keywords at once and aggregates all PAA questions and related searches — instant content strategy.

## LinkedIn Scraper: Free Proxycurl Alternative

Job search works without login. Profiles and people search need a one-time manual login:

1. Call the `login` tool — a browser window opens
2. Log in with your LinkedIn credentials
3. Session cookies are saved locally
4. All future requests run headlessly

Your credentials are never stored — only the browser cookies, which are gitignored.

## CAPTCHA Solver: The Glue

When Google Maps or Google Search shows a CAPTCHA, the CAPTCHA solver handles it:

```
CLIP (free, local) --> Gemini Vision (free, 250/day) --> External API (paid fallback)
```

Gemini Vision is free for 250 solves per day. That's enough for most use cases. The solver supports hCaptcha, reCAPTCHA v2/v3, and Cloudflare Turnstile.

## Cross-Server Magic

The real power is when the servers work together. One command:

> "Find plumbers in London, check which ones have bad SEO, get their owner's LinkedIn, and draft a cold email offering SEO services"

This chains:
1. Google Maps → find plumbers
2. Website enrichment → get emails, tech stack
3. SERP Scraper → check if they rank on Google
4. LinkedIn → find the business owner
5. AI → draft personalized cold email

No single SaaS tool does this. The MCP suite does it in one conversation.

## The Economics

| Item | Cost |
|------|------|
| Development | $0 (my time) |
| Hosting | $0 (runs locally) |
| API keys | $0 (Gemini free tier) |
| Infrastructure | $0 (GitHub for code) |
| **Total** | **$0** |

Value delivered: replaces $200+/month in SaaS tools.

## Getting Started

```bash
git clone https://github.com/dppalukuri/BlackHole.git
cd BlackHole/mcp-servers/google-maps
pip install -r requirements.txt
playwright install chromium
python server.py
```

Add to your Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json` on Windows, `~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "google-maps": {
      "command": "python",
      "args": ["/path/to/BlackHole/mcp-servers/google-maps/server.py"]
    }
  }
}
```

Then ask Claude: "Find me 20 restaurants in New York with their emails and export as CSV."

## What's Next

- **Apify actors** — run the scrapers in the cloud via Apify Store (pay-per-use)
- **More MCP servers** — e-commerce price tracking, job market intelligence
- **Autonomous agents** — scheduled lead gen that runs on autopilot
- **Data products** — pre-built lead lists by niche and city

## Links

- **GitHub**: [github.com/dppalukuri/BlackHole](https://github.com/dppalukuri/BlackHole)
- **Google Maps Extractor**: [mcp-servers/google-maps](https://github.com/dppalukuri/BlackHole/tree/main/mcp-servers/google-maps)
- **SERP Scraper**: [mcp-servers/serp-scraper](https://github.com/dppalukuri/BlackHole/tree/main/mcp-servers/serp-scraper)
- **LinkedIn Scraper**: [mcp-servers/linkedin](https://github.com/dppalukuri/BlackHole/tree/main/mcp-servers/linkedin)
- **CAPTCHA Solver**: [mcp-servers/captcha-solver](https://github.com/dppalukuri/BlackHole/tree/main/mcp-servers/captcha-solver)

Star the repo if you'd use this. PRs and issues welcome.

---

*Built with zero capital on a laptop. If you're interested in MCP servers or AI agents, follow me for updates.*
