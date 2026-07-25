#!/usr/bin/env bash
# Run one live kernel soak batch (no loop). Requires credentials + kernel flags in .env.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p "$ROOT/data/operational_kernel_reality"

BATCH_ID="${1:-$(date -u +%Y%m%d-%H%M%S)}"
SAVE_DAILY="${KERNEL_SOAK_SAVE_DAILY:-false}"
SOAK_DAY="${KERNEL_SOAK_DAY_INDEX:-}"

ARGS=(--batch-id "$BATCH_ID")
if [[ "$SAVE_DAILY" == "true" ]]; then
  ARGS+=(--save-daily)
fi
if [[ -n "$SOAK_DAY" ]]; then
  ARGS+=(--soak-day-index "$SOAK_DAY")
fi

python -m aethos_core.cli.kernel_soak_runner "${ARGS[@]}" --json | tee "data/operational_kernel_reality/soak_batch_${BATCH_ID}.json"
