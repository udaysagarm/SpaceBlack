from tools.vault import get_secret, set_secret, list_secrets, initialize_local_vault, unlock_local_vault, lock_local_vault
import os

print("--- Testing Keyring ---")
print(set_secret.invoke({"key": "test_key", "value": "test_value"}))
print("Get:", get_secret.invoke({"key": "test_key"}))

print("\n--- Testing Local Vault ---")
print("Init:", initialize_local_vault.invoke({"passphrase": "testpass"}))
print(set_secret.invoke({"key": "local_key", "value": "super_secret", "store_in_local_vault": True}))
print("List:", list_secrets.invoke({}))
print("Get:", get_secret.invoke({"key": "local_key"}))

print("Locking vault...")
print(lock_local_vault.invoke({}))
print("Get after lock:", get_secret.invoke({"key": "local_key"}))

print("Unlocking vault...")
print(unlock_local_vault.invoke({"passphrase": "testpass"}))
print("Get after unlock:", get_secret.invoke({"key": "local_key"}))
