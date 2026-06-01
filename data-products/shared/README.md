# Shared Resources — TechTools365

Files in this directory are shared across all subsites.

## ads.html
Single source of truth for all ad/monetization scripts (AdSense, Ezoic, future partners).
**DO NOT delete or modify without checking revenue impact.**

### How each site uses it:
- **PennyMath** (Astro): `src/components/AdScripts.astro` reads and inlines this file
- **ToolJury** (Hugo): `layouts/partials/ad-scripts.html` is a copy synced from here
- **Wanderwise** (Astro): `src/components/AdScripts.astro` reads and inlines this file

### Adding a new ad partner:
1. Add the script to `ads.html`
2. Rebuild all sites (`npm run build` / `hugo build`)
3. Push — Cloudflare auto-deploys all sites
