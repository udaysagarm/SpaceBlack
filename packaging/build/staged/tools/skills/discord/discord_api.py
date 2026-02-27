"""
discord_api.py — Space Black autonomous Discord Tool
Provides `discord_act` to send messages, manage channels, and interact with servers.
"""
import os
import requests
from typing import Optional
from langchain_core.tools import tool

# Constants
DISCORD_API_BASE = "https://discord.com/api/v10"

def _get_headers() -> dict:
    """Returns headers required for Discord API authentication."""
    token = None
    
    # Check config.json first (via TUI /skills menu)
    try:
        import json
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                config_data = json.load(f)
                token = config_data.get("skills", {}).get("discord", {}).get("bot_token")
    except Exception:
        pass
        
    # Fallback to .env
    if not token:
        token = os.environ.get("DISCORD_BOT_TOKEN")
        
    if not token:
        raise ValueError("Missing Discord Bot Token. Please add it via the /skills menu or set DISCORD_BOT_TOKEN in .env")
        
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

def _handle_response(resp: requests.Response) -> str:
    """Helper to consistently handle Discord JSON responses."""
    try:
        # Some endpoints return 204 No Content
        if resp.status_code == 204:
            return "Success (No Content)"
        data = resp.json()
        if resp.status_code >= 400:
            code = data.get("code", "Unknown")
            message = data.get("message", "Unknown Error")
            return f"Discord API Error ({resp.status_code}): {message} (Code: {code})"
        return str(data)
    except Exception:
        return f"HTTP {resp.status_code}: {resp.text}"

@tool
def discord_act(
    action: str,
    guild_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    message_id: Optional[str] = None,
    user_id: Optional[str] = None,
    content: Optional[str] = None,
    name: Optional[str] = None,
    emoji: Optional[str] = None
) -> str:
    """
    A unified tool for interacting with the Discord API via a Bot Token.
    
    Actions:
    — Messaging —
    - 'send_message': Send a message to a channel. (Requires 'channel_id', 'content')
    - 'get_messages': Fetch the 25 most recent messages in a channel. (Requires 'channel_id')
    - 'add_reaction': React to a message with an emoji. (Requires 'channel_id', 'message_id', 'emoji' e.g. '👍')
    - 'delete_message': Delete a specific message. (Requires 'channel_id', 'message_id')
    
    — Channels & Threads —
    - 'list_channels': List all channels in a server. (Requires 'guild_id')
    - 'create_channel': Create a new text channel. (Requires 'guild_id', 'name')
    - 'create_thread': Start a thread from a message. (Requires 'channel_id', 'message_id', 'name')
    
    — Server (Guild) Info —
    - 'list_guilds': List all servers the bot is in.
    - 'get_guild': Get server details. (Requires 'guild_id')
    - 'list_members': List members in a server. (Requires 'guild_id')
    
    — Direct Messages —
    - 'send_dm': Send a DM to a user. (Requires 'user_id', 'content')
    """
    try:
        headers = _get_headers()
    except Exception as e:
        return str(e)

    try:
        # ── MESSAGING ─────────────────────────────────────────────────────────
        if action == "send_message":
            if not channel_id or not content:
                return "Error: Missing 'channel_id' or 'content'."
            payload = {"content": content}
            resp = requests.post(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                headers=headers, json=payload
            )
            return _handle_response(resp)

        elif action == "get_messages":
            if not channel_id:
                return "Error: Missing 'channel_id'."
            resp = requests.get(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages?limit=25",
                headers=headers
            )
            data = resp.json()
            if resp.status_code >= 400:
                return _handle_response(resp)
            # Format messages for readability
            lines = []
            for msg in data:
                author = msg.get("author", {}).get("username", "Unknown")
                text = msg.get("content", "")
                ts = msg.get("timestamp", "")
                mid = msg.get("id", "")
                lines.append(f"[{ts}] {author} (id:{mid}): {text}")
            return "\n".join(lines) if lines else "No messages found."

        elif action == "add_reaction":
            if not channel_id or not message_id or not emoji:
                return "Error: Missing 'channel_id', 'message_id', or 'emoji'."
            # URL-encode the emoji for the path
            import urllib.parse
            encoded_emoji = urllib.parse.quote(emoji)
            resp = requests.put(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me",
                headers=headers
            )
            return _handle_response(resp)

        elif action == "delete_message":
            if not channel_id or not message_id:
                return "Error: Missing 'channel_id' or 'message_id'."
            resp = requests.delete(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}",
                headers=headers
            )
            return _handle_response(resp)

        # ── CHANNELS & THREADS ────────────────────────────────────────────────
        elif action == "list_channels":
            if not guild_id:
                return "Error: Missing 'guild_id'."
            resp = requests.get(
                f"{DISCORD_API_BASE}/guilds/{guild_id}/channels",
                headers=headers
            )
            data = resp.json()
            if resp.status_code >= 400:
                return _handle_response(resp)
            lines = []
            for ch in data:
                ch_type = {0: "text", 2: "voice", 4: "category", 5: "announcement", 13: "stage", 15: "forum"}.get(ch.get("type"), "other")
                lines.append(f"#{ch.get('name')} (id:{ch.get('id')}, type:{ch_type})")
            return "\n".join(lines) if lines else "No channels found."

        elif action == "create_channel":
            if not guild_id or not name:
                return "Error: Missing 'guild_id' or 'name'."
            payload = {"name": name, "type": 0}  # type 0 = text channel
            resp = requests.post(
                f"{DISCORD_API_BASE}/guilds/{guild_id}/channels",
                headers=headers, json=payload
            )
            return _handle_response(resp)

        elif action == "create_thread":
            if not channel_id or not message_id or not name:
                return "Error: Missing 'channel_id', 'message_id', or 'name'."
            payload = {"name": name}
            resp = requests.post(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/threads",
                headers=headers, json=payload
            )
            return _handle_response(resp)

        # ── SERVER (GUILD) INFO ───────────────────────────────────────────────
        elif action == "list_guilds":
            resp = requests.get(
                f"{DISCORD_API_BASE}/users/@me/guilds",
                headers=headers
            )
            data = resp.json()
            if resp.status_code >= 400:
                return _handle_response(resp)
            lines = []
            for g in data:
                lines.append(f"{g.get('name')} (id:{g.get('id')})")
            return "\n".join(lines) if lines else "Bot is not in any servers."

        elif action == "get_guild":
            if not guild_id:
                return "Error: Missing 'guild_id'."
            resp = requests.get(
                f"{DISCORD_API_BASE}/guilds/{guild_id}?with_counts=true",
                headers=headers
            )
            return _handle_response(resp)

        elif action == "list_members":
            if not guild_id:
                return "Error: Missing 'guild_id'."
            resp = requests.get(
                f"{DISCORD_API_BASE}/guilds/{guild_id}/members?limit=100",
                headers=headers
            )
            data = resp.json()
            if resp.status_code >= 400:
                return _handle_response(resp)
            lines = []
            for m in data:
                user = m.get("user", {})
                lines.append(f"{user.get('username')}#{user.get('discriminator', '0')} (id:{user.get('id')})")
            return "\n".join(lines) if lines else "No members found."

        # ── DIRECT MESSAGES ───────────────────────────────────────────────────
        elif action == "send_dm":
            if not user_id or not content:
                return "Error: Missing 'user_id' or 'content'."
            # Step 1: Create DM channel
            dm_resp = requests.post(
                f"{DISCORD_API_BASE}/users/@me/channels",
                headers=headers, json={"recipient_id": user_id}
            )
            if dm_resp.status_code >= 400:
                return f"Failed to open DM channel: {_handle_response(dm_resp)}"
            dm_channel_id = dm_resp.json().get("id")
            # Step 2: Send message
            payload = {"content": content}
            resp = requests.post(
                f"{DISCORD_API_BASE}/channels/{dm_channel_id}/messages",
                headers=headers, json=payload
            )
            return _handle_response(resp)

        else:
            return f"Error: Unknown action '{action}'"

    except Exception as e:
        import traceback
        return f"Discord Tool execution failed: {str(e)}\n{traceback.format_exc()}"
