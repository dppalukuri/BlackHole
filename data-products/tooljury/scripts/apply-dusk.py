"""Apply the Dusk design to ToolJury's already-built pages in public/.

Hugo is not installed on this machine, and the live site serves public/ directly, so these pages
are patched rather than rebuilt. The templates in layouts/ carry the same design but have not been
run; once Hugo is available, a `hugo` build replaces this script.

Each page is read from the commit before the redesign, so the script can be re-run. After changing
the shared brand kit:
    python data-products/shared/brand/sync.py
    python data-products/tooljury/scripts/apply-dusk.py
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
REPO_PATH = "data-products/tooljury/public/"
BEFORE_REDESIGN = "5dab550"
ICONS = {
    "VPN": '<path d="M12 3l8 3v6c0 4.5-3.2 7.7-8 9-4.8-1.3-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "Web Hosting": '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    "Email Marketing": '<rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M3.5 7l8.5 6 8.5-6"/>',
}
partial = lambda name: (ROOT / "layouts" / "partials" / name).read_text(encoding="utf-8").strip()
BAR = partial("family-bar.html")
FOOTER = partial("family-footer.html")


def original(rel):
    result = subprocess.run(["git", "show", f"{BEFORE_REDESIGN}:{REPO_PATH}{rel}"], capture_output=True, cwd=ROOT)
    return result.stdout.decode("utf-8") if result.returncode == 0 else (PUBLIC / rel).read_text(encoding="utf-8")


def frontmatter(md):
    text = md.read_text(encoding="utf-8")
    field = lambda name: (re.search(rf'^\s*{name}:\s*"?([^"\n]+)"?', text, re.M) or [None, ""])[1].strip()
    return {"slug": field("slug") or md.stem, "title": field("title"), "category": field("category"), "winner": field("winner")}


def directory():
    """Every built comparison, grouped by category, as the template does with GroupByParam."""
    groups = {}
    for md in sorted((ROOT / "content" / "compare").glob("*.md")):
        meta = frontmatter(md)
        if meta["title"] and (PUBLIC / "compare" / meta["slug"] / "index.html").exists():
            groups.setdefault(meta["category"], []).append(meta)
    out = ['<div class="panels">']
    for category in sorted(groups):
        items = groups[category]
        icon = ICONS.get(category, '<circle cx="12" cy="12" r="8"/><path d="M12 8v8M8 12h8"/>')
        out.append(
            f'<section class="topic"><header class="topic-head"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{icon}</svg>'
            f"<h2>{category}</h2><span>{len(items)}</span></header>"
        )
        for m in items:
            name = re.split(r"\s*[(:]", m["title"])[0].strip()
            out.append(f'<a class="row" href="/compare/{m["slug"]}/"><b>{name}</b><small>{m["winner"]}</small></a>')
        out.append("</section>")
    out.append("</div>")
    return "".join(out)


HERO = """<section class="tj-hero">
  <canvas class="tt-dusk" data-dusk="jury" data-orb-y="0.72" data-orb-y-narrow="0.68" aria-hidden="true"></canvas>
  <div class="tj-hero-copy">
    <h1>Honest software comparisons, with a named winner</h1>
    <p>Side-by-side pricing, features and verdicts for VPNs, web hosting and email marketing, based on public pricing and our own testing.</p>
  </div>
</section>
<script src="/js/dusk.js" defer></script>
"""


def top_nav(rel):
    section = rel.split("/")[0]
    links = [("/", "Home", rel == "index.html"), ("/compare/", "Comparisons", section == "compare"), ("/about/", "About", section == "about"), ("/contact/", "Contact", section == "contact")]
    items = "".join(f'<a href="{href}"{" class=is-active" if on else ""}>{label}</a>' for href, label, on in links)
    return f'<nav class="top" aria-label="ToolJury sections">{items}</nav>'


def transform(text, rel):
    text = re.sub(r"<meta name=theme-color content=[^>]*>", '<meta name=theme-color content="#15161E">', text, count=1)
    text, n = re.subn(
        r'<link href="https://fonts\.googleapis\.com/css2[^>]*>\s*<link rel=stylesheet href=/css/style\.css>',
        '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300..700&display=swap" rel=stylesheet><link rel=stylesheet href=/css/brand.css><link rel=stylesheet href=/css/style.css>',
        text, count=1)
    assert n == 1, (rel, "fonts")

    text, n = re.subn(r"<header class=site-header>.*?</header>", lambda _: BAR + top_nav(rel), text, count=1, flags=re.S)
    assert n == 1, (rel, "header")
    text, n = re.subn(r"<footer class=site-footer>.*?</footer>", lambda _: FOOTER, text, count=1, flags=re.S)
    assert n == 1, (rel, "footer")

    # Placeholder ad units never fill, so they only showed as empty boxes.
    text = re.sub(r'<aside class="rail rail-(?:left|right)".*?</aside>', "", text, flags=re.S)
    text = re.sub(r"<aside class=ad-inline.*?</aside>", "", text, flags=re.S)
    text = text.replace("<div class=frame>", "")
    text, n = re.subn(r"</main>\s*</div>", "</main>", text, count=1)
    assert n == 1, (rel, "frame")
    text = re.sub(r"<script>\s*\(function\(\)\{var e,n=document\.querySelectorAll\(\"ins\.adsbygoogle\"\).*?</script>", "", text, flags=re.S)
    text = re.sub(r"<script>\s*\(function\s*\(\)\s*\{\s*var ads = document\.querySelectorAll.*?</script>", "", text, flags=re.S)

    # Page styles now live in style.css, and section labels lose their emoji.
    text = re.sub(r"<style>.*?</style>", "", text, flags=re.S)
    text = text.replace("⭐ ", "").replace("🛡️ ", "")
    text = re.sub(r"<span class=tag>[^<]*</span>", "", text)
    text = text.replace("</a>/ ", "</a> / ")

    if rel == "index.html":
        text, n = re.subn(
            r"<section class=home-hero>.*?(?=<aside class=editors-pick)",
            lambda _: HERO + directory(),
            text, count=1, flags=re.S)
        assert n == 1, (rel, "home")
    elif re.match(r"compare/[^/]+/index\.html", rel):
        i = text.find("<h2>Feature Comparison</h2>")
        if i == -1:
            i = text.find("<h2", text.find("</h1>"))
        assert i != -1, (rel, "reading start")
        text = text[:i] + '<div class="reading">' + text[i:]
        j = text.rindex("</article>")
        text = text[:j] + "</div>" + text[j:]
    elif "<article>" in text:
        m = re.search(r"</h1>(?:<p class=subtitle>.*?</p>)?", text, flags=re.S)
        assert m, (rel, "h1")
        text = text[:m.end()] + '<div class="reading">' + text[m.end():]
        j = text.rindex("</article>")
        text = text[:j] + "</div>" + text[j:]
    return text


pages = sorted(p.relative_to(PUBLIC).as_posix() for p in PUBLIC.rglob("index.html"))
for rel in pages:
    (PUBLIC / rel).write_text(transform(original(rel), rel), encoding="utf-8", newline="\n")

for src, dest in (("css/style.css", "css/style.css"), ("css/brand.css", "css/brand.css"), ("js/dusk.js", "js/dusk.js"), ("favicon.svg", "favicon.svg"), ("ads.txt", "ads.txt")):
    (PUBLIC / dest).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "static" / src, PUBLIC / dest)
print("patched", len(pages), "pages")
