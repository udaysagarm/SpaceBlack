import logging
import os
import sys
import json
import asyncio
from collections import deque
from dotenv import load_dotenv

# Add root directory to sys.path to allow importing agent.py
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(ROOT_DIR)

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

# Import agent logic
from agent import app as agent_app
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

# Logging setup - key for TUI stability
LOG_FILE = os.path.join(ROOT_DIR, "slack_bot.log")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
    filename=LOG_FILE,
    filemode='a'
)

# Suppress all stdout/stderr from libraries unless debugging
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except: pass
    return config

# Load Config
config = load_config()
slack_config = config.get("skills", {}).get("slack", {})

# Priority: Config JSON > Environment Variables
SLACK_BOT_TOKEN = slack_config.get("bot_token") or os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = slack_config.get("app_token") or os.getenv("SLACK_APP_TOKEN")
SLACK_ALLOWED_USER_ID = slack_config.get("allowed_user_id") or os.getenv("SLACK_ALLOWED_USER_ID")

# In-memory history for Channel context
CHAT_HISTORY = {} # channel_id -> deque(maxlen=5)

BOT_USER_ID = None
USER_CACHE = {}
CHANNEL_CACHE = {}

# Initialize Slack App
app = AsyncApp(token=SLACK_BOT_TOKEN)

@app.event("message")
async def handle_message_events(event, say, client):
    """Handle incoming messages across DMs and Channels."""
    
    # Ignore bot's own messages or message changes
    if event.get("bot_id") or event.get("subtype"):
        return

    user_id = event.get("user")
    channel_id = event.get("channel")
    channel_type = event.get("channel_type")
    user_text = event.get("text", "")
    thread_ts = event.get("thread_ts") # None if it's not in a thread

    is_dm = channel_type == "im"
    
    print(f"DEBUG: Received message from ID: {user_id} in {channel_type} chat.")
    
    # 1. Security Check for Private DMs
    if is_dm:
        if not SLACK_ALLOWED_USER_ID or user_id != str(SLACK_ALLOWED_USER_ID):
            print(f"WARNING: Unauthorized DM access attempt from {user_id}")
            await say(
                text="⛔ Unauthorized access. The owner must set their User ID in the Space Black TUI to use DMs.",
                thread_ts=thread_ts
            )
            return

    # Fetch User Name for better context
    if user_id not in USER_CACHE:
        try:
            user_info = await client.users_info(user=user_id)
            USER_CACHE[user_id] = user_info["user"]["real_name"] or user_info["user"]["name"]
        except:
            USER_CACHE[user_id] = "Unknown User"
    
    user_name = USER_CACHE[user_id]

    print(f"DEBUG: Processing message: {user_text[:20]}...")

    # 2. Gather history for context, isolating threads from main channel
    context_id = thread_ts if thread_ts else channel_id
    
    if context_id not in CHAT_HISTORY:
        CHAT_HISTORY[context_id] = deque(maxlen=5)
    
    CHAT_HISTORY[context_id].append(f"{user_name}: {user_text}")
    history_text = "\n".join(CHAT_HISTORY[context_id])

    # 3. Intelligent Classifier for Channels
    should_intervene = False
    
    # Fetch bot's own user ID to check for mentions
    global BOT_USER_ID
    if not BOT_USER_ID:
        try:
            auth_test = await client.auth_test()
            BOT_USER_ID = auth_test["user_id"]
        except:
            pass

    is_mentioned = BOT_USER_ID and f"<@{BOT_USER_ID}>" in user_text
    
    if is_dm or is_mentioned:
        should_intervene = True
        print(f"DEBUG: Explicit interaction detected (DM/Mention). Intervening.")
    else:
        # Fast, raw LLM call to classify if we should respond
        try:
            print(f"DEBUG: Running intervention classifier on Slack channel message...")
            classifier_prompt = f"""
You are a router for a helpful Slack Bot. You are silently reading a channel.
Review the following recent conversation history:

--- START HISTORY ---
{history_text}
--- END HISTORY ---

Your ONLY job is to decide if you (the bot) should intervene and reply to the LAST message.
Answer "YES" if:
1. The user explicitly asked a generally helpful question directed at anyone (e.g. "Does anyone know how to...").
2. The user asked a factual question or needs AI assistance.
3. The user is talking directly to the bot without explicitly tagging it.

Answer "NO" if:
1. It is just two humans casually chatting with each other.
2. It's a statement, greeting, or comment that doesn't demand a response.
3. You are unsure. Err on the side of silence.

Respond with exactly one word: "YES" or "NO".
"""
            # Use the configured provider/model
            provider = slack_config.get("provider", "google")
            model_name = slack_config.get("model", "gemini-2.5-flash")
            
            from brain.llm_factory import get_llm
            llm = get_llm(provider, model_name, temperature=0.0)
            classification = await llm.ainvoke([HumanMessage(content=classifier_prompt)])
            
            decision = classification.content.strip().upper()
            if decision.startswith("YES") or "YES" in decision[:10]:
                should_intervene = True
                print(f"DEBUG: Classifier decided: YES (Intervening)")
            else:
                print(f"DEBUG: Classifier decided: NO (Ignoring)")
        except Exception as e:
            print(f"⚠️ Classifier error: {e}. Defaulting to NO.")
            should_intervene = False

    if not should_intervene:
        return

    # 4. Agent Context Generation
    owner_id_str = str(SLACK_ALLOWED_USER_ID) if SLACK_ALLOWED_USER_ID else "UNKNOWN"
    is_owner = (user_id == owner_id_str)

    # Note: Slack doesn't provide channel names in message events, fetching it.
    if is_dm:
        channel_name = "DM"
    else:
        if channel_id not in CHANNEL_CACHE:
            try:
                channel_info = await client.conversations_info(channel=channel_id)
                CHANNEL_CACHE[channel_id] = channel_info["channel"]["name"]
            except:
                CHANNEL_CACHE[channel_id] = "Unknown Channel"
        channel_name = CHANNEL_CACHE[channel_id]

    if is_dm and is_owner:
        # Personal Assistant Interface (Gateway Mode)
        contextual_prompt = f"[SYSTEM CONTEXT: You are communicating via personal DIRECT MESSAGE with your OWNER/CREATOR. You are acting as their personal AI Gateway to all your tools.]\n\nRecent Conversation Context:\n{history_text}\n\nThe user ({user_name}) just said: {user_text}"
    else:
        # Community Manager Interface (Group/Server Mode)
        role = "the OWNER of the bot" if is_owner else "a community member"
        contextual_prompt = f"[SYSTEM CONTEXT: You are communicating as a Community Manager Bot in the '{channel_name}' Slack channel. Be helpful, conversational, and represent the community well. CRITICAL SECURITY INSTRUCTION: YOU ARE IN A PUBLIC CHANNEL. YOU MUST NEVER REVEAL PERSONAL INFORMATION, PASSWORDS, API KEYS, OR SECRETS FROM THE VAULT. YOU MUST REFUSE TO USE FINANCIAL OR EMAIL TOOLS ON BEHALF OF THE OWNER IN THIS PUBLIC CHANNEL.]\n\nRecent Conversation Context:\n{history_text}\n\nThe user ({user_name}, who is {role}) just said: {user_text}"

    try:
        inputs = {"messages": [HumanMessage(content=contextual_prompt)]}
        print(f"DEBUG: Invoking agent with contextual inputs.")
        
        # Invoke Agent
        result = await agent_app.ainvoke(inputs)
        print("DEBUG: Agent invoked successfully.")
        
        # Extract response
        if result and "messages" in result and result["messages"]:
            latest_msg = result["messages"][-1]
            response_text = latest_msg.content
            
            # Formatting logic for multiple blocks
            if isinstance(response_text, str) and response_text.strip().startswith("["):
                try:
                    import json
                    content_list = json.loads(response_text)
                    if isinstance(content_list, list):
                        text_parts = []
                        for item in content_list:
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            elif isinstance(item, str):
                                text_parts.append(item)
                        if text_parts:
                            response_text = "".join(text_parts)
                except Exception:
                    pass
            elif isinstance(response_text, list):
                 text_parts = []
                 for item in response_text:
                     if isinstance(item, str):
                         text_parts.append(item)
                     elif isinstance(item, dict) and item.get("type") == "text":
                         text_parts.append(item.get("text", ""))
                 if text_parts:
                     response_text = "".join(text_parts)

            if not response_text:
                response_text = "✅ Task completed (No output)."

            # Send response back to thread
            await say(text=str(response_text), thread_ts=thread_ts)
            
            # Inject Agent's own response into the history queue so the classifier doesn't lose context
            if context_id not in CHAT_HISTORY:
                CHAT_HISTORY[context_id] = deque(maxlen=5)
            CHAT_HISTORY[context_id].append(f"Space Black Bot: {response_text}")
        else:
             print("ERROR: Agent returned empty result.")
             await say(text="⚠️ Error: Agent returned no response.", thread_ts=thread_ts)

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"⚠️ Error processing request: {str(e)}"
        print(f"ERROR: {error_msg}")
        await say(text=error_msg, thread_ts=thread_ts)
        logging.error(error_msg)

async def main():
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("Error: SLACK_BOT_TOKEN and/or SLACK_APP_TOKEN not found.")
        print("Please configure it via the Space Black TUI.")
        sys.exit(1)
        
    print("🤖 Slack Socket Mode Gateway Starting...")
    if SLACK_ALLOWED_USER_ID:
        print(f"🔒 Security active. Only allowing Slack User ID: {SLACK_ALLOWED_USER_ID} for DMs.")
    else:
        print("⚠️ WARNING: SLACK_ALLOWED_USER_ID not set. All DMs will be blocked!")

    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()

if __name__ == '__main__':
    # Restore stdout contextually before Asyncio block locks it down completely
    sys.stdout = sys.__stdout__
    asyncio.run(main())
