#!/bin/bash
# One-time setup for Masters Scout on a Mac. Double-click to run.
cd "$(dirname "$0")"
echo "== Masters Scout setup =="

PY=""
export PATH="/Library/Frameworks/Python.framework/Versions/Current/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
for p in python3.13 python3.12 python3.11 python3.10 python3.14 python3; do
  if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$p"; break
  fi
done

if [ -z "$PY" ]; then
  echo ""
  echo "Python 3.10 or newer is needed. Opening python.org - download the macOS installer,"
  echo "install it, then double-click setup.command again."
  open "https://www.python.org/downloads/macos/"
  read -n 1 -s -r -p "Press any key to close."
  exit 1
fi

echo "Using $($PY --version)"
"$PY" -m venv .venv || { echo "Could not create the environment."; exit 1; }
.venv/bin/pip install --upgrade pip -q
echo "Installing packages (a few minutes the first time)..."
.venv/bin/pip install -r requirements.txt -q || { echo "Install failed - check your internet connection and try again."; read -n 1 -s -r; exit 1; }
echo ""
echo "Setup done. Starting the app..."
exec ./start.command
