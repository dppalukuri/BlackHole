"""
Re-apply the TRUSTED_PATTERNS / _classify_confidence logic to an existing
verified-visas.json file in place. Useful after the trust pattern list expands
to promote previously-downgraded entries without hitting the API again.

Usage:
    python reclassify.py                      # default path (output/verified-visas.json)
    python reclassify.py path/to/file.json    # custom path
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

# Re-use the gating logic + pattern list from verifier.py
from verifier import _classify_confidence

DEFAULT_PATH = Path(__file__).resolve().parent / "output" / "verified-visas.json"


def reclassify(path: Path) -> None:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    changed = 0
    per_conf_before = {}
    per_conf_after = {}
    for passport, destinations in (payload.get("data") or {}).items():
        for dest, entry in destinations.items():
            before = entry.get("confidence")
            per_conf_before[before] = per_conf_before.get(before, 0) + 1
            # Rule-based entries (own-country) are valid without a URL — skip the URL gate.
            if str(entry.get("model", "")).startswith("rule:"):
                per_conf_after[before] = per_conf_after.get(before, 0) + 1
                continue
            source = entry.get("source")
            model_conf = entry.get("confidence", "")
            # If the model originally called it "low" but the URL is gov, the
            # gate would have returned "low". We re-gate against the updated
            # TRUSTED_PATTERNS. The model's self-declared confidence lives on
            # the `notes` / original entry, but we stored only the gated value.
            # Assume the model's original call was >= the gated value and
            # re-apply the gate. For "low" entries with a gov-trusted domain,
            # this promotes them to "medium" (conservative default).
            new_conf = _classify_confidence(source, model_conf)
            if new_conf == "low":
                # model_conf was already gated-down. Try treating as "high" to
                # see if the source is now trusted under the new patterns.
                promoted = _classify_confidence(source, "high")
                if promoted in ("high", "medium"):
                    # Didn't match under old patterns, does under new. Promote
                    # to "medium" (one notch down — we never asked the model
                    # for its raw confidence on the new pattern).
                    new_conf = "medium"
            per_conf_after[new_conf] = per_conf_after.get(new_conf, 0) + 1
            if new_conf != before:
                entry["confidence"] = new_conf
                # Also: if we previously set status=unknown because confidence
                # was unknown, re-sync. But only for promote, never demote.
                if before == "unknown" and new_conf != "unknown":
                    # (rare path — would only fire if status was unknown AND
                    # we now trust the source; leaves original status alone)
                    pass
                changed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, sort_keys=True)

    print(f"Re-classified {changed} entries in {path}")
    print(f"  before: {per_conf_before}")
    print(f"  after:  {per_conf_after}")


if __name__ == "__main__":
    p = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    reclassify(p)
