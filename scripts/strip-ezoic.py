"""One-off: strip Ezoic / gatekeeperconsent script tags from already-built HTML.

Used after removing Ezoic from sources when we can't re-run Hugo locally
(tooljury's pre-built public/ HTML still has the minified script tags).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Match any <script ...>...</script> whose attribute string or content
# contains one of these tokens. Hugo's minifier puts everything on one
# line so a single regex over <script> tags works.
TOKENS = ("ezoic", "gatekeeperconsent", "ezojs", "ezoicanalytics", "ezstandalone")
TOKEN_RE = "|".join(re.escape(t) for t in TOKENS)

# Non-greedy match between <script ...> and </script>. The 's' flag is
# not needed here because the minified output has no newlines inside
# script tags.
SCRIPT_RE = re.compile(
    r"<script\b[^>]*(?:" + TOKEN_RE + r")[^>]*>.*?</script>",
    re.IGNORECASE,
)
# Also handle <script>window.ezstandalone=...</script> where the token
# is in the body, not attributes.
SCRIPT_BODY_RE = re.compile(
    r"<script\b[^>]*>[^<]*(?:" + TOKEN_RE + r")[^<]*</script>",
    re.IGNORECASE,
)


def process(p: Path) -> int:
    try:
        text = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return 0
    new, n1 = SCRIPT_RE.subn("", text)
    new, n2 = SCRIPT_BODY_RE.subn("", new)
    n = n1 + n2
    if n:
        p.write_text(new, encoding="utf-8")
    return n


def main() -> int:
    targets = [
        ROOT / "data-products" / "tooljury" / "public",
    ]
    total_files = 0
    total_strips = 0
    for root in targets:
        if not root.exists():
            continue
        for html in root.rglob("*.html"):
            n = process(html)
            if n:
                total_files += 1
                total_strips += n
    print(f"stripped {total_strips} script tags from {total_files} html files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
