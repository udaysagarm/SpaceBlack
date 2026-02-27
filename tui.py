
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import (
    Header, Footer, Input, Static, Label, Select, Button,
    TabbedContent, TabPane, Switch, RadioSet, RadioButton,
    RichLog, LoadingIndicator, Rule,
)
from textual.screen import ModalScreen
from textual.binding import Binding
from textual import work, on
from textual.worker import Worker, WorkerState
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel
from rich.console import Group
from langchain_core.messages import HumanMessage
import asyncio
import json
import os
from brain.llm_factory import get_llm
from brain.memory_manager import SOUL_FILE

from agent import app as agent_app, CONFIG_FILE, ENV_FILE, run_autonomous_heartbeat, load_chat_history, save_chat_history, CHAT_HISTORY_FILE

try:
    from tools.voice.recorder import record_audio
    from brain.voice_factory import transcribe_audio, generate_audio_response
    from tools.voice.player import play_audio_bytes
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    record_audio = None
    transcribe_audio = None
    generate_audio_response = None
    play_audio_bytes = None

from brain.provider_models import get_provider_list, get_chat_models, get_tts_models, PROVIDERS


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat Message Widget
# ═══════════════════════════════════════════════════════════════════════════════

class ChatMessage(Static):
    """A single chat message — user or agent."""

    def __init__(self, text: str | list | dict, role: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role

        # Robust content extraction
        if isinstance(text, str):
            self.text = text
        elif isinstance(text, list):
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
        if self.role == "user":
            yield Static(f"[bold cyan]▸ You[/]\n{self.text}", classes="msg-content user-msg")
        elif self.role == "system":
            yield Static(f"[bold yellow]⚡ System[/]\n{self.text}", classes="msg-content system-msg")
        else:
            yield Static(f"[bold green]◆ Agent[/]\n{self.text}", classes="msg-content agent-msg")


# ═══════════════════════════════════════════════════════════════════════════════
#  Soul Sidebar
# ═══════════════════════════════════════════════════════════════════════════════

class SoulSidebar(Static):
    """Displays the agent's current Soul."""
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


# ═══════════════════════════════════════════════════════════════════════════════
#  Thinking Indicator
# ═══════════════════════════════════════════════════════════════════════════════

class ThinkingIndicator(Static):
    """Animated thinking indicator shown while agent is processing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._frame = 0
        self._frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def on_mount(self):
        self.update_animation()
        self._timer = self.set_interval(0.1, self.update_animation)

    def update_animation(self):
        spinner = self._frames[self._frame % len(self._frames)]
        self.update(f"[bold magenta]{spinner} Thinking...[/]")
        self._frame += 1


# ═══════════════════════════════════════════════════════════════════════════════
#  Chat Input with History
# ═══════════════════════════════════════════════════════════════════════════════

class ChatInput(Input):
    """Input field with prompt history support (Up/Down arrows)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._history: list[str] = []
        self._history_index: int = -1
        self._draft: str = ""

    def add_to_history(self, text: str):
        """Add a prompt to history (max 50)."""
        if text and (not self._history or self._history[-1] != text):
            self._history.append(text)
            if len(self._history) > 50:
                self._history.pop(0)
        self._history_index = -1
        self._draft = ""

    def on_key(self, event):
        if event.key == "up":
            if not self._history:
                return
            if self._history_index == -1:
                self._draft = self.value
                self._history_index = len(self._history) - 1
            elif self._history_index > 0:
                self._history_index -= 1
            self.value = self._history[self._history_index]
            self.cursor_position = len(self.value)
            event.prevent_default()
            event.stop()
        elif event.key == "down":
            if self._history_index == -1:
                return
            if self._history_index < len(self._history) - 1:
                self._history_index += 1
                self.value = self._history[self._history_index]
            else:
                self._history_index = -1
                self.value = self._draft
            self.cursor_position = len(self.value)
            event.prevent_default()
            event.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  Config Screen (unchanged logic, refined style)
# ═══════════════════════════════════════════════════════════════════════════════

class ConfigScreen(ModalScreen):
    """Modal screen for changing configuration mid-session."""
    CSS = """
    ConfigScreen {
        align: center middle;
        background: $surface 50%;
    }

    #dialog {
        width: 90%;
        max-width: 80;
        height: 90%;
        max-height: 45;
        border: tall $accent;
        padding: 1 2;
        background: $surface;
        overflow-y: auto;
    }

    .config-title {
        text-align: center;
        margin-bottom: 2;
        text-style: bold;
        background: $primary;
        color: white;
        padding: 1;
        width: 100%;
        border-bottom: solid $accent;
    }

    .section-header {
        margin-top: 2;
        margin-bottom: 1;
        color: $accent;
        text-style: bold;
        border-bottom: solid $secondary;
        padding-bottom: 0;
    }

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

    .btn-group {
        margin-top: 2;
        height: 3;
    }

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

    RadioSet {
        background: $panel;
        border: solid $secondary;
        padding: 1;
        height: auto;
        margin-bottom: 1;
    }

    RadioButton {
        width: 100%;
    }

    Select {
        width: 100%;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        current_provider = "google"
        current_model = ""
        current_voice_provider = "google"
        current_tts_model = "gemini-2.5-flash"
        current_stt_model = "gemini-2.5-flash"
        current_search_provider = "brave"

        if os.path.exists(CONFIG_FILE):
             try:
                 with open(CONFIG_FILE, "r") as f:
                     data = json.load(f)
                     current_provider = data.get("provider", "google")
                     current_model = data.get("model", "")
                     current_voice_provider = data.get("voice_provider", "google")
                     current_tts_model = data.get("tts_model", "gemini-2.5-flash")
                     current_stt_model = data.get("stt_model", "gemini-2.5-flash")
                     current_search_provider = data.get("search_provider", "brave")
             except: pass

        with Container(id="dialog"):
            yield Label("Agent Configuration", classes="field-group config-title")

            yield Label("AI Brain", classes="section-header")

            with Vertical(classes="field-group"):
                yield Label("Select AI Provider:")
                provider_list = get_provider_list()
                if current_provider not in dict(provider_list).values():
                    current_provider = provider_list[0][1] if provider_list else "google"
                yield Select(provider_list, value=current_provider, id="provider_select", allow_blank=False)

            with Vertical(classes="field-group"):
                yield Label("AI Provider API Key:", id="api_key_label")
                yield Input(placeholder="(Hidden)", password=True, id="api_key_input")
                yield Label("Leave empty to keep existing key. (Ollama requires none)", classes="help-text", id="api_key_help")

            with Vertical(classes="field-group"):
                yield Label("Model Name:")
                models_list = [(m, m) for m in get_chat_models(current_provider)]
                if not models_list and current_model:
                     models_list = [(current_model, current_model)]
                elif current_model and current_model not in [m[1] for m in models_list]:
                     models_list.insert(0, (current_model, current_model))
                
                val = current_model if current_model in [m[1] for m in models_list] else (models_list[0][1] if models_list else Select.BLANK)
                yield Select(models_list, value=val, id="model_select", allow_blank=False)
                yield Label("Select the model to be used by the agent.", classes="help-text")
                
            yield Label("Voice Settings", classes="section-header")

            with Vertical(classes="field-group"):
                yield Label("Select Voice Provider:")
                voice_provider_list = get_provider_list()
                if current_voice_provider not in dict(voice_provider_list).values():
                    current_voice_provider = voice_provider_list[0][1] if voice_provider_list else "google"
                yield Select(voice_provider_list, value=current_voice_provider, id="voice_provider_select", allow_blank=False)

            with Vertical(classes="field-group"):
                yield Label("TTS Model:")
                tts_models_list = [(m, m) for m in get_tts_models(current_voice_provider)]
                if not tts_models_list and current_tts_model:
                     tts_models_list = [(current_tts_model, current_tts_model)]
                elif current_tts_model and current_tts_model not in [m[1] for m in tts_models_list]:
                     tts_models_list.insert(0, (current_tts_model, current_tts_model))
                
                tts_val = current_tts_model if current_tts_model in [m[1] for m in tts_models_list] else (tts_models_list[0][1] if tts_models_list else Select.BLANK)
                yield Select(tts_models_list, value=tts_val, id="tts_model_select", allow_blank=False)

            with Vertical(classes="field-group"):
                from brain.provider_models import get_stt_models
                yield Label("STT Model:")
                stt_models_list = [(m, m) for m in get_stt_models(current_voice_provider)]
                if not stt_models_list and current_stt_model:
                     stt_models_list = [(current_stt_model, current_stt_model)]
                elif current_stt_model and current_stt_model not in [m[1] for m in stt_models_list]:
                     stt_models_list.insert(0, (current_stt_model, current_stt_model))
                
                stt_val = current_stt_model if current_stt_model in [m[1] for m in stt_models_list] else (stt_models_list[0][1] if stt_models_list else Select.BLANK)
                yield Select(stt_models_list, value=stt_val, id="stt_model_select", allow_blank=False)

            yield Label("Web Capabilities", classes="section-header")

            with Vertical(classes="field-group"):
                yield Label("Search Provider:")
                with RadioSet(id="search_provider_radioset"):
                    yield RadioButton("Brave Search", id="rb_brave", value=(current_search_provider == "brave"))
                    yield RadioButton("DuckDuckGo", id="rb_duckduckgo", value=(current_search_provider == "duckduckgo"))

            with Vertical(classes="field-group"):
                yield Label("Brave Search API Key:")
                yield Input(placeholder="(Hidden)", password=True, id="brave_key_input")
                yield Label("Required for Brave. Leave empty to keep existing.", classes="help-text")

            yield Static("", id="status_message")

            with Horizontal(classes="field-group btn-group"):
                yield Button("Save & Close", variant="primary", id="save_btn")
                yield Button("Cancel", variant="error", id="cancel_btn")

    def on_mount(self):
        # Trigger an initial API Key label update based on the mounted provider
        sel = self.query_one("#provider_select", Select)
        if sel.value:
            self.update_api_key_label(sel.value)

    @on(Select.Changed, "#provider_select")
    def on_provider_changed(self, event: Select.Changed) -> None:
        provider_id = event.value
        if not provider_id: return
        
        self.update_api_key_label(provider_id)
        
        # Read the saved model from config to preserve it if valid
        saved_model = ""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    saved_model = json.load(f).get("model", "")
            except: pass
        
        # Update models dropdown
        model_select = self.query_one("#model_select", Select)
        models_list = [(m, m) for m in get_chat_models(provider_id)]
        
        # Add saved model to list if not present but valid
        if saved_model and saved_model not in [m[1] for m in models_list]:
            models_list.insert(0, (saved_model, saved_model))
        
        model_select.set_options(models_list)
        
        # Preserve saved model if valid, otherwise fall back to first
        if saved_model and saved_model in [m[1] for m in models_list]:
            model_select.value = saved_model
        elif models_list:
            model_select.value = models_list[0][1]
        else:
            model_select.value = Select.BLANK

    @on(Select.Changed, "#voice_provider_select")
    def on_voice_provider_changed(self, event: Select.Changed) -> None:
        provider_id = event.value
        if not provider_id: return
        
        # Read saved voice models from config
        saved_tts = ""
        saved_stt = ""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    saved_tts = data.get("tts_model", "")
                    saved_stt = data.get("stt_model", "")
            except: pass
        
        # Update TTS models dropdown
        tts_model_select = self.query_one("#tts_model_select", Select)
        tts_models_list = [(m, m) for m in get_tts_models(provider_id)]
        if saved_tts and saved_tts not in [m[1] for m in tts_models_list]:
            tts_models_list.insert(0, (saved_tts, saved_tts))
        tts_model_select.set_options(tts_models_list)
        if saved_tts and saved_tts in [m[1] for m in tts_models_list]:
            tts_model_select.value = saved_tts
        elif tts_models_list:
            tts_model_select.value = tts_models_list[0][1]
        else:
            tts_model_select.value = Select.BLANK
            
        # Update STT models dropdown
        from brain.provider_models import get_stt_models
        stt_model_select = self.query_one("#stt_model_select", Select)
        stt_models_list = [(m, m) for m in get_stt_models(provider_id)]
        if saved_stt and saved_stt not in [m[1] for m in stt_models_list]:
            stt_models_list.insert(0, (saved_stt, saved_stt))
        stt_model_select.set_options(stt_models_list)
        if saved_stt and saved_stt in [m[1] for m in stt_models_list]:
            stt_model_select.value = saved_stt
        elif stt_models_list:
            stt_model_select.value = stt_models_list[0][1]
        else:
            stt_model_select.value = Select.BLANK

    def update_api_key_label(self, provider_id: str):
        provider_data = PROVIDERS.get(provider_id, {})
        env_var = provider_data.get("env_var")
        label = self.query_one("#api_key_label", Label)
        inp = self.query_one("#api_key_input", Input)
        if env_var:
            label.update(f"{provider_data.get('name')} API Key:")
            inp.disabled = False
        else:
            label.update(f"{provider_data.get('name')} (No API Key needed)")
            inp.disabled = True
            inp.value = ""

    @on(Button.Pressed)
    def handle_buttons(self, event: Button.Pressed):
        if event.button.id == "cancel_btn":
            self.dismiss()
        elif event.button.id == "save_btn":
            self.save_config()

    def save_config(self):
        provider = self.query_one("#provider_select", Select).value
        # Use str(value) explicitly to ensure we don't accidentally pass a BLANK instance
        model_val = self.query_one("#model_select", Select).value
        model = str(model_val) if model_val != Select.BLANK else ""
        
        voice_provider = self.query_one("#voice_provider_select", Select).value
        tts_model_val = self.query_one("#tts_model_select", Select).value
        tts_model = str(tts_model_val) if tts_model_val != Select.BLANK else ""
        
        stt_model_val = self.query_one("#stt_model_select", Select).value
        stt_model = str(stt_model_val) if stt_model_val != Select.BLANK else ""

        api_key = self.query_one("#api_key_input", Input).value
        brave_key = self.query_one("#brave_key_input", Input).value

        search_rs = self.query_one("#search_provider_radioset", RadioSet)
        search_provider = "brave"
        if search_rs.pressed_button:
             sid = search_rs.pressed_button.id
             if sid == "rb_brave": search_provider = "brave"
             elif sid == "rb_duckduckgo": search_provider = "duckduckgo"

        if not provider or not model:
            self.query_one("#status_message", Static).update("[red]Error: Provider and Model are required.[/red]")
            return

        config_data = {
            "provider": provider,
            "model": model,
            "voice_provider": voice_provider,
            "tts_model": tts_model,
            "stt_model": stt_model,
            "search_provider": search_provider
        }
        
        # Read existing to preserve skills
        existing_config = {}
        if os.path.exists(CONFIG_FILE):
             try:
                 with open(CONFIG_FILE, "r") as f:
                     existing_config = json.load(f)
             except: pass
             
        existing_config.update(config_data)

        try:
             with open(CONFIG_FILE, "w") as f:
                 json.dump(existing_config, f, indent=4)
        except Exception as e:
             self.query_one("#status_message", Static).update(f"[red]Error saving config: {e}[/red]")
             return

        # Environment Variable updates for API Keys
        if api_key and provider:
            provider_data = PROVIDERS.get(provider, {})
            env_var = provider_data.get("env_var")
            if env_var:
                lines = []
                if os.path.exists(ENV_FILE):
                    with open(ENV_FILE, "r") as f: lines = f.readlines()
                lines = [l for l in lines if not l.startswith(f"{env_var}=")]
                lines.append(f"{env_var}={api_key}\n")
                with open(ENV_FILE, "w") as f: f.writelines(lines)
                os.environ[env_var] = api_key

        # Environment Variable update for Brave Key
        if brave_key:
             lines = []
             if os.path.exists(ENV_FILE):
                 with open(ENV_FILE, "r") as f: lines = f.readlines()
             lines = [l for l in lines if not l.startswith("BRAVE_API_KEY=")]
             lines.append(f"BRAVE_API_KEY={brave_key}\n")
             with open(ENV_FILE, "w") as f: f.writelines(lines)
             os.environ["BRAVE_API_KEY"] = brave_key

        self.dismiss(result=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  Skills Screen (unchanged logic)
# ═══════════════════════════════════════════════════════════════════════════════

class SkillsScreen(ModalScreen):
    """Modal screen for managing agent skills."""
    CSS = """
    SkillsScreen {
        align: center middle;
        background: $surface 50%;
    }

    #skills-dialog {
        width: 85%;
        max-width: 80;
        height: 85%;
        max-height: 50;
        border: tall $accent;
        padding: 1 2;
        background: $surface;
        layout: vertical;
    }

    #skills-list {
        height: 1fr;
        width: 100%;
        overflow-y: auto;
        padding-right: 1;
        padding-bottom: 2;
        margin-bottom: 1;
    }

    .config-title {
        text-align: center;
        margin-bottom: 2;
        text-style: bold;
        background: $primary;
        color: white;
        padding: 1;
        width: 100%;
        border-bottom: solid $accent;
    }

    .help-text {
        color: $text-muted;
        text-style: italic;
        margin-top: 0;
        margin-bottom: 1;
        height: auto;
    }

    .skill-row {
        height: auto;
        margin-bottom: 2;
        border: solid $secondary;
        padding: 1;
        background: $panel;
    }

    .skill-header {
        height: 3;
        margin-bottom: 1;
        align: center middle;
    }

    .skill-name {
        text-style: bold;
        color: $accent;
        width: 1fr;
        content-align: left middle;
    }

    Switch {
        height: auto;
        dock: right;
    }

    .api-key-label {
        margin-top: 1;
        margin-left: 1;
        color: $text;
    }

    .api-key-input {
        margin-top: 0;
        margin-left: 1;
        width: 1fr;
        border: solid $accent;
        background: $surface;
    }

    .description {
        color: $text-muted;
        margin-bottom: 1;
    }
    
    .btn-group {
        height: auto;
        dock: bottom;
        margin-top: 1;
        align: right middle;
    }
    """

    def compose(self) -> ComposeResult:
        skills_config = {}
        if os.path.exists(CONFIG_FILE):
             try:
                 with open(CONFIG_FILE, "r") as f:
                     data = json.load(f)
                     skills_config = data.get("skills", {})
             except: pass

        openweather_cfg = skills_config.get("openweather", {})
        ow_enabled = openweather_cfg.get("enabled", False)

        browser_cfg = skills_config.get("browser", {})
        browser_enabled = browser_cfg.get("enabled", False)

        github_cfg = skills_config.get("github", {})
        gh_enabled = github_cfg.get("enabled", False)

        stripe_cfg = skills_config.get("stripe", {})
        stripe_enabled = stripe_cfg.get("enabled", False)

        discord_cfg = skills_config.get("discord", {})
        discord_enabled = discord_cfg.get("enabled", False)
        discord_user_id = discord_cfg.get("allowed_user_id", "")

        telegram_cfg = skills_config.get("telegram", {})
        tg_enabled = telegram_cfg.get("enabled", False)

        google_cfg = skills_config.get("google", {})
        google_enabled = google_cfg.get("enabled", False)

        slack_cfg = skills_config.get("slack", {})
        slack_enabled = slack_cfg.get("enabled", False)
        slack_bot_token = slack_cfg.get("bot_token", "")
        slack_app_token = slack_cfg.get("app_token", "")
        slack_user_id = slack_cfg.get("allowed_user_id", "")

        import platform
        macos_cfg = skills_config.get("macos", {})
        macos_enabled = macos_cfg.get("enabled", False) and platform.system() == "Darwin"

        with Container(id="skills-dialog"):
            yield Label("Agent Skills Manager", classes="config-title")

            with Vertical(id="skills-list"):
                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("Headless Browser (Autonomous Browsing)", classes="skill-name")
                        yield Switch(value=browser_enabled, id="browser_switch")
                    yield Label("Allows the agent to browse the web autonomously using Chromium.", classes="description")
                    yield Label("Requires 'playwright install chromium' to be run once.", classes="help-text")

                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("OpenWeather", classes="skill-name")
                        yield Switch(value=ow_enabled, id="openweather_switch")
                    yield Label("Provides real-time weather information for any city.", classes="description")
                    yield Label("API Key:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new key to update", password=True, id="openweather_key", classes="api-key-input")

                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("GitHub Autonomous Acts", classes="skill-name")
                        yield Switch(value=gh_enabled, id="github_switch")
                    yield Label("Manage repos, issues, and commit files remotely via the API.", classes="description")
                    yield Label("Personal Access Token (classic):", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new PAT to update", password=True, id="github_token", classes="api-key-input")
                    yield Label("Requires 'repo' scope permissions.", classes="help-text")

                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("Stripe API (Payments)", classes="skill-name")
                        yield Switch(value=stripe_enabled, id="stripe_switch")
                    yield Label("Allow the agent to autonomously process charges, create payment links, and manage customers.", classes="description")
                    yield Label("Stripe Secret Key:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new secret key (sk_...) to update", password=True, id="stripe_key", classes="api-key-input")
                    yield Label("Warning: The agent can spend real money with this enabled.", classes="help-text")

                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("Discord Bot", classes="skill-name")
                        yield Switch(value=discord_enabled, id="discord_switch")
                    yield Label("Send messages, manage channels, and interact with Discord servers.", classes="description")
                    yield Label("Bot Token:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new bot token to update", password=True, id="discord_token", classes="api-key-input")
                    yield Label("Allowed User ID:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new ID to update", id="discord_user_id", classes="api-key-input")
                    yield Label("Required for security. Get yours by turning on Developer Mode in Discord.", classes="help-text")

                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("Telegram Bot Gateway", classes="skill-name")
                        yield Switch(value=tg_enabled, id="telegram_switch")
                    yield Label("Chat with your agent remotely via Telegram.", classes="description")
                    yield Label("Bot Token:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new token to update", password=True, id="telegram_token", classes="api-key-input")
                    yield Label("Allowed User ID:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new ID to update", id="telegram_user_id", classes="api-key-input")
                    yield Label("Required for security. Get yours from @userinfobot.", classes="help-text")

                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("Google Workspace (Gmail, Drive, Docs, Sheets, Calendar)", classes="skill-name")
                        yield Switch(value=google_enabled, id="google_switch")
                    yield Label("Manage Gmail, Drive files, Docs, Sheets, and Calendar events.", classes="description")
                    yield Label("credentials.json Content (recommended):", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Paste entire credentials.json contents here", password=True, id="google_credentials_json", classes="api-key-input")
                    yield Label("OR enter manually:", classes="help-text")
                    yield Label("OAuth2 Client ID:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter Client ID", password=True, id="google_client_id", classes="api-key-input")
                    yield Label("OAuth2 Client Secret:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter Client Secret", password=True, id="google_client_secret", classes="api-key-input")
                    yield Label("Get credentials at console.cloud.google.com/apis/credentials", classes="help-text")

                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("macOS Native Control", classes="skill-name")
                        yield Switch(value=macos_enabled, id="macos_switch")
                    yield Label("Control Apple Mail, Calendar, Notes, Finder, Reminders, and system apps.", classes="description")
                with Vertical(classes="skill-row"):
                    with Horizontal(classes="skill-header"):
                        yield Label("Slack Bot Gateway", classes="skill-name")
                        yield Switch(value=slack_enabled, id="slack_switch")
                    yield Label("Chat with your agent remotely via Slack Socket Mode.", classes="description")
                    yield Label("Bot Token (xoxb-...):", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new bot token to update", password=True, id="slack_bot_token", classes="api-key-input")
                    yield Label("App Token (xapp-...):", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter new app token to update", password=True, id="slack_app_token", classes="api-key-input")
                    yield Label("Allowed User ID:", classes="api-key-label")
                    yield Input(value="", placeholder="(Hidden) - Enter your Member ID (e.g. U1234567)", id="slack_user_id", classes="api-key-input")
                    yield Label("Required for DM security. Get it from your Slack profile.", classes="help-text")

            with Horizontal(classes="btn-group"):
                yield Button("Save & Close", variant="primary", id="save_skills_btn")
                yield Button("Cancel", variant="error", id="cancel_skills_btn")

    @on(Button.Pressed)
    def handle_buttons(self, event: Button.Pressed):
        if event.button.id == "cancel_skills_btn":
            self.dismiss()
        elif event.button.id == "save_skills_btn":
            self.save_skills()

    def save_skills(self):
        ow_enabled = self.query_one("#openweather_switch").value
        ow_key = self.query_one("#openweather_key").value
        browser_enabled = self.query_one("#browser_switch").value
        gh_enabled = self.query_one("#github_switch").value
        gh_token = self.query_one("#github_token").value
        stripe_enabled = self.query_one("#stripe_switch").value
        stripe_key = self.query_one("#stripe_key").value
        discord_enabled = self.query_one("#discord_switch").value
        discord_token = self.query_one("#discord_token").value
        discord_user_id = self.query_one("#discord_user_id").value
        tg_enabled = self.query_one("#telegram_switch").value
        tg_token = self.query_one("#telegram_token").value
        tg_user_id = self.query_one("#telegram_user_id").value
        
        slack_enabled = self.query_one("#slack_switch").value
        slack_bot_token = self.query_one("#slack_bot_token").value
        slack_app_token = self.query_one("#slack_app_token").value
        slack_user_id = self.query_one("#slack_user_id").value

        config_data = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config_data = json.load(f)
            except: pass

        if "skills" not in config_data:
            config_data["skills"] = {}

        ow_data = config_data["skills"].get("openweather", {})
        ow_data["enabled"] = ow_enabled
        if ow_key:
             ow_data["api_key"] = ow_key
        config_data["skills"]["openweather"] = ow_data

        browser_data = config_data["skills"].get("browser", {})
        browser_data["enabled"] = browser_enabled
        config_data["skills"]["browser"] = browser_data

        gh_data = config_data["skills"].get("github", {})
        gh_data["enabled"] = gh_enabled
        if gh_token:
            gh_data["api_key"] = gh_token
        config_data["skills"]["github"] = gh_data

        stripe_data = config_data["skills"].get("stripe", {})
        stripe_data["enabled"] = stripe_enabled
        if stripe_key:
            stripe_data["api_key"] = stripe_key
        config_data["skills"]["stripe"] = stripe_data

        discord_data = config_data["skills"].get("discord", {})
        discord_data["enabled"] = discord_enabled
        if discord_token:
            discord_data["bot_token"] = discord_token
        if discord_user_id:
            discord_data["allowed_user_id"] = discord_user_id
        config_data["skills"]["discord"] = discord_data

        tg_data = config_data["skills"].get("telegram", {})
        tg_data["enabled"] = tg_enabled
        if tg_token:
             tg_data["bot_token"] = tg_token
        if tg_user_id:
             tg_data["allowed_user_id"] = tg_user_id
        config_data["skills"]["telegram"] = tg_data

        slack_data = config_data["skills"].get("slack", {})
        slack_data["enabled"] = slack_enabled
        if slack_bot_token:
            slack_data["bot_token"] = slack_bot_token
        if slack_app_token:
            slack_data["app_token"] = slack_app_token
        if slack_user_id:
            slack_data["allowed_user_id"] = slack_user_id
        config_data["skills"]["slack"] = slack_data

        google_enabled = self.query_one("#google_switch").value
        google_credentials_json = self.query_one("#google_credentials_json").value
        google_client_id = self.query_one("#google_client_id").value
        google_client_secret = self.query_one("#google_client_secret").value
        google_data = config_data["skills"].get("google", {})
        google_data["enabled"] = google_enabled
        if google_credentials_json:
            google_data["credentials_json"] = google_credentials_json
        if google_client_id:
            google_data["client_id"] = google_client_id
        if google_client_secret:
            google_data["client_secret"] = google_client_secret
        config_data["skills"]["google"] = google_data

        macos_enabled = self.query_one("#macos_switch").value
        macos_data = config_data["skills"].get("macos", {})
        macos_data["enabled"] = macos_enabled
        config_data["skills"]["macos"] = macos_data

        try:
             with open(CONFIG_FILE, "w") as f:
                 json.dump(config_data, f, indent=4)
        except Exception as e:
             self.notify(f"Error saving skills: {e}", severity="error")
             return

        self.dismiss(result=True)
        self.notify("Skills saved. Restart agent for changes to take effect.", severity="warning", timeout=5)


# ═══════════════════════════════════════════════════════════════════════════════
#  Tasks Screen (unchanged logic)
# ═══════════════════════════════════════════════════════════════════════════════

class TasksScreen(ModalScreen):
    """Modal screen for managing automated tasks."""
    CSS = """
    TasksScreen {
        align: center middle;
        background: $surface 50%;
    }

    #tasks-dialog {
        width: 90%;
        max-width: 90;
        height: 90%;
        max-height: 50;
        border: tall $accent;
        padding: 1 2;
        background: $surface;
        layout: vertical;
    }

    #tasks-list {
        height: 1fr;
        width: 100%;
        overflow-y: auto;
        border: solid $secondary;
        padding: 1;
        background: $panel;
        margin-bottom: 1;
    }

    .config-title {
        text-align: center;
        margin-bottom: 2;
        text-style: bold;
        background: $primary;
        color: white;
        padding: 1;
        width: 100%;
        border-bottom: solid $accent;
        dock: top;
    }

    .task-row {
        height: auto;
        margin-bottom: 1;
        border: solid $secondary;
        padding: 1;
        background: $panel;
        layout: horizontal;
    }

    .task-info {
        width: 1fr;
        height: auto;
        layout: vertical;
    }

    .task-time {
        color: yellow;
        text-style: bold;
    }

    .task-desc {
        color: white;
    }

    .task-recur {
        color: cyan;
        text-style: italic;
    }

    .delete-btn {
        dock: right;
        min-width: 10;
        height: 3;
        margin-left: 1;
    }

    .empty-msg {
        text-align: center;
        margin-top: 4;
        color: $text-muted;
    }

    .btn-group {
        margin-top: 1;
        height: 3;
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="tasks-dialog"):
            yield Label("Automated Tasks Manager", classes="config-title")
            with Vertical(id="tasks-list"):
                pass
            with Horizontal(classes="field-group btn-group"):
                yield Button("Close", variant="primary", id="close_tasks_btn")

    def on_mount(self):
        self.refresh_count = 0
        self.refresh_tasks()

    def refresh_tasks(self):
        self.refresh_count += 1
        tasks_list = self.query_one("#tasks-list")
        tasks_list.remove_children()

        tasks = []
        try:
            from brain.memory_manager import SCHEDULE_FILE, read_file_safe
            content = read_file_safe(SCHEDULE_FILE, "[]")
            tasks = json.loads(content)
        except Exception as e:
            tasks_list.mount(Label(f"Error loading tasks: {e}", classes="empty-msg"))
            return

        if not tasks:
            tasks_list.mount(Label("No scheduled tasks found.", classes="empty-msg"))
        else:
            for idx, task in enumerate(tasks):
                unique_sid = f"{idx}_{self.refresh_count}"
                info_children = [
                    Label(f"  {task.get('time', 'Unknown')}", classes="task-time"),
                    Label(f"  {task.get('task', '')}", classes="task-desc")
                ]
                if "recurrence" in task:
                    info_children.append(Label(f"  Repeats: {task['recurrence']}", classes="task-recur"))
                info = Container(*info_children, classes="task-info")
                delete_btn = Button("Delete", variant="error", id=f"delete-{unique_sid}", classes="delete-btn")
                row = Container(info, delete_btn, classes="task-row", id=f"row-{unique_sid}")
                tasks_list.mount(row)

    @on(Button.Pressed)
    def handle_buttons(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "close_tasks_btn":
            self.dismiss()
            return
        if btn_id and btn_id.startswith("delete-"):
            try:
                parts = btn_id.split("-")
                unique_id = parts[1]
                idx = int(unique_id.split("_")[0])
                self.delete_task(idx)
            except Exception as e:
                self.notify(f"Error deleting task: {e}", severity="error")

    def delete_task(self, idx: int):
        from brain.memory_manager import SCHEDULE_FILE, read_file_safe
        try:
            content = read_file_safe(SCHEDULE_FILE, "[]")
            tasks = json.loads(content)
            if 0 <= idx < len(tasks):
                tasks.pop(idx)
                with open(SCHEDULE_FILE, "w") as f:
                    json.dump(tasks, f, indent=4)
                self.notify("Deleted task.")
                self.refresh_tasks()
            else:
                self.notify("Task index out of range.", severity="error")
                self.refresh_tasks()
        except Exception as e:
             self.notify(f"Delete failed: {e}", severity="error")


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Application — AgentInterface
# ═══════════════════════════════════════════════════════════════════════════════

class AgentInterface(App):
    """Space Black Terminal — Premium Agent Interface."""

    TITLE = "Space Black"

    BINDINGS = [
        Binding("ctrl+l", "clear_chat", "Clear Chat", show=True),
        Binding("ctrl+r", "restart_session", "Restart", show=True),
        Binding("ctrl+x", "stop_agent", "Stop Agent", show=True),
        Binding("ctrl+s", "stop_agent", "Stop (Alt)", show=False),
        Binding("ctrl+v", "record_voice", "Speak (5s)", show=True),
        Binding("escape", "dismiss_modal", "Dismiss", show=False),
    ]

    CSS = """
    /* ── Layout ─────────────────────────────────────────────────── */
    #main-container {
        height: 1fr;
        width: 100%;
    }

    #sidebar {
        width: 28;
        height: 100%;
        border-right: tall $accent 40%;
        padding: 1;
        background: $surface;
    }

    #chat-container {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }

    /* ── Chat Area ──────────────────────────────────────────────── */
    #chat-history {
        height: 1fr;
        overflow-y: auto;
        padding: 1 2;
        background: $background;
    }

    /* ── Messages ───────────────────────────────────────────────── */
    ChatMessage {
        height: auto;
        width: 100%;
        margin-bottom: 1;
    }

    .msg-content {
        height: auto;
        width: 100%;
        padding: 1 2;
    }

    .user-msg {
        background: #1a3a4a;
        border-left: tall cyan;
        color: white;
    }

    .agent-msg {
        background: #1a3a2a;
        border-left: tall green;
        color: white;
    }

    .system-msg {
        background: #3a3a1a;
        border-left: tall yellow;
        color: white;
    }

    /* ── Thinking Indicator ─────────────────────────────────────── */
    ThinkingIndicator {
        height: auto;
        width: 100%;
        padding: 1 2;
        background: #2a1a3a;
        border-left: tall magenta;
        margin-bottom: 1;
    }

    /* ── Toolbar ─────────────────────────────────────────────────── */
    #toolbar {
        height: 3;
        padding: 0 1;
        background: $surface;
        border-top: solid $primary 40%;
    }

    #toolbar Button {
        min-width: 12;
        margin-right: 1;
    }

    .toolbar-spacer {
        width: 1fr;
    }

    #status-label {
        width: auto;
        content-align: right middle;
        color: $text-muted;
        padding-right: 1;
    }

    /* ── Input ───────────────────────────────────────────────────── */
    #input-area {
        height: auto;
        padding: 0 1;
        background: $surface;
    }

    #chat_input {
        width: 100%;
        border: tall $accent 60%;
        background: $panel;
        height: 3;
    }

    #chat_input:focus {
        border: tall $primary;
    }

    /* ── Banner ──────────────────────────────────────────────────── */
    .banner {
        color: $primary;
        text-style: bold;
        padding: 1 2;
        text-align: center;
    }

    .welcome-msg {
        color: $text-muted;
        padding: 0 2 1 2;
        text-align: center;
    }

    /* ── System Alerts ──────────────────────────────────────────── */
    .system-alert {
        color: red;
        text-style: bold;
        padding: 1;
    }

    /* ── Stop Button ────────────────────────────────────────────── */
    #stop-btn {
        display: none;
    }

    #stop-btn.visible {
        display: block;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="main-container"):
            # Sidebar
            with Container(id="sidebar"):
                yield SoulSidebar()

            # Main chat area
            with Container(id="chat-container"):
                with ScrollableContainer(id="chat-history"):
                    banner = r"""
   _____                      ____  _            _
  / ___/____  ____ _________ / __ )| | __ _ ____| | __
  \__ \/ __ \/ __ `/ ___/ _ \ __  \| |/ _` / ___| |/ /
 ___/ / /_/ / /_/ / /__/  __/ |_) /| | (_| ( (__|   <
/____/ .___/\__,_/\___/\___/_____/_|\__,_|\___|_|\_\
    /_/"""
                    yield Static(f"[rgb(27,242,34)]{banner}[/]", classes="banner")
                    yield Static(
                        "Type a message to chat  |  /config  /skills  /tasks  |  Ctrl+X stop  Ctrl+R restart  Ctrl+L clear  |  Up/Down for prompt history",
                        classes="welcome-msg",
                    )

                # Toolbar with controls
                with Horizontal(id="toolbar"):
                    yield Button("Stop", variant="error", id="stop-btn")
                    yield Button("Clear", variant="default", id="clear-btn")
                    yield Button("Restart", variant="warning", id="restart-btn")
                    yield Button("🎙️ Speak", variant="success", id="voice-btn")
                    yield Static("", classes="toolbar-spacer")
                    yield Label("Auto-Speak: ")
                    yield Switch(value=True, id="auto_speak_switch")
                    yield Label("Ready", id="status-label")

                # Input
                with Container(id="input-area"):
                    yield ChatInput(placeholder="Type your message... (Up/Down for history)", id="chat_input")

        yield Footer()

    def on_mount(self):
        self.messages: list = load_chat_history()
        self._msg_count = len([m for m in self.messages if getattr(m, 'type', '') in ['human', 'ai']])
        self._agent_worker: Worker | None = None
        self._thinking_widget: ThinkingIndicator | None = None
        self._msg_count = 0
        self._processing = False  # Guard: is agent currently processing?
        self.update_status_bar()
        self.set_interval(60, self.scheduled_heartbeat)
        self.scheduled_heartbeat()
        
        # Mount existing chat history
        chat_history_widget = self.query_one("#chat-history")
        for msg in self.messages:
            role = "user" if msg.type == "human" else "agent" if msg.type == "ai" else "system"
            if role in ["user", "agent"] and msg.content and isinstance(msg.content, str) and msg.content.strip():
                 chat_history_widget.mount(ChatMessage(msg.content, role))
        
        # Auto-focus the input box
        self.query_one("#chat_input").focus()

    # ── Status Bar ─────────────────────────────────────────────────────────

    def update_status_bar(self):
        """Update the status label with model info and message count."""
        provider = "Unknown"
        model = "Unknown"
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    provider = data.get("provider", "?").capitalize()
                    model = data.get("model", "?")
            except: pass

        label = self.query_one("#status-label", Label)
        label.update(f"{provider}/{model} | {self._msg_count} msgs")
        self.sub_title = f"{provider} ({model})"

    # ── Heartbeat ──────────────────────────────────────────────────────────

    @work(exclusive=True, thread=True, group="heartbeat")
    def scheduled_heartbeat(self):
        # NEVER call process_agent_response from here — it would cancel user's work
        if self._processing:
            return  # Don't disturb active agent work
        try:
             result = run_autonomous_heartbeat()
             if result:
                 self.call_from_thread(self.display_system_alert, result)
        except Exception:
            pass

    def display_system_alert(self, text: str):
         chat_history = self.query_one("#chat-history")
         chat_history.mount(ChatMessage(text, "system"))
         chat_history.scroll_end()

    # ── Input Handling ─────────────────────────────────────────────────────

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        event.input.value = ""

        if not user_input:
            return

        # Add to prompt history
        chat_input = self.query_one("#chat_input", ChatInput)
        chat_input.add_to_history(user_input)

        if user_input.lower() in ["exit", "quit"]:
            self.exit()
            return

        if user_input.lower() == "/config":
            self.push_screen(ConfigScreen(), self.on_config_closed)
            return

        if user_input.lower() == "/skills":
            self.push_screen(SkillsScreen(), self.on_config_closed)
            return

        if user_input.lower() == "/tasks":
            self.push_screen(TasksScreen(), self.on_config_closed)
            return

        if user_input.lower() == "/stop":
            self.action_stop_agent()
            return

        # Display user message
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(user_input, "user"))
        chat_history.scroll_end()
        self._msg_count += 1
        self.update_status_bar()

        # Start agent processing
        self._agent_worker = self.process_agent_response(user_input)

    def on_config_closed(self, result):
        if result:
            self.update_status_bar()
            chat_history = self.query_one("#chat-history")
            chat_history.mount(ChatMessage("Configuration updated.", "system"))
            chat_history.scroll_end()

    # ── Agent Processing ───────────────────────────────────────────────────

    @work(exclusive=True, group="agent")
    async def process_agent_response(self, user_input: str) -> None:
        self._processing = True
        self.messages.append(HumanMessage(content=user_input))
        inputs = {"messages": self.messages}

        # Show thinking indicator
        self._show_thinking()

        try:
            result = await agent_app.ainvoke(inputs)

            # Remove thinking
            self._hide_thinking()

            latest_msg = result["messages"][-1]
            response_text = latest_msg.content

            self.messages = result["messages"]
            self._msg_count += 1
            self.update_status_bar()
            self._display_agent_message(response_text)
            
            # Persist chat history
            save_chat_history(self.messages)
            
            # Speak if enabled
            try:
                auto_speak = self.query_one("#auto_speak_switch", Switch).value
            except:
                auto_speak = False
                
            if auto_speak and response_text:
                self.speak_response(response_text)

        except asyncio.CancelledError:
            self._hide_thinking()
            self._display_system_message("Agent interrupted.")
        except Exception as e:
            self._hide_thinking()
            self._display_agent_message(f"Error: {str(e)}")
        finally:
            self._processing = False

    def _show_thinking(self):
        """Show animated thinking indicator and stop button."""
        chat_history = self.query_one("#chat-history")
        self._thinking_widget = ThinkingIndicator()
        chat_history.mount(self._thinking_widget)
        chat_history.scroll_end()

        # Show stop button
        stop_btn = self.query_one("#stop-btn")
        stop_btn.add_class("visible")

        # Update status
        label = self.query_one("#status-label", Label)
        label.update("Processing...")

    def _hide_thinking(self):
        """Remove thinking indicator and hide stop button."""
        if self._thinking_widget:
            try:
                self._thinking_widget.remove()
            except Exception:
                pass
            self._thinking_widget = None

        # Hide stop button
        try:
            stop_btn = self.query_one("#stop-btn")
            stop_btn.remove_class("visible")
        except Exception:
            pass

        self.update_status_bar()

    def _display_agent_message(self, text: str) -> None:
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(text, "agent"))
        chat_history.scroll_end()

    def _display_system_message(self, text: str) -> None:
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(text, "system"))
        chat_history.scroll_end()

    # ── Actions (bound to keys + buttons) ──────────────────────────────────

    def action_stop_agent(self) -> None:
        """Stop the currently running agent response directly via stored worker."""
        if self._agent_worker and not self._agent_worker.is_cancelled and not self._agent_worker.is_finished:
            self._agent_worker.cancel()
            self._hide_thinking()
            self._display_system_message("Agent stopped.")
            self._agent_worker = None
        else:
            self.notify("No active agent response to stop.", severity="warning")

    def action_clear_chat(self) -> None:
        """Clear the chat display (keep conversation memory)."""
        chat_history = self.query_one("#chat-history")
        chat_history.remove_children()
        chat_history.mount(Static("[bold cyan]Chat cleared.[/]", classes="welcome-msg"))
        self.notify("Chat display cleared.", severity="information")

    def action_restart_session(self) -> None:
        """Restart the agent session — clears all conversation memory."""
        # Stop any running worker
        self.action_stop_agent()

        # Reset state
        self.messages = []
        if os.path.exists(CHAT_HISTORY_FILE):
             try:
                 os.remove(CHAT_HISTORY_FILE)
             except: pass
             
        self._msg_count = 0

        # Clear and reset UI
        chat_history = self.query_one("#chat-history")
        chat_history.remove_children()
        chat_history.mount(Static("[bold green]Session restarted.[/] Conversation memory cleared.", classes="welcome-msg"))
        chat_history.scroll_end()

        self.update_status_bar()
        self.notify("Session restarted.", severity="information")

    def action_dismiss_modal(self) -> None:
        """Dismiss the top modal screen."""
        if self.screen_stack:
            try:
                self.pop_screen()
            except Exception:
                pass

    # ── Button Handler ──────────────────────────────────

    @on(Button.Pressed)
    def handle_toolbar_buttons(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "stop-btn":
            self.action_stop_agent()
        elif btn_id == "clear-btn":
            self.action_clear_chat()
        elif btn_id == "restart-btn":
            self.action_restart_session()
        elif btn_id == "voice-btn":
            self.action_record_voice()

    @work(exclusive=True, thread=True, group="voice")
    def action_record_voice(self) -> None:
        if not VOICE_AVAILABLE:
            self.call_from_thread(self.notify, "Voice not available. Install: pip install sounddevice numpy scipy", severity="error")
            return
        self.call_from_thread(self._display_system_message, "🎙️ Listening for 5 seconds...")
        try:
            audio_path = record_audio(duration=5)
            self.call_from_thread(self._display_system_message, "⏳ Transcribing...")
            
            provider = "google"
            stt_model = "gemini-2.5-flash"
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r") as f:
                        data = json.load(f)
                        provider = data.get("voice_provider", data.get("provider", "google"))
                        stt_model = data.get("stt_model", "gemini-2.5-flash")
                except: pass
            
            from brain.provider_models import get_stt_models
            stt_models_list = get_stt_models(provider)
            if stt_model not in stt_models_list:
                stt_model = stt_models_list[0] if stt_models_list else "gemini-2.5-flash"
            
            transcript = transcribe_audio(audio_path, provider, stt_model)
            
            if transcript:
                self.call_from_thread(self._submit_voice_text, transcript)
            else:
                 self.call_from_thread(self._display_system_message, "❌ No speech detected.")

        except Exception as e:
            self.call_from_thread(self.notify, f"Microphone error: {e}", severity="error")
            
    def _submit_voice_text(self, text: str):
        chat_history = self.query_one("#chat-history")
        chat_history.mount(ChatMessage(text, "user"))
        chat_history.scroll_end()
        self._msg_count += 1
        self.update_status_bar()
        self._agent_worker = self.process_agent_response(text)

    @work(exclusive=True, thread=True, group="voice_out")
    def speak_response(self, text: str) -> None:
        if not VOICE_AVAILABLE:
            return
        try:
            self.call_from_thread(self.notify, "Generating audio...", severity="information")
            
            provider = "google"
            tts_model = "gemini-2.5-flash"
            if os.path.exists(CONFIG_FILE):
                try:
                     with open(CONFIG_FILE, "r") as f:
                         data = json.load(f)
                         provider = data.get("voice_provider", data.get("provider", "google"))
                         tts_model = data.get("tts_model", "gemini-2.5-flash")
                except: pass
            
            from brain.provider_models import get_tts_models
            tts_models_list = get_tts_models(provider)
            if tts_model not in tts_models_list:
                tts_model = tts_models_list[0] if tts_models_list else "gemini-2.5-flash"
            
            audio_bytes = generate_audio_response(text, provider, tts_model)
            play_audio_bytes(audio_bytes)
        except Exception as e:
            self.call_from_thread(self.notify, f"Audio Error: {e}", severity="error")


if __name__ == "__main__":
    app = AgentInterface()
    app.run()
