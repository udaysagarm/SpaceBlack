
import os
import json
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Input, Select, Button, Label, Static
from textual import work
from brain.llm_factory import get_llm

CONFIG_FILE = "config.json"
ENV_FILE = ".env"

class SetupWizard(App):
    """First-run setup wizard for the AI Agent."""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    Container {
        width: 60;
        height: auto;
        border: solid green;
        padding: 2;
        background: $surface;
    }
    
    Label {
        margin-top: 1;
        margin-bottom: 1;
    }
    
    Button {
        margin-top: 2;
        width: 100%;
    }
    
    .error {
        color: red;
        text-align: center;
        margin-top: 1;
    }
    
    .success {
        color: green;
        text-align: center;
        margin-top: 1;
    }

    .field-group {
        margin-bottom: 2;
    }

    .help-text {
        color: $text-muted;
        text-style: italic;
        margin-top: 0;
        margin-bottom: 0;
    }

    /* Fix Visibility */
    Input {
        background: $boost;
        border: tall $background;
        height: 3;
        color: $text;
    }
    
    Select {
        background: $boost;
        border: tall $background;
        height: 3;
        color: $text;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container():
            yield Label("[bold]Welcome to the AI Terminal Agent[/]", classes="field-group")
            yield Label("Please configure your AI Provider and Search tools.", classes="field-group")
            
            with Vertical(classes="field-group"):
                yield Label("Select AI Provider:")
                yield Select(
                    options=[("Google Gemini", "google"), ("OpenAI", "openai"), ("Anthropic", "anthropic")],
                    id="provider_select",
                    value="google"
                )
            
            with Vertical(classes="field-group"):
                yield Label("AI Provider API Key:")
                yield Input(placeholder="sk-...", password=True, id="api_key_input")
                yield Label("Get this from Google AI Studio, OpenAI, or Anthropic console.", classes="help-text")
            
            with Vertical(classes="field-group"):
                yield Label("Model Name (Optional):")
                yield Input(placeholder="Default depends on provider (e.g. gpt-4o, gemini-1.5-pro)", id="model_input")
                yield Label("Leave empty to use the recommended default model.", classes="help-text")
            
            with Vertical(classes="field-group"):
                yield Label("Brave Search API Key (Optional):")
                yield Input(placeholder="BSAA...", password=True, id="brave_key_input")
                yield Label("Required for agent to search the web. Free at brave.com/search/api", classes="help-text")
            
            yield Static("", id="status_message")
            yield Button("Verify & Save", variant="primary", id="save_btn")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            provider = self.query_one("#provider_select").value
            api_key = self.query_one("#api_key_input").value
            model = self.query_one("#model_input").value
            brave_key = self.query_one("#brave_key_input").value
            
            if not api_key:
                self.update_status("API Key is required!", "error")
                return
                
            # Set default models if empty
            if not model:
                defaults = {
                    "google": "gemini-1.5-pro",
                    "openai": "gpt-4o",
                    "anthropic": "claude-3-5-sonnet"
                }
                model = defaults.get(provider, "gpt-4o")
            
            self.update_status("Verifying key...", "normal")
            self.verify_and_save(provider, model, api_key, brave_key)

    def update_status(self, message: str, type: str = "normal"):
        status = self.query_one("#status_message")
        status.update(message)
        status.classes = type

    @work(exclusive=True, thread=True)
    def verify_and_save(self, provider, model, api_key, brave_key):
        try:
            # Temporarily set env var for the factory or pass it directly
            # The factory supports passing api_key directly now
            
            llm = get_llm(provider, model, api_key=api_key)
            
            # Simple invocation to test
            # We use invoke because get_llm returns a sync/async compatible object, 
            # but wrapping in a thread via @work is safest for blocking calls
            try:
                llm.invoke("Hello")
            except Exception as e:
                # Some verification might fail if models are different or auth fails
                 self.call_from_thread(self.update_status, f"Verification Failed: {str(e)}", "error")
                 return

            # If successful, save config
            config_data = {
                "provider": provider,
                "model": model
            }
            
            # Write config.json
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f, indent=4)
                
            # Write .env
            env_var_map = {
                "google": "GOOGLE_API_KEY",
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY"
            }
            env_var = env_var_map.get(provider)
            
            # Read existing .env if any
            existing_lines = []
            if os.path.exists(ENV_FILE):
                with open(ENV_FILE, "r") as f:
                    existing_lines = f.readlines()
            
            # Update or append
            new_lines = [line for line in existing_lines if not line.startswith(f"{env_var}=")]
            new_lines.append(f"{env_var}={api_key}\n")
            
            if brave_key:
                new_lines = [line for line in new_lines if not line.startswith("BRAVE_API_KEY=")]
                new_lines.append(f"BRAVE_API_KEY={brave_key}\n")
            
            with open(ENV_FILE, "w") as f:
                f.writelines(new_lines)
                
            self.call_from_thread(self.update_status, "Success! Configuration saved.", "success")
            
            # Wait a moment then exit
            # time.sleep(1) 
            # self.app.exit() -> cannot call app.exit() from thread directly easily without callback? 
            # Actually, call_from_thread can call a method that exits
            self.call_from_thread(self.exit_app)
            
        except Exception as e:
             self.call_from_thread(self.update_status, f"Error: {str(e)}", "error")

    def exit_app(self):
        self.exit(result=True)

if __name__ == "__main__":
    app = SetupWizard()
    app.run()
