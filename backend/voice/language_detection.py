from langdetect import detect, DetectorFactory

# Enforce consistent deterministic results in langdetect
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """
    Detects the language of the given text.
    Expected outputs for this project: 'en' (English), 'hi' (Hindi), 'es' (Spanish)
    Defaults to 'en' if detection fails or language is out of scope.
    """
    if not text or not text.strip():
        return "en"
        
    try:
        # detect() returns the ISO 639-1 language code
        lang = detect(text)
        
        # Verify it falls into our supported buckets
        if lang in ["en", "hi", "es"]:
            return lang
            
        # Fallback to english if they speak French, German, etc.
        return "en"
    except Exception as e:
        print(f"Language detection failed (e.g. text was just numbers) - defaulting to 'en'. Error: {e}")
        return "en"
