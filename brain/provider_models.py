# Centralized mapping of Providers to their Supported Models

PROVIDERS = {
    "google": {
        "name": "Google (Gemini)",
        "env_var": "GOOGLE_API_KEY",
        "chat_models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-3.1-pro-preview",
            "gemini-3-flash-preview",
            "gemini-3-pro-preview"
        ],
        "tts_models": ["gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"],
        "stt_models": ["gemini-2.5-flash", "gemini-2.0-flash"]
    },
    "openai": {
        "name": "OpenAI",
        "env_var": "OPENAI_API_KEY",
        "chat_models": [
            "gpt-5.2",
            "gpt-4.1",
            "gpt-4.1-mini",
            "gpt-4.1-nano",
            "gpt-4o",
            "gpt-4o-mini",
            "o3",
            "o4-mini"
        ],
        "tts_models": ["tts-1", "tts-1-hd"],
        "stt_models": ["whisper-1"]
    },
    "anthropic": {
        "name": "Anthropic",
        "env_var": "ANTHROPIC_API_KEY",
        "chat_models": [
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5"
        ],
        "tts_models": [],
        "stt_models": []
    },
    "groq": {
        "name": "Groq",
        "env_var": "GROQ_API_KEY",
        "chat_models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b"
        ],
        "tts_models": [],
        "stt_models": ["whisper-large-v3", "whisper-large-v3-turbo"]
    },
    "mistral": {
        "name": "Mistral AI",
        "env_var": "MISTRAL_API_KEY",
        "chat_models": [
            "mistral-large-3-latest",
            "mistral-medium-3.1-latest",
            "mistral-small-3.2-latest",
            "codestral-latest",
            "pixtral-large-latest",
            "ministral-8b-latest",
            "ministral-3b-latest"
        ],
        "tts_models": [],
        "stt_models": []
    },
    "ollama": {
        "name": "Ollama (Local)",
        "env_var": None,  # Ollama runs locally without an API key typically
        "chat_models": [
            "llama3.3",
            "llama3.2",
            "qwen3",
            "qwen2.5",
            "qwen2.5-coder",
            "phi4",
            "gemma2",
            "mistral",
            "deepseek-r1",
            "deepseek-v3"
        ],
        "tts_models": [],
        "stt_models": []
    },
    "xai": {
        "name": "xAI",
        "env_var": "XAI_API_KEY",
        "chat_models": [
            "grok-4",
            "grok-3",
            "grok-3-mini"
        ],
        "tts_models": [],
        "stt_models": []
    }
}

def get_provider_list():
    """Return a list of tuples (name, id) for Select UI dropdowns."""
    return [(pd["name"], pid) for pid, pd in PROVIDERS.items()]

def get_chat_models(provider_id: str):
    """Return a list of chat models for a given provider."""
    provider_data = PROVIDERS.get(provider_id, {})
    return provider_data.get("chat_models", [])

def get_tts_models(provider_id: str):
    """Return a list of TTS models for a given provider."""
    provider_data = PROVIDERS.get(provider_id, {})
    return provider_data.get("tts_models", [])

def get_stt_models(provider_id: str):
    """Return a list of STT models for a given provider."""
    provider_data = PROVIDERS.get(provider_id, {})
    return provider_data.get("stt_models", [])
