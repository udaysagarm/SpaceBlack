
import json
import datetime
import os
from langchain_core.tools import tool
from brain.memory_manager import SCHEDULE_FILE, read_file_safe

@tool
def schedule_task(time_str: str, task: str, recurrence: str = None):
    """
    Schedules a task for future execution.
    Args:
        time_str: "YYYY-MM-DD HH:MM" (24-hour format). Example: "2026-02-09 14:30"
        task: Description of the task to perform.
        recurrence: Optional interval for repeating tasks. 
        Supports: "30s", "10m", "2h", "5d", "1w".
        Aliases: "daily" (1d), "weekly" (1w), "hourly" (1h).
    
    NOTE: If the user asks for a time that is "now" or "in 1 minute" or even slightly passed, 
    just schedule it. The system checks every minute.
    """
    try:
        # Validate format
        datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        
        current_content = read_file_safe(SCHEDULE_FILE, "[]")
        schedule = json.loads(current_content)
        
        entry = {"time": time_str, "task": task}
        if recurrence:
            entry["recurrence"] = recurrence
            
        schedule.append(entry)
        
        # Sort by time
        schedule.sort(key=lambda x: x["time"])
        
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(schedule, f, indent=4)
            
        msg = f"Task scheduled for {time_str}: {task}"
        if recurrence:
            msg += f" (Repeats: {recurrence})"
        return msg
    except ValueError:
        return "Error: Invalid time format. Please use 'YYYY-MM-DD HH:MM'."
    except Exception as e:
        return f"Scheduling failed: {str(e)}"

@tool
def cancel_task(task_query: str):
    """
    Cancels a scheduled task by matching the task description.
    Args:
        task_query: A string to match against the task description. 
                    e.g. "bitcoin" will cancel any task containing "bitcoin".
    """
    try:
        current_content = read_file_safe(SCHEDULE_FILE, "[]")
        schedule = json.loads(current_content)
        
        initial_count = len(schedule)
        # Filter out matching tasks
        new_schedule = []
        for item in schedule:
            should_remove = False
            query = task_query.lower()
            
            # 1. Check for "recurring" keyword
            if query in ["recurring", "repeating"] and "recurrence" in item:
                should_remove = True
            # 2. Check for "all" keyword
            elif query == "all":
                should_remove = True
            # 3. Check for substring match in task description
            elif query in item["task"].lower():
                should_remove = True
                
            if not should_remove:
                new_schedule.append(item)
        
        removed_count = initial_count - len(new_schedule)
        
        if removed_count == 0:
            return f"No tasks found matching query: '{task_query}'."
            
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(new_schedule, f, indent=4)
            
        return f"Cancelled {removed_count} task(s) matching '{task_query}'."
        
    except Exception as e:
        return f"Cancellation failed: {str(e)}"
