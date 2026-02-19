
import time
import json
import os
from agent import run_autonomous_heartbeat, HEARTBEAT_STATE_FILE

print(f"Current time: {time.time()}")
print(f"State file before: {HEARTBEAT_STATE_FILE}")
if os.path.exists(HEARTBEAT_STATE_FILE):
    with open(HEARTBEAT_STATE_FILE, 'r') as f:
        print(f"Content before: {f.read()}")

result = run_autonomous_heartbeat()
print(f"Result: {result}")

if os.path.exists(HEARTBEAT_STATE_FILE):
    with open(HEARTBEAT_STATE_FILE, 'r') as f:
        print(f"Content after: {f.read()}")
