import os
from gtts import gTTS

def generate_speech(text: str, lang: str, output_path: str):
    """
    Converts text to speech in the specified language and saves it as an MP3 file.
    
    :param text: The text to be converted to speech.
    :param lang: ISO language code ('en', 'hi', 'es').
    :param output_path: Full absolute path to save the generated audio file (.mp3).
    """
    try:
        # Fallback to English if lang is obscure
        if lang not in ['en', 'hi', 'es']:
            lang = 'en'
            
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error generating TTS: {e}")
        raise e
