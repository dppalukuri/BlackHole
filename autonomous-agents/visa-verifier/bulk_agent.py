"""
bulk_agent.py — destination-axis verifier orchestrator.

For each destination, makes ONE Claude call to fetch the official visa policy
page and extract statuses for all configured passports at once. ~50-100x
cheaper and faster than the per-pair agent.py.

Output schema is identical to agent.py — same verified-visas.json. The two
agents can co-exist; bulk_agent.py is the faster path for big sweeps.

Usage:
    python bulk_agent.py                              # all pending destinations
    python bulk_agent.py --only-destination Japan     # one destination
    python bulk_agent.py --limit 5                    # cap destinations
    python bulk_agent.py --parallel 3 --sync          # 3 workers + site sync
    python bulk_agent.py --chunk 50                   # max passports per call
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
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)  # type: ignore[attr-defined]
except Exception:
    pass

from verifier import VerifiedEntry, ClaudeCLIError
from bulk_verifier import verify_destination_bulk

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
DEFAULT_OUTPUT = ROOT / "output" / "verified-visas.json"

# Save & site-sync cadence (in destinations). One destination = up to ~199 pairs,
# so save every destination by default to keep the website near-live.
SAVE_EVERY = 1


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
        json.dump(payload, f, indent=1, ensure_ascii=False, sort_keys=True)
    tmp.replace(path)


def is_stale(entry: dict, ttl_days: int) -> bool:
    try:
        verified = datetime.fromisoformat(entry["verified_at"]).date()
    except Exception:
        return True
    return (datetime.now(timezone.utc).date() - verified).days > ttl_days


def plan_destination(
    destination: str,
    passports: list[str],
    existing: dict,
    ttl_days: int,
) -> list[str]:
    """Return the subset of passports for this destination still needing verification."""
    pending = []
    for p in passports:
        entry = existing.get("data", {}).get(p, {}).get(destination)
        if entry and not is_stale(entry, ttl_days):
            continue
        pending.append(p)
    return pending


def merge_destination_results(payload: dict, results: dict[str, VerifiedEntry]) -> int:
    data = payload.setdefault("data", {})
    n = 0
    for passport, entry in results.items():
        data.setdefault(passport, {})[entry.destination] = entry.to_dict()
        n += 1
    return n


def update_meta(payload: dict, model: str, dest_done: int) -> None:
    total = sum(len(v) for v in payload.get("data", {}).values())
    payload["meta"] = {
        "last_run": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_entries": total,
        "model_default": model,
        "generator": "autonomous-agents/visa-verifier v0.2-bulk",
        "destinations_run": dest_done,
    }


def sync_to_site(output_path: Path, site_path: Path) -> None:
    site_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_path, site_path)
    print(f"[sync] copied -> {site_path}")


def _chunk(lst: list, n: int) -> list[list]:
    if n <= 0 or n >= len(lst):
        return [lst]
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def process_destination(
    destination: str,
    pending_passports: list[str],
    model: str,
    chunk_size: int,
    timeout_sec: int,
) -> tuple[str, dict[str, VerifiedEntry], Optional[Exception]]:
    """Verify all pending passports for one destination, chunked if needed."""
    if not pending_passports:
        return destination, {}, None
    out: dict[str, VerifiedEntry] = {}
    try:
        for chunk in _chunk(pending_passports, chunk_size):
            results = verify_destination_bulk(
                destination, chunk, model=model, timeout_sec=timeout_sec
            )
            out.update(results)
    except Exception as e:
        return destination, out, e
    return destination, out, None


QUOTA_MARKERS = ("hit your limit", "429", "rate_limit", "usage limit", "quota")


def _looks_like_quota(exc: Optional[Exception]) -> bool:
    if exc is None:
        return False
    msg = str(exc).lower()
    return any(m in msg for m in QUOTA_MARKERS)


def run_once(args) -> int:
    cfg = load_config()
    model = os.environ.get("VISA_VERIFIER_MODEL", args.model or "haiku")
    ttl_days = int(os.environ.get("VISA_VERIFIER_TTL_DAYS", args.ttl_days))
    chunk_size = args.chunk
    timeout_sec = args.timeout

    output_path = Path(args.output) if args.output else DEFAULT_OUTPUT
    existing = load_existing(output_path)

    passports = cfg["passports"]
    destinations = cfg["destinations"]
    if args.only_destination:
        destinations = [d for d in destinations if d.lower() == args.only_destination.lower()]

    plan = []
    for dest in destinations:
        pending = plan_destination(dest, passports, existing, ttl_days)
        if pending:
            plan.append((dest, pending))

    # Sort biggest first so we make progress fast even if quota dies early
    plan.sort(key=lambda kv: -len(kv[1]))

    if args.limit:
        plan = plan[: args.limit]

    total_pending_pairs = sum(len(p) for _, p in plan)
    print(
        f"[plan] {len(plan)} destinations covering {total_pending_pairs} pending pairs "
        f"(model={model}, ttl={ttl_days}d, chunk={chunk_size}, parallel={args.parallel})"
    )

    if args.dry_run:
        for d, p in plan[:25]:
            print(f"  - {d}: {len(p)} passports")
        if len(plan) > 25:
            print(f"  ... and {len(plan) - 25} more destinations")
        return 0

    if not plan:
        print("[done] nothing to verify.")
        if args.sync:
            sync_to_site(output_path, ROOT / cfg["site_sync_path"])
        return 0

    parallel = max(1, int(args.parallel or 1))
    site_path = (ROOT / cfg["site_sync_path"]) if args.sync else None
    QUOTA_BAIL_AFTER = 5

    dest_done = 0
    pairs_done = 0
    quota_errors = 0
    started_at = time.time()

    def _report(d: str, results: dict[str, VerifiedEntry], err: Optional[Exception]) -> None:
        nonlocal pairs_done, dest_done, quota_errors
        idx = dest_done + 1
        if err and not results:
            print(f"  [{idx}/{len(plan)}] {d}: ERROR {err!s}")
            if _looks_like_quota(err):
                quota_errors += 1
            return
        if err and results:
            # Partial: some chunks succeeded, one failed. Still merge what we got
            # but surface the error so we don't silently lose coverage.
            print(f"  [{idx}/{len(plan)}] {d}: PARTIAL — merging {len(results)} entries, then ERROR {err!s}")
        n = merge_destination_results(existing, results)
        pairs_done += n
        dest_done += 1
        sample = next(iter(results.values()), None)
        src_label = (sample.source or "-") if sample else "-"
        conf_label = sample.confidence if sample else "-"
        # Count breakdown for visibility
        hi = sum(1 for e in results.values() if e.confidence == "high")
        lo = sum(1 for e in results.values() if e.confidence == "low")
        un = sum(1 for e in results.values() if e.confidence == "unknown")
        rate = pairs_done / max(1, time.time() - started_at) * 60
        print(
            f"  [{idx}/{len(plan)}] {d}: +{n} entries (hi={hi} lo={lo} un={un})"
            f" {rate:.0f}/min  src={src_label[:80]}"
        )
        update_meta(existing, model, dest_done)
        if dest_done % SAVE_EVERY == 0:
            save(output_path, existing)
            if site_path is not None:
                sync_to_site(output_path, site_path)
        # reset quota counter on success
        quota_errors = 0

    if parallel <= 1:
        for dest, pending in plan:
            d, results, err = process_destination(
                dest, pending, model, chunk_size, timeout_sec
            )
            _report(d, results, err)
            if quota_errors >= QUOTA_BAIL_AFTER:
                print(f"  [bail] {quota_errors} consecutive quota errors — stopping")
                break
    else:
        print(f"[parallel] {parallel} destination workers")
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = {
                pool.submit(
                    process_destination, dest, pending, model, chunk_size, timeout_sec
                ): dest
                for (dest, pending) in plan
            }
            bailed = False
            for fut in as_completed(futures):
                if bailed:
                    fut.cancel()
                    continue
                try:
                    d, results, err = fut.result()
                except Exception as e:
                    d = futures[fut]
                    results = {}
                    err = e
                _report(d, results, err)
                if quota_errors >= QUOTA_BAIL_AFTER:
                    print(
                        f"  [bail] {quota_errors} consecutive quota errors — cancelling remaining workers"
                    )
                    bailed = True
                    for f in futures:
                        f.cancel()

    save(output_path, existing)
    if site_path is not None:
        sync_to_site(output_path, site_path)

    elapsed = time.time() - started_at
    print(
        f"[done] {dest_done}/{len(plan)} destinations, {pairs_done} pairs in "
        f"{elapsed/60:.1f} min  ->  {output_path}"
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Bulk verifier: one Claude call per destination, all passports at once."
    )
    ap.add_argument("--model", help="Claude model (default: haiku)")
    ap.add_argument("--ttl-days", type=int, default=30)
    ap.add_argument("--only-destination", help="Verify only this destination")
    ap.add_argument("--limit", type=int, help="Cap destinations per run")
    ap.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Parallel destination workers (try 2-3; higher risks rate-limit)",
    )
    ap.add_argument(
        "--chunk",
        type=int,
        default=60,
        help="Max passports per Claude call (default 60 ≈ 1 chunk for ~half the matrix)",
    )
    ap.add_argument(
        "--timeout",
        type=int,
        default=480,
        help="Per-call timeout (sec). Bulk calls take longer than per-pair.",
    )
    ap.add_argument("--output", help="Override output path")
    ap.add_argument(
        "--sync",
        action="store_true",
        help="Copy output to the wanderwise public/data dir after each save",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    return run_once(args)


if __name__ == "__main__":
    sys.exit(main())
