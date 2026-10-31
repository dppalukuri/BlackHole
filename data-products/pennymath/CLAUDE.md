# PennyMath — Financial Calculator Network

Programmatic SEO site targeting high-CPC financial calculator queries across India, UAE, UK and US.

## Architecture
- **Framework:** Astro v6 + Preact (Islands Architecture)
- **Interactive:** Preact components hydrated via `client:visible`. The only other script is the small inline one for search and the homepage hero
- **Charts:** `LineChart` (hand-written SVG, no chart library)
- **Styling:** Hand-rolled CSS in `src/styles/global.css` (the "Dusk" design)
- **SEO:** Schema markup (WebApplication, FAQPage, BreadcrumbList), sitemap via @astrojs/sitemap

## Structure
- `src/data/calculators.ts` — The list of every calculator. The homepage, country pages and search all read from it
- `src/lib/formulas/` — Pure math functions, tested in `formulas.test.ts`
- `src/lib/chart-scale.ts` — Chart layout maths, tested in the same file
- `src/components/calculators/engines/` — One Preact widget per calculator
- `src/components/calculators/ui/` — SliderInput, ResultCard, Verdict, ChoiceButtons, LineChart, GrowthChart
- `src/components/` — SiteSearch, CalculatorDirectory, DuskHero, FAQ, AffiliateCTA, CalculatorSchema
- `src/pages/{country}/{slug}.astro` — Calculator pages with full SEO content
- `src/pages/{country}/index.astro` — Country pages, generated from the calculator list

## Adding a New Calculator
1. Add the formula to `src/lib/formulas/` (or reuse one) with tests
2. Create the engine in `src/components/calculators/engines/`, using the layout below
3. Create the `.astro` page in `src/pages/{country}/`, with everything after the calculator inside `<div class="reading">`
4. Add one entry to `src/data/calculators.ts`. It then appears on the homepage, its country page and in search

## Engine layout
```tsx
<div class="calculator-widget">
  <div class="calc-inputs">…SliderInput, ChoiceButtons…</div>
  <div class="calc-answer"><ResultCard results={[{ highlight: true, … }, …]} /><Verdict … /></div>
  <div class="calc-below"><LineChart … /></div>
</div>
```

## Design rules
- **No redundancy.** Say each thing once: one set of country links (the header), one search box per page, no result row that repeats an input, and no intro that repeats a subtitle.
- **One large answer.** Exactly one `highlight` row in each ResultCard. It also drives the pinned answer on phones.
- **Use a LineChart wherever a number changes over time or across a range**, such as a balance, a payment, growth or a break-even. Skip it for one-off sums like GST or VAT. Use `GrowthChart` for "value against amount invested".
- **Colours come from tokens.** No hex values in engines. Chart series use `--series-1` to `--series-3`, checked for colour-blind separation on the dark panel.
- **Dark for tools, light for reading.** `.reading` swaps the tokens to a light page, so content inside it can use normal colours.
- **Local terms.** "EMI" and "tenure" are for India. UK, US and UAE pages say "payment" and "term".

## Monetization
- AdSense ads (slots are off until IDs are set in `src/lib/ads.ts`)
- Affiliate CTAs (Groww, Zerodha for India; Sarwa for UAE; Betterment for US)
- All affiliate links must use `rel="nofollow sponsored"`

## Commands
```bash
npm run dev      # Dev server at localhost:4321
npm test         # Formula and chart tests
npm run build    # Build static site to dist/
npm run preview  # Preview built site
```
