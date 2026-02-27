import os
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile

def record_audio(duration: int = 5, fs: int = 44100) -> str:
    """
    Records audio from the default microphone for a specified duration.
    Returns the path to the temporary WAV file containing the recording.
    """
    print(f"\n🎙️  Listening for {duration} seconds...")
    # Record audio (mono)
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    print("✅  Done listening.")
    
    # Save to a temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav.write(temp_file.name, fs, recording)
    
    return temp_file.name
