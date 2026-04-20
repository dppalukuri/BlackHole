# Gig Listing Templates

Ready-to-paste copy for Upwork, Fiverr, and Gumroad. Each gig maps to one
fulfillment script. Run the listing template exactly once per marketplace,
link back to your delivery email, and let inbound orders come to you.

---

## 1. Google Maps leads (`leads_maps.py`)

### Fiverr gig

**Title (max 80 chars):**
> I will deliver 500 verified business leads in your niche within 24 hours

**Tags:**
`lead generation`, `b2b leads`, `email list`, `google maps leads`,
`data entry`, `email scraping`

**Basic / Standard / Premium tiers:**

| Tier | Leads | Delivery | Price |
|---|---|---|---|
| Basic | 100 | 48 hr | $29 |
| Standard | 300 | 24 hr | $79 |
| Premium | 500 + LinkedIn cross-ref | 24 hr | $149 |

**Gig description:**
> I'll hand-deliver a clean, CSV-ready lead list of real businesses in your
> target niche — pulled live from Google Maps and enriched with emails,
> phone numbers, social links, and a lead-quality score.
>
> **What you get:**
> - Name, category, address, phone, website
> - Verified emails (scraped from each business's website)
> - Social links (LinkedIn, Facebook, Instagram where public)
> - Lead score (0–100) so you can prioritise outreach
> - UTF-8 CSV that opens directly in Excel or Google Sheets
>
> **Why me:** I run a proprietary scraping stack (no cheap data-broker
> reselling). Delivery is a fresh scrape, not a recycled list. You get
> buyers nobody else is hitting yet.
>
> **I need from you:**
> 1. Your niche (e.g. "dental practice", "yoga studio", "custom joiners")
> 2. Your city or region (e.g. "Dubai Marina", "Austin, TX")
> 3. Optional: minimum Google rating filter (usually I'd say 4.0+)
>
> **Turnaround:** 12–24 hours on Standard, 48 hr buffer for Basic.
> **Revisions:** 1 free re-filter if the niche/location needs tweaking.

**Order-fulfillment workflow:**
```bash
python leads_maps.py --niche "dental practice" --location "Dubai" --count 500 --min-rating 4.0
# zip path printed → attach to Fiverr message → "delivered"
```

### Upwork proposal template

> Hi {{client_name}},
>
> I can deliver the {{niche}} lead list in {{location}} within 24 hours.
> My delivery includes name, category, address, phone, website, emails
> scraped from each site, social links, and a 0–100 lead score so you
> can prioritise who to email first.
>
> A 100-lead sample runs $29 (if you want to test quality before committing
> to 500). Full 500-lead package is $149, includes a free re-filter if the
> niche needs tightening.
>
> Delivery format: UTF-8 CSV, opens cleanly in Excel/Sheets/your CRM.
> No long-tail data-broker resale — this is a fresh live scrape.
>
> Ready to start when you confirm the niche + location.

### Gumroad product (self-serve, no bidding)

**Title:** "1,000 [NICHE] Leads in [CITY] — 24h delivery"
**Price:** $99 intro (raise to $149 after first 10 sales + reviews)
**Description:** copy from Fiverr gig above, remove the Basic/Standard/Premium.
**Fulfillment:** manual — Gumroad emails you the buyer's order; you run the
script, upload the zip to the Gumroad "deliverables" field.

---

## 2. UAE Property Intelligence (`uae_properties.py`)

### Fiverr gig

**Title:**
> I will research Dubai property listings with agent contacts — live data

| Tier | Listings | Delivery | Price |
|---|---|---|---|
| Basic | 30 (one area, one filter) | 24 hr | $29 |
| Standard | 100 (any area, full filters) | 24 hr | $79 |
| Premium | 200 + cross-portal dedupe + CSV + market summary | 12 hr | $149 |

**Gig description:**
> Live-scraped property listings across Bayut, Dubizzle, and PropertyFinder —
> deduplicated across all three portals so you don't chase the same unit
> three times.
>
> **What you get per listing:**
> - Source portal, listing ID, title, URL
> - Price, price-per-sqft (in AED)
> - Bedrooms, bathrooms, area
> - Location, emirate, community, sub-community
> - GPS coordinates (lat/lng)
> - Agent name, agent phone, agency name
> - Listing date, reference, amenities
>
> **Why me:** Same data you'd get from 3 manual searches, already merged
> and cleaned. Median + average price included in the delivery summary so
> you can sanity-check the market instantly.
>
> **I need from you:**
> 1. Location (e.g. "Dubai Marina", "Downtown Dubai", "JVC")
> 2. For-sale or for-rent
> 3. Optional: bedrooms, max price (AED)
>
> **Turnaround:** 12–24 hr.
> **Revisions:** Unlimited re-scrapes if your filters change.

**Fulfillment:**
```bash
python uae_properties.py --location "Dubai Marina" --purpose for-sale \
    --bedrooms 2 --max-price 3500000 --min-results 100
```

---

## 3. SEO SERP Reports (`serp_report.py`)

### Fiverr gig

**Title:**
> I will deliver a deep Google SERP report for any keyword — organic, ads, PAA

| Tier | Depth | Delivery | Price |
|---|---|---|---|
| Basic | Top 20 | 24 hr | $9 |
| Standard | Top 50 + ads + featured snippet | 24 hr | $19 |
| Premium | Top 100 + ads + PAA + related + 5 keyword bundle | 24 hr | $49 |

**Gig description:**
> Full Google SERP snapshot for competitor mapping, SEO audits, or content
> briefs. Choose your country/language and I'll hand over:
>
> - `organic.csv` — ranked organic results with title, URL, domain, snippet
> - `ads.csv` — paid ads on page 1 (if any)
> - `features.json` — featured snippet, People Also Ask questions, related searches
> - `README-buyer.txt` — summary: unique domains, PAA count, SERP features
>
> **Use cases:**
> - Content brief: what's ranking for your target term + PAA to answer
> - Competitor audit: who owns the SERP + what ads are running
> - Backlink research: shortcut to a seed list of sites to outreach
> - Local SEO: query by country to see your real market, not US defaults
>
> **I need from you:**
> 1. The keyword (or up to 5 for Premium)
> 2. Country (default US) and language (default English)
>
> Delivery is live data at scrape time — re-run weekly for tracking.

**Fulfillment:**
```bash
python serp_report.py --query "{{keyword}}" --depth 50 --country {{cc}}
```

---

## 4. LinkedIn Job-Market Snapshot (`linkedin_jobs.py`)

### Fiverr gig

**Title:**
> I will deliver 200 live LinkedIn job postings in your niche + location

| Tier | Postings | Delivery | Price |
|---|---|---|---|
| Basic | 50 | 24 hr | $19 |
| Standard | 200 + hiring-company breakdown | 24 hr | $39 |
| Premium | 500 + seniority/employment-type/salary analysis | 24 hr | $79 |

**Gig description:**
> Live snapshot of the LinkedIn job market for any role + location. You
> get the raw postings (title, company, location, seniority, employment
> type, salary if disclosed, posting date, applicants, LinkedIn URL),
> plus a top-10 hiring-companies summary.
>
> **Perfect for:**
> - Recruiters scoping new markets before launching outreach
> - Career coaches building personalised target lists for clients
> - Founders sizing the hiring-market before launching a product
> - ATS vendors who need fresh job-market demo data
>
> **What's included:**
> - `linkedin-jobs-*.csv` — all postings (UTF-8, opens in Excel)
> - `README-buyer.txt` — top 10 hiring cos, employment-type split,
>   seniority split, filter recap
>
> **I need from you:**
> 1. Job keywords (e.g. "machine learning engineer", "CFO")
> 2. Location or "Remote"
> 3. Optional: remote-type, employment-type, seniority level
>
> **Note:** Public LinkedIn data only — no login session used. Some fields
> (salary, applicants) are only filled by ~30–40% of posters. That's not me
> missing them, it's LinkedIn's publisher behaviour.

**Fulfillment:**
```bash
python linkedin_jobs.py --query "{{keywords}}" --location "{{loc}}" \
    --remote "{{remote_type}}" --count 200
```

---

## Pricing philosophy

Start low to get first reviews, raise fast:

| Product | Launch price | Target price (after 10 reviews) |
|---|---|---|
| Google Maps leads (500) | $99 | $199 |
| UAE property intel (100) | $49 | $99 |
| SERP deep report (50) | $19 | $39 |
| LinkedIn jobs (200) | $39 | $79 |

**Rule of thumb:** your fulfillment time per order is 10–30 min. At launch
price $39 with 30 min fulfillment, effective hourly rate is $78. Once
you're above 4.7 stars and 20+ reviews, raise prices 50–100%.

## What to do on day 1

1. Set up a Fiverr seller account (fiverr.com/start_selling).
2. Publish `leads_maps.py` gig first — highest margin, clearest buyer persona.
3. Price the Basic tier at $19 for the first week to trigger the algorithm.
4. Accept first 3–5 orders under-priced on purpose to build reviews.
5. Raise Basic to $29 after 5 orders, Standard to $79 after 10 orders.
6. Repeat for the other 3 gigs once the first is in orbit.

Expected timeline: first order within 3–10 days of listing. First $500 MRR
within 30–45 days if you maintain 4.8+ stars.
