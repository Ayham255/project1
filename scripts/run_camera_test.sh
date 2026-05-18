#!/bin/bash
echo "Starting Two-Camera Test..."
source venv/bin/activate
DISPLAY=:0 python3 tests/test_two_cameras.py
