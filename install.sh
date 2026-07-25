#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# AethOS installer for macOS and Linux.
set -Eeuo pipefail

AETHOS_VERSION="0.2.0"
REPO_URL="${AETHOS_REPO_URL:-https://github.com/pilotmain/AethOS.git}"
INSTALLER_URL="${AETHOS_INSTALLER_URL:-https://raw.githubusercontent.com/pilotmain/AethOS/main/install.sh}"
INSTALL_DIR="${AETHOS_INSTALL_DIR:-${HOME}/aethos}"
BRANCH="${AETHOS_BRANCH:-main}"
API_PORT="${AETHOS_API_PORT:-8010}"
WEB_PORT="${AETHOS_WEB_PORT:-3000}"
MIN_PYTHON="3.11"
MIN_NODE="20"
RECOMMENDED_NODE="24"
MIN_DISK_MB=1024

MODE="install"
RESUME=0
FROM_STEP=""
SKIP_WEB=0
DETAILED=0
HELP_STEP=""
CURRENT_STEP="startup"
ROOT=""
PYTHON_BIN=""
STATE_ROOT=""
STATE_DIR=""
LOG_FILE=""
STEPS=(preflight source backend frontend verify)

PRIMARY='\033[38;5;45m'
SUCCESS='\033[38;5;42m'
WARNING='\033[38;5;220m'
MUTATION='\033[38;5;203m'
SLATE='\033[38;5;245m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

if [[ ! -t 1 || -n "${NO_COLOR:-}" ]]; then
  PRIMARY=''; SUCCESS=''; WARNING=''; MUTATION=''; SLATE=''; BOLD=''; DIM=''; RESET=''
fi

say()       { printf '%b\n' "${PRIMARY}[AethOS]${RESET} $*"; }
ok()        { printf '%b\n' "${SUCCESS}[AethOS]${RESET} $*"; }
warn()      { printf '%b\n' "${WARNING}[AethOS]${RESET} $*"; }
fail()      { printf '%b\n' "${MUTATION}[AethOS]${RESET} $*" >&2; }
note()      { printf '%b\n' "${SLATE}         $*${RESET}"; }
section()   { printf '\n%b\n%b\n' "${SLATE}────────────────────────────────────────────────────────${RESET}" "${BOLD}${PRIMARY}$1${RESET}"; }

usage() {
  cat <<'EOF'
AethOS installer — macOS and Linux

Usage:
  ./install.sh [options]
  curl -fsSL https://raw.githubusercontent.com/pilotmain/AethOS/main/install.sh | bash

Options:
  --resume               Continue after the last completed step
  --from STEP            Re-run STEP and every step after it
  --status               Show prerequisites and saved install progress
  --help-step STEP       Explain a step and its recovery actions
  --install-dir PATH     Install location (default: ~/aethos)
  --branch NAME          Git branch or tag (default: main)
  --api-port PORT        API port (default: 8010)
  --web-port PORT        Mission Control port (default: 3000)
  --skip-web             Install the API and CLI without Mission Control
  --detailed             Show full pip and npm output
  -h, --help             Show this help

Steps: preflight, source, backend, frontend, verify

Environment equivalents:
  AETHOS_INSTALL_DIR, AETHOS_REPO_URL, AETHOS_BRANCH,
  AETHOS_API_PORT, AETHOS_WEB_PORT, NO_COLOR

Examples:
  ./install.sh --resume
  ./install.sh --from frontend
  ./install.sh --help-step preflight
  AETHOS_INSTALL_DIR="$HOME/ops/aethos" ./install.sh
EOF
}

step_help() {
  case "$1" in
    preflight)
      cat <<EOF
preflight checks the operating system, disk space, Git, Python ${MIN_PYTHON}+, and
Node ${MIN_NODE}+ (Node ${RECOMMENDED_NODE} LTS recommended). It never installs system packages or
runs sudo. On macOS, use Homebrew or the official installers. On Linux, use your
distribution package manager, pyenv, or nvm, then run the installer with --resume.
EOF
      ;;
    source)
      cat <<EOF
source uses the current AethOS checkout when run inside one; otherwise it clones
${REPO_URL} into ${INSTALL_DIR}. Existing local changes are never overwritten.
EOF
      ;;
    backend)
      cat <<'EOF'
backend creates .venv, installs AethOS with cloud and secure-vault support, and
creates .env from .env.example only when .env does not already exist. Credentials
and existing configuration are never overwritten.
EOF
      ;;
    frontend)
      cat <<'EOF'
frontend installs the locked Mission Control dependencies with npm ci and creates
web/.env.local only when missing. Use --skip-web for an API/CLI-only installation.
EOF
      ;;
    verify)
      cat <<'EOF'
verify imports the installed Python package, exercises the CLI, and checks the
Mission Control toolchain. It does not start services or contact configured
providers. Afterward, run ./run.sh and then `aethos doctor` for live probes.
EOF
      ;;
    *) fail "Unknown step '$1'. Valid steps: ${STEPS[*]}"; return 2 ;;
  esac
}

is_step() {
  local candidate="$1" step
  for step in "${STEPS[@]}"; do
    [[ "$candidate" == "$step" ]] && return 0
  done
  return 1
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --resume) RESUME=1 ;;
      --status) MODE="status" ;;
      --from) [[ $# -ge 2 ]] || { fail "--from requires a step"; exit 2; }; FROM_STEP="$2"; shift ;;
      --help-step) [[ $# -ge 2 ]] || { fail "--help-step requires a step"; exit 2; }; HELP_STEP="$2"; shift ;;
      --install-dir) [[ $# -ge 2 ]] || { fail "--install-dir requires a path"; exit 2; }; INSTALL_DIR="$2"; shift ;;
      --branch) [[ $# -ge 2 ]] || { fail "--branch requires a name"; exit 2; }; BRANCH="$2"; shift ;;
      --api-port) [[ $# -ge 2 ]] || { fail "--api-port requires a port"; exit 2; }; API_PORT="$2"; shift ;;
      --web-port) [[ $# -ge 2 ]] || { fail "--web-port requires a port"; exit 2; }; WEB_PORT="$2"; shift ;;
      --skip-web) SKIP_WEB=1 ;;
      --detailed) DETAILED=1 ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Unknown option: $1"; usage >&2; exit 2 ;;
    esac
    shift
  done

  if [[ -n "$FROM_STEP" ]] && ! is_step "$FROM_STEP"; then
    fail "Unknown step '$FROM_STEP'. Valid steps: ${STEPS[*]}"
    exit 2
  fi
  if [[ -n "$HELP_STEP" ]]; then
    step_help "$HELP_STEP"
    exit $?
  fi
  [[ "$API_PORT" =~ ^[0-9]+$ ]] || { fail "Invalid API port: $API_PORT"; exit 2; }
  [[ "$WEB_PORT" =~ ^[0-9]+$ ]] || { fail "Invalid web port: $WEB_PORT"; exit 2; }
}

init_state() {
  local existing_root
  existing_root="$(resolve_existing_root)"
  if [[ -n "$existing_root" ]]; then
    STATE_ROOT="${AETHOS_STATE_DIR:-${existing_root}/.aethos-installer}"
  else
    STATE_ROOT="${AETHOS_STATE_DIR:-${INSTALL_DIR}.installer}"
  fi
  STATE_DIR="${STATE_ROOT}/v${AETHOS_VERSION}"
  mkdir -p "$STATE_DIR"
  LOG_FILE="${STATE_DIR}/install.log"
  : >>"$LOG_FILE"
}

marker() { printf '%s/%s.done' "$STATE_DIR" "$1"; }
mark_done() { printf '%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" >"$(marker "$1")"; }
is_done() { [[ -f "$(marker "$1")" ]]; }

resume_command() {
  if [[ -f "${ROOT:-$INSTALL_DIR}/install.sh" ]]; then
    printf 'cd %q && ./install.sh --resume' "${ROOT:-$INSTALL_DIR}"
  else
    printf 'curl -fsSL %q | bash -s -- --resume --install-dir %q' "$INSTALLER_URL" "$INSTALL_DIR"
  fi
}

step_help_command() {
  if [[ -f "${ROOT:-$INSTALL_DIR}/install.sh" ]]; then
    printf 'cd %q && ./install.sh --help-step %q' "${ROOT:-$INSTALL_DIR}" "$CURRENT_STEP"
  else
    printf 'curl -fsSL %q | bash -s -- --help-step %q' "$INSTALLER_URL" "$CURRENT_STEP"
  fi
}

on_error() {
  local code=$? line="${1:-unknown}"
  set +e
  printf '\n' >&2
  fail "Installation stopped during '${CURRENT_STEP}' (line ${line}, exit ${code})."
  note "Nothing completed earlier was rolled back or overwritten."
  note "Step help: $(step_help_command)"
  note "Continue:  $(resume_command)"
  note "Log:       ${LOG_FILE}"
  exit "$code"
}

print_banner() {
  printf '\n%b\n' "${BOLD}${PRIMARY}     A E T H O S${RESET}  ${DIM}v${AETHOS_VERSION}${RESET}"
  printf '%b\n' "${SLATE}     Governed operations. Evidence before action.${RESET}"
  printf '%b\n\n' "${SLATE}     Local-first · resumable · safe by default${RESET}"
}

version_at_least() {
  local actual="$1" minimum="$2"
  local actual_major=0 actual_minor=0 actual_patch=0 minimum_major=0 minimum_minor=0 minimum_patch=0
  IFS=. read -r actual_major actual_minor actual_patch <<<"$actual"
  IFS=. read -r minimum_major minimum_minor minimum_patch <<<"$minimum"
  actual_major="${actual_major//[^0-9]/}"; actual_minor="${actual_minor//[^0-9]/}"; actual_patch="${actual_patch//[^0-9]/}"
  minimum_major="${minimum_major//[^0-9]/}"; minimum_minor="${minimum_minor//[^0-9]/}"; minimum_patch="${minimum_patch//[^0-9]/}"
  actual_major="${actual_major:-0}"; actual_minor="${actual_minor:-0}"; actual_patch="${actual_patch:-0}"
  minimum_major="${minimum_major:-0}"; minimum_minor="${minimum_minor:-0}"; minimum_patch="${minimum_patch:-0}"
  (( actual_major > minimum_major )) ||
    (( actual_major == minimum_major && actual_minor > minimum_minor )) ||
    (( actual_major == minimum_major && actual_minor == minimum_minor && actual_patch >= minimum_patch ))
}

resolve_python() {
  local candidate version
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      version="$($candidate -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || true)"
      if [[ -n "$version" ]] && version_at_least "$version" "$MIN_PYTHON"; then
        PYTHON_BIN="$candidate"
        return 0
      fi
    fi
  done
  return 1
}

resolve_existing_root() {
  local script_dir=""
  if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  fi
  if [[ -f "$PWD/pyproject.toml" ]] && grep -Eq '^name[[:space:]]*=[[:space:]]*"aethos"' "$PWD/pyproject.toml"; then
    printf '%s' "$PWD"
  elif [[ -n "$script_dir" && -f "$script_dir/pyproject.toml" ]] && grep -Eq '^name[[:space:]]*=[[:space:]]*"aethos"' "$script_dir/pyproject.toml"; then
    printf '%s' "$script_dir"
  elif [[ -f "$INSTALL_DIR/pyproject.toml" ]] && grep -Eq '^name[[:space:]]*=[[:space:]]*"aethos"' "$INSTALL_DIR/pyproject.toml"; then
    printf '%s' "$INSTALL_DIR"
  fi
}

run_quiet() {
  if [[ "$DETAILED" == "1" ]]; then
    "$@"
    return
  fi
  if ! "$@" >>"$LOG_FILE" 2>&1; then
    fail "Command failed: $*"
    note "Last log lines:"
    tail -n 35 "$LOG_FILE" >&2 || true
    return 1
  fi
}

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -i ":${port}" -sTCP:LISTEN -t >/dev/null 2>&1
  elif command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
  else
    return 1
  fi
}

prerequisite_help() {
  case "$(uname -s 2>/dev/null || true)" in
    Darwin)
      note "macOS help: https://github.com/pilotmain/AethOS/blob/main/docs/GETTING_STARTED.md#macos-prerequisites"
      note "With Homebrew: brew install git python@3.12 node@24"
      ;;
    *)
      note "Linux help: https://github.com/pilotmain/AethOS/blob/main/docs/GETTING_STARTED.md#linux-prerequisites"
      note "Install Git, Python ${MIN_PYTHON}+, and Node ${RECOMMENDED_NODE} LTS with your package/version manager."
      ;;
  esac
}

step_preflight() {
  section "1 / 5  Preflight"
  local os missing=0 node_version available_kb existing_root
  os="$(uname -s 2>/dev/null || true)"
  case "$os" in
    Darwin) ok "macOS detected" ;;
    Linux) ok "Linux detected" ;;
    *) fail "Unsupported operating system: ${os:-unknown}. On Windows, use install.ps1."; return 2 ;;
  esac

  existing_root="$(resolve_existing_root)"
  if [[ -z "$existing_root" ]] && ! command -v git >/dev/null 2>&1; then
    fail "Git is required to download AethOS."
    missing=1
  elif command -v git >/dev/null 2>&1; then
    ok "Git $(git --version | awk '{print $3}')"
  else
    ok "Local source detected; Git is optional for this run"
  fi

  if resolve_python; then
    ok "Python $($PYTHON_BIN --version 2>&1 | awk '{print $2}')"
  else
    fail "Python ${MIN_PYTHON}+ is required."
    missing=1
  fi

  if [[ "$SKIP_WEB" == "1" ]]; then
    note "Mission Control skipped by request"
  elif ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
    fail "Node.js ${MIN_NODE}+ and npm are required for Mission Control."
    missing=1
  else
    node_version="$(node --version | sed 's/^v//')"
    if ! version_at_least "$node_version" "$MIN_NODE"; then
      fail "Node.js ${MIN_NODE}+ is required; found ${node_version}."
      missing=1
    else
      ok "Node ${node_version} with npm $(npm --version)"
      if ! version_at_least "$node_version" "$RECOMMENDED_NODE"; then
        warn "Node ${RECOMMENDED_NODE} LTS is recommended for the public release path"
      fi
    fi
  fi

  if command -v df >/dev/null 2>&1; then
    available_kb="$(df -Pk "$HOME" 2>/dev/null | awk 'NR==2 {print $4}' || printf '0')"
    if [[ "$available_kb" =~ ^[0-9]+$ ]] && (( available_kb < MIN_DISK_MB * 1024 )); then
      fail "At least ${MIN_DISK_MB} MB of free disk space is required."
      missing=1
    else
      ok "Disk space check passed"
    fi
  fi

  if (( missing != 0 )); then
    prerequisite_help
    return 2
  fi
  port_in_use "$API_PORT" && warn "Port ${API_PORT} is already in use; AethOS may already be running"
  if [[ "$SKIP_WEB" != "1" ]]; then
    port_in_use "$WEB_PORT" && warn "Port ${WEB_PORT} is already in use; Mission Control may already be running"
  fi
  note "Mutation execution and host shell access remain disabled by default."
}

step_source() {
  section "2 / 5  Source"
  ROOT="$(resolve_existing_root)"
  if [[ -n "$ROOT" ]]; then
    ok "Using existing AethOS source: ${ROOT}"
    return
  fi

  if [[ -e "$INSTALL_DIR" && ! -d "$INSTALL_DIR/.git" ]]; then
    fail "Install path exists but is not an AethOS Git checkout: $INSTALL_DIR"
    note "Choose another path with --install-dir or move that directory yourself."
    return 2
  fi
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    ROOT="$INSTALL_DIR"
    if [[ -n "$(git -C "$ROOT" status --porcelain)" ]]; then
      warn "Existing checkout has local changes; source update skipped"
    else
      say "Updating existing checkout without rewriting history…"
      run_quiet git -C "$ROOT" fetch --depth 1 origin "$BRANCH"
      run_quiet git -C "$ROOT" checkout "$BRANCH"
      run_quiet git -C "$ROOT" merge --ff-only "origin/$BRANCH"
    fi
  else
    say "Cloning AethOS into ${INSTALL_DIR}…"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    run_quiet git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
    ROOT="$INSTALL_DIR"
  fi
  ok "Source ready at ${ROOT}"
}

ensure_root() {
  if [[ -z "$ROOT" ]]; then
    ROOT="$(resolve_existing_root)"
  fi
  [[ -n "$ROOT" && -f "$ROOT/pyproject.toml" ]] || { fail "AethOS source is unavailable; re-run from the source step."; return 2; }
}

step_backend() {
  section "3 / 5  Backend and CLI"
  ensure_root
  resolve_python || { fail "Python ${MIN_PYTHON}+ is no longer available."; return 2; }
  cd "$ROOT"
  if [[ ! -x .venv/bin/python ]]; then
    say "Creating an isolated Python environment…"
    run_quiet "$PYTHON_BIN" -m venv .venv
  else
    ok "Python environment already exists"
  fi
  say "Installing AethOS, cloud adapters, and secure-vault support…"
  run_quiet .venv/bin/python -m pip install --upgrade pip
  run_quiet .venv/bin/python -m pip install -c requirements.lock -e '.[cloud,secrets]'
  if [[ ! -f .env ]]; then
    cp .env.example .env
    ok "Created .env from the safe-default template"
  else
    ok "Preserved existing .env"
  fi
  ok "API and CLI installed"
}

step_frontend() {
  section "4 / 5  Mission Control"
  if [[ "$SKIP_WEB" == "1" ]]; then
    note "Skipped by --skip-web"
    return
  fi
  ensure_root
  cd "$ROOT/web"
  if [[ ! -f .env.local ]]; then
    {
      printf '%s\n' '# Same-origin /api/v1 proxy is recommended for auth cookies.'
      printf '%s\n' "# NEXT_PUBLIC_API_BASE=http://127.0.0.1:${API_PORT}"
    } >.env.local
    ok "Created web/.env.local"
  else
    ok "Preserved existing web/.env.local"
  fi
  say "Installing the locked Mission Control dependency graph…"
  run_quiet npm ci --no-audit --no-fund
  ok "Mission Control dependencies installed"
}

step_verify() {
  section "5 / 5  Verification"
  ensure_root
  cd "$ROOT"
  say "Checking the installed API and CLI…"
  run_quiet .venv/bin/python -c 'import aethos_core; from aethos_core.api.main import app; assert app'
  run_quiet .venv/bin/aethos --help
  if [[ "$SKIP_WEB" != "1" ]]; then
    [[ -x web/node_modules/.bin/next ]] || { fail "Mission Control dependency check failed."; return 1; }
    say "Checking Mission Control types…"
    (cd web && run_quiet npm run typecheck)
  fi
  ok "Local installation verified"
}

step_index() {
  local wanted="$1" idx=0 step
  for step in "${STEPS[@]}"; do
    [[ "$wanted" == "$step" ]] && { printf '%s' "$idx"; return; }
    idx=$((idx + 1))
  done
}

run_steps() {
  local step from_index=-1 index=0
  [[ -n "$FROM_STEP" ]] && from_index="$(step_index "$FROM_STEP")"
  for step in "${STEPS[@]}"; do
    if [[ "$SKIP_WEB" == "1" && "$step" == "frontend" ]]; then
      CURRENT_STEP="$step"
      step_frontend
      mark_done "$step"
      index=$((index + 1))
      continue
    fi
    if (( from_index >= 0 && index < from_index )); then
      note "Skipping ${step}; --from starts at ${FROM_STEP}"
    elif [[ "$RESUME" == "1" && from_index -lt 0 ]] && is_done "$step"; then
      ok "${step} already complete"
    else
      CURRENT_STEP="$step"
      "step_${step}"
      mark_done "$step"
    fi
    index=$((index + 1))
  done
}

show_status() {
  print_banner
  section "Install status"
  printf '  %-12s %s\n' "Install dir" "$INSTALL_DIR"
  printf '  %-12s %s\n' "Version" "$AETHOS_VERSION"
  printf '  %-12s %s\n' "State" "$STATE_DIR"
  printf '\n'
  local step
  for step in "${STEPS[@]}"; do
    if is_done "$step"; then
      printf '  %b%-10s%b complete\n' "$SUCCESS" "$step" "$RESET"
    else
      printf '  %b%-10s%b pending\n' "$SLATE" "$step" "$RESET"
    fi
  done
  printf '\n'
  command -v git >/dev/null 2>&1 && ok "Git available" || warn "Git not found"
  resolve_python && ok "Python $($PYTHON_BIN --version 2>&1 | awk '{print $2}')" || warn "Python ${MIN_PYTHON}+ not found"
  command -v node >/dev/null 2>&1 && ok "Node $(node --version)" || warn "Node not found"
  note "Continue: $(resume_command)"
}

print_success() {
  section "AethOS is ready"
  ok "Installation and local verification completed."
  printf '\n'
  printf '  %bStart%b             cd %q && ./run.sh\n' "$BOLD" "$RESET" "$ROOT"
  printf '  %bMission Control%b   http://localhost:%s\n' "$BOLD" "$RESET" "$WEB_PORT"
  printf '  %bAPI health%b        http://127.0.0.1:%s/api/v1/health\n' "$BOLD" "$RESET" "$API_PORT"
  printf '  %bDoctor%b            cd %q && .venv/bin/aethos doctor\n' "$BOLD" "$RESET" "$ROOT"
  printf '\n'
  printf '  %bAI provider%b       Set USE_REAL_LLM=true and at least one key in %q/.env\n' "$BOLD" "$RESET" "$ROOT"
  note "Supported: Anthropic · OpenRouter · OpenAI · Gemini · Mistral · Groq · xAI · DeepSeek · Together · local (Ollama/LM Studio)"
  printf '\n'
  note "Installer status: ./install.sh --status"
  note "Step help:        ./install.sh --help-step STEP"
  note "Detailed log:     ${LOG_FILE}"
  note "Mutation execution and host shell access are still disabled."
}

main() {
  parse_args "$@"
  init_state
  if [[ "$MODE" == "status" ]]; then
    show_status
    return
  fi
  trap 'on_error "$LINENO"' ERR
  print_banner
  note "Progress is checkpointed; a failed run can continue with --resume."
  run_steps
  CURRENT_STEP="complete"
  print_success
}

main "$@"
