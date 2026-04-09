import os
from faster_whisper import WhisperModel

# Load the model globally to prevent reloading on each request
# We use "small" instead of "base" because "small" recognizes non-English scripts (like Hindi Devanagari) much better and stops it from transliterating into English letters.
model_size = "small"
# Ensure device='cpu' to work on typical local machines unless explicitly configured for GPU
model = WhisperModel(model_size, device="cpu", compute_type="int8")

def transcribe_audio(file_path: str) -> str:
    """
    Uses faster-whisper to transcribe an audio file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at {file_path}")
        
    # task="transcribe" ensures it doesn't accidentally try to completely translate to English
    # beam_size helps improve accuracy lightly
    segments, info = model.transcribe(file_path, beam_size=5, task="transcribe")
    
    text = []
    for segment in segments:
        text.append(segment.text)
        
    return " ".join(text).strip()
