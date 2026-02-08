
from textual.app import App, ComposeResult
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Static, Label, Select, Button, TabbedContent, TabPane
from textual.screen import ModalScreen
from textual import work, on
from langchain_core.messages import HumanMessage
import json
import os
from brain.llm_factory import get_llm
from brain.memory_manager import SOUL_FILE

from agent import app as agent_app, CONFIG_FILE, ENV_FILE, run_autonomous_heartbeat


class ChatMessage(Static):
    """A widget to display a single chat message."""
    def __init__(self, text: str | list | dict, role: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        
        # Robust content extraction
        if isinstance(text, str):
            self.text = text
        elif isinstance(text, list):
            # Join text parts if it's a list of parts
            parts = []
            for part in text:
                if isinstance(part, dict) and "text" in part:
                    parts.append(part["text"])
                elif isinstance(part, str):
                    parts.append(part)
            self.text = "".join(parts)
        elif isinstance(text, dict) and "text" in text:
            self.text = text["text"]
        else:
            self.text = str(text)

    def compose(self) -> ComposeResult:
        # Icons: Safe Unicode
        # User: ► (U+25BA)
        # Agent: ◼ (U+25FC) or ◆ (U+25C6)
        
        if self.role == "user":
            prefix = "[bold cyan]► User:[/]" 
        else:
            prefix = "[bold green]◼ Agent:[/]"
        
        yield Label(prefix + " " + self.text, classes=f"message {self.role}")


class SoulSidebar(Static):
    """A widget to display the current Soul."""
    def on_mount(self) -> None:
        self.update_soul()
        self.set_interval(2.0, self.update_soul)

    def update_soul(self) -> None:
        try:
            with open(SOUL_FILE, "r") as f:
                content = f.read()
            self.update(f"[bold underline]Current Soul[/]\n\n{content}")
        except Exception:
            self.update("Error reading Soul file.")

class ConfigScreen(ModalScreen):
    """Modal screen for changing configuration mid-session."""
    CSS = """
    ConfigScreen {
        align: center middle;
    }
    
    #dialog {
        width: 90%;
        max-width: 80;
        min-width: 40;
        height: 80%;
        max-height: 40;
        border: solid green;
        padding: 1 2;
        background: $surface;
        overflow-y: auto;
    }
    
    Label {
        margin-top: 0;
        margin-bottom: 0;
        height: auto;
    }
    
    Button {
        margin-top: 1;
        width: 100%;
        min-width: 10;
    }
    
    .error { color: red; }
    .success { color: green; }

    .field-group {
        margin-bottom: 1;
        height: auto;
    }
    
    .help-text {
        color: $text-muted;
        text-style: italic;
        margin-top: 0;
        height: 1;
    }

    .config-title {
        text-align: center;
        margin-bottom: 1;
        height: 1;
    }
    
    .section-header {
        margin-top: 1;
        margin-bottom: 1;
        color: $accent;
        text-style: bold;
        height: 1;
    }

    .btn-group {
        margin-top: 1;
        height: 3;
    }

    /* High Contrast Inputs */
    Input {
        background: $panel; 
        border: solid $accent;
        height: 3;
        min-height: 3;
        color: $text;
        width: 100%;
    }
    
    Input:focus {
        border: double $primary;
    }
    
    Select {
        background: #1a1a2e;
        border: solid $accent;
        height: 3;
        min-height: 3;
        color: white;
        width: 100%;
    }
    
    Select:focus {
        border: double $primary;
    }
    
    SelectCurrent {
        background: #1a1a2e;
        color: white;
    }
    
    SelectCurrent > Static {
        color: white;
    }
    """

    def compose(self) -> ComposeResult:
        # Load current config
        current_provider = "google"
        current_model = ""
        current_search_provider = "brave"
        
        if os.path.exists(CONFIG_FILE):
             try:
                 with open(CONFIG_FILE, "r") as f:
                     data = json.load(f)
                     current_provider = data.get("provider", "google")
                     current_model = data.get("model", "")
                     current_search_provider = data.get("search_provider", "brave")
             except: pass

        with Container(id="dialog"):
            yield Label("[bold]Agent Configuration[/]", classes="field-group config-title")
            
            # AI Section
            yield Label("🧠 AI Brain", classes="section-header")
            
            with Vertical(classes="field-group"):
                yield Label("Select AI Provider:")
                yield Select(
                    options=[("Google Gemini", "google"), ("OpenAI", "openai"), ("Anthropic", "anthropic")],
                    id="provider_select",
                    value=current_provider,
                    allow_blank=False
                )
            
            with Vertical(classes="field-group"):
                yield Label("AI Provider API Key:")
                yield Input(placeholder="(Hidden)", password=True, id="api_key_input")
                yield Label("Leave empty to keep existing key.", classes="help-text")
            
            with Vertical(classes="field-group"):
                yield Label("Model Name:")
                yield Input(value=current_model, placeholder="e.g. gemini-1.5-pro", id="model_input")
                yield Label("Specific model identifier (optional).", classes="help-text")
            
            # Web Section
            yield Label("🌐 Web Capabilities", classes="section-header")
            
            with Vertical(classes="field-group"):
                yield Label("Search Provider:")
                yield Select(
                    options=[("Brave Search (Recommended)", "brave"), ("DuckDuckGo (Free/Slower)", "duckduckgo")],
                    id="search_provider_select",
                    value=current_search_provider,
                    allow_blank=False
                )
            
            with Vertical(classes="field-group"):
                yield Label("Brave Search API Key:")
                yield Input(placeholder="(Hidden)", password=True, id="brave_key_input")
                yield Label("Required for Brave. Leave empty to keep existing.", classes="help-text")

            yield Static("", id="status_message")
            
            with Horizontal(classes="field-group btn-group"):
                yield Button("Save & Close", variant="primary", id="save_btn")
                yield Button("Cancel", variant="error", id="cancel_btn")

    @on(Button.Pressed)
    def handle_buttons(self, event: Button.Pressed):
        if event.button.id == "cancel_btn":
            self.dismiss()
        elif event.button.id == "save_btn":
            self.save_config()

    def save_config(self):
        provider = self.query_one("#provider_select").value
        api_key = self.query_one("#api_key_input").value
        model = self.query_one("#model_input").value
        brave_key = self.query_one("#brave_key_input").value
        
        # 1. Update Config File
        config_data = {"provider": provider, "model": model}
        try:
             with open(CONFIG_FILE, "w") as f:
                 json.dump(config_data, f, indent=4)
        except Exception as e:
             self.query_one("#status_message").update(f"Error saving config: {e}")
             return

        # 2. Update .env if key provided
        if api_key:
            env_var_map = {
                "google": "GOOGLE_API_KEY",
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY"
            }
            env_var = env_var_map.get(provider)
            
            # Update .env file safely
            lines = []
            if os.path.exists(ENV_FILE):
                with open(ENV_FILE, "r") as f: lines = f.readlines()
            
            lines = [l for l in lines if not l.startswith(f"{env_var}=")]
            lines.append(f"{env_var}={api_key}\n")
            
            with open(ENV_FILE, "w") as f: f.writelines(lines)
            
            # Update os.environ
            os.environ[env_var] = api_key

        self.dismiss(result=True)


class AgentInterface(App):
    """The main TUI App."""
    CSS = """
    #main-container {
        height: 100%;
        width: 100%;
    }
    
    #sidebar {
        width: 30%;
        height: 100%;
        border-right: solid green;
        padding: 1;
        background: $surface;
    }

    #chat-container {
        width: 70%;
        height: 100%;
        layout: vertical;
    }

    #chat-history {
        height: 1fr;
        border: solid blue;
        overflow-y: auto;
        padding: 1;
    }

    #chat_input {
        dock: bottom;
        margin: 1;
    }

    .message {
        padding: 1;
        margin-bottom: 1;
        width: 100%;
        height: auto;
    }
    
    ChatMessage {
        height: auto;
        width: 100%;
    }
    
    .user { color: cyan; }
    .agent { color: green; }
    .system-alert { color: red; text-style: bold; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        
        # Main Body
        with Horizontal(id="main-container"):
            # Sidebar for Soul
            with Container(id="sidebar"):
                yield SoulSidebar()

            # Main Chat Area
            with Container(id="chat-container"):
                with Vertical(id="chat-history"):
                    yield Static("System: Agent initialized. Type '/config' to change settings or 'exit' to quit.", classes="agent")
                yield Input(placeholder="Type your command or message here...", id="chat_input")
        
        yield Footer()

    def on_mount(self):
        self.update_footer_model()
        # Schedule heartbeat every 60 seconds (1 minute) for task scheduler
        self.set_interval(60, self.scheduled_heartbeat)
        
        # Run once on startup (optional, maybe check if missed)
        self.scheduled_heartbeat()

    def update_footer_model(self):
        # Read config to get current model
        provider = "Unknown"
        model = "Unknown"
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    provider = data.get("provider", "Unknown").capitalize()
                    model = data.get("model", "Unknown")
            except: pass
        self.sub_title = f"Connected to: {provider} ({model})"


    @work(exclusive=True, thread=True)
    def scheduled_heartbeat(self):
        # Run the autonomous check
        # Since it calls LLM sync, we wrap or use thread. 
        # But get_llm invocation is sync in run_autonomous_heartbeat.
        # @work runs in a worker thread, so blocking is okay-ish, but let's be safe.
        try:
             # We can't await a sync function directly, but @work handles it if we don't await?
             # Actually @work makes the decorated function async-like in TUI loop but runs in thread?
             # Textual: "Workers are useful for running long running tasks... avoiding blocking the UI"
             # So we can just call it.
             
             # Note: run_autonomous_heartbeat checks timestamp, so safe to call often.
             result = run_autonomous_heartbeat()
             
             if result:
                 # 1. Show visual alert
                 self.call_from_thread(self.display_system_alert, result)
                 # 2. Trigger Agent Response automatically
                 self.process_agent_response(f"SYSTEM ALERT: {result}")
                 
        except Exception as e:
            # Silently fail or log?
            pass

    def display_system_alert(self, text: str):
         chat_history = self.query_one("#chat-history")
         chat_history.mount(Label(f"💓 System Alert: {text}", classes="message system-alert"))
         chat_history.scroll_end()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        # ... (Rest of input handling same as before) ...
        user_input = event.value
        event.input.value = ""
        
        if not user_input:
            return

        if user_input.lower() in ["exit", "quit"]:
            self.exit()
            return
            
        if user_input.lower() == "/config":
            self.push_screen(ConfigScreen(), self.on_config_closed)
            return

        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(user_input, "user"))
        
        self.process_agent_response(user_input)

    def on_config_closed(self, result):
        if result:
            self.update_footer_model()
            chat_history = self.query_one("#chat-history")
            chat_history.mount(Static("System: Configuration updated.", classes="agent"))

    @work(exclusive=True)
    async def process_agent_response(self, user_input: str) -> None:
        if not hasattr(self, "messages"): self.messages = []
        self.messages.append(HumanMessage(content=user_input))
        
        inputs = {"messages": self.messages}
        
        # Show thinking indicator
        chat_history = self.query_one("#chat-history")
        loading_indicator = Label("... thinking ...", classes="message agent")
        chat_history.mount(loading_indicator)
        chat_history.scroll_end()
        
        try:
            result = await agent_app.ainvoke(inputs)
            loading_indicator.remove() # Remove indicator
            
            latest_msg = result["messages"][-1]
            response_text = latest_msg.content
            
            self.messages = result["messages"]
            self.display_agent_message(response_text)
            
        except Exception as e:
            self.display_agent_message(f"Error: {str(e)}")

    def display_agent_message(self, text: str) -> None:
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(text, "agent"))
        chat_history.scroll_end()

if __name__ == "__main__":
    app = AgentInterface()
    app.run()
