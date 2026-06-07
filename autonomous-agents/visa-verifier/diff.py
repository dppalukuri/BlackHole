"""
diff.py — diff two verified-visas snapshots into a structured change set.

Generates Travel Radar "changes" content. Output JSON is consumed by the
wanderwise Astro build at src/data/visa-changes/<slug>.json to render a
public-facing change page at /travel-radar/changes/<slug>/.

Usage:
    python diff.py                            # compare two most recent snapshots
    python diff.py 2026-06-01 2026-06-08      # compare specific dates
    python diff.py --site                     # also write to wanderwise src/data/visa-changes/

Output: output/changes-<from>--<to>.json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
SNAP_DIR = ROOT / "snapshots"
OUT_DIR = ROOT / "output"
SITE_DIR = ROOT.parent.parent / "data-products" / "wanderwise" / "src" / "data" / "visa-changes"

STATUS_LABEL = {
    "vf": "visa-free",
    "voa": "visa on arrival",
    "ev": "e-visa",
    "eta": "ETA",
    "vr": "visa required",
    "unknown": "unknown",
}


def list_snapshots() -> list[Path]:
    if not SNAP_DIR.exists():
        return []
    files = [p for p in SNAP_DIR.glob("*.json")]
    files.sort()
    return files


def find_snapshot(date_or_filename: str) -> Optional[Path]:
    """Locate a snapshot by date (YYYY-MM-DD) or filename."""
    candidates = list_snapshots()
    if not candidates:
        return None
    # exact-filename match
    direct = SNAP_DIR / date_or_filename
    if direct.exists():
        return direct
    # by date prefix
    for c in candidates:
        if c.stem.startswith(date_or_filename):
            return c
    return None


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def diff_payloads(a: dict, b: dict) -> dict:
    """Diff two verified-visa payloads. Returns a structured change set:

    {
      "from": "<source snapshot label>",
      "to":   "<target snapshot label>",
      "added":   [...],   # entries in b not in a
      "removed": [...],   # entries in a not in b
      "status_changed": [...],  # entries where status differs
      "days_changed":   [...],  # entries where days differ (status same)
      "source_changed": [...],  # entries where source URL changed (status & days same)
    }
    """
    a_data = a.get("data", {})
    b_data = b.get("data", {})

    a_keys = {(p, d) for p, dests in a_data.items() for d in dests}
    b_keys = {(p, d) for p, dests in b_data.items() for d in dests}

    added_keys = b_keys - a_keys
    removed_keys = a_keys - b_keys
    common_keys = a_keys & b_keys

    def get(payload: dict, p: str, d: str) -> dict:
        return payload["data"][p][d]

    added = [get(b, p, d) for (p, d) in sorted(added_keys)]
    removed = [get(a, p, d) for (p, d) in sorted(removed_keys)]

    status_changed = []
    days_changed = []
    source_changed = []
    for (p, d) in sorted(common_keys):
        ae, be = get(a, p, d), get(b, p, d)
        if ae.get("status") != be.get("status"):
            status_changed.append({
                "passport": p,
                "destination": d,
                "from": {"status": ae.get("status"), "days": ae.get("days"), "source": ae.get("source"), "notes": ae.get("notes")},
                "to":   {"status": be.get("status"), "days": be.get("days"), "source": be.get("source"), "notes": be.get("notes")},
                "verified_at": be.get("verified_at"),
            })
        elif ae.get("days") != be.get("days"):
            days_changed.append({
                "passport": p,
                "destination": d,
                "from_days": ae.get("days"),
                "to_days":   be.get("days"),
                "status":    be.get("status"),
                "source":    be.get("source"),
                "verified_at": be.get("verified_at"),
            })
        elif ae.get("source") != be.get("source"):
            source_changed.append({
                "passport": p,
                "destination": d,
                "from_source": ae.get("source"),
                "to_source":   be.get("source"),
                "status":      be.get("status"),
                "verified_at": be.get("verified_at"),
            })

    return {
        "added": added,
        "removed": removed,
        "status_changed": status_changed,
        "days_changed": days_changed,
        "source_changed": source_changed,
    }


def summarize(diff: dict) -> dict:
    return {
        "added_count": len(diff["added"]),
        "removed_count": len(diff["removed"]),
        "status_changed_count": len(diff["status_changed"]),
        "days_changed_count": len(diff["days_changed"]),
        "source_changed_count": len(diff["source_changed"]),
        "total_changes": (
            len(diff["added"]) + len(diff["removed"])
            + len(diff["status_changed"]) + len(diff["days_changed"])
            + len(diff["source_changed"])
        ),
    }


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("from_snap", nargs="?", help="Source snapshot (YYYY-MM-DD or filename)")
    ap.add_argument("to_snap", nargs="?", help="Target snapshot (YYYY-MM-DD or filename)")
    ap.add_argument("--site", action="store_true", help="Also write to wanderwise src/data/visa-changes/")
    args = ap.parse_args()

    snaps = list_snapshots()
    if len(snaps) < 2:
        print(f"[diff] need 2 snapshots; found {len(snaps)} in {SNAP_DIR}")
        print("       run `python snapshot.py` once today and again later")
        return 1

    if args.from_snap and args.to_snap:
        a_path = find_snapshot(args.from_snap)
        b_path = find_snapshot(args.to_snap)
    else:
        a_path = snaps[-2]
        b_path = snaps[-1]

    if not a_path or not b_path:
        print(f"[diff] could not resolve snapshots: from={a_path} to={b_path}")
        return 1

    a = load(a_path)
    b = load(b_path)
    raw = diff_payloads(a, b)
    summary = summarize(raw)

    payload = {
        "from_snapshot": a_path.stem,
        "to_snapshot": b_path.stem,
        "from_date": a.get("meta", {}).get("snapshot_date"),
        "to_date": b.get("meta", {}).get("snapshot_date"),
        "summary": summary,
        "changes": raw,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_name = f"changes-{a_path.stem}--{b_path.stem}.json"
    out_path = OUT_DIR / out_name
    out_path.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    print(f"[diff] {a_path.stem} -> {b_path.stem}")
    for k, v in summary.items():
        print(f"  {k:25s} {v}")
    print(f"[diff] wrote {out_path}")

    if args.site:
        SITE_DIR.mkdir(parents=True, exist_ok=True)
        slug = f"{b_path.stem}-vs-{a_path.stem}"
        slug = slugify(slug)
        site_path = SITE_DIR / f"{slug}.json"
        site_path.write_text(
            json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        print(f"[diff] also wrote {site_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
