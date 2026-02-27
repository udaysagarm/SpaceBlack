
import os
from langchain_core.tools import tool

@tool
def read_file(path: str):
    """
    Reads the content of a file from the local file system.
    
    Args:
        path (str): The absolute or relative path to the file.
    
    Returns:
        str: The content of the file, or an error message if reading fails.
    """
    try:
        # Resolve path
        abs_path = os.path.abspath(path)
        
        if not os.path.exists(abs_path):
            return f"Error: File not found at {abs_path}"
            
        if not os.path.isfile(abs_path):
            return f"Error: Path exists but is not a file: {abs_path}"
            
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return content
    except UnicodeDecodeError:
        return f"Error: File at {abs_path} appears to be binary or non-text."
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def write_file(path: str, content: str):
    """
    Writes content to a file. Overwrites if the file exists.
    
    Args:
        path (str): The absolute or relative path to the file.
        content (str): The text content to write.
    
    Returns:
        str: A success message or error description.
    """
    try:
        # Resolve path
        abs_path = os.path.abspath(path)
        directory = os.path.dirname(abs_path)
        
        # Ensure parent directory exists
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return f"Successfully wrote to {abs_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def list_directory(path: str = "."):
    """
    Lists the files and subdirectories in a given directory.
    
    Args:
        path (str): The directory path to list (defaults to current directory).
    
    Returns:
        str: A formatted list of file names and types.
    """
    try:
        abs_path = os.path.abspath(path)
        
        if not os.path.exists(abs_path):
            return f"Error: Directory not found at {abs_path}"
            
        if not os.path.isdir(abs_path):
            return f"Error: Path is not a directory: {abs_path}"
            
        items = os.listdir(abs_path)
        items.sort()
        
        result = [f"Directory listing for {abs_path}:\n"]
        
        for item in items:
            item_path = os.path.join(abs_path, item)
            if os.path.isdir(item_path):
                result.append(f"[DIR]  {item}")
            else:
                result.append(f"[FILE] {item}")
                
        return "\n".join(result)
        
    except Exception as e:
        return f"Error listing directory: {str(e)}"
