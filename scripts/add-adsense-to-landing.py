"""Add the AdSense script + verification meta tag to the landing site's HTML.

The landing site (data-products/techtools365-landing) is hand-written HTML
with no build system, so we edit public/*.html directly. Idempotent — runs
again as a no-op if the snippet is already present.

Adds:
  <meta name="google-adsense-account" content="ca-pub-9446467058878539" />
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9446467058878539" crossorigin="anonymous"></script>

Right before </head>. Skips files that already have the AdSense pub ID.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANDING = ROOT / "data-products" / "techtools365-landing" / "public"

PUB_ID = "ca-pub-9446467058878539"
SNIPPET = (
    '  <!-- AdSense site verification + display script -->\n'
    f'  <meta name="google-adsense-account" content="{PUB_ID}" />\n'
    f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUB_ID}" crossorigin="anonymous"></script>\n'
)
HEAD_END = re.compile(r"</head>", re.IGNORECASE)


def process(p: Path) -> str:
    text = p.read_text(encoding="utf-8")
    if PUB_ID in text:
        return "skip-already-present"
    if not HEAD_END.search(text):
        return "skip-no-head-tag"
    new = HEAD_END.sub(SNIPPET + "</head>", text, count=1)
    p.write_text(new, encoding="utf-8")
    return "updated"


def main() -> int:
    if not LANDING.exists():
        print(f"missing: {LANDING}")
        return 1
    counts: dict[str, int] = {}
    for html in LANDING.rglob("*.html"):
        status = process(html)
        counts[status] = counts.get(status, 0) + 1
        rel = html.relative_to(ROOT)
        print(f"  [{status}] {rel}")
    print()
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
