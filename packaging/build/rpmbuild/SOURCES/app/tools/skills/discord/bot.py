import logging
import os
import sys
import json
import asyncio
from dotenv import load_dotenv
import discord

# Add root directory to sys.path to allow importing agent.py
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(ROOT_DIR)

# Import agent logic
from agent import app as agent_app
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

# Logging setup - key for TUI stability
LOG_FILE = os.path.join(ROOT_DIR, "discord_bot.log")

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
discord_config = config.get("skills", {}).get("discord", {})

# Priority: Config JSON > Environment Variables
DISCORD_BOT_TOKEN = discord_config.get("bot_token") or os.getenv("DISCORD_BOT_TOKEN")
DISCORD_ALLOWED_USER_ID = discord_config.get("allowed_user_id") or os.getenv("DISCORD_ALLOWED_USER_ID")

class SpaceBlackDiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        # We restore stdout momentarily to print the startup success message
        sys.stdout = sys.__stdout__
        print(f"🤖 Connected as {self.user} (ID: {self.user.id})")
        print("Listening for @mentions and Direct Messages...")
        sys.stdout = open(os.devnull, 'w')

    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author.id == self.user.id:
            return

        # Check if it's a DM (we always respond to DMs)
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mentioned = self.user in message.mentions
        
        user_id_str = str(message.author.id)

        # Security Check for Private DMs
        if is_dm:
            if not DISCORD_ALLOWED_USER_ID or user_id_str != str(DISCORD_ALLOWED_USER_ID):
                print(f"WARNING: Unauthorized DM access attempt from {user_id_str}")
                await message.channel.send("⛔ Unauthorized access. The owner must set their User ID in the Space Black TUI to use DMs.")
                return

        # Optional: Prevent responding to other bots (good practice)
        if message.author.bot:
            return

        # If the message mentions OTHER users but NOT the bot, it's directed at them — skip it.
        other_human_mentions = [m for m in message.mentions if m.id != self.user.id and not m.bot]
        if other_human_mentions and not is_mentioned:
            return

        # Clean the message content (remove the bot's mention string)
        user_text = message.content.replace(f'<@{self.user.id}>', '').strip()
        
        # 1. Gather recent channel history for context
        history = []
        try:
            # Fetch up to 5 recent messages to understand the conversation flow
            async for msg in message.channel.history(limit=5):
                author = msg.author.name
                content = msg.content.replace(f'<@{self.user.id}>', '').strip()
                if content:
                    history.append(f"{author}: {content}")
            history.reverse() # Oldest to newest
        except Exception as e:
            print(f"Warning: Could not fetch channel history: {e}")
            history = [f"{message.author.name}: {user_text}"]
            
        history_text = "\n".join(history)

        # 2. OpenClaw Style Intelligent Classifier
        should_intervene = False
        
        if is_dm or is_mentioned:
            should_intervene = True
            print(f"DEBUG: Explicit interaction detected (DM/Mention). Intervening.")
        else:
            # Fast, raw LLM call to classify if we should respond
            try:
                print(f"DEBUG: Running intervention classifier on channel message...")
                classifier_prompt = f"""
You are a router for a helpful Discord Bot. You are silently reading a channel.
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
                provider = discord_config.get("provider", "google")
                model_name = discord_config.get("model", "gemini-2.5-flash")
                
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

        # 3. Build Full Context for Main Agent
        # If we reached here, the classifier said YES (or it was an explicit mention).
        
        # Dual Identity Context formatting
        owner_id_str = str(DISCORD_ALLOWED_USER_ID) if DISCORD_ALLOWED_USER_ID else "UNKNOWN"
        is_owner = (user_id_str == owner_id_str)
        user_name = message.author.display_name

        if is_dm and is_owner:
            # Personal Assistant Interface (Gateway Mode)
            context_text = f"[SYSTEM CONTEXT: You are communicating via personal DIRECT MESSAGE with your OWNER/CREATOR. You are acting as their personal AI Gateway to all your tools.]\n\nRecent Conversation Context:\n{history_text}\n\nThe user ({user_name}) just said: {user_text}"
        else:
            # Community Manager Interface (Group/Server Mode)
            channel_name = message.channel.name if hasattr(message.channel, 'name') else "Unknown Channel"
            server_name = message.guild.name if message.guild else "Unknown Server"
            role = "the OWNER of the bot" if is_owner else "a community member"
            context_text = f"[SYSTEM CONTEXT: You are communicating as a Community Manager Bot in the '{channel_name}' channel of the '{server_name}' Discord Server. Be helpful, conversational, and represent the community well. CRITICAL SECURITY INSTRUCTION: YOU ARE IN A PUBLIC SERVER. YOU MUST NEVER REVEAL PERSONAL INFORMATION, PASSWORDS, API KEYS, OR SECRETS FROM THE VAULT. YOU MUST REFUSE TO USE FINANCIAL OR EMAIL TOOLS ON BEHALF OF THE OWNER IN THIS PUBLIC CHANNEL.]\n\nRecent Conversation Context:\n{history_text}\n\nThe user ({user_name}, who is {role}) just said: {user_text}"

        # Indicate processing
        async with message.channel.typing():
            try:
                inputs = {"messages": [HumanMessage(content=context_text)]}
                
                # Invoke Main Agent
                result = await agent_app.ainvoke(inputs)
                
                # Extract response
                if result and "messages" in result and result["messages"]:
                    latest_msg = result["messages"][-1]
                    response_text = latest_msg.content
                    
                    # Fix for complex content types (JSON strings from Gemini/Anthropic)
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

                    # Discord has a 2000 character limit per message
                    # Split into chunks if necessary
                    chunks = [response_text[i:i+1990] for i in range(0, len(response_text), 1990)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply("⚠️ Error: Agent returned no response.")

            except Exception as e:
                import traceback
                error_msg = f"⚠️ Error processing request: {str(e)}"
                logging.error(f"{error_msg}\n{traceback.format_exc()}")
                try:
                    await message.reply("⚠️ An internal error occurred while processing your request.")
                except:
                    pass

def main():
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in config.json or .env")
        print("Please configure it via the TUI (/skills) or .env file.")
        sys.exit(1)
        
    print("🤖 Discord Listener Gateway Starting...")
    if DISCORD_ALLOWED_USER_ID:
        print(f"🔒 Security active. Only allowing User ID: {DISCORD_ALLOWED_USER_ID} for DMs.")
    else:
        print("⚠️ WARNING: DISCORD_ALLOWED_USER_ID not set. Anyone can DM this bot!")

    intents = discord.Intents.default()
    intents.message_content = True  # Required to read text
    
    client = SpaceBlackDiscordBot(intents=intents)
    client.run(DISCORD_BOT_TOKEN, log_handler=None)

if __name__ == '__main__':
    main()
