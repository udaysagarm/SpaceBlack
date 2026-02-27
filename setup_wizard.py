
import os
import json
import time
from brain.llm_factory import get_llm
from brain.provider_models import get_provider_list, get_chat_models, get_tts_models, get_stt_models, PROVIDERS
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()
CONFIG_FILE = "config.json"
ENV_FILE = ".env"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def save_config(provider: str, model: str, voice_provider: str, tts_model: str, stt_model: str, api_key: str, brave_key: str = None):
    # 1. Save config.json (preserving existing data like skills/tasks)
    config_data = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config_data = json.load(f)
        except Exception:
            pass

    config_data["provider"] = provider
    config_data["model"] = model
    config_data["voice_provider"] = voice_provider
    config_data["tts_model"] = tts_model
    config_data["stt_model"] = stt_model

    if "skills" not in config_data:
        config_data["skills"] = {
            "browser": {"enabled": True},
            "openweather": {"enabled": False, "api_key": ""},
            "telegram": {"enabled": False, "bot_token": "", "allowed_user_id": ""},
            "google": {"enabled": False, "credentials_json": ""},
            "macos": {"enabled": True}
        }

    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

    # 2. Update .env
    provider_data = PROVIDERS.get(provider, {})
    env_var = provider_data.get("env_var")

    # Read existing
    existing_lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            existing_lines = f.readlines()

    new_lines = existing_lines.copy()
    
    if env_var and api_key:
        new_lines = [line for line in new_lines if not line.startswith(f"{env_var}=")]
        new_lines.append(f"{env_var}={api_key}\n")
        os.environ[env_var] = api_key

    if brave_key:
        new_lines = [line for line in new_lines if not line.startswith("BRAVE_API_KEY=")]
        new_lines.append(f"BRAVE_API_KEY={brave_key}\n")
        os.environ["BRAVE_API_KEY"] = brave_key

    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)

def main():
    clear_screen()
    console.print(Panel.fit("[bold cyan]Space Black | Setup Wizard[/]", border_style="cyan"))
    console.print("Welcome! Let's get you connected to the AI.\n")

    # 1. Select Provider
    console.print("[bold]Step 1: Choose your AI Provider[/]")
    choices = list(PROVIDERS.keys())
    provider = Prompt.ask("Select Provider", choices=choices, default="google")
    
    provider_data = PROVIDERS.get(provider, {})

    # 2. Enter API Key
    api_key = ""
    env_var = provider_data.get("env_var")
    if env_var:
        console.print(f"\n[bold]Step 2: Enter {provider_data.get('name')} API Key[/]")
        api_key = Prompt.ask("API Key", password=True)
        if not api_key:
            console.print("[red]API Key is required![/]")
            return
    else:
        console.print(f"\n[bold]Step 2: {provider_data.get('name')} requires no API Key. Skipping.[/]")
    
    # 3. Model Name
    chat_models = get_chat_models(provider)
    default_model = chat_models[0] if chat_models else ""
    
    console.print(f"\n[bold]Step 3: Model Name[/]")
    if chat_models:
        console.print("Available models:")
        for idx, m in enumerate(chat_models):
            console.print(f"  {idx + 1}. {m}")
        
    model_name = Prompt.ask("Enter Model Name (or press Enter for default)", default=default_model)

    # 4. Voice Provider and Model
    console.print("\n[bold]Step 4: Voice Configuration[/]")
    voice_provider = Prompt.ask("Select Voice Provider", choices=choices, default=provider)
    tts_models = get_tts_models(voice_provider)
    default_tts = tts_models[0] if tts_models else ""
    
    if tts_models:
        console.print("Available TTS models:")
        for idx, m in enumerate(tts_models):
            console.print(f"  {idx + 1}. {m}")
            
    tts_model = Prompt.ask("Enter TTS Model Name (or press Enter for default)", default=default_tts)

    stt_models = get_stt_models(voice_provider)
    default_stt = stt_models[0] if stt_models else ""
    if stt_models:
        console.print("Available STT models:")
        for idx, m in enumerate(stt_models):
            console.print(f"  {idx + 1}. {m}")
    stt_model = Prompt.ask("Enter STT Model Name (or press Enter for default)", default=default_stt)

    # 5. Brave Search
    console.print("\n[bold]Step 5: Web Search[/]")
    brave_key = None
    if Confirm.ask("Do you have a Brave Search API Key?"):
        brave_key = Prompt.ask("Enter Brave Search API Key", password=True)

    # 6. Verify
    console.print("\n[yellow]Verifying credentials...[/]")
    try:
        llm = get_llm(provider, model_name, api_key=api_key)
        response = llm.invoke("Hello, are you online?")
        console.print(f"[green]Success![/] AI replied: [italic]\"{response.content}\"[/]")
    except Exception as e:
        console.print(f"[bold red]Verification Failed![/] {str(e)}")
        if not Confirm.ask("Save configuration anyway?"):
            console.print("[red]Setup aborted.[/]")
            return

    # 7. Save
    save_config(provider, model_name, voice_provider, tts_model, stt_model, api_key, brave_key)
    console.print("\n[bold green]Configuration Saved! 🚀[/]")
    console.print("\nYou can now run the agent with:\n[bold]python main.py[/]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Setup cancelled.[/]")
    except EOFError:
        console.print("\n[yellow]⚠️  Cannot read input (non-interactive terminal).[/]")
        console.print("[yellow]Please run [bold]ghost start[/bold] directly in your terminal.[/]")
