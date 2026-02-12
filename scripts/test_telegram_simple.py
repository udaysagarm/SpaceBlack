
import logging
import os
import sys
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Add root directory to sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT_DIR)

# Load environment variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ Connection Successful! I am just a simple echo bot for testing.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Echo: {update.message.text}")

if __name__ == '__main__':
    print("--- SIMPLE TELEGRAM TEST ---")
    if not TELEGRAM_BOT_TOKEN:
        print("Error: No Token Found!")
        exit(1)
        
    print(f"Token: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    
    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    
    print("Polling started... Message the bot now.")
    application.run_polling()
