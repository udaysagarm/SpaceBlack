
import os
from typing import Optional

def get_llm(provider: str, model_name: str, temperature: float = 0.7, api_key: Optional[str] = None):
    """
    Returns a LangChain chat model instance based on the provider.
    
    Args:
        provider: 'google', 'openai', or 'anthropic'
        model_name: e.g. 'gemini-1.5-pro', 'gpt-4o', 'claude-3-5-sonnet'
        temperature: randomness of the output
        api_key: Optional API key. If not provided, it's expected to be in the environment.
    """
    provider = provider.lower().strip()
    
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
        
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: google, openai, anthropic.")
