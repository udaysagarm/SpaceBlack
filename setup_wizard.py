
import os
import json
import time
from brain.llm_factory import get_llm
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()
CONFIG_FILE = "config.json"
ENV_FILE = ".env"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def save_config(provider, model_name, api_key, brave_key):
    # 1. Save config.json
    config_data = {
        "provider": provider,
        "model": model_name,
        "skills": {
            "browser": {
                "enabled": True
            },
            "openweather": {
                "enabled": False,
                "api_key": ""
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "allowed_user_id": ""
            },
            "google": {
                "enabled": False,
                "credentials_json": ""
            },
            "macos": {
                "enabled": True
            }
        }
    }
    # Persist search provider if it was already there, or default to brave
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                existing = json.load(f)
                if "search_provider" in existing:
                    config_data["search_provider"] = existing["search_provider"]
        except: pass

    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

    # 2. Update .env
    env_var_map = {
        "google": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY"
    }
    env_var = env_var_map.get(provider)

    # Read existing
    existing_lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            existing_lines = f.readlines()

    # Filter out old key for this provider
    new_lines = [line for line in existing_lines if not line.startswith(f"{env_var}=")]
    new_lines.append(f"{env_var}={api_key}\n")

    if brave_key:
        new_lines = [line for line in new_lines if not line.startswith("BRAVE_API_KEY=")]
        new_lines.append(f"BRAVE_API_KEY={brave_key}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)
    
    # Update current env for verification usage
    os.environ[env_var] = api_key
    if brave_key:
        os.environ["BRAVE_API_KEY"] = brave_key

def main():
    clear_screen()
    console.print(Panel.fit("[bold cyan]Space Black | Setup Wizard[/]", border_style="cyan"))
    console.print("Welcome! Let's get you connected to the AI.\n")

    # 1. Select Provider
    console.print("[bold]Step 1: Choose your AI Provider[/]")
    choices = ["google", "anthropic", "openai"]
    provider = Prompt.ask("Select Provider", choices=choices, default="google")

    # 2. Enter API Key
    console.print(f"\n[bold]Step 2: Enter {provider.capitalize()} API Key[/]")
    api_key = Prompt.ask("API Key", password=True)
    if not api_key:
        console.print("[red]API Key is required![/]")
        return
    
    # 3. Model Name (Optional)
    default_models = {
        "google": "gemini-1.5-pro",
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet"
    }
    default_model = default_models.get(provider, "gemini-1.5-pro")
    
    console.print(f"\n[bold]Step 3: Model Name[/] (Default: [green]{default_model}[/])")
    model_name = Prompt.ask("Enter Model Name (or press Enter for default)", default=default_model)

    # 4. Brave Search
    console.print("\n[bold]Step 4: Web Search[/]")
    brave_key = None
    if Confirm.ask("Do you have a Brave Search API Key?"):
        brave_key = Prompt.ask("Enter Brave Search API Key", password=True)

    # 5. Verify
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

    # 6. Save
    save_config(provider, model_name, api_key, brave_key)
    console.print("\n[bold green]Configuration Saved! 🚀[/]")
    console.print("\nYou can now run the agent with:\n[bold]python main.py[/]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[red]Setup cancelled.[/]")
