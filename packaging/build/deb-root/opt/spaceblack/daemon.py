import time
import sys
import os
import signal
from agent import app, run_autonomous_heartbeat
from brain.memory_manager import read_file_safe, BRAIN_DIR
import datetime

# Daemon configuration
LOOP_INTERVAL = 60  # Check every 60 seconds

def log_daemon(message):
    """
    Logs daemon activity to a dedicated file.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(BRAIN_DIR, "daemon.log")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def run_daemon():
    """
    Main loop for the background daemon.
    """
    log_daemon("👻 Space Black Daemon Started. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Run the heartbeat check
            # This checks SCHEDULE.json and HEARTBEAT.md
            result = run_autonomous_heartbeat()
            
            if result:
                log_daemon(f"❤️  Heartbeat Triggered:\n{result}")
                
                # Create a message to feed into the agent
                # This simulates a "System" or "Scheduler" message
                from langchain_core.messages import HumanMessage
                
                # We treat the heartbeat result as a user prompt
                # e.g. "Scheduled Task Due: Check emails"
                message = HumanMessage(content=result)
                
                # Invoke the graph!
                log_daemon("🚀 Executing Agent Workflow...")
                final_state = app.invoke({"messages": [message]})
                
                # Log the result
                last_msg = final_state["messages"][-1]
                log_daemon(f"✅ Agent Response: {last_msg.content}")
                
            time.sleep(LOOP_INTERVAL)
            
    except KeyboardInterrupt:
        log_daemon("🛑 Daemon stopped by user.")
        sys.exit(0)
    except Exception as e:
        log_daemon(f"🔥 Daemon crashed: {e}")
        # Build robustness: Wait a bit and retry? 
        # For now, exit to avoid loop spam
        sys.exit(1)

if __name__ == "__main__":
    run_daemon()
