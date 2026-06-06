"""One-off: replace the inline data: favicon with /favicon.svg in tooljury's
pre-built public/ HTML files, and copy static/favicon.svg → public/favicon.svg.

Used because Hugo isn't installed locally so we can't rebuild tooljury cleanly.
"""
from __future__ import annotations
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLJURY = ROOT / "data-products" / "tooljury"

# Hugo minified output: <link rel=icon href="data:image/svg+xml,...T..." />
# Match the entire <link rel=icon ...> tag through its closing >
FAVICON_RE = re.compile(
    r"<link\s+rel=(?:\"icon\"|icon)\s+href=\"data:image/svg\+xml,[^\"]*\"\s*/?>",
    re.IGNORECASE,
)
REPLACEMENT = '<link rel="icon" type="image/svg+xml" href="/favicon.svg"/>'


def main() -> int:
    public = TOOLJURY / "public"
    if not public.exists():
        print(f"missing {public}")
        return 1

    # Copy the static favicon into public so it serves at /favicon.svg
    src = TOOLJURY / "static" / "favicon.svg"
    dst = public / "favicon.svg"
    if src.exists():
        shutil.copy2(src, dst)
        print(f"copied: {src.name} -> public/{dst.name}")

    # Rewrite the inline favicon link in every HTML file
    files = 0
    total = 0
    for html in public.rglob("*.html"):
        try:
            text = html.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        new, n = FAVICON_RE.subn(REPLACEMENT, text)
        if n:
            html.write_text(new, encoding="utf-8")
            files += 1
            total += n
    print(f"rewrote favicon link in {files} html files ({total} replacements)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
