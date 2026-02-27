import os
import base64
import requests

def transcribe_audio(file_path: str, provider: str, stt_model: str = None, api_key: str = None) -> str:
    """
    Transcribes audio from a WAV file to text using the specified API provider.
    """
    provider = provider.lower().strip()
    
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=stt_model or "whisper-1", 
                file=audio_file,
                response_format="text"
            )
        return transcript.strip() if transcript else ""
        
    elif provider == "google":
        from google import genai
        from google.genai import types
        # Gemini 1.5 or 2.5 supports native audio STT
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        client = genai.Client(api_key=key)
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type='audio/wav')
        
        response = client.models.generate_content(
            model=stt_model or 'gemini-2.5-flash',
            contents=[
                audio_part, 
                "Transcribe this audio exactly. Only return the transcribed text, without any additional comments or formatting."
            ]
        )
        return response.text.strip() if response.text else ""
        
    elif provider == "groq":
        from groq import Groq
        client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY"))
        with open(file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(file_path, audio_file.read()),
                model=stt_model or "whisper-large-v3-turbo",
                response_format="text",
            )
        return transcription.strip() if transcription else ""
        
    elif provider == "anthropic":
        raise NotImplementedError("Anthropic does not natively support Speech-to-Text API currently.")
    else:
        raise ValueError(f"Unknown provider for STT: {provider}")


def generate_audio_response(text: str, provider: str, tts_model: str = None, api_key: str = None) -> bytes:
    """
    Synthesizes speech from text using the specified API provider.
    Returns the raw WAV audio bytes.
    """
    provider = provider.lower().strip()
    
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        response = client.audio.speech.create(
            model=tts_model or "tts-1",
            voice="alloy",
            input=text
        )
        return response.content
        
    elif provider == "google":
        key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Google API Key not found.")
            
        # Using REST API for Gemini 2.5 Flash Audio Modality to avoid SDK version conflicts
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{tts_model or 'gemini-2.5-flash'}:generateContent?key={key}"
        payload = {
            "contents": [{
                "parts": [{"text": f"Generate audio for the following text transcript: {text}"}]
            }],
            "generationConfig": {
                "responseModalities": ["AUDIO"]
            }
        }
        res = requests.post(url, json=payload)
        
        if res.status_code == 200:
            data = res.json()
            try:
                # The response structure contains an inlineData block with base64 encoded audio
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ValueError("No candidates returned from Gemini TTS.")
                    
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inlineData" in part:
                        base64_audio = part["inlineData"]["data"]
                        return base64.b64decode(base64_audio)
                
                raise ValueError("No audio inlineData found in response parts.")
            except KeyError as e:
                raise ValueError(f"Unexpected response structure from Gemini: {e}")
        else:
            raise Exception(f"Gemini TTS request failed: {res.text}")
            
    elif provider == "anthropic":
        raise NotImplementedError("Anthropic does not natively support Text-to-Speech API currently.")
    else:
        raise ValueError(f"Unknown provider for TTS: {provider}")
