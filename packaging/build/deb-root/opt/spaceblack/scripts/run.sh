#!/bin/bash

# run.sh - Launcher for Mac/Linux

# Ensure setup has been run
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found."
    echo "   Please run ./setup.sh first."
    exit 1
fi

# Activate and Run
source .venv/bin/activate
python main.py
