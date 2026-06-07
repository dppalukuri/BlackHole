"""
snapshot.py — freeze a copy of verified-visas.json for diff comparison.

Usage:
    python snapshot.py                # writes snapshots/YYYY-MM-DD.json
    python snapshot.py --label v3-bulk  # writes snapshots/YYYY-MM-DD_v3-bulk.json

Snapshots are committed to git. They power the diff tracker (diff.py) which
generates Travel Radar "changes" pages on the wanderwise site.
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "output" / "verified-visas.json"
SNAP_DIR = ROOT / "snapshots"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", help="Optional suffix appended to the filename")
    ap.add_argument("--source", help="Override source path", default=str(SOURCE))
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        print(f"[error] source not found: {src}")
        return 1

    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()
    suffix = f"_{args.label}" if args.label else ""
    dest = SNAP_DIR / f"{today}{suffix}.json"

    payload = json.loads(src.read_text(encoding="utf-8"))
    # Lightweight: drop the meta.last_run noise so unrelated re-runs don't
    # dirty diffs. Keep the data block intact.
    payload.setdefault("meta", {})
    payload["meta"]["snapshot_date"] = today
    payload["meta"].pop("last_run", None)
    payload["meta"].pop("added_this_run", None)
    payload["meta"].pop("destinations_run", None)
    payload["meta"].pop("cleanup_at", None)

    dest.write_text(
        json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    total = sum(len(v) for v in payload.get("data", {}).values())
    print(f"[snapshot] wrote {dest.name}  ({total} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
