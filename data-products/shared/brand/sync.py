"""Copy the TechTools365 brand kit into each site, and build the landing page's search index.

Run after editing anything in shared/brand, or after adding pages to a site:
    python data-products/shared/brand/sync.py

The Astro sites read family-bar.html and family-footer.html directly at build time.
Hugo cannot read outside its project, so ToolJury gets generated partials instead.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "shared" / "brand"

STATIC_DIRS = {
    "landing": ROOT / "techtools365-landing" / "public",
    "pennymath": ROOT / "pennymath" / "public",
    "wanderwise": ROOT / "wanderwise" / "public",
    "tooljury": ROOT / "tooljury" / "static",
}

TOOLJURY_LINKS = """<nav aria-label="ToolJury">
      <h2>ToolJury</h2>
      <ul>
        <li><a href="/compare/">Comparisons</a></li>
        <li><a href="/about/">About</a></li>
        <li><a href="/contact/">Contact</a></li>
      </ul>
    </nav>"""
TOOLJURY_FINE = (
    "We may earn affiliate commissions when you purchase through our links. This does not affect our "
    "editorial independence. Our rankings are based on publicly available pricing, features and our testing."
)


def brand_mark(grad_id):
    return (BRAND / "brand-mark.html").read_text(encoding="utf-8").strip().replace("GRADID", grad_id)


def family_bar(extra=""):
    text = (BRAND / "family-bar.html").read_text(encoding="utf-8")
    return text.replace("<!--BRAND-->", brand_mark("bar")).replace("<!--EXTRA-->", extra).strip()


def family_footer(site_links, fine):
    text = (BRAND / "family-footer.html").read_text(encoding="utf-8")
    return (
        text.replace("<!--BRAND-->", brand_mark("foot"))
        .replace("<!--SITE_LINKS-->", site_links)
        .replace("<!--SITE_FINE-->", fine)
        .strip()
    )


def copy_assets():
    for static in STATIC_DIRS.values():
        (static / "css").mkdir(parents=True, exist_ok=True)
        (static / "js").mkdir(parents=True, exist_ok=True)
        (static / "css" / "brand.css").write_text((BRAND / "brand.css").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        (static / "js" / "dusk.js").write_text((BRAND / "dusk.js").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def tooljury_partials():
    partials = ROOT / "tooljury" / "layouts" / "partials"
    bar = family_bar().replace(
        'data-site="tooljury"', 'data-site="tooljury" aria-current="page"'
    )
    (partials / "family-bar.html").write_text(bar + "\n", encoding="utf-8", newline="\n")
    (partials / "family-footer.html").write_text(family_footer(TOOLJURY_LINKS, TOOLJURY_FINE) + "\n", encoding="utf-8", newline="\n")


def pennymath_entries():
    source = (ROOT / "pennymath" / "src" / "data" / "calculators.ts").read_text(encoding="utf-8")
    pattern = re.compile(r"path: '([^']+)', name: '([^']+)', country: '([^']+)', topic: '[^']+', desc: '(?:[^'\\]|\\.)*', tags: '([^']*)'")
    for path, name, country, tags in pattern.findall(source):
        yield {"n": name, "s": f"PennyMath, {country}", "p": f"https://pennymath.techtools365.com{path}", "t": f"{country} calculator {tags}"}


def tooljury_entries():
    compare = ROOT / "tooljury" / "content" / "compare"
    built = ROOT / "tooljury" / "public" / "compare"
    for md in sorted(compare.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        slug = re.search(r'^slug:\s*"?([^"\n]+)"?', text, re.M)
        title = re.search(r'^title:\s*"?([^"\n]+)"?', text, re.M)
        category = re.search(r'^category:\s*"?([^"\n]+)"?', text, re.M)
        slug = slug.group(1).strip() if slug else md.stem
        if not title or not (built / slug / "index.html").exists():
            continue  # Written but not built yet, so there is no page to send anyone to.
        name = re.split(r"\s*[(:]", title.group(1))[0].strip()
        yield {"n": name, "s": "ToolJury", "p": f"https://tooljury.techtools365.com/compare/{slug}/", "t": f"{category.group(1) if category else ''} comparison compare review"}


def wanderwise_entries():
    dist = ROOT / "wanderwise" / "dist"
    yield {"n": "Multi-passport visa checker", "s": "WanderWise", "p": "https://wanderwise.techtools365.com/", "t": "visa checker passport residence permit travel"}
    for page in sorted(dist.glob("*/index.html")):
        slug = page.parent.name
        if slug in {"about", "privacy", "methodology"}:
            continue
        title = re.search(r"<title>([^<]+)</title>", page.read_text(encoding="utf-8"))
        if not title:
            continue
        name = re.split(r"\s*[|—–:]\s*", html.unescape(title.group(1)))[0].strip()
        yield {"n": name, "s": "WanderWise", "p": f"https://wanderwise.techtools365.com/{slug}/", "t": "visa free travel " + slug.replace("-", " ")}


def search_index():
    entries = list(pennymath_entries()) + list(tooljury_entries()) + list(wanderwise_entries())
    out = STATIC_DIRS["landing"] / "search-index.json"
    out.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    counts = {}
    for e in entries:
        site = e["s"].split(",")[0]
        counts[site] = counts.get(site, 0) + 1
    print("search index:", counts)


if __name__ == "__main__":
    copy_assets()
    tooljury_partials()
    search_index()
