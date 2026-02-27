import os
import requests
import json
from langchain_core.tools import tool
from dotenv import load_dotenv

# Load env in case it wasn't loaded
load_dotenv()

@tool
def send_telegram_message(message: str, chat_id: str = None):
    """
    Sends a message to the user via Telegram.
    Args:
        message: The text content to send.
        chat_id: (Optional) The Chat ID to send to. Defaults to TELEGRAM_CHAT_ID or TELEGRAM_ALLOWED_USER_ID from env.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        # Try to load from config.json as fallback
        try:
             with open("config.json", "r") as f:
                 config = json.load(f)
                 token = config.get("skills", {}).get("telegram", {}).get("bot_token")
        except: pass
        
    if not token:
        return "Error: TELEGRAM_BOT_TOKEN is not set. Please configure it in .env or config.json."

    # Determine Chat ID
    # Priority: Argument > Env (CHAT_ID) > Env (ALLOWED_USER) > Config (allowed_user_id)
    target_chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_ALLOWED_USER_ID")
    
    if not target_chat_id:
        try:
             with open("config.json", "r") as f:
                 config = json.load(f)
                 target_chat_id = config.get("skills", {}).get("telegram", {}).get("allowed_user_id")
        except: pass
        
    if not target_chat_id:
        return "Error: No chat_id provided and TELEGRAM_CHAT_ID/TELEGRAM_ALLOWED_USER_ID not set in env or config.json."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return f"Message sent successfully to {target_chat_id}."
    except requests.exceptions.HTTPError as e:
        return f"Failed to send Telegram message. HTTP Error: {e}"
    except Exception as e:
        return f"Failed to send Telegram message. Error: {e}"
