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

# ---- Input size limits (shared by REST schema, WS handler, body middleware) ----
# ~10 MB audio limit expressed as base64 character count (10 * 1024 * 1024 * 4 / 3)
MAX_AUDIO_B64_LEN = 14_316_558
# Max plain-text query length to prevent LLM abuse / DoS via massive prompts
MAX_TEXT_LEN = 5_000
# Hard cap on any request body — slightly above the audio limit to leave
# room for JSON framing around a maximal payload.
MAX_BODY_BYTES = 15 * 1024 * 1024
