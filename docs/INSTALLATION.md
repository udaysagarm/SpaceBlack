# Installation Guide

Follow these steps to install and configure Space Black on your system.

## Prerequisites

-   **Python 3.10 or higher**: Ensure you have a modern version of Python installed.
-   **Git**: Required to clone the repository.
-   **Terminal**: 
    -   **Windows**: Recommended to use PowerShell or Windows Terminal.
    -   **Mac/Linux**: Default terminal is sufficient. Nerd Fonts are recommended for the best experience.

## Installation Steps

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/udaysagar/SpaceBlack.git
cd SpaceBlack
```

### 2. Run Setup
We provide a unified wrapper script to handle environment creation and dependency installation.

**Mac/Linux**
```bash
./spaceblack onboard
```

**Windows (PowerShell)**
```powershell
spaceblack onboard
```

The script will:
1.  Create a virtual environment (`.venv`).
2.  Install dependencies from `requirements.txt`.
3.  Launch the configuration wizard.

### 3. Start the Agent
Once installed, start the application using the same wrapper:

**Mac/Linux**
```bash
./spaceblack start
```

**Windows**
```powershell
spaceblack start
```

## Manual Configuration (Advanced)

If you prefer to configure the application manually, you can create the `.env` file yourself in the project root:

```tex
GOOGLE_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
BRAVE_API_KEY=your_key_here  # Optional
```

Once the `.env` file is created, running `python main.py` will skip the wizard and launch the TUI directly.
