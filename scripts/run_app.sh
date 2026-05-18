#!/bin/bash
echo "Starting Main Application..."
source venv/bin/activate
DISPLAY=:0 python3 -m app.main
