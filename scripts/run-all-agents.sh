#!/bin/bash
# Run all 4 job-hunt agents + auto-sync to GitHub/Vercel.
# Use this when you want a "full sweep" without waiting for the cron.

set -e

AGENTS=(job-scout career-scraper aggregator-poller networking-sniper)
LOG_DIR="$HOME/.mavis/job-hunt/logs"
mkdir -p "$LOG_DIR"
TS=$(date +%Y%m%d_%H%M%S)

echo "=== Launching 4 job-hunt agents in parallel at $(date) ==="
echo

for agent in "${AGENTS[@]}"; do
  LOG_FILE="$LOG_DIR/${agent}_${TS}.log"
  echo "  → $agent (log: $LOG_FILE)"
  mavis session new "$agent" \
    --prompt "Run a fresh scrape/poll and append any new jobs to ~/.mavis/job-hunt/data.json. Be concise — return a 2-line summary at the end." \
    > "$LOG_FILE" 2>&1 &
done

echo
echo "All 4 agents launched in background. Waiting for completion..."
wait

echo
echo "=== Done at $(date) ==="
echo
echo "=== Last 5 lines of each agent log ==="
for agent in "${AGENTS[@]}"; do
  LOG_FILE="$LOG_DIR/${agent}_${TS}.log"
  if [ -f "$LOG_FILE" ]; then
    echo "--- $agent ---"
    tail -5 "$LOG_FILE"
    echo
  fi
done

echo "Auto-syncing to GitHub/Vercel..."
bash ~/.mavis/job-hunt/scripts/post-scrape-sync.sh