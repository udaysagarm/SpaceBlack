
import json
import datetime
import os
from langchain_core.tools import tool
from brain.memory_manager import SCHEDULE_FILE, read_file_safe

@tool
def schedule_task(time_str: str, task: str):
    """
    Schedules a task for future execution.
    Args:
        time_str: "YYYY-MM-DD HH:MM" (24-hour format). Example: "2026-02-09 14:30"
        task: Description of the task to perform.
    
    NOTE: If the user asks for a time that is "now" or "in 1 minute" or even slightly passed, 
    just schedule it. The system checks every minute and will execute overdue tasks immediately.
    """
    try:
        # Validate format
        datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        
        current_content = read_file_safe(SCHEDULE_FILE, "[]")
        schedule = json.loads(current_content)
        
        schedule.append({"time": time_str, "task": task})
        
        # Sort by time
        schedule.sort(key=lambda x: x["time"])
        
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(schedule, f, indent=4)
            
        return f"Task scheduled for {time_str}: {task}"
    except ValueError:
        return "Error: Invalid time format. Please use 'YYYY-MM-DD HH:MM'."
    except Exception as e:
        return f"Scheduling failed: {str(e)}"
