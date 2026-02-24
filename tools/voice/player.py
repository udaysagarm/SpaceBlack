import os
import tempfile
import base64
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np

def play_audio_file(file_path: str):
    """
    Plays a WAV audio file.
    """
    try:
        fs, data = wav.read(file_path)
        print("🔊 Speaking...")
        sd.play(data, fs)
        sd.wait()
    except Exception as e:
        print(f"Error playing audio: {e}")

def play_audio_bytes(audio_bytes: bytes):
    """
    Plays raw audio bytes (WAV format) directly.
    """
    try:
        # Write bytes to temp file and play
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio.flush()
            play_audio_file(temp_audio.name)
            
        # Clean up
        try:
            os.remove(temp_audio.name)
        except:
            pass
    except Exception as e:
        print(f"Error processing audio bytes: {e}")

def play_base64_audio(b64_string: str):
    """
    Decodes a base64 string to audio bytes and plays it.
    """
    try:
        audio_bytes = base64.b64decode(b64_string)
        play_audio_bytes(audio_bytes)
    except Exception as e:
        print(f"Error decoding base64 audio: {e}")
