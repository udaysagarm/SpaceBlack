
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tui import SkillsScreen
from textual.app import App, ComposeResult
from textual.widgets import Button

class DebugApp(App):
    def compose(self) -> ComposeResult:
         yield Button("Open Skills")

    def on_mount(self):
        self.push_screen(SkillsScreen())
        # self.set_timer(2.0, self.exit) # Keep it open for a bit if running manually, but for auto test close it.
        self.set_timer(2.0, self.exit)

if __name__ == "__main__":
    app = DebugApp()
    app.run()
