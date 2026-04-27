"""Add trailing slashes to internal href attributes in all .astro files.

Why: Cloudflare Pages 308-redirects /foo → /foo/, which Google flags as
"Page with redirect" indexing failures. Sitemap URLs already use trailing
slashes; canonical tags do too. This script makes the internal links
consistent so Google never sees a redirect during crawl.

Patterns it fixes:
  href="/about"           → href="/about/"
  href="/foo-bar"         → href="/foo-bar/"
  href={`/${slug}`}       → href={`/${slug}/`}
  href={`/visa-free-to-${d.slug}`} → href={`/visa-free-to-${d.slug}/`}

Patterns it leaves alone:
  href="/"                — root, already has slash
  href="/?p=...&d=..."    — query-string, no path-trailing-slash needed
  href="/foo/"            — already has slash
  href="https://..."      — external URLs
  href="#anchor"          — anchor links
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

SRC = Path(r"C:\Prasad\Projects\claude_workspace\BlackHole\data-products\visapathway\src")

# 1. Quoted string href: href="/foo" or href="/foo-bar" → add trailing /
#    But NOT if it ends with /, ?, #, or has a . (file ext).
QUOTED_RE = re.compile(r'href="(/[a-z][a-z0-9-]*)"')

# 2. Template literal href: href={`/${...}`} or href={`/visa-free-to-${...}`}
#    Add / right before the closing backtick if not already present.
TEMPLATE_RE = re.compile(r'href=\{`(/[^`]*[^/`])`\}')

changed_files: list[tuple[str, int]] = []

for path in SRC.rglob("*.astro"):
    text = path.read_text(encoding="utf-8")
    orig = text

    # Quoted-string fix
    text = QUOTED_RE.sub(r'href="\1/"', text)

    # Template-literal fix — only if the inner path is route-like (starts with /, has $ or letters)
    def template_replace(m: re.Match[str]) -> str:
        inner = m.group(1)
        # Skip if it's a query-string URL or anchor — these don't need trailing slash
        if "?" in inner or "#" in inner:
            return m.group(0)
        # Skip if it's a file (has extension like .json, .css, etc.)
        if re.search(r"\.[a-z]{2,5}$", inner):
            return m.group(0)
        return f'href={{`{inner}/`}}'

    text = TEMPLATE_RE.sub(template_replace, text)

    if text != orig:
        n_changes = sum(1 for _ in re.finditer(r'href="[^"]+/"|href=\{`[^`]+/`\}', text)) - sum(
            1 for _ in re.finditer(r'href="[^"]+/"|href=\{`[^`]+/`\}', orig)
        )
        path.write_text(text, encoding="utf-8")
        changed_files.append((str(path.relative_to(SRC)), n_changes))

print(f"\nFiles modified: {len(changed_files)}")
for f, n in sorted(changed_files):
    print(f"  +{n} trailing slashes  {f}")
