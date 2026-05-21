#!/bin/bash
echo "Starting Main Application..."
source venv/bin/activate
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-0
python3 -m app.main
