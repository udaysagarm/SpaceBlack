# Installation Guide

Follow these steps to get Space Black up and running on your machine.

## Prerequisites

-   **Python 3.10+**: Ensure you have a modern version of Python installed.
-   **Git**: To clone the repository.
-   **Terminal**: 
    -   **Windows**: Recommended to use PowerShell or Windows Terminal.
    -   **Mac/Linux**: Default terminal is fine. Nerd Fonts recommended for best experience.

## Step-by-Step Setup

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/udaysagar/SpaceBlack.git
cd SpaceBlack
```

### 2. Create a Virtual Environment (Recommended)
Isolate dependencies to avoid conflicts.
```bash
# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*Dependencies include `textual`, `langchain`, `langgraph`, `google-generativeai`, `openai`, `anthropic`, etc.*

### 4. Setup API Keys
The application needs API keys to function. On first run, it will look for a `.env` file.

You can copy the example or create one manually:
```bash
touch .env
```
Open `.env` in your editor and add:
```ini
# Primary AI Provider (Choose at least one)
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Web Search (Recommended for live info)
BRAVE_API_KEY=your_brave_search_key
```

### 5. Run the Application
```bash
python main.py
```
You should see the Terminal User Interface (TUI) launch!
