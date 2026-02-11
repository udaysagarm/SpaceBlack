from textual.app import App
try:
    from textual.widgets import TabbedContent, TabPane
    print("Tabs available")
except ImportError:
    print("Tabs NOT available")
