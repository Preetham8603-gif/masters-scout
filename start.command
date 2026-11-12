#!/bin/bash
# Start Masters Scout. Double-click to run; close this window to stop the app.
cd "$(dirname "$0")"
if [ ! -x .venv/bin/streamlit ]; then
  exec ./setup.command
fi
echo "Masters Scout is starting at http://localhost:8501"
echo "Keep this window open while you use the app. Close it to stop."
(sleep 4; open "http://localhost:8501") &
exec .venv/bin/streamlit run Home.py
