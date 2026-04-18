"""
visa-verifier agent

Runs in the background (one-shot, cron, or --watch loop) and produces a
verified-visas.json keyed by passport → destination. Each entry carries a
domain-gated confidence score + gov-sourced URL (or is marked "unknown" and
skipped by the site).

Usage:
    python agent.py                          # run once, all configured pairs
    python agent.py --only-passport India    # one passport, all destinations
    python agent.py --only-destination Japan # one destination, all passports
    python agent.py --sync                   # run + copy into the Astro public/data dir
    python agent.py --watch 3600             # run, sleep 1h, repeat
    python agent.py --dry-run                # list pending pairs, don't call the API

Requires ANTHROPIC_API_KEY in environment (or .env).
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, Optional

# Make print() work on Windows cp1252 consoles with Unicode (arrows, symbols)
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

from verifier import VerifiedEntry, verify_pair, ClaudeCLIError

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
DEFAULT_OUTPUT = ROOT / "output" / "verified-visas.json"


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing(path: Path) -> dict:
    if not path.exists():
        return {"meta": {}, "data": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)
    tmp.replace(path)


def is_stale(entry: dict, ttl_days: int) -> bool:
    try:
        verified = datetime.fromisoformat(entry["verified_at"]).date()
    except Exception:
        return True
    return (datetime.now(timezone.utc).date() - verified).days > ttl_days


def plan_pairs(
    cfg: dict,
    existing: dict,
    ttl_days: int,
    only_passport: Optional[str] = None,
    only_destination: Optional[str] = None,
) -> list[tuple[str, str]]:
    passports = [cfg["passports"]] if False else cfg["passports"]
    destinations = cfg["destinations"]
    if only_passport:
        passports = [p for p in passports if p.lower() == only_passport.lower()]
    if only_destination:
        destinations = [d for d in destinations if d.lower() == only_destination.lower()]

    pending: list[tuple[str, str]] = []
    for p in passports:
        for d in destinations:
            entry = existing.get("data", {}).get(p, {}).get(d)
            if entry and not is_stale(entry, ttl_days):
                continue
            pending.append((p, d))
    return pending


def merge_entry(payload: dict, entry: VerifiedEntry) -> None:
    payload.setdefault("data", {}).setdefault(entry.passport, {})[entry.destination] = entry.to_dict()


def update_meta(payload: dict, total: int, added: int, model: str) -> None:
    payload["meta"] = {
        "last_run": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_entries": total,
        "added_this_run": added,
        "model_default": model,
        "generator": "autonomous-agents/visa-verifier v0.1",
    }


def sync_to_site(output_path: Path, site_path: Path) -> None:
    site_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_path, site_path)
    print(f"[sync] copied → {site_path}")


def run_once(args) -> int:
    cfg = load_config()
    model = os.environ.get("VISA_VERIFIER_MODEL", args.model or "haiku")
    ttl_days = int(os.environ.get("VISA_VERIFIER_TTL_DAYS", args.ttl_days))

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    existing = load_existing(output_path)

    pending = plan_pairs(
        cfg,
        existing,
        ttl_days=ttl_days,
        only_passport=args.only_passport,
        only_destination=args.only_destination,
    )

    if args.limit:
        pending = pending[: args.limit]

    print(f"[plan] {len(pending)} pairs to verify (model={model}, ttl={ttl_days}d)")
    if args.dry_run:
        for p, d in pending:
            print(f"  - {p} → {d}")
        return 0

    if not pending:
        print("[done] nothing to verify.")
        if args.sync:
            sync_to_site(output_path, ROOT / cfg["site_sync_path"])
        return 0

    added = 0
    for idx, (p, d) in enumerate(pending, start=1):
        try:
            entry = verify_pair(p, d, model=model)
        except ClaudeCLIError as e:
            msg = str(e)
            if "rate" in msg.lower() or "429" in msg:
                print(f"  [{idx}/{len(pending)}] {p} → {d}: rate-limited; sleeping 30s and retrying")
                time.sleep(30)
                try:
                    entry = verify_pair(p, d, model=model)
                except Exception as e2:
                    print(f"  [{idx}/{len(pending)}] {p} → {d}: RETRY-FAILED {e2!s}")
                    continue
            else:
                print(f"  [{idx}/{len(pending)}] {p} → {d}: CLI ERROR {msg}")
                continue
        except Exception as e:
            print(f"  [{idx}/{len(pending)}] {p} → {d}: ERROR {e!s}")
            continue

        merge_entry(existing, entry)
        added += 1
        label = entry.status.upper()
        suffix = "" if entry.confidence == "unknown" else f"  src={entry.source or '-'}"
        print(f"  [{idx}/{len(pending)}] {p} → {d}: {label} (conf={entry.confidence}){suffix}")

        # Persist incrementally so an interrupted run isn't lost
        total = sum(len(v) for v in existing.get("data", {}).values())
        update_meta(existing, total, added, model)
        save(output_path, existing)

    print(f"[done] wrote {added} entries → {output_path}")
    if args.sync:
        sync_to_site(output_path, ROOT / cfg["site_sync_path"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify visa requirements via Claude + web_search.")
    ap.add_argument("--model", help="Claude model id (default: env VISA_VERIFIER_MODEL or claude-haiku-4-5)")
    ap.add_argument("--ttl-days", type=int, default=30, help="Re-verify entries older than this many days (default 30)")
    ap.add_argument("--only-passport", help="Verify only this passport (e.g., 'India')")
    ap.add_argument("--only-destination", help="Verify only this destination (e.g., 'Japan')")
    ap.add_argument("--limit", type=int, help="Cap pairs per run (useful for test/budget)")
    ap.add_argument("--output", help="Override output file path")
    ap.add_argument("--sync", action="store_true", help="After run, copy output into the Astro public/data dir")
    ap.add_argument("--dry-run", action="store_true", help="List pending pairs without calling the API")
    ap.add_argument("--watch", type=int, metavar="SECONDS", help="Run continuously, sleeping this many seconds between runs")
    args = ap.parse_args()

    if args.watch:
        while True:
            rc = run_once(args)
            if rc != 0:
                return rc
            print(f"[watch] sleeping {args.watch}s …")
            time.sleep(args.watch)
    return run_once(args)


if __name__ == "__main__":
    sys.exit(main())
