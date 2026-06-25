"""
CommerceMind VoiceCare AI — Shared Constants
"""

# Maps display language names to BCP-47 codes used by Bhashini and other services.
# Hinglish is treated as Hindi for STT/TTS purposes.
LANGUAGE_CODES: dict[str, str] = {
    "Hindi": "hi",
    "English": "en",
    "Malayalam": "ml",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Bengali": "bn",
    "Marathi": "mr",
    "Hinglish": "hi",
}

LANGUAGE_NAMES: dict[str, str] = {v: k for k, v in LANGUAGE_CODES.items()}
