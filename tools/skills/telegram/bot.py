
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the /start command."""
    user_id = str(update.effective_user.id)
    if ALLOWED_USER_ID and user_id != ALLOWED_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Unauthorized access.")
        logging.warning(f"Unauthorized access attempt from User ID: {user_id}")
        return

    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text="👋 Connected to Space Black Agent.\nI am ready for your commands."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for incoming text messages."""
    user_id = str(update.effective_user.id)
    
    print(f"DEBUG: Received message from ID: {user_id}")
    
    # Security Check
    if ALLOWED_USER_ID and user_id != str(ALLOWED_USER_ID):
        print(f"WARNING: Unauthorized access attempt from {user_id}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="⛔ Unauthorized access.")
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    print(f"DEBUG: Processing message: {user_text[:20]}...")

    # Indicate processing
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        inputs = {"messages": [HumanMessage(content=user_text)]}
        print(f"DEBUG: Invoking agent with inputs: {inputs}")
        
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
