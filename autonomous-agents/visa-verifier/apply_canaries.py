"""
apply_canaries.py — patch tripwire canary entries into verified-visas.json.

Why: every entry in canaries.json is a real-looking visa-policy record with a
distinctive phrase in its `notes` field. We deliberately overwrite the verifier
output for those (passport, destination) pairs so the static site renders the
canary wording. If those exact phrases ever appear on a competitor's site or
in someone's leaked dataset for the same passport->destination pair, that is
strong evidence of scraping.

Canaries sit on obscure passport->destination pairs (Tuvalu->Kiribati,
San Marino->Palau, etc.) so end users are not affected — those pages get
near-zero traffic. The visa status (vf / voa / etc.) and day-counts are real
even on canary entries; only the WORDING is the tripwire.

Run this AFTER every bulk_agent.py / agent.py sweep, because the verifier
overwrites the canary entries with whatever the model returned.

Usage:
    python apply_canaries.py              # patch output/verified-visas.json
    python apply_canaries.py --sync       # also push to the wanderwise src dir
    python apply_canaries.py --verify     # report whether canaries are intact
"""
from __future__ import annotations
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANARIES = ROOT / "canaries.json"
OUTPUT = ROOT / "output" / "verified-visas.json"


def load_canaries() -> list[dict]:
    if not CANARIES.exists():
        print(f"[error] canary registry not found: {CANARIES}")
        print(f"        if this is a fresh checkout, that's expected — canaries.json is gitignored.")
        return []
    payload = json.loads(CANARIES.read_text(encoding="utf-8"))
    return payload.get("canaries", [])


def load_output() -> dict:
    if not OUTPUT.exists():
        print(f"[error] verified-visas.json not found: {OUTPUT}")
        sys.exit(1)
    return json.loads(OUTPUT.read_text(encoding="utf-8"))


def save_output(payload: dict) -> None:
    tmp = OUTPUT.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    tmp.replace(OUTPUT)


def apply(payload: dict, canaries: list[dict]) -> int:
    data = payload.setdefault("data", {})
    n = 0
    for c in canaries:
        p = c["passport"]
        d = c["destination"]
        data.setdefault(p, {})[d] = c["entry"]
        n += 1
    return n


def verify(payload: dict, canaries: list[dict]) -> tuple[int, int]:
    data = payload.get("data", {})
    intact = 0
    missing = 0
    for c in canaries:
        cur = data.get(c["passport"], {}).get(c["destination"])
        if not cur:
            print(f"  [MISSING] {c['id']} {c['passport']} -> {c['destination']}")
            missing += 1
            continue
        phrase = c["distinctive_phrase"]
        if phrase in (cur.get("notes") or ""):
            intact += 1
        else:
            print(f"  [OVERWRITTEN] {c['id']} {c['passport']} -> {c['destination']}")
            print(f"    expected phrase: {phrase!r}")
            print(f"    current notes:   {cur.get('notes')!r}")
            missing += 1
    return intact, missing


def sync_to_site() -> None:
    site = ROOT.parent.parent / "data-products" / "wanderwise" / "src" / "data" / "_verified" / "verified-visas.json"
    site.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUTPUT, site)
    print(f"[sync] copied -> {site}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true", help="Check whether canaries are still intact")
    ap.add_argument("--sync", action="store_true", help="After patching, copy to wanderwise src/data/_verified")
    args = ap.parse_args()

    canaries = load_canaries()
    if not canaries:
        return 1

    payload = load_output()

    if args.verify:
        intact, missing = verify(payload, canaries)
        total = intact + missing
        print(f"\n[verify] {intact}/{total} canaries intact")
        return 0 if missing == 0 else 1

    n = apply(payload, canaries)
    save_output(payload)
    print(f"[apply] patched {n} canary entries into {OUTPUT}")

    if args.sync:
        sync_to_site()

    return 0


if __name__ == "__main__":
    sys.exit(main())
