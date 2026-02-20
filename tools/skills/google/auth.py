"""
auth.py — Shared Google OAuth2 Authentication Module for Space Black
Provides a single function `get_google_service` that all Google tools use.

Supports TWO methods of credential loading (in priority order):
1. credentials.json file path (set via /skills TUI menu)
2. Manual client_id + client_secret (set via /skills TUI menu)

Handles token refresh and triggers first-time browser consent flow.
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# All scopes needed across Gmail, Drive, Docs, Sheets, Calendar
ALL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
]

TOKEN_PATH = os.path.join("brain", "google_token.json")
CONFIG_FILE = "config.json"


def _load_google_config() -> dict:
    """Reads Google OAuth credentials from config.json."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config.get("skills", {}).get("google", {})
    except Exception:
        return {}


def _get_oauth_flow(google_config: dict, scopes: list) -> InstalledAppFlow:
    """
    Creates the OAuth2 flow using either:
    1. A credentials.json string (pasted directly into TUI)
    2. Manual client_id + client_secret from config.json
    """
    # Method 1: credentials.json raw content (preferred)
    credentials_json = google_config.get("credentials_json", "")
    if credentials_json:
        try:
            client_config = json.loads(credentials_json)
            return InstalledAppFlow.from_client_config(client_config, scopes)
        except json.JSONDecodeError:
            raise ValueError("Error parsing credentials JSON. Please ensure you pasted the valid file contents.")

    # Method 2: Manual client_id + client_secret
    client_id = google_config.get("client_id", "")
    client_secret = google_config.get("client_secret", "")

    if not client_id or not client_secret:
        raise ValueError(
            "Google OAuth credentials not configured. "
            "Please either paste the contents of your credentials.json file, "
            "or enter your Client ID and Client Secret via the /skills menu."
        )

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }
    return InstalledAppFlow.from_client_config(client_config, scopes)


def get_google_service(service_name: str, version: str, scopes: list = None):
    """
    Returns an authenticated Google API service client.

    Args:
        service_name: e.g. 'gmail', 'drive', 'docs', 'sheets', 'calendar'
        version: e.g. 'v1', 'v3', 'v4'
        scopes: Optional list of scopes. Defaults to ALL_SCOPES.

    Returns:
        googleapiclient.discovery.Resource
    """
    from googleapiclient.discovery import build

    if scopes is None:
        scopes = ALL_SCOPES

    creds = None

    # Load existing token
    if os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, scopes)
        except Exception:
            creds = None

    # Refresh or re-authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            # First-time authorization — opens browser
            google_config = _load_google_config()
            flow = _get_oauth_flow(google_config, scopes)
            creds = flow.run_local_server(port=0)

        # Save token for future use
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build(service_name, version, credentials=creds)
