import os
import json
from langchain_core.tools import tool

# Determine the brain/vault path
# Assumes this file is in project/tools/vault.py
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
VAULT_DIR = os.path.join(ROOT_DIR, "brain", "vault")
SECRETS_FILE = os.path.join(VAULT_DIR, "secrets.json")

def _load_secrets():
    """Helper to load secrets from JSON file."""
    if not os.path.exists(SECRETS_FILE):
        return {}
    try:
        with open(SECRETS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_secrets(secrets):
    """Helper to save secrets to JSON file securely."""
    if not os.path.exists(VAULT_DIR):
        os.makedirs(VAULT_DIR)
    
    with open(SECRETS_FILE, "w") as f:
        json.dump(secrets, f, indent=4)
        
    # Set permissions to read/write only by owner (600)
    try:
        os.chmod(SECRETS_FILE, 0o600)
    except:
        pass # Windows might fail here, that's okay

@tool
def get_secret(key: str) -> str:
    """
    Retrieves a secret value from the secure vault.
    Use this to get passwords, API keys, or other sensitive data.
    """
    secrets = _load_secrets()
    val = secrets.get(key)
    if val:
        return val
    return f"Secret '{key}' not found in vault."

@tool
def set_secret(key: str, value: str) -> str:
    """
    Saves a secret value to the secure vault.
    Use this to store user credentials, API keys, etc.
    The data is stored locally in brain/vault/secrets.json and is NOT git-tracked.
    """
    secrets = _load_secrets()
    secrets[key] = value
    _save_secrets(secrets)
    return f"Secret '{key}' saved successfully."

@tool
def list_secrets() -> str:
    """
    Lists the keys of all stored secrets (but NOT the values).
    Use this to see what credentials are available.
    """
    secrets = _load_secrets()
    keys = list(secrets.keys())
    if not keys:
        return "Vault is empty."
    return "Available Secrets:\n" + "\n".join([f"- {k}" for k in keys])
