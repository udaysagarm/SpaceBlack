#!/bin/bash

# run.sh - Launcher for Mac/Linux

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

# Auto-setup if venv is missing
if [ ! -d ".venv" ]; then
    echo "🔧 Virtual environment not found. Running setup..."
    bash "$SCRIPT_DIR/setup.sh"
    if [ $? -ne 0 ]; then
        exit 1
    fi
fi

# Activate and Run
source .venv/bin/activate
python main.py
