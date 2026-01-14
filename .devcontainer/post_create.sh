#!/usr/bin/env bash
set -euo pipefail

echo "[post_create] Starting bootstrap..."

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is not available in the container. Please use an image with Python 3 installed."
  exit 1
fi

echo "[post_create] Creating virtualenv .venv using python3"
python3 -m venv .venv

if [ ! -x .venv/bin/python3 ]; then
  echo "ERROR: .venv/bin/python3 not found after venv creation."
  ls -la .venv || true
  exit 1
fi

echo "[post_create] Upgrading pip and installing requirements"
.venv/bin/python3 -m pip install --upgrade pip
.venv/bin/python3 -m pip install -r requirements.txt

echo "[post_create] Bootstrap complete."

echo "[post_create] Configuring automatic venv activation for interactive shells"
# Add an idempotent line to the user's ~/.bashrc so new terminals auto-activate the repo venv
BASHRC="$HOME/.bashrc"
ABS_REPO_DIR="$(pwd)"
AUTOACT_LINE="if [ -f \"$ABS_REPO_DIR/.venv/bin/activate\" ]; then . \"$ABS_REPO_DIR/.venv/bin/activate\"; fi"

if ! grep -Fq "$AUTOACT_LINE" "$BASHRC" 2>/dev/null; then
  printf '%s\n' "# Auto-activate the project virtualenv" >> "$BASHRC"
  printf '%s\n' "$AUTOACT_LINE" >> "$BASHRC"
  echo "[post_create] Added venv auto-activation to $BASHRC"
else
  echo "[post_create] venv auto-activation already present in $BASHRC"
fi

echo "[post_create] post-create script finished. Open a new terminal to get the venv activated automatically."
