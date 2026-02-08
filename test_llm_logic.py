
import os
import json
import unittest
from unittest.mock import patch, MagicMock
from brain.llm_factory import get_llm
from agent_logic import load_config


class TestLLMFactory(unittest.TestCase):
    def test_google_provider(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_key"}):
            with patch("langchain_google_genai.ChatGoogleGenerativeAI") as mock_cls:
                get_llm("google", "gemini-1.5-pro")
                mock_cls.assert_called_once()
                self.assertEqual(mock_cls.call_args[1]["model"], "gemini-1.5-pro")

    def test_openai_provider(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake_key"}):
            with patch("langchain_openai.ChatOpenAI") as mock_cls:
                get_llm("openai", "gpt-4o")
                mock_cls.assert_called_once()
                self.assertEqual(mock_cls.call_args[1]["model"], "gpt-4o")

    def test_anthropic_provider(self):
         with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake_key"}):
            with patch("langchain_anthropic.ChatAnthropic") as mock_cls:
                get_llm("anthropic", "claude-3-opus")
                mock_cls.assert_called_once()
                self.assertEqual(mock_cls.call_args[1]["model"], "claude-3-opus")

    def test_invalid_provider(self):
        with self.assertRaises(ValueError):
            get_llm("unknown", "model")

class TestAgentConfig(unittest.TestCase):
    def setUp(self):
        self.config_file = "config.json"
        
    def tearDown(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_load_default_config(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        config = load_config()
        self.assertEqual(config["provider"], "openai")

    def test_load_custom_config(self):
        with open(self.config_file, "w") as f:
            json.dump({"provider": "google", "model": "gemini-pro"}, f)
        config = load_config()
        self.assertEqual(config["provider"], "google")
        self.assertEqual(config["model"], "gemini-pro")

if __name__ == "__main__":
    unittest.main()
