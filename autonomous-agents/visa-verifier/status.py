"""
status.py — quick progress report for the hourly verifier job.

Usage:
    python status.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output" / "verified-visas.json"


def fmt_pct(n: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{100.0 * n / total:.1f}%"


def main() -> int:
    with open(ROOT / "config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    with open(OUTPUT, "r", encoding="utf-8") as f:
        payload = json.load(f)

    passports = cfg["passports"]
    destinations = cfg["destinations"]
    target = len(passports) * len(destinations)

    done = sum(len(v) for v in payload.get("data", {}).values())
    conf = {}
    vres = {}
    for p, dests in payload.get("data", {}).items():
        for d, e in dests.items():
            c = e.get("confidence", "unknown")
            conf[c] = conf.get(c, 0) + 1
            r = e.get("validation_result")
            if r:
                vres[r] = vres.get(r, 0) + 1

    print(f"target:     {target} pairs (config: {len(passports)} passports x {len(destinations)} destinations)")
    print(f"done:       {done} pairs ({fmt_pct(done, target)})")
    remaining = target - done
    print(f"remaining:  {remaining} pairs")
    if conf:
        print("confidence:")
        for k in ("high", "medium", "low", "unknown"):
            if k in conf:
                print(f"  {k:8s} {conf[k]}")
    if vres:
        print("sonnet-validation:")
        for k in ("agree", "differ-status", "differ-days", "error"):
            if k in vres:
                print(f"  {k:14s} {vres[k]}")
    meta = payload.get("meta", {})
    if meta:
        print(f"last verifier run:   {meta.get('last_run', '(none)')}")
        print(f"last validation:     {meta.get('last_validation', '(none)')}")

    # Estimate time to finish at recent pace: count entries verified in last 24 hours from meta? Skip.
    # Simple estimate based on --limit 150/hour default
    hours_at_150 = remaining / 150
    days_at_150 = hours_at_150 / 24
    print(f"\nat 150 pairs/hour: ~{hours_at_150:.0f} hours ({days_at_150:.1f} days of hourly runs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
