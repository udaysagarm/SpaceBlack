import os
from typing import Optional
from brain.provider_models import PROVIDERS

def get_llm(provider: str, model_name: str, temperature: float = 0.7, api_key: Optional[str] = None):
    """
    Returns a LangChain chat model instance based on the provider.
    """
    provider = provider.lower().strip()
    
    # 1. GOOGLE
    if provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
        except ImportError:
            raise ImportError("Please install langchain-google-genai to use Google models.")
            
        return ChatGoogleGenerativeAI(
            model=model_name, 
            temperature=temperature, 
            google_api_key=api_key or os.environ.get("GOOGLE_API_KEY"),
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
    # 2. OPENAI
    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("Please install langchain-openai to use OpenAI models.")
            
        return ChatOpenAI(
            model=model_name, 
            temperature=temperature, 
            api_key=api_key or os.environ.get("OPENAI_API_KEY")
        )
        
    # 3. ANTHROPIC
    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError("Please install langchain-anthropic to use Anthropic models.")
            
        return ChatAnthropic(
            model=model_name, 
            temperature=temperature, 
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    # 4. GROQ
    elif provider == "groq":
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ImportError("Please install langchain-groq to use Groq models.")
            
        return ChatGroq(
            model=model_name,
            temperature=temperature,
            api_key=api_key or os.environ.get("GROQ_API_KEY")
        )

    # 5. MISTRAL
    elif provider == "mistral":
        try:
            from langchain_mistralai import ChatMistralAI
        except ImportError:
            raise ImportError("Please install langchain-mistralai to use Mistral models.")
            
        return ChatMistralAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key or os.environ.get("MISTRAL_API_KEY")
        )

    # 6. OLLAMA
    elif provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError("Please install langchain-ollama to use Ollama models.")
            
        return ChatOllama(
            model=model_name,
            temperature=temperature
        )
        
    # 7. XAI
    elif provider == "xai":
        try:
            from langchain_xai import ChatXAI
        except ImportError:
            raise ImportError("Please install langchain-xai to use xAI models.")
        
        return ChatXAI(
            model=model_name,
            temperature=temperature,
            xai_api_key=api_key or os.environ.get("XAI_API_KEY")
        )
        
    else:
        supported = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider: {provider}. Supported: {supported}.")
