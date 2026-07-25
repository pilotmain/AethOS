#!/usr/bin/env bash
# Masterpiece behavioral acceptance corpus — explicit files, not broad -k keywords.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export USE_REAL_LLM="${USE_REAL_LLM:-false}"
export ACTIVE_PROVIDER="${ACTIVE_PROVIDER:-none}"
python -m pytest -q -p no:cacheprovider \
  tests/test_beta_smoke_harness.py \
  tests/test_chat_single_loop_corpus.py \
  tests/test_chat_layer_rebuild_corpus.py \
  tests/test_mutation_informational_guard_corpus.py \
  tests/test_context_budget_compaction.py \
  tests/test_tool_call_repair.py \
  tests/test_cold_start_lazy_mount.py \
  tests/test_deep_research_runtime.py \
  tests/test_blind_model_compare.py \
  tests/test_documents_ai_assist_diff.py \
  tests/test_foundry_fit_and_serve.py \
  tests/test_long_term_memory_recall.py \
  tests/test_workspace_email.py \
  tests/test_workspace_calendar.py \
  tests/test_workspace_notes_scheduled.py \
  tests/test_net_policy_egress.py \
  tests/test_byo_subscription.py \
  tests/test_no_legacy_polish_pipeline.py \
  tests/test_canvas_render_honesty.py \
  tests/test_canvas_store_cross_process.py
