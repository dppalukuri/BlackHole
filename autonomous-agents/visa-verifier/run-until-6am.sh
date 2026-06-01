#!/usr/bin/env bash
# Continuous burst loop — runs python agent.py back-to-back until 06:00 local time.
# Each burst auto-syncs into data-products/wanderwise/public/data/.
# Quota bails are handled by the agent's own circuit-breaker; we just retry.

set -u
LOG="output/loop-$(date +%Y%m%d-%H%M%S).log"
echo "[loop] starting at $(date)" | tee -a "$LOG"

burst_count=0
total_added=0

while :; do
  HOUR=$(date +%H)
  # Stop at 6 AM
  if [ "$HOUR" = "06" ] || [ "$HOUR" = "07" ]; then
    echo "[loop] reached 06:00 cutoff — exiting" | tee -a "$LOG"
    break
  fi

  burst_count=$((burst_count + 1))
  echo "[burst $burst_count] starting at $(date) (hour=$HOUR)" | tee -a "$LOG"

  # Capture before/after counts to track progress
  BEFORE=$(python -c "import json; print(json.load(open('output/verified-visas.json',encoding='utf-8'))['meta']['total_entries'])" 2>/dev/null || echo 0)

  python agent.py --limit 150 --parallel 4 --sync >> "$LOG" 2>&1

  AFTER=$(python -c "import json; print(json.load(open('output/verified-visas.json',encoding='utf-8'))['meta']['total_entries'])" 2>/dev/null || echo "$BEFORE")
  ADDED=$((AFTER - BEFORE))
  total_added=$((total_added + ADDED))
  echo "[burst $burst_count done] added=$ADDED  total_now=$AFTER  cumulative_session=$total_added" | tee -a "$LOG"

  # Brief pause between bursts so we don't hammer if quota is bailing immediately
  sleep 30
done

echo "[loop] finished at $(date) — bursts=$burst_count, total_added=$total_added" | tee -a "$LOG"
