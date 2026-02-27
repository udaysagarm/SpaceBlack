import os
import json
import keyring
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from langchain_core.tools import tool

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
VAULT_DIR = os.path.join(ROOT_DIR, "brain", "vault")
LOCAL_VAULT_FILE = os.path.join(VAULT_DIR, "secrets.enc")

KEYRING_SERVICE_NAME = "spaceblack_agent"

# Global state for the unlocked session
_UNLOCKED_FERNET = None
_LOCAL_VAULT_CACHE = None
_CURRENT_SALT = None

def _get_encryption_key(passphrase: str, salt: bytes) -> bytes:
    """Derives a secure symmetric key from the passphrase."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))

def _read_local_vault() -> dict:
    """Reads and decrypts the local vault."""
    global _UNLOCKED_FERNET, _LOCAL_VAULT_CACHE, _CURRENT_SALT
    if not os.path.exists(LOCAL_VAULT_FILE):
        return {}
    if not _UNLOCKED_FERNET:
        return {} # Can't read if locked
    
    if _LOCAL_VAULT_CACHE is not None:
        return _LOCAL_VAULT_CACHE
        
    try:
        with open(LOCAL_VAULT_FILE, "rb") as f:
            data = f.read()
            
        # Extract salt (first 16 bytes) and ciphertext
        salt = data[:16]
        ciphertext = data[16:]
        
        decrypted_data = _UNLOCKED_FERNET.decrypt(ciphertext)
        _LOCAL_VAULT_CACHE = json.loads(decrypted_data.decode("utf-8"))
        _CURRENT_SALT = salt
        return _LOCAL_VAULT_CACHE
    except InvalidToken:
        return {} # Wrong password or corrupted
    except Exception as e:
        print(f"Error reading vault: {e}")
        return {}

def _write_local_vault(secrets: dict) -> bool:
    """Encrypts and writes the local vault."""
    global _UNLOCKED_FERNET, _LOCAL_VAULT_CACHE, _CURRENT_SALT
    if not os.path.exists(VAULT_DIR):
        os.makedirs(VAULT_DIR, exist_ok=True)
        
    if not _UNLOCKED_FERNET or not _CURRENT_SALT:
        return False
        
    try:
        plaintext = json.dumps(secrets).encode("utf-8")
        ciphertext = _UNLOCKED_FERNET.encrypt(plaintext)
        
        with open(LOCAL_VAULT_FILE, "wb") as f:
            f.write(_CURRENT_SALT + ciphertext)
            
        # Set permissions securely
        if os.name != "nt":
            os.chmod(LOCAL_VAULT_FILE, 0o600)
            
        _LOCAL_VAULT_CACHE = secrets
        return True
    except Exception as e:
        print(f"Error writing vault: {e}")
        return False

@tool
def initialize_local_vault(passphrase: str) -> str:
    """
    Initializes a new encrypted local vault with the given passphrase.
    WARNING: This will overwrite any existing local vault!
    Use this only when setting up a new vault.
    """
    global _UNLOCKED_FERNET, _LOCAL_VAULT_CACHE, _CURRENT_SALT
    try:
        salt = os.urandom(16)
        key = _get_encryption_key(passphrase, salt)
        _UNLOCKED_FERNET = Fernet(key)
        _LOCAL_VAULT_CACHE = {}
        _CURRENT_SALT = salt
        
        success = _write_local_vault({})
        if success:
            return "Local vault initialized and unlocked successfully."
        else:
            return "Failed to initialize local vault."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def unlock_local_vault(passphrase: str) -> str:
    """
    Unlocks the local encrypted vault for the current session.
    Provides access to secrets stored in the local file fallback.
    """
    global _UNLOCKED_FERNET, _LOCAL_VAULT_CACHE, _CURRENT_SALT
    if not os.path.exists(LOCAL_VAULT_FILE):
        return "Local vault does not exist. Initialize it first."
        
    try:
        with open(LOCAL_VAULT_FILE, "rb") as f:
            salt = f.read(16)
            
        key = _get_encryption_key(passphrase, salt)
        temp_fernet = Fernet(key)
        
        # Test decryption
        with open(LOCAL_VAULT_FILE, "rb") as f:
            ciphertext = f.read()[16:]
            
        decrypted = temp_fernet.decrypt(ciphertext)
        
        # If successful, set globals
        _UNLOCKED_FERNET = temp_fernet
        _LOCAL_VAULT_CACHE = json.loads(decrypted.decode("utf-8"))
        _CURRENT_SALT = salt
        return "Local vault unlocked successfully."
    except InvalidToken:
        return "Incorrect passphrase. Failed to unlock local vault."
    except Exception as e:
        return f"Error unlocking vault: {str(e)}"

@tool
def lock_local_vault() -> str:
    """
    Locks the local encrypted vault, clearing the decryption keys from memory.
    """
    global _UNLOCKED_FERNET, _LOCAL_VAULT_CACHE, _CURRENT_SALT
    _UNLOCKED_FERNET = None
    _LOCAL_VAULT_CACHE = None
    _CURRENT_SALT = None
    return "Local vault locked securely."

@tool
def get_secret(key: str) -> str:
    """
    Retrieves a secret value. 
    Checks the OS-native Keychain first. If not found, checks the unlocked local encrypted vault.
    Use this to get passwords, API keys, or other sensitive data during tasks.
    """
    # 1. Try OS Native Keyring
    try:
        val = keyring.get_password(KEYRING_SERVICE_NAME, key)
        if val:
            return val
    except Exception as e:
        pass # Fallback to local vault
        
    # 2. Try Local Encrypted Vault
    global _UNLOCKED_FERNET
    if _UNLOCKED_FERNET:
        secrets = _read_local_vault()
        if key in secrets:
            return secrets[key]
        return f"Secret '{key}' not found in Keyring or Local Vault."
    else:
        return f"Secret '{key}' not found in Keyring. Local vault is locked or uninitialized."

@tool
def set_secret(key: str, value: str, store_in_local_vault: bool = False) -> str:
    """
    Saves a secret value securely.
    By default, stores in the OS-native Keychain (Credential Manager/Keychain Access).
    If store_in_local_vault is True, it stores it in the encrypted local vault file instead 
    (must be unlocked first).
    """
    if store_in_local_vault:
        global _UNLOCKED_FERNET
        if not _UNLOCKED_FERNET:
            return "Cannot store in local vault: Vault is locked. Use unlock_local_vault first."
            
        secrets = _read_local_vault()
        secrets[key] = value
        success = _write_local_vault(secrets)
        if success:
            return f"Secret '{key}' saved successfully in Encrypted Local Vault."
        else:
            return f"Failed to save secret '{key}' to Local Vault."
    else:
        try:
            keyring.set_password(KEYRING_SERVICE_NAME, key, value)
            return f"Secret '{key}' saved successfully in OS-Native Keyring."
        except Exception as e:
            return f"Failed to save to OS Keyring: {str(e)}. You can try storing in local vault instead."

@tool
def list_secrets() -> str:
    """
    Lists the keys of all stored secrets in the unlocked local vault.
    NOTE: For security and OS limitations, this may not list all secrets in the OS Keyring.
    """
    messages = []
    
    # OS Keyring listing is poorly supported across platforms, so we only list local vault keys reliably
    # We could attempt to list them on some backends but it's often disabled.
    messages.append("OS Keyring: (Listing keys is restricted by OS)")
    
    global _UNLOCKED_FERNET
    if _UNLOCKED_FERNET:
        secrets = _read_local_vault()
        keys = list(secrets.keys())
        if keys:
            messages.append("Local Encrypted Vault (Unlocked):\n" + "\n".join([f"- {k}" for k in keys]))
        else:
            messages.append("Local Encrypted Vault is empty.")
    else:
        messages.append("Local Encrypted Vault is [LOCKED].")
        
    return "\n".join(messages)
