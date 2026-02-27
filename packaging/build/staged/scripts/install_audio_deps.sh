#!/bin/bash

# install_audio_deps.sh
# Installs PortAudio dependencies for Linux / Raspberry Pi so voice features work out-of-the-box.
# Automatically skips macOS and Windows as they use pre-compiled binaries.

OS="$(uname -s)"

if [ "$OS" = "Linux" ]; then
    echo "🐧 Linux / Raspberry Pi detected."
    echo "Installing required audio drivers (PortAudio & ALSA)..."
    
    # Check if apt-get is available (Debian/Ubuntu/Raspbian)
    if command -v apt-get &> /dev/null; then
        # We don't strictly update unless the install fails, to save time, but it's safer to update.
        # We'll just run the install.
        sudo apt-get install -y portaudio19-dev libportaudio2 libasound2-dev
        if [ $? -eq 0 ]; then
            echo "✅ Audio dependencies installed successfully."
        else
            echo "❌ Failed to install audio dependencies. You may need to run 'sudo apt-get update' first."
        fi
    else
        echo "⚠️ 'apt-get' package manager not found."
        echo "If you are on an Arch, RHEL, or Fedora system, please install the equivalent PortAudio and ALSA development packages manually."
    fi
else
    echo "💻 Current OS ($OS) handles PortAudio natively via Python wheels. Skipping system install."
fi
