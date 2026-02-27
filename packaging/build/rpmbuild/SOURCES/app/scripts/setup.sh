#!/bin/bash

# setup.sh - Environment Setup Script for Mac/Linux

echo "Setting up Space Black..."

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 could not be found."
    echo "   Please install Python 3.10 or newer."
    exit 1
fi

# 2. Virtual Environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "Virtual environment found."
fi

# 3. Activation & Installation
echo "⬇Installing dependencies..."
source .venv/bin/activate

# 4. Install OS-Specific System Dependencies (Voice/Audio)
bash scripts/install_audio_deps.sh

# Upgrade pip just in case
pip install --upgrade pip > /dev/null 2>&1

if pip install -r requirements.txt; then
    echo " "
    echo "Setup Complete!"
    
    # Check for Playwright and install browsers if needed
    if pip show playwright > /dev/null 2>&1; then
        echo "🌍 Installing Playwright browsers..."
        playwright install chromium
    fi

    echo " "
    echo "To start the agent, run:"
    echo "   ./spaceblack start"
else
    echo "❌ Dependencies failed to install."
    exit 1
fi
