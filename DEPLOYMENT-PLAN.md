# Deployment & Monetization Plan — CalcStack + ToolVersus

*Zero-cost deployment to start earning money.*

---

## Phase 1: Deploy CalcStack (Week 1)

### Step 1: Get a Domain
- **Namecheap**: calcstack.com or calcstack.io (~$9-12/year — this is the ONE cost)
- Alternative: Use GitHub Pages free subdomain `dppalukuri.github.io/calcstack` (zero cost but worse for SEO)
- **Recommendation:** Buy the domain. A $10 domain is the only investment that matters for SEO credibility.

### Step 2: Deploy to Cloudflare Pages (FREE)
Cloudflare Pages free tier includes:
- Unlimited bandwidth (GitHub Pages caps at 100GB/mo)
- Global CDN with edge caching (faster than GitHub Pages)
- Free SSL
- Custom domain support
- Automatic builds on git push

**Setup steps:**
1. Go to dash.cloudflare.com > Pages > Create a project
2. Connect your GitHub repo `dppalukuri/BlackHole`
3. Build settings:
   - Build command: `cd data-products/calcstack && npm install && npm run build`
   - Build output directory: `data-products/calcstack/dist`
   - Root directory: `/` (leave default)
4. Add custom domain: calcstack.com (update nameservers at Namecheap to Cloudflare)
5. Every push to `main` auto-deploys

### Step 3: Google Search Console (FREE, Day 1)
1. Go to search.google.com/search-console
2. Add property: `calcstack.com`
3. Verify via DNS TXT record (Cloudflare dashboard)
4. Submit sitemap: `https://calcstack.com/sitemap-index.xml`
5. Request indexing for all 13 pages manually

### Step 4: Google Analytics (FREE, Day 1)
1. Create GA4 property at analytics.google.com
2. Add tracking snippet to BaseLayout.astro `<head>`
3. Set up conversion events: affiliate link clicks, calculator usage

---

## Phase 2: Apply for Monetization (Week 2-3)

### AdSense Application
**Requirement:** 15+ pages of quality content (we have 13 — add 2-3 more calculators)

1. Go to adsense.google.com > Sign up
2. Add site: calcstack.com
3. Place AdSense verification code in `<head>`
4. Wait 2-7 days for review
5. Once approved, place ad units:
   - Above calculator (leaderboard 728x90)
   - Between calculator and content (responsive)
   - Before FAQ section (responsive)
   - Max 3-4 ads per page

**Expected timeline:** Approval in 1-2 weeks if content is quality.

### Alternative Ad Networks (if AdSense is slow)
| Network | Minimum Traffic | RPM | Notes |
|---------|----------------|-----|-------|
| Ezoic | None (free tier) | $5-15 | Good for new sites |
| Mediavine | 50K sessions/mo | $15-30 | Apply when traffic grows |
| AdThrive | 100K pageviews/mo | $20-40 | Premium, apply later |

**Start with Ezoic** — no minimum traffic requirement and higher RPM than AdSense for finance content.

### Affiliate Program Applications (Week 2)

Apply to these immediately — most approve within 1-7 days:

**India (for SIP/EMI/FD/PPF calculators):**
| Program | Commission | Apply At |
|---------|-----------|----------|
| Groww | INR 400-800/lead | groww.in/p/affiliate-program |
| Zerodha | INR 300-500/account | zerodha.com/referral |
| Kuvera | Referral credits | kuvera.in |

**UAE (for gratuity/VAT calculators):**
| Program | Commission | Apply At |
|---------|-----------|----------|
| Sarwa | Per signup | sarwa.co/affiliate |
| eToro | $250/funded account | partners.etoro.com |

**US (for compound interest calculator):**
| Program | Commission | Apply At |
|---------|-----------|----------|
| Betterment | Per funded account | betterment.com/affiliate |
| Wealthfront | Per funded account | wealthfront.com/affiliate |

**Global (for all pages):**
| Program | Commission | Apply At |
|---------|-----------|----------|
| Amazon Associates | 1-10% | affiliate-program.amazon.com |
| Impact (multiple brands) | Varies | impact.com |

---

## Phase 3: SEO Growth Strategy (Month 1-3)

### Content Calendar
| Week | Action | Pages Added |
|------|--------|-------------|
| 1 | Deploy, submit to Search Console, apply for ads | 0 |
| 2 | Add 5 more India calculators (GST, HRA, TDS, step-up SIP, NPS) | +5 |
| 3 | Add 3 UAE calculators (mortgage, salary, DEWA) | +3 |
| 4 | Add 3 US calculators (401k, Roth IRA, mortgage) | +3 |
| 5-8 | Add 2 calculators/week + improve existing content | +8 |
| 9-12 | Total 30+ calculators, SEO starts compounding | - |

### Backlink Strategy (FREE)
1. **Submit to directories:**
   - Product Hunt (free launch)
   - IndieHackers (share building story)
   - Hacker News (Show HN post)
   - Reddit: r/IndiaInvestments, r/personalfinance, r/dubai (share calculators genuinely)

2. **Guest post offers:**
   - Finance blogs in India (offer free calculator embeds)
   - UAE expat blogs (gratuity calculator is genuinely useful)

3. **Social signals:**
   - Share on Twitter/X with calculator screenshots
   - LinkedIn posts about the tools
   - Quora answers linking to relevant calculators

### Technical SEO Checklist
- [x] Sitemap auto-generated
- [x] Schema markup on all pages
- [x] Mobile responsive
- [x] Fast (static HTML, islands architecture)
- [ ] Add `hreflang` tags for cross-country calculators
- [ ] Add `about.astro` page (E-E-A-T signal)
- [ ] Add `privacy.astro` page (required for AdSense)
- [ ] Add `terms.astro` page
- [ ] Generate OG images per calculator (Python script with Pillow)

---

## Phase 4: ToolVersus Deployment (Month 2)

Same pattern:
1. Domain: toolversus.com (~$10/year)
2. Deploy to Cloudflare Pages (free)
3. Google Search Console + Analytics
4. Apply for SaaS affiliate programs:

| Program | Commission | Priority |
|---------|-----------|----------|
| NordVPN | 40-100% first sale | HIGH — launch with VPN comparisons |
| Hostinger | 40-60% | HIGH — web hosting comparisons |
| Semrush | $200-350/sale | HIGH — SEO tool comparisons |
| HubSpot | 33% recurring | MEDIUM |
| Notion | 50% for 12 months | MEDIUM |

---

## Revenue Projections (Conservative)

### CalcStack
| Month | Organic Traffic | Ad Revenue | Affiliate | Total |
|-------|----------------|------------|-----------|-------|
| 1 | 100-500 | $0 | $0 | $0 |
| 2 | 500-2,000 | $5-20 | $0 | $5-20 |
| 3 | 2,000-5,000 | $50-100 | $20-50 | $70-150 |
| 6 | 10,000-30,000 | $200-600 | $100-300 | $300-900 |
| 9 | 30,000-80,000 | $600-1,600 | $300-800 | $900-2,400 |
| 12 | 80,000-200,000 | $1,500-4,000 | $500-1,500 | $2,000-5,500 |

### ToolVersus
| Month | Organic Traffic | Affiliate | Ad Revenue | Total |
|-------|----------------|-----------|------------|-------|
| 1 | 100-300 | $0 | $0 | $0 |
| 3 | 1,000-5,000 | $50-200 | $20-50 | $70-250 |
| 6 | 5,000-20,000 | $300-1,000 | $100-300 | $400-1,300 |
| 9 | 20,000-50,000 | $800-2,500 | $300-700 | $1,100-3,200 |
| 12 | 50,000-100,000 | $2,000-5,000 | $600-1,200 | $2,600-6,200 |

### Combined (Month 12)
| Source | Low | High |
|--------|-----|------|
| CalcStack ads | $1,500 | $4,000 |
| CalcStack affiliates | $500 | $1,500 |
| ToolVersus affiliates | $2,000 | $5,000 |
| ToolVersus ads | $600 | $1,200 |
| **Total** | **$4,600** | **$11,700** |

---

## Monthly Costs

| Item | Cost |
|------|------|
| 2 domains (calcstack.com + toolversus.com) | ~$20/year ($1.67/mo) |
| Cloudflare Pages hosting (x2) | $0 |
| Google Search Console / Analytics | $0 |
| Claude API for ToolVersus editorial | ~$15-30 one-time, $5/mo for updates |
| **Total monthly cost** | **~$7/month** |

---

## Immediate Next Steps (This Week)

1. **Buy calcstack.com domain** (Namecheap, ~$10)
2. **Set up Cloudflare Pages** (connect GitHub repo, add domain)
3. **Submit to Google Search Console** (verify, submit sitemap)
4. **Add privacy + about pages** (required for AdSense)
5. **Apply for Ezoic** (no minimum traffic, better than AdSense for finance)
6. **Apply for Groww + Zerodha affiliate** (India financial calculators)
7. **Share SIP calculator on r/IndiaInvestments** (genuine value, not spam)
8. **Post on Twitter/LinkedIn** about building in public

---

*Total investment needed: ~$10 for a domain. Everything else is free.*
