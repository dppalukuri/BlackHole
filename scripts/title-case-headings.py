"""Convert h1/h2/h3 headings to title case across techtools365-landing pages.

Rules (US/AP-style title case):
- Capitalize first and last word always
- Capitalize all other words EXCEPT: articles (a/an/the), short conjunctions
  (and/but/or/nor/for/yet/so), short prepositions (a/at/by/in/of/on/per/to/up/via etc.)
- Preserve mixed-case words as-is (TechTools365, NordVPN, iPhone)
- Preserve all-uppercase acronyms (UAE, US, VPN, API)
- Capitalize first word after period, em-dash, colon, question mark
- Apostrophes don't break words (Don't, We're, etc.)

Only operates on the inner text of h1/h2/h3 tags. Preserves nested HTML
(em, strong, span) by recursively processing only text nodes.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\Prasad\Projects\claude_workspace\BlackHole\data-products\techtools365-landing\public")

SMALL_WORDS = {
    "a", "an", "the",
    "and", "but", "or", "nor", "for", "yet", "so",
    "as", "at", "by", "for", "in", "of", "off", "on", "out", "per", "to", "up", "via",
    "from", "into", "like", "near", "onto", "over", "past", "with", "than", "till",
    "until", "is", "be",
}


def smart_capitalize(word: str) -> str:
    """Capitalize first letter only if word is all-lowercase. Otherwise leave alone
    (preserves TechTools365, NordVPN, UAE, US, iPhone, etc.)."""
    if not word:
        return word
    # Mixed-case (has both upper and lower): leave alone
    if word != word.lower() and word != word.upper():
        return word
    # All-uppercase, length > 1: acronym (UAE, US, VPN), leave alone
    if len(word) > 1 and word.isupper():
        return word
    # All-lowercase: capitalize first alpha
    chars = list(word)
    for i, c in enumerate(chars):
        if c.isalpha():
            chars[i] = c.upper()
            return "".join(chars)
    return word


def title_case_text(text: str) -> str:
    """Apply title case to a string, respecting punctuation and small-word rules."""
    # Split by whitespace tokens (preserve whitespace runs separately would be nice, but
    # standard headings use single spaces — keep it simple)
    tokens = re.split(r"(\s+)", text)
    word_tokens_idx = [i for i, t in enumerate(tokens) if t.strip()]
    if not word_tokens_idx:
        return text

    first_idx = word_tokens_idx[0]
    last_idx = word_tokens_idx[-1]
    prev_was_break = True  # treat start of string as a break point

    for i, tok in enumerate(tokens):
        if not tok.strip():
            continue
        # Identify leading and trailing non-alpha punctuation
        m = re.match(r"^([^A-Za-z]*)(.*?)([^A-Za-z]*)$", tok, re.DOTALL)
        if not m:
            continue
        leading, core, trailing = m.group(1), m.group(2), m.group(3)
        if not core:
            continue

        # Bare alphabetic word for SMALL_WORDS check
        bare = "".join(c for c in core if c.isalpha()).lower()

        is_first_or_last = (i == first_idx or i == last_idx)
        is_after_break = prev_was_break

        if is_first_or_last or is_after_break or bare not in SMALL_WORDS:
            new_core = smart_capitalize(core)
        else:
            # Lowercase (only if all-lowercase already; never demote acronyms/mixed)
            if core == core.lower():
                new_core = core
            else:
                new_core = core  # leave alone
        tokens[i] = leading + new_core + trailing

        # Update prev_was_break: the trailing punctuation of THIS token determines
        # whether the next word starts a "phrase"
        if trailing and trailing[-1] in ".:?!\u2014\u2013-" or any(c in trailing for c in ".:?!"):
            prev_was_break = True
        else:
            prev_was_break = False
    return "".join(tokens)


# Match <h1>...</h1>, <h2>...</h2>, <h3>...</h3>. Inner content can have nested tags.
HEADING_RE = re.compile(r"(<(h[123])>)(.*?)(</\2>)", flags=re.DOTALL | re.IGNORECASE)
TEXT_NODE_RE = re.compile(r"(>)([^<]+)(<)|^([^<]+)(<)|(>)([^<]+)$|^([^<]+)$")


def process_inner(inner: str) -> str:
    """Apply title case to text between tags, leave tags themselves alone."""
    parts = re.split(r"(<[^>]+>)", inner)
    out = []
    for part in parts:
        if part.startswith("<"):
            out.append(part)
        else:
            out.append(title_case_text(part))
    return "".join(out)


def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    orig = text
    changes = [0]

    def replace(m: re.Match[str]) -> str:
        open_tag, _, inner, close_tag = m.group(1), m.group(2), m.group(3), m.group(4)
        new_inner = process_inner(inner)
        if new_inner != inner:
            changes[0] += 1
        return open_tag + new_inner + close_tag

    text = HEADING_RE.sub(replace, text)
    if text != orig:
        path.write_text(text, encoding="utf-8")
    return changes[0]


# Pages to process
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

total = 0
for rel in PAGES:
    p = ROOT / rel
    if not p.exists():
        continue
    n = process_file(p)
    total += n
    if n:
        print(f"  [updated] {rel} ({n} headings title-cased)")
    else:
        print(f"  [no change] {rel}")
print(f"\nTotal headings title-cased: {total}")
