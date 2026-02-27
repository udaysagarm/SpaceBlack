# Space Black — Packaging

This directory contains everything needed to build `.deb` and `.rpm` packages.

## Quick Build

```bash
bash packaging/build_packages.sh
```

Packages are output to `packaging/dist/`.

## Prerequisites

| Format | Tool       | Install                        |
|--------|------------|--------------------------------|
| `.deb` | `dpkg-deb` | `sudo apt install dpkg` or `brew install dpkg` |
| `.rpm` | `rpmbuild` | `sudo dnf install rpm-build` or `brew install rpm` |

The build script skips any format whose tool is missing.

## Install & Run

```bash
# Debian / Ubuntu
sudo dpkg -i packaging/dist/spaceblack_1.0.0_all.deb

# Fedora / RHEL
sudo rpm -i packaging/dist/spaceblack-1.0.0-1.noarch.rpm

# Then launch the agent
ghost start
```

Setup (venv, dependencies, Playwright) happens automatically on first `ghost start`.

## Directory Structure

```
packaging/
├── build_packages.sh      # Master build script
├── ghost                   # CLI launcher (installed to /usr/local/bin/ghost)
├── README.md               # This file
├── deb/
│   └── DEBIAN/
│       ├── control         # Debian package metadata
│       ├── postinst        # Post-install script
│       └── prerm           # Pre-removal script
└── rpm/
    └── spaceblack.spec     # RPM spec file
```
