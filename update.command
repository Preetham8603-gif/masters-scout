#!/bin/bash
# Get the latest version of Masters Scout. Double-click to run.
# Your profile, professor tracker, ranks and settings in data/ are never touched.
REPO="GITHUB_USERNAME/masters-scout"   # <- set once, e.g. "yourname/masters-scout"
BRANCH="main"

cd "$(dirname "$0")"
echo "== Updating Masters Scout =="

if [ -d .git ]; then
  git pull --ff-only || { echo "Update failed."; read -n 1 -s -r; exit 1; }
else
  TMP="$(mktemp -d)"
  curl -fsSL "https://github.com/$REPO/archive/refs/heads/$BRANCH.zip" -o "$TMP/update.zip" \
    || { echo "Could not download the update (check internet, or the REPO line in update.command)."; read -n 1 -s -r; exit 1; }
  unzip -q "$TMP/update.zip" -d "$TMP"
  SRC="$(find "$TMP" -mindepth 1 -maxdepth 1 -type d | head -1)"
  rsync -a \
    --exclude ".venv/" --exclude "data/cache/" \
    --exclude "data/profile.json" --exclude "data/settings.json" \
    --exclude "data/scout.db" --exclude "data/rankings.csv" \
    "$SRC"/ ./
  rm -rf "$TMP"
  chmod +x ./*.command
fi

if [ -x .venv/bin/pip ]; then
  echo "Checking packages..."
  .venv/bin/pip install -r requirements.txt -q
fi
echo ""
echo "Updated. Start the app with start.command."
read -n 1 -s -r -p "Press any key to close."
