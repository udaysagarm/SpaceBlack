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

The fastest way to get started. This script detects your OS, downloads the right package (or clones from source), and sets everything up.

**Via spaceblack.info:**
```bash
curl -fsSL https://spaceblack.info/install.sh | bash
```

**Via GitHub (alternative):**
```bash
curl -fsSL https://raw.githubusercontent.com/udaysagarm/SpaceBlack/main/install.sh | bash
```

The installer will:
1.  Detect your operating system.
2.  On Debian/Ubuntu: download and install the `.deb` package.
3.  On Fedora/RHEL: download and install the `.rpm` package.
4.  On macOS or other systems: clone the repository to `~/SpaceBlack`.
5.  Print instructions to launch Ghost.

After install, run:
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

Pre-built packages are available for Debian/Ubuntu and Fedora/RHEL systems. Download from [GitHub Releases](https://github.com/udaysagarm/SpaceBlack/releases).

### Debian / Ubuntu
```bash
sudo dpkg -i spaceblack_1.0.0_all.deb
ghost start
```

### Fedora / RHEL
```bash
sudo rpm -i spaceblack-1.0.0-1.noarch.rpm
ghost start
```

Packages install to `/opt/spaceblack/` and provide the `ghost` CLI at `/usr/local/bin/ghost`. First `ghost start` runs auto-setup.

See [**Packaging Guide**](./PACKAGING.md) for building packages from source.

---

## Hosting the Install Script

To make `curl -fsSL https://spaceblack.info/install.sh | bash` work, you need to host the `install.sh` file on your domain. Two options:

### Option A: Direct hosting
Upload `install.sh` to your web server so that `https://spaceblack.info/install.sh` returns the raw script with `Content-Type: text/plain`.

### Option B: Redirect to GitHub
Configure your web server to redirect `https://spaceblack.info/install.sh` to the raw GitHub URL:
```
https://raw.githubusercontent.com/udaysagarm/SpaceBlack/main/install.sh
```

For example, with Nginx:
```nginx
location = /install.sh {
    return 302 https://raw.githubusercontent.com/udaysagarm/SpaceBlack/main/install.sh;
}
```

Or with Vercel/Netlify `_redirects`:
```
/install.sh https://raw.githubusercontent.com/udaysagarm/SpaceBlack/main/install.sh 200
```

### GitHub Releases Setup
For the installer to download `.deb`/`.rpm` packages automatically, create a [GitHub Release](https://github.com/udaysagarm/SpaceBlack/releases/new) and attach the built packages:
1.  Build packages: `bash packaging/build_packages.sh`
2.  Go to GitHub → Releases → "Create a new release"
3.  Tag: `v1.0.0`
4.  Upload `packaging/dist/spaceblack_1.0.0_all.deb` and `packaging/dist/spaceblack-1.0.0-1.noarch.rpm`
5.  Publish the release

---

## Manual Configuration (Advanced)

If you prefer to configure the application manually, you can create the `.env` file yourself in the project root:

```tex
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here  # Optional
```

Once the `.env` file is created, running `python main.py` will skip the wizard and launch the TUI directly.
