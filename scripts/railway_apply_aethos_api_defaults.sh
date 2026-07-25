#!/usr/bin/env bash
# Apply non-secret Railway defaults for aethos-api from deploy/railway/aethos-api.defaults.env
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ROOT}/deploy/railway/aethos-api.defaults.env"
SERVICE="${RAILWAY_SERVICE:-aethos-api}"

if ! command -v railway >/dev/null 2>&1; then
  echo "railway CLI not found" >&2
  exit 1
fi

pairs=()
while IFS= read -r line || [[ -n "$line" ]]; do
  line="${line%%#*}"
  line="$(echo "$line" | xargs)"
  [[ -z "$line" ]] && continue
  pairs+=("$line")
done < "$ENV_FILE"

echo "Setting ${#pairs[@]} variables on service ${SERVICE}..."
railway variable set --service "$SERVICE" "${pairs[@]}"
echo "Done. Add secrets (ANTHROPIC_API_KEY, etc.) in Railway UI if not already set."
