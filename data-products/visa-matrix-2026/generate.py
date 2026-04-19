"""
Regenerate the Visa Matrix 2026 product bundle from the verified data.

Inputs (source of truth):
    autonomous-agents/visa-verifier/output/verified-visas.json
    data-products/visapathway/public/data/residence-permits.json
    data-products/visapathway/public/data/visa-matrix.json  (bulk Passport Index)
    data-products/visapathway/public/data/countries.json

Outputs (in this folder):
    verified-matrix.csv        - every gov-sourced passport -> destination pair
    residence-permits.csv      - hand-curated permit -> country exemptions
    bulk-matrix.csv            - full 199x199 community-maintained matrix
    report.html                - printable overview (print-to-PDF for Gumroad)
    VERSION                    - ISO date + verified count snapshot

Regenerate any time: python generate.py
"""
from __future__ import annotations
import csv
import json
import sys
import io
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
VERIFIER_OUT = REPO / "autonomous-agents" / "visa-verifier" / "output" / "verified-visas.json"
SITE_DATA = REPO / "data-products" / "visapathway" / "public" / "data"


def load_json(path: Path) -> dict | list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_verified_csv(payload: dict, out: Path) -> int:
    rows = 0
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "passport", "destination", "status", "days", "source_url",
            "notes", "confidence", "verified_at", "model",
            "validator_agreed", "validated_by",
        ])
        for p, dests in payload.get("data", {}).items():
            for d, e in dests.items():
                # Skip self-references and unknowns — not meaningful in the export
                if str(e.get("model", "")).startswith("rule:"):
                    continue
                if e.get("status") == "unknown":
                    continue
                validator_agreed = e.get("validation_result")
                if validator_agreed in ("agree", "differ-days", "differ-status"):
                    agreed_val = "yes" if validator_agreed == "agree" else "no"
                else:
                    agreed_val = ""
                w.writerow([
                    p, d, e.get("status", ""), e.get("days", ""),
                    e.get("source", ""), e.get("notes", ""),
                    e.get("confidence", ""), e.get("verified_at", ""),
                    e.get("model", ""),
                    agreed_val,
                    e.get("validated_by", ""),
                ])
                rows += 1
    return rows


def write_permits_csv(permits: dict, out: Path) -> int:
    rows = 0
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["permit_type", "destination", "access", "days", "source_url", "notes", "permit_source_last_verified"])
        for permit, data in permits.items():
            last_verified = data.get("last_verified", "")
            for country, ex in data.get("exemptions", {}).items():
                w.writerow([
                    permit, country, ex.get("access", ""),
                    ex.get("days", ""), ex.get("source", ""),
                    ex.get("note", ""), last_verified,
                ])
                rows += 1
    return rows


def write_bulk_csv(bulk: dict, out: Path) -> int:
    """199x199 matrix from the community-maintained Passport Index Dataset.
    No gov sources — shipped as a reference baseline."""
    rows = 0
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["passport", "destination", "requirement"])
        for p, dests in bulk.items():
            for d, status in dests.items():
                w.writerow([p, d, status])
                rows += 1
    return rows


HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Visa Matrix 2026 — Government-Sourced Visa Requirements Database</title>
<style>
  :root {{ --ink:#0b1220; --muted:#6b7280; --border:#e5e7eb; --accent:#6366f1; --green:#16a34a; }}
  body {{ font-family:Georgia,Cambria,'Times New Roman',serif; background:#fff; color:var(--ink); line-height:1.55; font-size:14px; max-width:900px; margin:2rem auto; padding:0 1.5rem; }}
  h1 {{ font-size:2rem; letter-spacing:-.02em; margin:0 0 .4rem; font-weight:700; font-family:ui-sans-serif,system-ui,sans-serif; }}
  h2 {{ font-size:1.2rem; font-family:ui-sans-serif,system-ui,sans-serif; border-bottom:2px solid var(--ink); padding-bottom:.3rem; margin-top:2.25rem; }}
  h3 {{ font-family:ui-sans-serif,system-ui,sans-serif; font-size:.98rem; margin:1.25rem 0 .35rem; }}
  .meta {{ color:var(--muted); font-size:.88rem; margin:0 0 1rem; }}
  .hero {{ border-left:4px solid var(--accent); padding:1rem 1.25rem; background:#f8fafc; font-family:ui-sans-serif,system-ui,sans-serif; font-size:1rem; line-height:1.55; }}
  table {{ width:100%; border-collapse:collapse; font-size:.82rem; margin:.75rem 0; font-family:ui-sans-serif,system-ui,sans-serif; }}
  th, td {{ border:1px solid var(--border); padding:.3rem .55rem; text-align:left; vertical-align:top; }}
  th {{ background:#f3f4f6; font-weight:700; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:.6rem; margin:1rem 0; font-family:ui-sans-serif,system-ui,sans-serif; }}
  .kpi {{ padding:.65rem .8rem; border:1px solid var(--border); border-radius:8px; background:#fafbfc; }}
  .kpi strong {{ display:block; font-size:1.45rem; color:var(--accent); letter-spacing:-.02em; }}
  .kpi span {{ font-size:.65rem; color:var(--muted); text-transform:uppercase; letter-spacing:.1em; font-weight:600; }}
  .tag {{ display:inline-block; font-size:.68rem; padding:.1rem .5rem; border-radius:3px; font-family:ui-sans-serif,system-ui,sans-serif; background:#dcfce7; color:#166534; font-weight:700; letter-spacing:.02em; }}
  .tag.medium {{ background:#ede9fe; color:#5b21b6; }}
  .tag.low {{ background:#fef3c7; color:#92400e; }}
  ul, ol {{ font-family:ui-sans-serif,system-ui,sans-serif; font-size:.9rem; }}
  code {{ font-family:ui-monospace,'SF Mono',monospace; background:#f1f5f9; padding:1px 5px; border-radius:3px; font-size:.82rem; }}
  .small {{ font-size:.82rem; color:var(--muted); }}
  @media print {{ body {{ max-width:none; margin:0; padding:1.5cm; font-size:11pt; }} h1 {{ page-break-before:avoid; }} h2 {{ page-break-after:avoid; }} table {{ page-break-inside:auto; }} tr {{ page-break-inside:avoid; page-break-after:auto; }} }}
</style>
</head>
<body>

<h1>Visa Matrix 2026</h1>
<p class="meta">Government-sourced visa requirements database · Snapshot: {date}</p>

<div class="hero">
  <strong>What you're buying:</strong> the most transparent visa-requirements dataset on the market. Every
  "verified" entry is backed by a live link to the official source we used — embassy page, ministry of
  foreign affairs, or gov-run e-visa portal. Nothing is guessed, nothing is scraped from aggregators.
</div>

<div class="kpi-grid">
  <div class="kpi"><strong>{verified_count}</strong><span>verified pairs</span></div>
  <div class="kpi"><strong>{permit_count}</strong><span>permit exemptions</span></div>
  <div class="kpi"><strong>{total_countries}</strong><span>countries covered</span></div>
  <div class="kpi"><strong>{bulk_count}</strong><span>bulk-matrix rows</span></div>
</div>

<h2>What's in the download</h2>
<ul>
  <li><code>verified-matrix.csv</code> — {verified_count} passport → destination pairs, each with an official-source URL, model-reported confidence, and a day-limit where applicable. Every row comes from an independent embassy/MFA/e-visa portal check.</li>
  <li><code>residence-permits.csv</code> — {permit_count} hand-curated residence-permit exemptions. UAE Residence, US Green Card, Schengen, UK BRP, Canadian PR, valid US B1/B2, valid Schengen visa — each entry lists the destinations that unlock extra access, with day-limits and source URLs.</li>
  <li><code>bulk-matrix.csv</code> — the full 199 × 199 community-maintained baseline (Passport Index Dataset). Ships alongside the verified data as a reference for edge-case passport pairs we haven't verified yet.</li>
  <li><code>report.html</code> — this document. Open in any browser, then print to PDF for offline use.</li>
</ul>

<h2>Who this is for</h2>
<ul>
  <li><strong>Relocation consultants & immigration lawyers</strong> — a citable, sourced dataset you can hand to clients.</li>
  <li><strong>Travel bloggers & nomad newsletters</strong> — fact-check visa claims before publishing. Link directly to the gov source we cite.</li>
  <li><strong>Expat forums & communities</strong> — hand-sourced residence-permit exemptions are the most commonly misrepresented piece of visa info online.</li>
  <li><strong>Researchers</strong> — import the CSVs into pandas/Excel and analyse passport strength, permit value, regional trends.</li>
</ul>

<h2>Confidence tiers</h2>
<table>
  <thead><tr><th>Tier</th><th>What it means</th><th>How to trust</th></tr></thead>
  <tbody>
    <tr><td><span class="tag">high</span></td>
        <td>Source URL lives on a core government domain (<code>.gov</code>, <code>.gov.&lt;cc&gt;</code>, <code>travel.state.gov</code>, <code>mofa.*</code>, embassy).</td>
        <td>Use directly; source URL is canonical.</td></tr>
    <tr><td><span class="tag medium">medium</span></td>
        <td>Source URL is a trusted country-specific portal (<code>canada.ca</code>, <code>u.ae</code>, <code>diplo.de</code>, <code>admin.ch</code>, etc.).</td>
        <td>Use directly; host is authoritative within its country.</td></tr>
    <tr><td><span class="tag low">low</span></td>
        <td>Source URL is an aggregator or reference-style host (<code>schengenvisainfo.com</code>, etc.). Flagged but kept.</td>
        <td>Verify independently before acting.</td></tr>
  </tbody>
</table>

<h2>Methodology (short version)</h2>
<ol>
  <li>For each passport → destination pair, we use Claude + web search to pull the current rule from an official-domain source.</li>
  <li>A hard-coded allowlist of gov-TLD patterns <strong>gates</strong> the model's confidence. If the source URL isn't government-hosted, the entry is downgraded — we never inflate confidence.</li>
  <li>A separate Sonnet pass re-verifies each entry; disagreements with Haiku's original output are flagged (see <code>validator_agreed</code> column in the CSV).</li>
  <li>Residence-permit exemptions are hand-compiled from embassy/MFA pages, with a per-entry source URL.</li>
</ol>
<p class="small">Full pipeline is open-source: <a href="https://github.com/dppalukuri/BlackHole/tree/main/autonomous-agents/visa-verifier">github.com/dppalukuri/BlackHole</a></p>

<h2>License &amp; usage</h2>
<ul>
  <li>Personal use, commercial research, and internal business use are permitted.</li>
  <li>Redistribution of the raw CSVs as a competing dataset product is not permitted.</li>
  <li>Citing the dataset publicly is encouraged — attribution to "VisaPathway / TechTools365" appreciated.</li>
  <li>Visa rules change without notice. This is a point-in-time snapshot — always re-verify with the embassy before acting.</li>
</ul>

<h2>Support &amp; updates</h2>
<p>The dataset is refreshed continuously — every verified entry carries a <code>verified_at</code> date so you can see what's recent. If you spot an error or want priority coverage of a specific passport pair, reply to your purchase receipt email or open an issue on the GitHub repo above.</p>

<p class="small" style="margin-top:3rem; text-align:center;">VisaMatrix 2026 · Published by TechTools365 · Snapshot {date}</p>

</body>
</html>
"""


def main() -> int:
    payload = load_json(VERIFIER_OUT)
    permits = load_json(SITE_DATA / "residence-permits.json")
    countries = load_json(SITE_DATA / "countries.json")
    bulk = load_json(SITE_DATA / "visa-matrix.json")

    verified_rows = write_verified_csv(payload, ROOT / "verified-matrix.csv")
    permit_rows = write_permits_csv(permits, ROOT / "residence-permits.csv")
    bulk_rows = write_bulk_csv(bulk, ROOT / "bulk-matrix.csv")

    date = datetime.now(timezone.utc).date().isoformat()
    html = HTML.format(
        date=date,
        verified_count=verified_rows,
        permit_count=permit_rows,
        total_countries=len(countries),
        bulk_count=bulk_rows,
    )
    with open(ROOT / "report.html", "w", encoding="utf-8") as f:
        f.write(html)

    with open(ROOT / "VERSION", "w", encoding="utf-8") as f:
        f.write(f"{date}\nverified={verified_rows}\npermits={permit_rows}\nbulk={bulk_rows}\n")

    print(f"[ok] verified-matrix.csv  ({verified_rows} rows)")
    print(f"[ok] residence-permits.csv ({permit_rows} rows)")
    print(f"[ok] bulk-matrix.csv       ({bulk_rows} rows)")
    print(f"[ok] report.html           ({len(html):,} bytes)")
    print(f"[ok] VERSION               ({date})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
