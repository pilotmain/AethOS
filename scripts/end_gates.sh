#!/usr/bin/env bash
# §End gates (corrected gate #1 — source only, no docs/*.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Gate 1: forbidden codenames (aethos_core + web source) ==="
gate1=$(grep -rinE "odysseus|openclaw|clawhub|exfoliate|paperclip|earendil|\bpi-coding\b|tongyi|llmfit|opencode" \
  aethos_core web --include='*.py' --include='*.ts' --include='*.tsx' 2>/dev/null | grep -v node_modules || true)
if [ -n "$gate1" ]; then
  echo "$gate1"
  exit 1
fi
echo "clean"

echo "=== Gate 2: legacy polish pipeline remnants ==="
gate2=$(grep -rinE "route_ownership|Blocked unauthorized route takeover|maybe_append_rest_nudge" \
  aethos_core --include='*.py' 2>/dev/null | grep -v node_modules || true)
if [ -n "$gate2" ]; then
  echo "$gate2"
  exit 1
fi
conv_count=$(ls aethos_core | { grep -E '^conversational_' || true; } | wc -l | tr -d ' ')
echo "conversational_* packages: ${conv_count}"

echo "=== Gate 3: ruff (syntax / undefined) ==="
ruff check --select=E9,F63,F7,F82 aethos_core aethos_sdk

echo "=== Gate 4: web ==="
(cd web && npm run typecheck && npm run test && npm run build)

echo "=== Gate 5: behavioral corpus ==="
bash scripts/run_behavioral_corpus.sh

echo "=== Gate 6: reliability ==="
USE_REAL_LLM=false ACTIVE_PROVIDER=none AUTH_ENABLED=false python -m pytest tests/test_chat_20_turn.py -q -p no:cacheprovider

echo "=== All §End gates passed ==="
