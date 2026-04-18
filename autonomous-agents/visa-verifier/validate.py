"""
validate.py — second-opinion pass over an existing verified-visas.json.

Runs a stronger (or different) model over Haiku's entries and annotates each
with validation metadata. Disagreements are logged in-line on the entry AND
aggregated into output/validation-issues.json for quick review.

Usage:
    python validate.py                         # sonnet, all entries, sequential
    python validate.py --parallel 4            # 4 concurrent workers
    python validate.py --model opus            # use opus (slower/costlier, highest-quality)
    python validate.py --only-passport India   # subset
    python validate.py --only-destination Turkey
    python validate.py --limit 10              # cheap smoke test
    python validate.py --ttl-days 7            # re-validate entries older than a week
    python validate.py --dry-run               # no API calls — list what would be validated
    python validate.py --sync                  # after, copy to the Astro public/data dir

Validation metadata added to each entry (cleared the next time Haiku
re-verifies — since that replaces the whole entry):

    validated_by:        "claude-code:sonnet"
    validated_at:        "2026-04-18"
    validation_result:   "agree" | "differ-status" | "differ-days" | "error"
    validation_notes:    one-line human summary
    validator_status:    only present on disagreement
    validator_days:      only present on disagreement
    validator_source:    only present on disagreement
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

# UTF-8 stdout for Windows cp1252 terminals
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

from verifier import verify_pair, ClaudeCLIError

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
DEFAULT_INPUT = ROOT / "output" / "verified-visas.json"
DEFAULT_REPORT = ROOT / "output" / "validation-issues.json"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    tmp.replace(path)


def is_stale(entry: dict, ttl_days: int) -> bool:
    vat = entry.get("validated_at")
    if not vat:
        return True
    try:
        d = datetime.fromisoformat(vat).date()
    except Exception:
        return True
    return (datetime.now(timezone.utc).date() - d).days > ttl_days


def validate_one(existing: dict, model: str) -> dict:
    """Re-verify with `model`, return the validation-metadata fields to merge in.

    Does not mutate `existing` — the caller does that.
    """
    p = existing["passport"]
    d = existing["destination"]
    existing_status = existing.get("status")
    existing_days = existing.get("days")

    date = datetime.now(timezone.utc).date().isoformat()
    try:
        v = verify_pair(p, d, model=model)
    except ClaudeCLIError as e:
        return {
            "validated_by": f"claude-code:{model}",
            "validated_at": date,
            "validation_result": "error",
            "validation_notes": f"validator raised: {e!s}"[:240],
        }
    except Exception as e:
        return {
            "validated_by": f"claude-code:{model}",
            "validated_at": date,
            "validation_result": "error",
            "validation_notes": f"validator raised: {e!s}"[:240],
        }

    new_status = v.status
    new_days = v.days
    meta = {
        "validated_by": f"claude-code:{model}",
        "validated_at": date,
    }
    if new_status == existing_status:
        if existing_days == new_days or new_days is None or existing_days is None:
            meta.update({
                "validation_result": "agree",
                "validation_notes": f"both agree: {existing_status}"
                                    + (f" ({existing_days}d)" if existing_days else ""),
            })
        else:
            meta.update({
                "validation_result": "differ-days",
                "validation_notes": f"both {existing_status} but days differ — haiku={existing_days}, {model}={new_days}",
                "validator_status": new_status,
                "validator_days": new_days,
                "validator_source": v.source,
            })
    else:
        meta.update({
            "validation_result": "differ-status",
            "validation_notes": f"haiku said {existing_status}, {model} said {new_status}",
            "validator_status": new_status,
            "validator_days": new_days,
            "validator_source": v.source,
        })
    return meta


def plan_pairs(
    payload: dict,
    ttl_days: int,
    only_passport: str | None,
    only_destination: str | None,
) -> list[Tuple[str, str]]:
    pending: list[Tuple[str, str]] = []
    for passport, dests in (payload.get("data") or {}).items():
        if only_passport and passport.lower() != only_passport.lower():
            continue
        for dest, entry in dests.items():
            if only_destination and dest.lower() != only_destination.lower():
                continue
            # Skip rule-based entries — own-country is trivially visa-free, no need
            if str(entry.get("model", "")).startswith("rule:"):
                continue
            if not is_stale(entry, ttl_days):
                continue
            pending.append((passport, dest))
    return pending


def run_once(args) -> int:
    cfg = load_config()
    input_path = Path(args.input) if args.input else DEFAULT_INPUT
    report_path = Path(args.report) if args.report else DEFAULT_REPORT
    payload = load_json(input_path)

    pending = plan_pairs(
        payload,
        ttl_days=args.ttl_days,
        only_passport=args.only_passport,
        only_destination=args.only_destination,
    )
    if args.limit:
        pending = pending[: args.limit]

    print(f"[plan] {len(pending)} entries to validate (model={args.model}, parallel={args.parallel})")
    if args.dry_run:
        for p, d in pending:
            print(f"  - {p} → {d}")
        return 0
    if not pending:
        print("[done] nothing to validate.")
        return 0

    results_meta: dict[str, dict[str, dict]] = {}  # passport -> dest -> meta
    issues: list[dict] = []
    count = 0

    def task(p: str, d: str):
        existing = payload["data"][p][d]
        return p, d, validate_one(existing, args.model)

    if args.parallel <= 1:
        for idx, (p, d) in enumerate(pending, start=1):
            _, _, meta = task(p, d)
            count += _apply(payload, issues, p, d, meta, idx, len(pending), input_path, report_path)
    else:
        print(f"[parallel] running {args.parallel} workers")
        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = {pool.submit(task, p, d): (p, d) for (p, d) in pending}
            for idx, fut in enumerate(as_completed(futures), start=1):
                try:
                    p, d, meta = fut.result()
                except Exception as e:
                    p, d = futures[fut]
                    meta = {
                        "validated_by": f"claude-code:{args.model}",
                        "validated_at": datetime.now(timezone.utc).date().isoformat(),
                        "validation_result": "error",
                        "validation_notes": f"future raised: {e!s}"[:240],
                    }
                count += _apply(payload, issues, p, d, meta, idx, len(pending), input_path, report_path)

    # Final write
    payload.setdefault("meta", {})["last_validation"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload["meta"]["last_validation_model"] = args.model
    save_json(input_path, payload)
    save_json(report_path, {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validator_model": args.model,
        "total_validated": count,
        "issues": issues,
    })

    # Summary
    stats = {}
    for p, dests in (payload.get("data") or {}).items():
        for d, e in dests.items():
            r = e.get("validation_result")
            if r:
                stats[r] = stats.get(r, 0) + 1
    print(f"[done] validated {count} entries. Totals on file: {stats}")
    if issues:
        print(f"[issues] {len(issues)} disagreements written to {report_path}")

    if args.sync:
        site_path = ROOT / cfg["site_sync_path"]
        site_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(input_path, site_path)
        print(f"[sync] copied → {site_path}")
    return 0


def _apply(
    payload: dict,
    issues: list,
    p: str,
    d: str,
    meta: dict,
    idx: int,
    total: int,
    input_path: Path,
    report_path: Path,
) -> int:
    """Merge meta into the entry, emit log line, collect issue, persist periodically."""
    entry = payload["data"][p][d]
    # Keep pre-existing fields — validation metadata coexists with verification metadata
    entry.update(meta)
    res = meta.get("validation_result")
    icon = {"agree": "✓", "differ-status": "⚠", "differ-days": "·", "error": "✗"}.get(res, "?")
    note = meta.get("validation_notes", "")
    print(f"  [{idx}/{total}] {icon} {p} → {d}: {res}  {note}")
    if res in ("differ-status", "differ-days"):
        issues.append({
            "passport": p,
            "destination": d,
            "original_status": entry.get("status"),
            "original_days": entry.get("days"),
            "original_source": entry.get("source"),
            "validator_status": meta.get("validator_status"),
            "validator_days": meta.get("validator_days"),
            "validator_source": meta.get("validator_source"),
            "notes": note,
        })

    # Persist every 10 entries so Ctrl-C loses little
    if idx % 10 == 0:
        save_json(input_path, payload)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Second-opinion pass over verified-visas.json.")
    ap.add_argument("--model", default="sonnet", help="Validator model (default: sonnet). Try opus for edge cases.")
    ap.add_argument("--ttl-days", type=int, default=30, help="Re-validate entries whose validation is older than N days (default: 30). Entries never validated count as stale.")
    ap.add_argument("--only-passport", help="Validate only this passport")
    ap.add_argument("--only-destination", help="Validate only this destination")
    ap.add_argument("--limit", type=int, help="Cap entries per run")
    ap.add_argument("--parallel", type=int, default=1, metavar="N", help="Concurrent workers (default 1).")
    ap.add_argument("--input", help="Override input file (default output/verified-visas.json)")
    ap.add_argument("--report", help="Override disagreement report path (default output/validation-issues.json)")
    ap.add_argument("--sync", action="store_true", help="After the run, copy input file into the Astro public/data dir")
    ap.add_argument("--dry-run", action="store_true", help="List pending pairs without calling the API")
    args = ap.parse_args()
    return run_once(args)


if __name__ == "__main__":
    sys.exit(main())
