"""
Core verification logic: one (passport, destination) pair → structured visa status.

Uses the `claude` CLI in non-interactive mode so verification runs on the user's
Claude Code subscription (no API key needed). Claude Code has WebSearch and
WebFetch tools built-in; we allowlist only those for safety.

Output is the same VerifiedEntry shape as before. Domain trust gates confidence.
"""
from __future__ import annotations
import json
import re
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional

# Trusted domain patterns — if the source URL matches any of these we mark the
# entry "verified". Anything else falls through to "low" confidence even if the
# model returns a URL. Keep this conservative; add domains only when proven.
#
# Most countries host their visa info on one of: a .gov / .gob / .gouv domain,
# an embassy/consulate page, an MFA (mfa/mofa/esteri/kln/etc), or an official
# e-visa portal. The patterns below cover the common shapes.
TRUSTED_PATTERNS = [
    # English-world gov TLDs
    r"\.gov($|\.|/)",           # *.gov (US federal, Canada .gov in some subdomains)
    r"\.gov\.[a-z]+($|/)",      # .gov.uk, .gov.in, .gov.au, .gov.sg, .gov.my …
    # Spanish-world gov
    r"\.gob\.[a-z]+($|/)",      # .gob.mx, .gob.es, .gob.ar …
    # French-world gov
    r"\.gouv\.[a-z]+($|/)",     # .gouv.fr, .gouv.ci …
    r"france-visas\.gouv\.fr",  # France visa portal explicitly
    # Asian gov TLDs
    r"\.go\.jp($|/)",           # Japan
    r"\.go\.kr($|/)",           # South Korea
    r"\.go\.th($|/)",           # Thailand
    r"\.go\.id($|/)",           # Indonesia
    # European government sub-systems
    r"\.admin\.ch($|/)",        # Switzerland federal
    r"\.bund\.de($|/)",         # Germany federal
    r"diplo\.de($|/)",          # German diplomatic / embassy network
    r"\.esteri\.it($|/)",       # Italy MFA
    r"\.sre\.gob\.mx",          # Mexico Foreign Affairs
    r"\.kln\.gov\.my",          # Malaysia MFA
    r"mofa\.go\.",              # Japan/Korea/Vietnam MFAs
    r"mfa\.",                   # generic MFA subdomain on many gov domains
    r"canada\.ca($|/)",         # Canada's federal portal (uses .ca, not .gov)
    r"netherlandsworldwide\.nl",# Netherlands MFA
    r"imigrasi\.go\.id",        # Indonesia immigration
    r"immigration\.",           # immigration.nz, immigration.gov.nz, etc.
    r"ukba\.",                  # UK Border Agency / legacy
    r"emb-japan\.go\.jp",       # Japan embassies abroad
    # Generic signals
    r"embassy|consulate",       # embassy / consulate pages on various domains
    r"evisa\.",                 # official e-visa portals (evisa.gov.tr, etc.)
    r"e-visa\.",                # e-visa.go.id etc.
    r"vfsglobal\.com",          # VFS — outsourced but officially gov-contracted
    r"gvcworld\.eu",            # Greek Visa Centre — official contractor
    r"u\.ae($|/)",              # UAE official government portal
    r"travel\.gc\.ca",          # Canada official travel advisories
    # EU
    r"europa\.eu($|/)",         # EU official
    r"ec\.europa\.eu",
    r"home-affairs\.ec\.europa\.eu",
    r"eeas\.europa\.eu",        # EU External Action Service
    # US-specific
    r"travel\.state\.gov",
    r"state\.gov",
]
TRUSTED_RE = re.compile("|".join(TRUSTED_PATTERNS), re.IGNORECASE)


@dataclass
class VerifiedEntry:
    """One verified visa-requirement fact."""
    passport: str
    destination: str
    status: str          # vf | voa | ev | eta | vr | unknown
    days: Optional[int]
    source: Optional[str]
    notes: str
    confidence: str      # high | medium | low | unknown
    verified_at: str     # ISO date
    model: str

    def to_dict(self) -> dict:
        return asdict(self)


PROMPT_TEMPLATE = (
    "Research the current tourist-visa requirement for a {passport} passport holder "
    "traveling to {destination} as a tourist. Use WebSearch and WebFetch to look up "
    "the information. Prefer official government sources ONLY: embassy pages, "
    "ministries of foreign affairs, official e-visa portals, immigration-department "
    "sites. Recognizable by domains like *.gov, *.gov.{{country}}, embassy.*, mfa.*, "
    "evisa.gov.*, travel.state.gov.\n\n"
    "Return exactly ONE valid JSON object with these keys — no prose before or after, "
    "no markdown fences:\n"
    "{{\n"
    '  "status":     "vf" | "voa" | "ev" | "eta" | "vr" | "unknown",\n'
    '  "days":       integer (max days allowed for short stay) or null,\n'
    '  "source":     "https://..." official gov URL or null,\n'
    '  "notes":      "one short sentence summarizing the requirement",\n'
    '  "confidence": "high" | "medium" | "low"\n'
    "}}\n\n"
    "Status codes:\n"
    "- vf      = visa-free (walk in)\n"
    "- voa     = visa on arrival\n"
    "- ev      = e-visa (apply online before travel)\n"
    "- eta     = electronic travel authorization\n"
    "- vr      = visa required (embassy application in advance)\n"
    "- unknown = no authoritative source found\n\n"
    "Rules:\n"
    "1. If you cannot find an authoritative government source, set status to \"unknown\" "
    "and source to null. Do NOT guess. Do NOT cite blog posts or travel-agent sites.\n"
    "2. Return only tourist / short-stay info — ignore work, student, transit visas.\n"
    "3. Cite ONE source URL only — the most authoritative you found."
)


def _extract_json(text: str) -> Optional[dict]:
    """Pull the first balanced {...} object out of a string."""
    try:
        return json.loads(text)
    except Exception:
        pass
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except Exception:
                    return None
    return None


def _classify_confidence(source: Optional[str], model_conf: str) -> str:
    """Gate confidence on domain trust. Model can only downgrade, not upgrade."""
    if not source:
        return "unknown"
    trusted = bool(TRUSTED_RE.search(source))
    if not trusted:
        return "low"
    if model_conf in ("high", "medium", "low"):
        return model_conf
    return "medium"


class ClaudeCLIError(RuntimeError):
    pass


def _run_claude(
    prompt: str,
    model: str = "haiku",
    timeout_sec: int = 240,
) -> str:
    """
    Invoke `claude -p` in non-interactive mode. Returns the 'result' text
    (the assistant's final textual output). Raises ClaudeCLIError on failure.
    """
    cmd = [
        "claude",
        "-p",
        prompt,
        "--output-format", "json",
        "--model", model,
        "--allowed-tools", "WebSearch,WebFetch",
        "--no-session-persistence",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as e:
        raise ClaudeCLIError(f"claude CLI timed out after {timeout_sec}s") from e
    except FileNotFoundError as e:
        raise ClaudeCLIError("`claude` CLI not found on PATH") from e

    if proc.returncode != 0:
        snippet = (proc.stderr or proc.stdout or "").strip()[:500]
        raise ClaudeCLIError(f"claude CLI exited {proc.returncode}: {snippet}")

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise ClaudeCLIError(f"claude returned non-JSON: {proc.stdout[:200]!r}") from e

    if payload.get("is_error"):
        raise ClaudeCLIError(f"claude API error: {payload.get('result', '')[:300]}")

    return payload.get("result", "") or ""


def verify_pair(
    passport: str,
    destination: str,
    model: str = "haiku",
    timeout_sec: int = 240,
) -> VerifiedEntry:
    """Query Claude via the CLI for one passport→destination pair."""
    if passport.strip().lower() == destination.strip().lower():
        return VerifiedEntry(
            passport=passport,
            destination=destination,
            status="vf",
            days=None,
            source=None,
            notes=f"{passport} citizens enter their own country without a visa.",
            confidence="high",
            verified_at=datetime.now(timezone.utc).date().isoformat(),
            model="rule:own-country",
        )

    prompt = PROMPT_TEMPLATE.format(passport=passport, destination=destination)
    body = _run_claude(prompt, model=model, timeout_sec=timeout_sec)
    parsed = _extract_json(body) or {}

    status = parsed.get("status", "unknown")
    if status not in {"vf", "voa", "ev", "eta", "vr", "unknown"}:
        status = "unknown"
    days = parsed.get("days")
    try:
        days = int(days) if days is not None else None
    except (TypeError, ValueError):
        days = None
    source = parsed.get("source")
    if source and not str(source).startswith(("http://", "https://")):
        source = None
    notes = str(parsed.get("notes") or "").strip()
    confidence = _classify_confidence(source, str(parsed.get("confidence") or ""))
    if confidence == "unknown":
        status = "unknown"

    return VerifiedEntry(
        passport=passport,
        destination=destination,
        status=status,
        days=days,
        source=source,
        notes=notes,
        confidence=confidence,
        verified_at=datetime.now(timezone.utc).date().isoformat(),
        model=f"claude-code:{model}",
    )
