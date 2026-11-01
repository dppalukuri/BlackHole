"""Apply the shared TechTools365 bar, footer, fonts and icons to every page on the landing site.

Pages hold marker comments (<!-- tt:bar --> and so on) and the script fills them, so it can be
re-run after any edit to shared/brand. Older pages without markers get converted on the first run.

    python data-products/techtools365-landing/scripts/sync-shell.py
"""
import importlib.util
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1] / "public"
spec = importlib.util.spec_from_file_location("brand_sync", Path(__file__).resolve().parents[2] / "shared" / "brand" / "sync.py")
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)

PAGES = [
    ("index.html", None),
    ("about/index.html", "about"),
    ("privacy/index.html", None),
    ("contact/index.html", "contact"),
    ("blog/index.html", "blog"),
    ("blog/how-to-choose-a-vpn-2026/index.html", "blog"),
    ("blog/visa-stacking-explained-2026/index.html", "blog"),
    ("blog/uae-vs-india-take-home-salary-2026/index.html", "blog"),
    ("blog/techtools365-methodology/index.html", "blog"),
]

ICON_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Cdefs%3E"
    "%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%23F7C39B'/%3E"
    "%3Cstop offset='1' stop-color='%237786F0'/%3E%3C/linearGradient%3E%3C/defs%3E"
    "%3Ccircle cx='16' cy='16' r='15.5' fill='url(%23g)'/%3E"
    "%3Cpath d='M9.5 10h13v3.2h-4.9V23h-3.2v-9.8H9.5z' fill='white'/%3E%3C/svg%3E"
)
ICONS = f'<link rel="icon" href="{ICON_SVG}" />\n  <link rel="apple-touch-icon" href="{ICON_SVG}" />'
STYLE = (
    '<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@300..700&display=swap" rel="stylesheet" />\n'
    '  <link rel="stylesheet" href="/css/brand.css" />\n'
    '  <link rel="stylesheet" href="/css/site.css" />'
)
SITE_LINKS = """<nav aria-label="Contact">
      <h2>Contact</h2>
      <ul>
        <li><a href="mailto:palukuri.biz@gmail.com">palukuri.biz@gmail.com</a></li>
        <li><a href="/blog/techtools365-methodology/">Methodology</a></li>
      </ul>
    </nav>"""
FINE = (
    "&copy; 2026 TechTools365. We may earn affiliate commissions on outbound links to NordVPN and Proton. "
    "Partnerships are disclosed on every relevant page."
)


def spark():
    """Sparkline for the PennyMath card: ₹5,000 a month at 12% for 10 years, against what went in."""
    r, values, invested = 0.01, [0.0], [0.0]
    for year in range(1, 11):
        n = year * 12
        values.append(5000 * ((1 + r) ** n - 1) / r * (1 + r))
        invested.append(5000.0 * n)
    top = values[-1]
    path = lambda series: " ".join(
        f"{'M' if i == 0 else 'L'}{i * 30} {54 - v / top * 50:.1f}" for i, v in enumerate(series)
    )
    return (
        '<svg viewBox="0 0 300 56" preserveAspectRatio="none" role="img" '
        'aria-label="Growth of a monthly investment over 10 years, compared with the amount paid in">'
        f'<path class="spark-invested" d="{path(invested)}"></path>'
        f'<path class="spark-value" d="{path(values)}"></path></svg>'
    )


def fill(text, name, content):
    pattern = re.compile(rf"<!-- tt:{name} -->.*?<!-- /tt:{name} -->", flags=re.S)
    return pattern.sub(lambda _: f"<!-- tt:{name} -->\n  {content}\n  <!-- /tt:{name} -->", text)


def add_markers(text):
    """Convert a page from the old nav, footer and font tags on its first run."""
    text = re.sub(r'<nav class="site-nav".*?</nav>', "<!-- tt:bar -->\n  <!-- /tt:bar -->", text, count=1, flags=re.S)
    text = re.sub(r'<footer class="site-footer">.*?</footer>', "<!-- tt:footer -->\n  <!-- /tt:footer -->", text, count=1, flags=re.S)
    if "<!-- tt:style -->" not in text:
        text, n = re.subn(r'<link href="https://fonts\.googleapis\.com/css2[^>]*>\s*<link rel="stylesheet" href="/css/site\.css"\s*/?>', "<!-- tt:style -->\n  <!-- /tt:style -->", text, count=1)
        assert n == 1, "font and stylesheet tags not found"
    if "<!-- tt:icons -->" not in text:
        text = re.sub(r'\s*<link rel="apple-touch-icon"[^>]*>', "", text)
        text, n = re.subn(r'<link rel="icon"[^>]*>', "<!-- tt:icons -->\n  <!-- /tt:icons -->", text, count=1)
        assert n == 1, "icon tag not found"
    text = re.sub(r'<meta name="theme-color" content="[^"]*"\s*/?>', '<meta name="theme-color" content="#15161E" />', text)
    return text


def page_bar(active):
    links = [("/about/", "About", "about"), ("/blog/", "Blog", "blog"), ("/contact/", "Contact", "contact")]
    extra = '<nav class="tt-extra" aria-label="TechTools365">' + "".join(
        f'<a href="{href}"{" aria-current=" + chr(34) + "page" + chr(34) if key == active else ""}>{label}</a>'
        for href, label, key in links
    ) + "</nav>"
    return brand.family_bar(extra)


for rel, active in PAGES:
    path = ROOT / rel
    text = add_markers(path.read_text(encoding="utf-8"))
    text = fill(text, "icons", ICONS)
    text = fill(text, "style", STYLE)
    text = fill(text, "bar", page_bar(active))
    text = fill(text, "footer", brand.family_footer(SITE_LINKS, FINE))
    text = fill(text, "spark", spark())
    path.write_text(text, encoding="utf-8", newline="\n")
    print("updated", rel)
