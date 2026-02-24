# Centralized mapping of Providers to their Supported Models

PROVIDERS = {
    "google": {
        "name": "Google (Gemini)",
        "env_var": "GOOGLE_API_KEY",
        "chat_models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-2.0-pro-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b"
        ],
        "tts_models": ["gemini-2.5-flash", "gemini-2.5-flash-preview-tts", "gemini-2.0-flash"],
        "stt_models": ["gemini-2.5-flash", "gemini-2.0-flash"]
    },
    "openai": {
        "name": "OpenAI",
        "env_var": "OPENAI_API_KEY",
        "chat_models": [
            "gpt-4.5-preview",
            "gpt-4o",
            "gpt-4o-mini",
            "o1",
            "o1-mini",
            "o1-preview",
            "o3-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        "tts_models": ["tts-1", "tts-1-hd"],
        "stt_models": ["whisper-1"]
    },
    "anthropic": {
        "name": "Anthropic",
        "env_var": "ANTHROPIC_API_KEY",
        "chat_models": [
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
            "claude-3-opus-latest"
        ],
        "tts_models": [],
        "stt_models": []
    },
    "groq": {
        "name": "Groq",
        "env_var": "GROQ_API_KEY",
        "chat_models": [
            "llama3-70b-8192",
            "llama3-8b-8192",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "llama-3.2-11b-vision-preview",
            "llama-3.2-3b-preview",
            "llama-3.2-90b-vision-preview",
            "llama-3.3-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "deepseek-r1-distill-llama-70b"
        ],
        "tts_models": [],
        "stt_models": ["whisper-large-v3", "whisper-large-v3-turbo", "distil-whisper-large-v3-en"]
    },
    "mistral": {
        "name": "Mistral AI",
        "env_var": "MISTRAL_API_KEY",
        "chat_models": [
            "mistral-large-latest",
            "mistral-small-latest",
            "open-mistral-nemo",
            "open-mixtral-8x22b",
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
            "llama3",
            "llama3.1",
            "llama3.2",
            "mistral",
            "phi3",
            "qwen2.5",
            "qwen2.5-coder",
            "gemma2",
            "deepseek-r1",
            "deepseek-coder-v2"
        ],
        "tts_models": [],
        "stt_models": []
    },
    "xai": {
        "name": "xAI",
        "env_var": "XAI_API_KEY",
        "chat_models": [
            "grok-2",
            "grok-2-latest",
            "grok-beta",
            "grok-vision-beta"
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
