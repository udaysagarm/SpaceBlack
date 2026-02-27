# Installation Guide

Follow these steps to install and configure Space Black on your system.

## Prerequisites

-   **Python 3.10 or higher**: Ensure you have a modern version of Python installed.
-   **Git**: Required for source install.
-   **Terminal**: 
    -   **Windows**: Recommended to use PowerShell or Windows Terminal.
    -   **Mac/Linux**: Default terminal is sufficient. Nerd Fonts are recommended for the best experience.
-   **Audio Drivers (Linux/Raspberry Pi Only)**:
    -   Space Black uses PortAudio for native microphone integrations. On Mac and Windows, this is pre-packaged. On Linux variants, setup will install `portaudio19-dev` via `apt-get`.

---

## Option 1: One-Line Install (Recommended)

The fastest way to get started on **macOS and Linux**. This script detects your OS, downloads the right package (or clones from source), and sets everything up.

```bash
curl -fsSL https://spaceblack.info/install.sh | bash
```

> **Alternative** (via GitHub directly):
> ```bash
> curl -fsSL https://raw.githubusercontent.com/udaysagarm/SpaceBlack/main/install.sh | bash
> ```

The installer will:
1.  Detect your operating system.
2.  On **Debian/Ubuntu**: download and install the `.deb` package from [GitHub Releases](https://github.com/udaysagarm/SpaceBlack/releases).
3.  On **Fedora/RHEL**: download and install the `.rpm` package.
4.  On **macOS** or other systems: clone the repository to `~/SpaceBlack`.
5.  Print instructions to launch Ghost.

After install, launch the agent:
```bash
ghost start
```

---

## Option 2: Manual Clone

### 1. Clone the Repository
```bash
git clone https://github.com/udaysagarm/SpaceBlack.git
cd SpaceBlack
```

### 2. Launch Ghost
**Mac/Linux**
```bash
./ghost start
```

**Windows (PowerShell)**
```powershell
ghost start
```

On first run, the `ghost` CLI will automatically:
1.  Create a virtual environment (`.venv`).
2.  Install all dependencies from `requirements.txt`.
3.  Install Playwright browser binaries.
4.  Launch the configuration wizard (if no config exists).
5.  Start the Ghost agent TUI.

Subsequent runs skip setup and launch instantly.

---

## Option 3: Linux Packages (.deb / .rpm)

Pre-built packages are available on [GitHub Releases](https://github.com/udaysagarm/SpaceBlack/releases).

### Debian / Ubuntu
```bash
# Download
curl -fsSL -o spaceblack.deb https://github.com/udaysagarm/SpaceBlack/releases/latest/download/spaceblack_1.0.0_all.deb

# Install
sudo dpkg -i spaceblack.deb

# Launch
ghost start
```

### Fedora / RHEL
```bash
# Download
curl -fsSL -o spaceblack.rpm https://github.com/udaysagarm/SpaceBlack/releases/latest/download/spaceblack-1.0.0-1.noarch.rpm

# Install
sudo rpm -i spaceblack.rpm

# Launch
ghost start
```

Packages install to `/opt/spaceblack/` and provide the `ghost` CLI at `/usr/local/bin/ghost`. First `ghost start` runs auto-setup.

See [**Packaging Guide**](./PACKAGING.md) for building packages from source.

---

## Updating

To update an existing installation to the latest version:

**Source install (macOS / Linux / Windows):**
```bash
./ghost update
```
This pulls the latest code from GitHub and updates any changed dependencies.

**Package install (.deb / .rpm):**
Re-run the installer to download the latest package:
```bash
curl -fsSL https://spaceblack.info/install.sh | bash
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `ghost start` | Launch Ghost (auto-setup on first run) |
| `ghost update` | Pull latest code & update dependencies |
| `ghost daemon` | Start the background daemon |
| `ghost help` | Show available commands |

---

## Manual Configuration (Advanced)

If you prefer to configure the application manually, you can create the `.env` file yourself in the project root:

```tex
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here  # Optional
```

Once the `.env` file is created, running `ghost start` will skip the wizard and launch the TUI directly.
