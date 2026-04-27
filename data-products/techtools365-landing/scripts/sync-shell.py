"""Sync the nav + footer + Google Fonts link across all techtools365.com pages.

Why: the landing got a Truvista-inspired redesign with a new nav/footer/font-stack.
The supporting pages (about, privacy, contact, blog index, 4 articles) need to
match. This script does a one-shot replacement of:

  1. Old `<link href="...family=Inter:...">` → new Plus Jakarta Sans + Inter link
  2. Old <nav class="site-nav">...</nav> → new nav with "Browse tools" CTA
  3. Old <footer class="site-footer">...</footer> → new multi-column footer

After the script: build, verify, commit.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Prasad\Projects\claude_workspace\BlackHole\data-products\techtools365-landing\public")

# New <link> for Google Fonts
NEW_FONTS = (
    '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800'
    '&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />'
)

NEW_NAV = """<nav class="site-nav" aria-label="Primary">
    <div class="nav-inner">
      <a href="/" class="nav-brand" aria-label="TechTools365 home">
        <span class="nav-brand-mark">T</span>
        <span>Tech<span class="nav-brand-accent">Tools</span>365</span>
      </a>
      <ul class="nav-links">
        <li><a href="/about/"{about_active}>About</a></li>
        <li><a href="/blog/"{blog_active}>Blog</a></li>
        <li><a href="/contact/"{contact_active}>Contact</a></li>
        <li><a href="/#tools" class="nav-cta">Browse tools</a></li>
      </ul>
    </div>
  </nav>"""

NEW_FOOTER = """<footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <a href="/" class="nav-brand">
          <span class="nav-brand-mark">T</span>
          <span>Tech<span class="nav-brand-accent">Tools</span>365</span>
        </a>
        <p>Free tools for finance, travel, and tech decisions. Built in Dubai, open source on GitHub.</p>
      </div>
      <div class="footer-col">
        <h4>Tools</h4>
        <ul>
          <li><a href="https://calcstack.techtools365.com/" target="_blank" rel="noopener">CalcStack \u2197</a></li>
          <li><a href="https://toolversus.techtools365.com/" target="_blank" rel="noopener">ToolVersus \u2197</a></li>
          <li><a href="https://visapathway.techtools365.com/" target="_blank" rel="noopener">VisaPathway \u2197</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Site</h4>
        <ul>
          <li><a href="/about/">About</a></li>
          <li><a href="/blog/">Blog</a></li>
          <li><a href="/contact/">Contact</a></li>
          <li><a href="/privacy/">Privacy</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Open</h4>
        <ul>
          <li><a href="https://github.com/dppalukuri/BlackHole" target="_blank" rel="noopener">GitHub repo \u2197</a></li>
          <li><a href="/blog/techtools365-methodology/">Methodology</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <p>&copy; 2026 TechTools365 \u2014 free tools, no tricks. We may earn affiliate commissions on outbound links to NordVPN and Proton; partnerships are disclosed on every relevant page.</p>
    </div>
  </footer>"""

# Files to update — exclude index.html (the landing — already redesigned)
SECTION_PAGES = [
    ("about/index.html", "about"),
    ("privacy/index.html", None),
    ("contact/index.html", "contact"),
    ("blog/index.html", "blog"),
    ("blog/how-to-choose-a-vpn-2026/index.html", "blog"),
    ("blog/visa-stacking-explained-2026/index.html", "blog"),
    ("blog/uae-vs-india-take-home-salary-2026/index.html", "blog"),
    ("blog/techtools365-methodology/index.html", "blog"),
]

NAV_RE = re.compile(r'<nav class="site-nav".*?</nav>', flags=re.DOTALL)
FOOTER_RE = re.compile(r'<footer class="site-footer">.*?</footer>', flags=re.DOTALL)
FONTS_RE = re.compile(r'<link href="https://fonts\.googleapis\.com/css2\?family=Inter[^"]*"[^>]*/>')

count_pages = 0
for rel_path, active in SECTION_PAGES:
    path = ROOT / rel_path
    if not path.exists():
        print(f"  [skip] {rel_path} (does not exist)")
        continue
    text = path.read_text(encoding="utf-8")
    orig = text

    # 1. Fonts: replace any old Inter-only link with Plus Jakarta Sans + Inter
    text = FONTS_RE.sub(NEW_FONTS, text)

    # 2. Nav: insert active markers based on which page this is
    nav = NEW_NAV.format(
        about_active=' class="active"' if active == "about" else "",
        blog_active=' class="active"' if active == "blog" else "",
        contact_active=' class="active"' if active == "contact" else "",
    )
    text = NAV_RE.sub(nav, text)

    # 3. Footer
    text = FOOTER_RE.sub(NEW_FOOTER, text)

    if text != orig:
        path.write_text(text, encoding="utf-8")
        count_pages += 1
        print(f"  [updated] {rel_path}")
    else:
        print(f"  [no change] {rel_path}")

print(f"\nUpdated {count_pages} pages.")
