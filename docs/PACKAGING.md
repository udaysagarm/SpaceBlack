# Packaging Guide

Space Black can be distributed as `.deb` (Debian/Ubuntu) and `.rpm` (Fedora/RHEL) Linux packages.

## Building Packages

From the project root:

```bash
bash packaging/build_packages.sh
```

Packages are output to `packaging/dist/`:
-   `spaceblack_1.0.0_all.deb`
-   `spaceblack-1.0.0-1.noarch.rpm`

### Build Prerequisites

| Format | Tool       | Install                                        |
|--------|------------|------------------------------------------------|
| `.deb` | `dpkg-deb` | `sudo apt install dpkg` or `brew install dpkg` |
| `.rpm` | `rpmbuild` | `sudo dnf install rpm-build` or `brew install rpm` |

The build script automatically skips any format whose tool is not available.

---

## Installing Packages

### Debian / Ubuntu
```bash
sudo dpkg -i packaging/dist/spaceblack_1.0.0_all.deb
```

### Fedora / RHEL
```bash
sudo rpm -i packaging/dist/spaceblack-1.0.0-1.noarch.rpm
```

### After Installation
```bash
ghost start
```

On first run, `ghost start` automatically:
1.  Creates a Python virtual environment.
2.  Installs all pip dependencies.
3.  Downloads Playwright browser binaries.
4.  Launches the Ghost agent TUI.

---

## Package Details

| Property       | Value                        |
|----------------|------------------------------|
| Package Name   | `spaceblack`                 |
| Version        | `1.0.0`                      |
| Architecture   | `noarch` / `all` (pure Python) |
| Install Path   | `/opt/spaceblack/`           |
| CLI Command    | `/usr/local/bin/ghost`       |
| License        | MIT                          |
| Dependencies   | `python3 (>= 3.10)`, `python3-pip` |

## Uninstalling

### Debian / Ubuntu
```bash
sudo dpkg -r spaceblack
```

### Fedora / RHEL
```bash
sudo rpm -e spaceblack
```

This removes the application files and the `ghost` CLI. The virtual environment at `/opt/spaceblack/.venv` is cleaned up automatically.

---

## Directory Structure

```
packaging/
├── build_packages.sh      # Master build script
├── ghost                   # CLI launcher (→ /usr/local/bin/ghost)
├── README.md               # Quick reference
├── deb/
│   └── DEBIAN/
│       ├── control         # Debian metadata & dependencies
│       ├── postinst        # Post-install setup
│       └── prerm           # Pre-removal cleanup
└── rpm/
    └── spaceblack.spec     # RPM spec file
```
