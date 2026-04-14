# Zero-Capital to $10K/Month: The Playbook

## The Core Insight

Money flows where **human time is expensive and AI time is cheap**. You're selling the *delta* between what AI can do for pennies and what businesses pay humans hundreds of dollars to do.

---

## 3 Viable Paths (Pick 1-2, Not All)

### Path A: AI Data Products — Sell Enriched Intelligence

**What:** Scrape public data, enrich it with AI (categorize, score, extract insights), sell subscriptions to businesses who need it but can't build it.

| Layer | Detail |
|-------|--------|
| **Source** | Public government registries, job boards, permit filings, company filings, court records, import/export data |
| **Enrichment** | AI classifies, scores, extracts entities, detects trends, generates summaries |
| **Packaging** | Weekly/monthly datasets, API access, Slack/email alerts |
| **Distribution** | Gumroad, Lemon Squeezy, or self-hosted Stripe checkout |
| **Customers** | Sales teams, investors, recruiters, real estate developers, law firms |

**Concrete examples that sell today:**
- **New business filings dataset** — scraped from state registries, enriched with industry, founder LinkedIn, estimated funding. Sold to sales teams. ($99-299/mo per subscriber)
- **Construction permit tracker** — scraped from city portals, AI-categorized by project type/size. Sold to building suppliers, contractors. ($149-499/mo)
- **Job market intelligence** — scraped from job boards, AI-analyzed for hiring trends by company/sector. Sold to recruiters, investors. ($99-199/mo)
- **Import/export trade data** — from public customs filings, enriched with supplier relationships. Sold to sourcing teams. ($199-499/mo)

**Revenue math:** 50 subscribers x $200/mo = **$10,000/mo**

| Layer | Stack |
|-------|-------|
| Scraping | Python + Playwright/httpx, rotating free proxies, scheduled via cron |
| Storage | SQLite -> PostgreSQL (free tier Supabase/Neon) |
| Enrichment | Claude API (Haiku for bulk = ~$0.25/1000 records) |
| Delivery | Static site + Stripe + email automation (Resend free tier) |
| Automation | GitHub Actions (2000 free min/mo) or local cron |

**Cost:** ~$5-20/mo for API calls. Everything else is free tier.

---

### Path B: Automated Lead Gen Agency — AI Agents That Find & Qualify Leads

**What:** Build automated pipelines that find, qualify, and deliver leads to businesses. Charge per lead or monthly retainer. No client calls — sell through self-serve landing pages.

| Layer | Detail |
|-------|--------|
| **Discovery** | Google Maps, LinkedIn, industry directories, job boards |
| **Enrichment** | Find emails (Hunter.io free tier, pattern matching), phone numbers, company info |
| **Qualification** | AI scores leads by fit (company size, tech stack, hiring signals, review count) |
| **Delivery** | CSV export, Google Sheets auto-update, webhook to client CRM |
| **Verticals** | Pick 3 niches: e.g., dentists, SaaS companies, e-commerce stores |

**Concrete niches that pay for leads:**
- **Home service leads** (plumbers, HVAC, roofers) — $25-75 per qualified lead
- **Real estate investor leads** (off-market properties) — $50-200 per lead
- **SaaS buyer intent leads** (companies searching for specific software) — $20-50 per lead
- **Recruiting leads** (passive candidates with specific skills) — $50-100 per lead

**Revenue math:** Deliver 200-400 leads/month across 5-10 clients = **$10,000/mo**

| Layer | Stack |
|-------|-------|
| Scraping | Python + httpx + Playwright for JS-heavy sites |
| Email finding | Pattern matching (first.last@domain.com) + verification via free SMTP check |
| AI scoring | Claude Haiku — score each lead against ideal customer profile |
| Delivery | Google Sheets API (free) or simple dashboard |
| Sales page | Single Carrd page ($0) or static HTML on GitHub Pages |
| Payment | Stripe (no monthly fee, 2.9% per transaction) |

**Cost:** ~$10-30/mo total.

---

### Path C: Programmatic Content Empire — AI-Generated Sites That Earn While You Sleep

**What:** Build 5-10 niche content sites, each targeting a specific high-value keyword cluster. AI generates the content. Revenue from ads + affiliates.

| Layer | Detail |
|-------|--------|
| **Niche selection** | Find niches with high CPC ($5+), low competition, and affiliate programs |
| **Content generation** | Claude generates comprehensive, expert-level articles |
| **SEO** | Programmatic internal linking, schema markup, topical authority |
| **Monetization** | Google AdSense -> Mediavine (at 50K sessions), Amazon/niche affiliates |
| **Scale** | 100-500 articles per site, published over 2-3 months |

**Concrete niches:**
- **B2B software comparisons** ("best CRM for real estate agents") — affiliate commissions $50-200 per signup
- **Financial calculators + guides** ("HELOC vs home equity loan calculator") — AdSense CPC $8-15
- **Health/supplement reviews** — affiliate commissions 15-30% on $40-80 products
- **Home improvement guides** — affiliate links to tools, materials on Amazon

**Revenue math:** 5 sites x 30K visits/mo x $0.07 RPM+ affiliate = **$10,000-15,000/mo** (takes 4-8 months to ramp)

| Layer | Stack |
|-------|-------|
| Hosting | GitHub Pages or Cloudflare Pages (free) |
| CMS | Astro or Hugo (static site generators, free) |
| Content | Claude API — $0.50-1.00 per 2000-word article |
| SEO tools | Google Search Console (free), Ubersuggest (free tier) |
| Analytics | Plausible (free self-hosted) or Umami |
| Monetization | Google AdSense (free), affiliate networks (free to join) |

**Cost:** $50-100 total for initial content generation across all sites. Then ~$10/mo ongoing.

---

## The Layer Map

```
+-----------------------------------------------------------+
|                    REVENUE ($10K/mo)                       |
+-----------------------------------------------------------+
|              DISTRIBUTION (the hard part)                  |
|  - SEO (free, slow: 3-6 months)                           |
|  - Twitter/Reddit/communities (free, medium speed)        |
|  - Cold email (free, fast, but grindy at start)           |
|  - Product Hunt / HN launches (free, one-shot spikes)     |
|  - Affiliate partners (free, slow to build)               |
+-----------------------------------------------------------+
|                  TRUST / CONVERSION                        |
|  - Landing page with clear value prop                     |
|  - Free sample / free tier to prove quality               |
|  - Testimonials (first 3 clients = free or discounted)    |
|  - Stripe checkout (instant credibility)                  |
+-----------------------------------------------------------+
|                 PRODUCT / VALUE LAYER                      |
|  - Data enrichment pipeline                               |
|  - Lead qualification engine                              |
|  - Content generation system                              |
|  - Automated delivery (email, API, dashboard)             |
+-----------------------------------------------------------+
|                   AI ENRICHMENT LAYER                      |
|  - Claude Haiku for bulk classification ($0.25/K)         |
|  - Claude Sonnet for complex analysis ($3/K)              |
|  - Structured output for reliable parsing                 |
+-----------------------------------------------------------+
|                    DATA COLLECTION                         |
|  - Web scrapers (Playwright, httpx)                       |
|  - Public APIs (government, social, business)             |
|  - RSS feeds, webhooks, file monitoring                   |
+-----------------------------------------------------------+
|                    INFRASTRUCTURE                          |
|  - Free tiers: Supabase, GitHub Actions, Cloudflare      |
|  - Local cron jobs for scraping                           |
|  - Total cost: $10-30/month                               |
+-----------------------------------------------------------+
```

---

## Recommended: Path A + B Hybrid

**Why:** Paths A and B share 80% of the same infrastructure (scraping -> enrichment -> delivery). Build the pipeline once, sell the output two ways:

1. **Raw data subscriptions** (Path A) — recurring, passive, scales without you
2. **Qualified lead packages** (Path B) — higher price per unit, faster to first dollar

### Phase Plan

| Phase | Timeline | Focus | Target Revenue |
|-------|----------|-------|----------------|
| 1 | Week 1-2 | Pick ONE vertical. Build scraper + enrichment pipeline | $0 |
| 2 | Week 3-4 | Create landing page. Offer free samples on Reddit/Twitter/communities | $0 |
| 3 | Month 2 | First 3-5 paying customers at $99-199/mo | $500-1,000 |
| 4 | Month 3-4 | Add second vertical. Automate delivery. Start cold outreach | $2,000-3,000 |
| 5 | Month 5-6 | 3 verticals running. SEO kicking in. Referrals starting | $5,000-7,000 |
| 6 | Month 7-9 | Optimize, add API access tier, raise prices | $10,000+ |

---

*Created: 2026-04-13*
