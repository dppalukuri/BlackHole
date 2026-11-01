# Shared Resources — TechTools365

Files in this directory are shared across all subsites.

## ads.html
Single source of truth for all ad/monetization scripts (AdSense, Ezoic, future partners).
**DO NOT delete or modify without checking revenue impact.**

### How each site uses it:
- **PennyMath** (Astro): `src/components/AdScripts.astro` reads and inlines this file
- **ToolJury** (Hugo): `layouts/partials/ad-scripts.html` is a copy synced from here
- **WanderWise** (Astro): `src/components/AdScripts.astro` reads and inlines this file

### Adding a new ad partner:
1. Add the script to `ads.html`
2. Rebuild all sites (`npm run build` / `hugo build`)
3. Push — Cloudflare auto-deploys all sites

## brand/
The TechTools365 brand and the Dusk design, shared by the landing page, PennyMath, ToolJury and WanderWise. The parent brand comes first on every page: a top bar with the logo and links to each tool, then the site's own navigation, and the same footer at the bottom.

| File | Purpose |
|------|---------|
| `brand.css` | `--tt-*` colours, the top bar, the footer and the hero canvas |
| `dusk.js` | Paints `canvas[data-dusk="sun\|penny\|jury\|globe"]`. Optional: `data-orb-y`, `data-orb-y-narrow` (below 640px), `data-orb-scale` |
| `family-bar.html`, `family-footer.html`, `brand-mark.html` | The bar, footer and logo markup |
| `sync.py` | Copies the files above into each site and regenerates the landing search index |

### After changing anything in brand/, or adding pages
1. `python data-products/shared/brand/sync.py`
2. Landing: `python data-products/techtools365-landing/scripts/sync-shell.py`
3. PennyMath and WanderWise: `npm run build` (`FamilyBar.astro` and `FamilyFooter.astro` read this folder at build time)
4. ToolJury: `python data-products/tooljury/scripts/apply-dusk.py`. Hugo isn't installed, so its built pages are patched. The Hugo templates match but have not been run; check the homepage's `impact-site-verification` tag after the first real build, because Hugo's minifier changes its quotes.

Run from the repo root. `sync.py` writes `techtools365-landing/public/search-index.json` from PennyMath's calculator list, ToolJury's built comparisons and WanderWise's built pages, so run it after adding any of those.
