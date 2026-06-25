"""
Mock fixtures for Bhashini STT/TTS responses.
"""

# STT response tuples: (transcript, detected_language_code)
STT_RESPONSES = {
    "hindi_order_status": ("मेरा ऑर्डर कहाँ है?", "hi"),
    "english_refund": ("I want a refund for my order", "en"),
    "tamil_complaint": ("என் ஆர்டர் வரவில்லை", "ta"),
    "hindi_payment": ("मेरा पेमेंट कट गया लेकिन ऑर्डर नहीं आया", "hi"),
}

# Translation responses
TRANSLATION_RESPONSES = {
    "hindi_to_english": "Where is my order?",
    "tamil_to_english": "My order has not arrived",
}

# TTS responses (base64-encoded audio placeholder strings)
TTS_RESPONSES = {
    "hindi_response": "SGluZGkgYXVkaW9fYmFzZTY0X3BsYWNlaG9sZGVy",
    "english_response": "RW5nbGlzaF9hdWRpb19iYXNlNjRfcGxhY2Vob2xkZXI=",
}

# Error simulation triggers
STT_ERROR_SCENARIOS = {
    "network_timeout": Exception("Connection timeout to Bhashini API"),
    "invalid_credentials": Exception("401 Unauthorized — invalid Bhashini credentials"),
    "audio_format_unsupported": Exception("Unsupported audio format"),
}
