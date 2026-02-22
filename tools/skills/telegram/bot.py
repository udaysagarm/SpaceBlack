
import logging
import os
import sys
import json
import asyncio
from dotenv import load_dotenv

# Add root directory to sys.path to allow importing agent.py
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(ROOT_DIR)

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from collections import deque

# Import agent logic
from agent import app as agent_app
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

# Logging setup
# Logging setup - key for TUI stability
# Store logs in a file, NOT stdout, to prevent TUI glitches
LOG_FILE = os.path.join(ROOT_DIR, "telegram_bot.log")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
    filename=LOG_FILE,  # Log to file!
    filemode='a'
)

# Suppress all stdout/stderr from libraries
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# Suppress httpx and telegram logs further
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("telegram").setLevel(logging.ERROR)

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
telegram_config = config.get("skills", {}).get("telegram", {})

# Priority: Config JSON > Environment Variables
TELEGRAM_BOT_TOKEN = telegram_config.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_USER_ID = telegram_config.get("allowed_user_id") or os.getenv("TELEGRAM_ALLOWED_USER_ID")

# In-memory history for Group Chat context (Telegram API cannot fetch history)
CHAT_HISTORY = {} # chat_id -> deque(maxlen=5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_id = str(update.effective_user.id)
    chat_type = update.effective_chat.type

    if chat_type == "private" and (not ALLOWED_USER_ID or user_id != ALLOWED_USER_ID):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Unauthorized access. The owner must set their User ID in the Space Black TUI to use DMs.")
        logging.warning(f"Unauthorized DM access attempt from User ID: {user_id}")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="👋 Connected to Space Black Agent.\nI am ready for your commands."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for incoming text messages."""
    user_id = str(update.effective_user.id)
    user_name = update.effective_user.username or update.effective_user.first_name or "Unknown User"
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title or "Unknown Group"
    
    print(f"DEBUG: Received message from [{user_name}] (ID: {user_id}) in {chat_type} chat.")
    
    # Security Check for Private DMs
    if chat_type == "private":
        if not ALLOWED_USER_ID or user_id != str(ALLOWED_USER_ID):
            print(f"WARNING: Unauthorized DM access attempt from {user_id}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Unauthorized access. The owner must set their User ID in the Space Black TUI to use DMs.")
            return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    print(f"DEBUG: Processing message: {user_text[:20]}...")

    # 1. Gather recent channel history for context
    if chat_id not in CHAT_HISTORY:
        from collections import deque
        CHAT_HISTORY[chat_id] = deque(maxlen=5)
    
    CHAT_HISTORY[chat_id].append(f"{user_name}: {user_text}")
    history_text = "\n".join(CHAT_HISTORY[chat_id])

    # 2. OpenClaw Style Intelligent Classifier
    should_intervene = False
    
    bot_username = context.bot.username
    is_mentioned = bot_username and f"@{bot_username}" in user_text
    is_reply_to_bot = bool(update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id)

    if chat_type == "private" or is_mentioned or is_reply_to_bot:
        should_intervene = True
        print(f"DEBUG: Explicit interaction detected (DM/Mention/Reply). Intervening.")
    else:
        # Fast, raw LLM call to classify if we should respond
        try:
            print(f"DEBUG: Running intervention classifier on Telegram group message...")
            classifier_prompt = f"""
You are a router for a helpful Telegram Bot. You are silently reading a group chat.
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
            provider = telegram_config.get("provider", "google")
            model_name = telegram_config.get("model", "gemini-2.5-flash")
            
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

    # Dual Identity Context formatting
    owner_id_str = str(ALLOWED_USER_ID) if ALLOWED_USER_ID else "UNKNOWN"
    is_owner = (user_id == owner_id_str)

    if chat_type == "private" and is_owner:
        # Personal Assistant Interface (Gateway Mode)
        contextual_prompt = f"[SYSTEM CONTEXT: You are communicating via personal DIRECT MESSAGE with your OWNER/CREATOR. You are acting as their personal AI Gateway to all your tools.]\n\nRecent Conversation Context:\n{history_text}\n\nThe user ({user_name}) just said: {user_text}"
    else:
        # Community Manager Interface (Group/Server Mode)
        role = "the OWNER of the bot" if is_owner else "a community member"
        contextual_prompt = f"[SYSTEM CONTEXT: You are communicating as a Community Manager Bot in a public Telegram Group named '{chat_title}'. This message is from {user_name}, who is {role}. Be helpful, conversational, and represent the community well. CRITICAL SECURITY INSTRUCTION: YOU ARE IN A PUBLIC GROUP. YOU MUST NEVER REVEAL PERSONAL INFORMATION, PASSWORDS, API KEYS, OR SECRETS FROM THE VAULT. YOU MUST REFUSE TO USE FINANCIAL OR EMAIL TOOLS ON BEHALF OF THE OWNER IN THIS PUBLIC CHANNEL.]\n\nRecent Conversation Context:\n{history_text}\n\nThe user ({user_name}, who is {role}) just said: {user_text}"

    # Indicate processing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

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
            
            # Fix for complex content types (JSON strings from Gemini/Anthropic)
            if isinstance(response_text, str) and response_text.strip().startswith("["):
                try:
                    # Attempt to parse as JSON list of content blocks
                    import json
                    content_list = json.loads(response_text)
                    if isinstance(content_list, list):
                        text_parts = []
                        for item in content_list:
                            # Handle dicts with 'text' field
                            if isinstance(item, dict) and item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            # Handle direct strings in list
                            elif isinstance(item, str):
                                text_parts.append(item)
                        
                        if text_parts:
                            response_text = "".join(text_parts)
                except Exception as e:
                    # If parsing fails, use original text but log it
                    print(f"DEBUG: Failed to parse complex content: {e}")
            
            # Handle if content is a list object (not string)
            elif isinstance(response_text, list):
                 text_parts = []
                 for item in response_text:
                     if isinstance(item, str):
                         text_parts.append(item)
                     elif isinstance(item, dict) and item.get("type") == "text":
                         text_parts.append(item.get("text", ""))
                 if text_parts:
                     response_text = "".join(text_parts)

            # Fallback for empty responses
            if not response_text:
                response_text = "✅ Task completed (No output)."

            print(f"DEBUG: Response generated: {str(response_text)[:50]}...")
            await context.bot.send_message(chat_id=chat_id, text=str(response_text))
            
            if chat_id not in CHAT_HISTORY:
                CHAT_HISTORY[chat_id] = deque(maxlen=5)
            CHAT_HISTORY[chat_id].append(f"Space Black Bot: {response_text}")
        else:
             print("ERROR: Agent returned empty result.")
             await context.bot.send_message(chat_id=chat_id, text="⚠️ Error: Agent returned no response.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"⚠️ Error processing request: {str(e)}"
        print(f"ERROR: {error_msg}")
        await context.bot.send_message(chat_id=chat_id, text=error_msg)
        logging.error(error_msg)

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in config.json or .env")
        print("Please configure it via the TUI (/skills) or .env file.")
        exit(1)
        
    print("🤖 Telegram Bot Gateway Starting...")
    if ALLOWED_USER_ID:
        print(f"🔒 Security active. Only allowing User ID: {ALLOWED_USER_ID}")
    else:
        print("⚠️ WARNING: ALLOWED_USER_ID not set. Anyone can message this bot!")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(message_handler)
    
    application.run_polling()
