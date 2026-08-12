#!/usr/bin/env bash
# Idempotent Linux/macOS setup for Ollama, the external Jinn model, and Python runtime.
set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd)"
MODELFILE="$PROJECT_DIR/ollama/Modelfile"
BASE_MODEL="qwen2.5:1.5b"
MODEL_NAME="jinn"
DRY_RUN=0
SKIP_OLLAMA_INSTALL=0
SKIP_PYTHON=0

usage() {
  cat <<'EOF'
Usage: ./scripts/install-jinn.sh [options]

Options:
  --dry-run               Print commands without changing the computer.
  --skip-ollama-install   Require an existing Ollama installation.
  --skip-python           Do not create .venv or install Python dependencies.
  -h, --help              Show this help.

The local model is always created as "jinn" so the application can find it.
Model weights stay in Ollama's external model store and are never copied into Git.
EOF
}

while (($#)); do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --skip-ollama-install) SKIP_OLLAMA_INSTALL=1 ;;
    --skip-python) SKIP_PYTHON=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

log() { printf '\n[Jinn] %s\n' "$*"; }
run() {
  printf '+ '
  printf '%q ' "$@"
  printf '\n'
  if ((DRY_RUN == 0)); then "$@"; fi
}

case "$(uname -s)" in
  Linux) PLATFORM=linux ;;
  Darwin) PLATFORM=macos ;;
  *) printf 'Unsupported operating system. Use Linux or macOS.\n' >&2; exit 1 ;;
esac

if [[ ! -f "$MODELFILE" ]]; then
  printf 'Jinn Modelfile not found: %s\n' "$MODELFILE" >&2
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  printf 'curl is required for secure downloads and the Ollama readiness check.\n' >&2
  exit 1
fi

install_ollama() {
  if ((SKIP_OLLAMA_INSTALL)); then
    if ((DRY_RUN)); then
      log 'Assuming an existing Ollama installation (dry run)'
      return
    fi
    printf 'Ollama is required but was not found. Install it from https://ollama.com/download\n' >&2
    exit 1
  fi
  if [[ "$PLATFORM" == macos ]]; then
    if command -v brew >/dev/null 2>&1; then
      log 'Installing Ollama with Homebrew'
      run brew install ollama
      return
    fi
    cat >&2 <<'EOF'
Homebrew was not found. Install Ollama from the signed macOS download:
  https://ollama.com/download/mac
Then rerun this installer with --skip-ollama-install.
EOF
    exit 1
  fi

  local installer
  installer="$(mktemp "${TMPDIR:-/tmp}/jinn-ollama-install.XXXXXX")"
  trap 'rm -f -- "$installer"' EXIT
  log 'Downloading the official Ollama Linux installer over HTTPS'
  run curl --proto '=https' --tlsv1.2 --fail --show-error --location \
    --output "$installer" https://ollama.com/install.sh
  if ((DRY_RUN == 0)); then
    chmod 700 "$installer"
    # The downloaded script is retained only for this invocation and removed by the trap.
    run sh "$installer"
  else
    printf '+ chmod 700 %q\n' "$installer"
    printf '+ sh %q\n' "$installer"
  fi
  rm -f -- "$installer"
  trap - EXIT
}

if ! command -v ollama >/dev/null 2>&1; then
  install_ollama
fi

if ((DRY_RUN == 0)) && ! command -v ollama >/dev/null 2>&1; then
  printf 'Ollama installation finished but the ollama command is not on PATH. Open a new shell and rerun.\n' >&2
  exit 1
fi

if ((DRY_RUN)); then
  log 'Preparing Ollama service (dry run)'
  printf '+ start Ollama service if it is not already listening\n'
else
  if ! curl --silent --fail --max-time 2 http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
    log 'Starting Ollama'
    if [[ "$PLATFORM" == macos ]] && command -v brew >/dev/null 2>&1; then
      run brew services start ollama
    elif command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files ollama.service >/dev/null 2>&1; then
      if systemctl --user list-unit-files ollama.service >/dev/null 2>&1; then
        run systemctl --user start ollama
      else
        run sudo systemctl start ollama
      fi
    else
      cat >&2 <<'EOF'
Start Ollama in another terminal with:
  ollama serve
Then rerun this installer with --skip-ollama-install.
EOF
      exit 1
    fi
    for _ in {1..30}; do
      if curl --silent --fail --max-time 2 http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    if ! curl --silent --fail --max-time 2 http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
      printf 'Ollama did not become ready at http://127.0.0.1:11434.\n' >&2
      exit 1
    fi
  fi
fi

log "Downloading external base model: $BASE_MODEL"
run ollama pull "$BASE_MODEL"
log "Creating local Ollama model: $MODEL_NAME"
run ollama create "$MODEL_NAME" --file "$MODELFILE"

PYTHON_COMMAND=python3
if ((SKIP_PYTHON == 0)); then
  if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    printf 'Python 3.10+ is required. Install Python, then rerun with --skip-ollama-install.\n' >&2
    exit 1
  fi
  PYTHON_COMMAND="$PROJECT_DIR/.venv/bin/python"
  log 'Preparing the isolated Python environment'
  [[ -d "$PROJECT_DIR/.venv" ]] || run python3 -m venv "$PROJECT_DIR/.venv"
  run "$PROJECT_DIR/.venv/bin/python" -m pip install --upgrade pip
  run "$PROJECT_DIR/.venv/bin/python" -m pip install -r "$PROJECT_DIR/requirements.txt"
fi

if [[ ! -e "$PROJECT_DIR/.env" ]]; then
  log 'Creating private .env from the safe example'
  run cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
fi
if [[ -e "$PROJECT_DIR/.env" ]]; then
  run chmod 600 "$PROJECT_DIR/.env"
fi

cat <<EOF

Jinn setup is ready.
  Model: $MODEL_NAME (base weights remain in Ollama's external store)
  Start GUI: $PYTHON_COMMAND ${PROJECT_DIR}/main.py --gui-only
  Open: http://127.0.0.1:8765

Choose “Ollama · Jinn” in Settings if the local provider is not already selected.
EOF
