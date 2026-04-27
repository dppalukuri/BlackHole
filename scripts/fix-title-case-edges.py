"""Fix edge cases the auto title-caser missed:
- 'For' that should be 'for' when it's mid-phrase (split by <em> tags)
- 'Vs' → 'vs' (small word)
- Hyphenated compounds: title-case both halves (Top-ranked → Top-Ranked)
- 'the' after em-dash should be 'The' (start of clause)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Prasad\Projects\claude_workspace\BlackHole\data-products\techtools365-landing\public")

PAGES = [
    "index.html",
    "about/index.html",
    "contact/index.html",
    "privacy/index.html",
    "blog/index.html",
    "blog/how-to-choose-a-vpn-2026/index.html",
    "blog/visa-stacking-explained-2026/index.html",
    "blog/uae-vs-india-take-home-salary-2026/index.html",
    "blog/techtools365-methodology/index.html",
]

# Apply only to heading text — match heading tags first, then fix the inner.
HEADING_RE = re.compile(r"(<h[123]>)(.*?)(</h[123]>)", flags=re.DOTALL | re.IGNORECASE)

# Specific replacements to apply inside heading inner text:
INNER_FIXES = [
    # Article-style: "the" after em-dash → "The"
    (re.compile(r"(\u2014\s+)the\b"), r"\1The"),
    # Vs → vs (used as preposition in titles)
    (re.compile(r"\bVs\b"), "vs"),
    # Common hyphenated compounds — title-case the second half
    ("Top-ranked", "Top-Ranked"),
    ("Take-home", "Take-Home"),
    ("Highest-leverage", "Highest-Leverage"),
    ("Stack-on", "Stack-On"),
    ("C-visa", "C-Visa"),
    ("Visa-data", "Visa-Data"),
    ("Long-stay", "Long-Stay"),
    ("Multi-passport", "Multi-Passport"),
    ("Multi-hop", "Multi-Hop"),
    ("Two-year", "Two-Year"),
    ("Open-source", "Open-Source"),
    ("Tax-regime", "Tax-Regime"),
    ("No-logs", "No-Logs"),
    ("Re-verified", "Re-Verified"),
    ("Re-verify", "Re-Verify"),
    ("In-depth", "In-Depth"),
    ("Cost-of-living", "Cost-of-Living"),
    ("Single-source", "Single-Source"),
    ("Real-time", "Real-Time"),
    # "For" specifically as mid-heading prepostion (only if preceded by space and a word, followed by space)
    # Apply only when in heading context and rest of sentence follows
    (re.compile(r"(\b[A-Z][a-z]+ Tools )For(\s|<)"), r"\1for\2"),
]

total = 0
for rel in PAGES:
    p = ROOT / rel
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    orig = text

    def fix(m: re.Match[str]) -> str:
        open_, inner, close_ = m.group(1), m.group(2), m.group(3)
        for rule, repl in INNER_FIXES:
            if isinstance(rule, str):
                inner = inner.replace(rule, repl)
            else:
                inner = rule.sub(repl, inner)
        return open_ + inner + close_

    text = HEADING_RE.sub(fix, text)
    if text != orig:
        p.write_text(text, encoding="utf-8")
        total += 1
        print(f"  [updated] {rel}")
print(f"\nFiles updated: {total}")
