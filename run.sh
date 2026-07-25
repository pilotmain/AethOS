#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Start the local AethOS API and Mission Control processes.
set -euo pipefail

PRIMARY='\033[38;5;45m'
SUCCESS='\033[38;5;42m'
SLATE='\033[38;5;245m'
BOLD='\033[1m'
RESET='\033[0m'
if [[ ! -t 1 || -n "${NO_COLOR:-}" ]]; then PRIMARY=''; SUCCESS=''; SLATE=''; BOLD=''; RESET=''; fi

API_PORT="${AETHOS_API_PORT:-8010}"
WEB_PORT="${AETHOS_WEB_PORT:-3000}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_API=1
START_WEB=1
RELOAD=1
API_PID=""
WEB_PID=""

log() { printf '%b\n' "${PRIMARY}[AethOS]${RESET} $*"; }

usage() {
  cat <<'EOF'
Start AethOS locally

Usage: ./run.sh [options]

Options:
  --api-only        Start only the API
  --web-only        Start only Mission Control
  --no-reload       Disable the API source reloader
  --api-port PORT   API port (default: 8010)
  --web-port PORT   Mission Control port (default: 3000)
  -h, --help        Show this help

Press Ctrl+C to stop every process started by this command.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-only) START_WEB=0 ;;
    --web-only) START_API=0 ;;
    --no-reload) RELOAD=0 ;;
    --api-port) [[ $# -ge 2 ]] || { printf 'Missing API port\n' >&2; exit 2; }; API_PORT="$2"; shift ;;
    --web-port) [[ $# -ge 2 ]] || { printf 'Missing web port\n' >&2; exit 2; }; WEB_PORT="$2"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

if [[ "$START_API" == "1" && ! -x "${ROOT}/.venv/bin/python" ]]; then
  log "Python environment missing. Run ./install.sh --resume first."
  exit 1
fi
if [[ "$START_WEB" == "1" ]]; then
  command -v npm >/dev/null 2>&1 || { log "npm is missing. Run ./install.sh --help-step preflight."; exit 1; }
  [[ -d "${ROOT}/web/node_modules" ]] || { log "Mission Control dependencies missing. Run ./install.sh --from frontend."; exit 1; }
fi

# ── Version gate ─────────────────────────────────────────────────────────────
# Warns when a newer release exists; blocks startup once an update has been
# available for AETHOS_VERSION_GATE_DAYS (default 30). ./install.sh --update fixes it.
version_lt() { # version_lt A B → 0 when A < B
  [[ "$1" == "$2" ]] && return 1
  [[ "$(printf '%s\n%s\n' "$1" "$2" | sort -t. -k1,1n -k2,2n -k3,3n | head -1)" == "$1" ]]
}

check_updates() {
  [[ "${AETHOS_SKIP_UPDATE_CHECK:-0}" == "1" ]] && return 0
  local current latest="" cached_at=0 first_seen=0 now days gate_days cache
  current="$(cat "${ROOT}/VERSION" 2>/dev/null || printf '0.0.0')"
  gate_days="${AETHOS_VERSION_GATE_DAYS:-30}"
  cache="${ROOT}/.aethos-installer/update-check"
  mkdir -p "${ROOT}/.aethos-installer"
  now="$(date +%s)"
  if [[ -f "$cache" ]]; then
    latest="$(grep -m1 '^latest=' "$cache" 2>/dev/null | cut -d= -f2 || true)"
    cached_at="$(grep -m1 '^checked_at=' "$cache" 2>/dev/null | cut -d= -f2 || true)"
    first_seen="$(grep -m1 '^first_seen=' "$cache" 2>/dev/null | cut -d= -f2 || true)"
  fi
  [[ "$cached_at" =~ ^[0-9]+$ ]] || cached_at=0
  [[ "$first_seen" =~ ^[0-9]+$ ]] || first_seen=0
  if (( now - cached_at > 86400 )) && command -v curl >/dev/null 2>&1; then
    local fetched
    fetched="$(curl -m 6 -fsSL https://api.github.com/repos/pilotmain/AethOS/releases/latest 2>/dev/null \
      | grep -m1 '"tag_name"' | sed -E 's/.*"v?([0-9][0-9.]*)".*/\1/' || true)"
    if [[ "$fetched" =~ ^[0-9]+\.[0-9]+ ]]; then
      latest="$fetched"
      cached_at="$now"
    fi
  fi
  [[ -n "$latest" ]] || return 0
  if version_lt "$current" "$latest"; then
    (( first_seen == 0 )) && first_seen="$now"
    days=$(( (now - first_seen) / 86400 ))
    printf 'latest=%s\nchecked_at=%s\nfirst_seen=%s\n' "$latest" "$cached_at" "$first_seen" >"$cache"
    if (( days >= gate_days )); then
      printf '%b\n' "${BOLD}[AethOS] Update required.${RESET}" >&2
      printf '%s\n' "         Version ${current} is installed; ${latest} has been available for ${days} days" >&2
      printf '%s\n' "         (limit: ${gate_days} days). To keep local installs current and safe, AethOS" >&2
      printf '%s\n' "         will not start until it is updated:" >&2
      printf '%s\n' "             cd ${ROOT} && ./install.sh --update" >&2
      printf '%s\n' "         Broken install? Reinstall fresh (your .env can be kept):" >&2
      printf '%s\n' "             ./install.sh --reinstall" >&2
      exit 1
    fi
    log "Update available: v${current} → v${latest}. Run: ./install.sh --update ($(( gate_days - days )) days before updating is required)"
  else
    printf 'latest=%s\nchecked_at=%s\nfirst_seen=0\n' "$latest" "$cached_at" >"$cache"
  fi
}

check_updates

cleanup() {
  log "Shutting down…"
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "$WEB_PID" ]] && kill "$WEB_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && wait "$API_PID" 2>/dev/null || true
  [[ -n "$WEB_PID" ]] && wait "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

printf '\n%b\n%b\n\n' "${BOLD}${PRIMARY}  AethOS Mission Control${RESET}" "${SLATE}  Governed local runtime${RESET}"

if [[ "$START_API" == "1" ]]; then
  log "API → http://127.0.0.1:${API_PORT}"
  if [[ "$RELOAD" == "0" || "${AETHOS_NO_RELOAD:-0}" == "1" ]]; then
    (cd "$ROOT" && .venv/bin/python -m uvicorn aethos_core.api.main:app --host 127.0.0.1 --port "$API_PORT") &
  else
    (cd "$ROOT" && .venv/bin/python -m uvicorn aethos_core.api.main:app --host 127.0.0.1 --port "$API_PORT" \
      --reload --reload-dir aethos_core --reload-exclude 'data/*' --reload-exclude '*.json' --reload-exclude '*.log') &
  fi
  API_PID=$!
fi

if [[ "$START_WEB" == "1" ]]; then
  log "UI  → http://localhost:${WEB_PORT}"
  (cd "$ROOT/web" && npm run dev -- --port "$WEB_PORT") &
  WEB_PID=$!
fi

printf '\n%b\n\n' "${SUCCESS}[AethOS]${RESET} Runtime active. Press Ctrl+C to stop."
wait
