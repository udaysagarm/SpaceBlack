
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
    
    # Print "Space Black" banner (Simulating figlet)
    # Color: \033[38;2;27;242;34m (Green)
    banner = """
\033[38;2;27;242;34m
  ____                         ____  _            _      
 / ___| _ __   __ _  ___ ___  | __ )| | __ _  ___| | __ 
 \___ \| '_ \ / _` |/ __/ _ \ |  _ \| |/ _` |/ __| |/ / 
  ___) | |_) | (_| | (_|  __/ | |_) | | (_| | (__|   <  
 |____/| .__/ \__,_|\___\___| |____/|_|\__,_|\___|_|\_\\
       |_|                                              
\033[0m"""
    print(banner)
    print("System: Ghost initialised.")

    # Process Management
    processes = []

    # 1. Start Telegram Bot if enabled
    try:
        import json
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            
        tg_config = config.get("skills", {}).get("telegram", {})
        if tg_config.get("enabled"):
            print("🚀 Launching Telegram Bot...")
            # Use sys.executable to ensure same venv
            # bot.py is in tools/skills/telegram/bot.py
            bot_path = os.path.join("tools", "skills", "telegram", "bot.py")
            if os.path.exists(bot_path):
                 # Run in background
                 p = subprocess.Popen([sys.executable, bot_path])
                 processes.append(p)
                 print(f"   Telegram Bot PID: {p.pid}")
            else:
                 print(f"⚠️  Telegram Bot script not found at {bot_path}")
    except Exception as e:
        print(f"⚠️  Failed to launch background skills: {e}")

    # 2. Start TUI (Blocking)
    try:
        subprocess.run([sys.executable, "tui.py"])
    except KeyboardInterrupt:
        print("\nAgent stopped.")
    finally:
        # Cleanup background processes
        print("\nStopping background services...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=2)
            except:
                p.kill()
        print("Goodbye.")

if __name__ == "__main__":
    main()
