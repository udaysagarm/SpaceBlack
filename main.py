
import os
import sys
import subprocess
from textual.app import App
from brain.memory_manager import ensure_brain_initialized

CONFIG_FILE = "config.json"
ENV_FILE = ".env"

def main():
    """
    Main entry point.
    Checks if configuration exists.
    If not, runs setup_wizard.
    If yes, runs tui.py.
    """
    print("Checking configuration...")
    ensure_brain_initialized()
    
    # Check if config exists
    if not os.path.exists(CONFIG_FILE) or not os.path.exists(ENV_FILE):
        print("Configuration not found. Launching Setup Wizard...")
        
        # Run setup wizard
        # We run it as a subprocess to ensure clean environment or just import it?
        # Importing is better for flow, but Textual apps usually capture full screen.
        # Let's import and run.
        
        from setup_wizard import main as run_setup_wizard
        run_setup_wizard()
        
        # Check again if config was created
        if not os.path.exists(CONFIG_FILE):
            print("Setup did not complete. Exiting.")
            sys.exit(1)
            
        print("Setup complete. Starting Agent...")
    
    # Now run the main TUI
    # We can use subprocess to run "python tui.py" to ensure a fresh process 
    # and to properly load the new .env file we just wrote (if we rely on dotenv loading at startup)
    
    try:
        subprocess.run([sys.executable, "tui.py"])
    except KeyboardInterrupt:
        print("\nAgent stopped.")

if __name__ == "__main__":
    main()
