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

from verifier import (
    VerifiedEntry,
    TRUSTED_RE,
    _run_claude,
    _extract_json,
)


BULK_PROMPT_TEMPLATE = (
    "Research the short-stay tourist visa policy for entry into {destination}.\n\n"
    "Use WebSearch + WebFetch to find the most authoritative single source — the\n"
    "official immigration / ministry of foreign affairs / e-visa portal page for\n"
    "{destination} that lists visa-exemption rules by nationality. Prefer the\n"
    "destination country's own government domain (.gov, .gob, .gouv, .go.<cc>,\n"
    "embassy or MFA), not third-party travel sites. ONE source page is enough —\n"
    "do not chain many fetches.\n\n"
    "From that ONE source, determine the visa status for tourist visits for each\n"
    "of these passport-holder nationalities:\n"
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
    "- unknown = nationality not listed on source page\n\n"
    "Rules:\n"
    "1. EVERY listed nationality MUST appear as a key in entries. None skipped.\n"
    "2. Use the EXACT nationality strings shown above as keys (e.g. 'United States',\n"
    "   not 'USA' or 'American').\n"
    "3. If a nationality is not mentioned on the source page, set its status to\n"
    "   'unknown' and notes to 'Not listed on source page.'\n"
    "4. Cite ONE source URL only — the most authoritative one you used.\n"
    "5. If you cannot find an authoritative source, set 'source' to null and mark\n"
    "   every entry as 'unknown'.\n"
    "6. Return only short-stay tourist info — ignore work, student, transit visas."
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
