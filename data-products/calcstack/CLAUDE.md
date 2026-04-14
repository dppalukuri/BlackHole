# CalcStack — Financial Calculator Network

Programmatic SEO site targeting high-CPC financial calculator queries across India, UAE, and US.

## Architecture
- **Framework:** Astro v6 + Preact (Islands Architecture)
- **Interactive:** Preact components hydrated via `client:visible` — zero JS on non-calculator sections
- **Charts:** Chart.js (doughnut charts for investment breakdowns)
- **Styling:** Hand-rolled CSS (no framework)
- **SEO:** Schema markup (WebApplication, FAQPage, BreadcrumbList), sitemap via @astrojs/sitemap

## Structure
- `src/lib/formulas/` — Pure math functions (compound-growth, loan-emi, flat-rate, tax-slab)
- `src/components/calculators/engines/` — Preact calculator widgets (SIP, EMI, FD, PPF, Tax, Gratuity, VAT, CompoundInterest, LumpSum)
- `src/components/calculators/ui/` — Reusable UI (SliderInput, ResultCard, DoughnutChart)
- `src/pages/{country}/{slug}.astro` — Calculator pages with full SEO content
- `src/pages/{country}/index.astro` — Country hub pages

## Adding a New Calculator
1. Add formula to `src/lib/formulas/` (or reuse existing)
2. Create Preact engine component in `src/components/calculators/engines/`
3. Create `.astro` page in `src/pages/{country}/`
4. Update country hub page to include it
5. Update homepage if it's a top calculator

## Monetization
- AdSense ads (placeholder slots ready)
- Affiliate CTAs (Groww, Zerodha for India; Sarwa for UAE; Betterment for US)
- All affiliate links must use `rel="nofollow sponsored"`

## Commands
```bash
npm run dev      # Dev server at localhost:4321
npm run build    # Build static site to dist/
npm run preview  # Preview built site
```
