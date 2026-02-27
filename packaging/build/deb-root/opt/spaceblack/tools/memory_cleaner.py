import os
import re

def clean_memory_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"Cleaning {filepath}...")
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    last_content = ""
    hidden_count = 0

    for line in lines:
        # Extract content after timestamp
        # Format: [HH:MM:SS] Content...
        match = re.match(r"\[.*?\] (.*)", line)
        if match:
            content = match.group(1).strip()
            
            # Smart Filter for "Gathering user information"
            if "Gathering user information" in content:
                if "Gathering user information" in last_content:
                    hidden_count += 1
                    continue
            
            # Generic Deduplication
            if content == last_content:
                hidden_count += 1
                continue

            last_content = content
            new_lines.append(line)
        else:
            new_lines.append(line)

    with open(filepath, 'w') as f:
        f.writelines(new_lines)
    
    if hidden_count > 0:
        print(f"✅ Removed {hidden_count} duplicate lines.")
    else:
        print("✨ File was already clean.")

if __name__ == "__main__":
    # Clean all files in brain/memory
    memory_dir = "brain/memory"
    if os.path.exists(memory_dir):
        for filename in os.listdir(memory_dir):
            if filename.endswith(".md"):
                clean_memory_file(os.path.join(memory_dir, filename))
    else:
        print("No memory directory found.")
