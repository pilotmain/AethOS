#!/usr/bin/env bash
# Loop kernel soak batches every N minutes until gates pass or max batches reached.
#
# Staging acceleration (optional — compresses 7 calendar soak days):
#   export KERNEL_SOAK_DEV_ACCELERATE=true
#
# Usage:
#   ./scripts/kernel_soak_loop.sh              # every 12 min, until ready
#   KERNEL_SOAK_INTERVAL_MIN=15 ./scripts/kernel_soak_loop.sh
#   KERNEL_SOAK_MAX_BATCHES=7 ./scripts/kernel_soak_loop.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INTERVAL_MIN="${KERNEL_SOAK_INTERVAL_MIN:-12}"
MAX_BATCHES="${KERNEL_SOAK_MAX_BATCHES:-0}"
INTERVAL_SEC=$((INTERVAL_MIN * 60))
LOG_DIR="${ROOT}/data/operational_kernel_reality"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/soak_loop.log"

log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"
}

log "Starting kernel soak loop (interval=${INTERVAL_MIN}m max_batches=${MAX_BATCHES:-unlimited})"
log "KERNEL_SOAK_DEV_ACCELERATE=${KERNEL_SOAK_DEV_ACCELERATE:-false}"

BATCH=0
while true; do
  BATCH=$((BATCH + 1))
  BATCH_ID="$(date -u +%Y%m%d-%H%M%S)-b${BATCH}"
  log "Batch ${BATCH} id=${BATCH_ID}"

  export KERNEL_SOAK_SAVE_DAILY=true
  export KERNEL_SOAK_DAY_INDEX="$BATCH"

  if ! OUT="$(./scripts/kernel_soak_batch.sh "$BATCH_ID" 2>&1)"; then
    log "Batch failed (continuing): ${OUT:0:200}"
  else
    log "Batch complete"
  fi

  if python -m aethos_core.cli.kernel_soak_runner --check-gates --json >>"$LOG_FILE" 2>&1; then
    log "Gates ready — stopping loop"
    python -m aethos_core.cli.kernel_soak_runner --check-gates --json | tee -a "$LOG_FILE"
    exit 0
  fi

  if [[ "$MAX_BATCHES" -gt 0 && "$BATCH" -ge "$MAX_BATCHES" ]]; then
    log "Reached KERNEL_SOAK_MAX_BATCHES=${MAX_BATCHES} — stopping"
    python -m aethos_core.cli.kernel_reality_report --json | jq '{total_turns, acceptance, soak: .soak_progress, provider_proof}' | tee -a "$LOG_FILE"
    exit 0
  fi

  log "Sleeping ${INTERVAL_MIN} minutes…"
  sleep "$INTERVAL_SEC"
done
