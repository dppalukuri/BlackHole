"""
Bulk per-destination visa verification.

One Claude call per destination resolves visa-status for many passports at once
by reading the destination country's official visa-policy page. ~50–100x
cheaper and faster than the per-pair `verifier.verify_pair`.

Output entries use the same VerifiedEntry shape so the on-disk format and
the site reader code do not change.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional

import re

from verifier import (
    VerifiedEntry,
    TRUSTED_RE,
    _run_claude,
    _extract_json,
)

# Hard blocklist for sources that the model sometimes cites despite prompt
# instructions. These are encyclopedic or aggregator URLs — not authoritative
# even if their content is largely correct. Treat them as if the model returned
# no source at all (forces 'unknown' status, hidden from site).
SOURCE_BLOCKLIST = re.compile(
    r"(iatatravelcentre\.com|timaticweb|ivisa\.com|visahq\.com|"
    r"tripadvisor|reddit\.com|quora\.com)",
    re.IGNORECASE,
)


BULK_PROMPT_TEMPLATE = (
    "Research the short-stay tourist visa policy for entry into {destination}.\n\n"
    "SOURCE PRIORITY — pick the highest-tier source you can confirm:\n"
    "  TIER 1 (preferred): an OFFICIAL government page from {destination} —\n"
    "    .gov / .gov.<cc> / .gob.<cc> / .gouv.<cc> / .go.<cc> domains, or the\n"
    "    destination's ministry of foreign affairs / immigration department /\n"
    "    official e-visa portal. ALWAYS look for this FIRST.\n"
    "  TIER 2 (fallback): if a comprehensive Tier-1 page cannot be found after a\n"
    "    real search, use a maintained reference such as Wikipedia's\n"
    "    'Visa policy of {destination}' page. Tier 2 sources still get returned;\n"
    "    they just carry lower trust.\n\n"
    "Forbidden anywhere: travel blogs, news articles, visa-aggregator sites,\n"
    "forums (Reddit/Quora), TripAdvisor, the SOURCE-passport's MFA. Stick to\n"
    "Tier 1 or Tier 2 only.\n\n"
    "Search strategy — try Tier 1 queries first:\n"
    "- 'site:gov.<cc> visa exemption {destination}'\n"
    "- '{destination} ministry of foreign affairs visa policy'\n"
    "- '{destination} immigration visa-free nationalities list'\n"
    "- '{destination} e-visa official site'\n"
    "Only after those genuinely fail, fall back to 'Visa policy of {destination}'.\n\n"
    "Cite the ONE source URL you used. If ALL searches fail (no usable page found):\n"
    "set source=null, mark every entry status='unknown'.\n\n"
    "Determine the visa status for tourist visits for each of these\n"
    "passport-holder nationalities:\n"
    "{passport_list_block}\n\n"
    "Return EXACTLY ONE valid JSON object — no prose before or after, no\n"
    "markdown fences:\n\n"
    "{{\n"
    '  "destination": "{destination}",\n'
    '  "source": "https://..." or null,\n'
    '  "entries": {{\n'
    '    "<Passport Country Name>": {{\n'
    '      "status": "vf" | "voa" | "ev" | "eta" | "vr" | "unknown",\n'
    '      "days":   <integer max stay> or null,\n'
    '      "notes":  "<one short sentence>"\n'
    "    }},\n"
    "    ...\n"
    "  }}\n"
    "}}\n\n"
    "Status codes:\n"
    "- vf      = visa-free walk-in entry\n"
    "- voa     = visa on arrival (purchased at border)\n"
    "- ev      = e-visa (apply online before travel)\n"
    "- eta     = electronic travel authorization (ESTA, eTA, K-ETA style)\n"
    "- vr      = visa required (embassy application in advance)\n"
    "- unknown = nationality not listed on source page OR no official source found\n\n"
    "Rules:\n"
    "1. EVERY listed nationality MUST appear as a key in entries. None skipped.\n"
    "2. Use the EXACT nationality strings shown above as keys (e.g. 'United States',\n"
    "   not 'USA' or 'American').\n"
    "3. If a nationality is not mentioned on the source page, set its status to\n"
    "   'unknown' and notes to 'Not listed on source page.'\n"
    "4. Cite ONE source URL only — the most authoritative {destination} government one.\n"
    "5. Return only short-stay tourist info — ignore work, student, transit visas."
)


def _format_passport_list(passports: list[str]) -> str:
    return "\n".join(f"- {p}" for p in passports)


def _bulk_confidence(source: Optional[str], status: str) -> str:
    """Bulk confidence: trust gate the shared source URL; unknown stays unknown."""
    if status == "unknown":
        return "unknown" if not source else "low"
    if not source:
        return "unknown"
    return "high" if TRUSTED_RE.search(source) else "low"


def verify_destination_bulk(
    destination: str,
    passports: list[str],
    model: str = "haiku",
    timeout_sec: int = 480,
) -> dict[str, VerifiedEntry]:
    """One Claude call → {passport_name: VerifiedEntry} for the given destination.

    Self-references (passport == destination) are answered by rule, not by the
    model. If the model omits a passport, that passport is filled in with an
    'unknown' entry pointing at the shared source URL (so the site hides it but
    the orchestrator knows it's been processed for TTL purposes).
    """
    if not passports:
        return {}

    verified_at = datetime.now(timezone.utc).date().isoformat()
    out: dict[str, VerifiedEntry] = {}

    # Pull out self-refs — handle by rule, don't include in the prompt
    asked: list[str] = []
    for p in passports:
        if p.strip().lower() == destination.strip().lower():
            out[p] = VerifiedEntry(
                passport=p,
                destination=destination,
                status="vf",
                days=None,
                source=None,
                notes=f"{p} citizens enter their own country without a visa.",
                confidence="high",
                verified_at=verified_at,
                model="rule:own-country",
            )
        else:
            asked.append(p)

    if not asked:
        return out

    prompt = BULK_PROMPT_TEMPLATE.format(
        destination=destination,
        passport_list_block=_format_passport_list(asked),
    )
    body = _run_claude(prompt, model=model, timeout_sec=timeout_sec)
    parsed = _extract_json(body) or {}

    source = parsed.get("source")
    if source and not str(source).startswith(("http://", "https://")):
        source = None
    if source and SOURCE_BLOCKLIST.search(source):
        # Aggregator / forum / blog sources are unrecoverable as data. Drop.
        # Wikipedia is NOT in the blocklist — it lands as 'low' confidence,
        # which is intentional: data is preserved, badge is withheld.
        source = None

    entries_raw = parsed.get("entries")
    if not isinstance(entries_raw, dict):
        entries_raw = {}

    model_tag = f"claude-code:{model}:bulk"

    for passport in asked:
        e = entries_raw.get(passport)
        if not isinstance(e, dict):
            out[passport] = VerifiedEntry(
                passport=passport,
                destination=destination,
                status="unknown",
                days=None,
                source=source,
                notes="Not listed on source page.",
                confidence="unknown" if not source else "low",
                verified_at=verified_at,
                model=model_tag,
            )
            continue

        status = e.get("status", "unknown")
        if status not in {"vf", "voa", "ev", "eta", "vr", "unknown"}:
            status = "unknown"

        days = e.get("days")
        try:
            days = int(days) if days is not None else None
        except (TypeError, ValueError):
            days = None

        notes = str(e.get("notes") or "").strip()
        confidence = _bulk_confidence(source, status)
        if confidence == "unknown":
            status = "unknown"

        out[passport] = VerifiedEntry(
            passport=passport,
            destination=destination,
            status=status,
            days=days,
            source=source,
            notes=notes,
            confidence=confidence,
            verified_at=verified_at,
            model=model_tag,
        )

    return out
