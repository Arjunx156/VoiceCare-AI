"""The nine supported languages, end to end.

VoiceCare's whole premise is that a customer speaks their own language, so a
language silently falling back to English is a product failure, not a cosmetic
one. These tests cover the two ways that happens: a language code getting lost
between the layers, and a native-script reply being mangled on the way out.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.constants import LANGUAGE_CODES, LANGUAGE_NAMES
from tests.conftest import make_mock_db, patch_all_services

# One utterance per language, in its own script, with the reply the pipeline
# should carry through untouched.
LANGUAGE_SAMPLES = [
    ("Hindi", "hi", "मेरा ऑर्डर कहाँ है?", "आपका ऑर्डर कल पहुँचेगा।"),
    ("English", "en", "Where is my order?", "Your order arrives tomorrow."),
    ("Malayalam", "ml", "എന്റെ ഓർഡർ എവിടെയാണ്?", "നിങ്ങളുടെ ഓർഡർ നാളെ എത്തും."),
    ("Tamil", "ta", "எனது ஆர்டர் எங்கே?", "உங்கள் ஆர்டர் நாளை வரும்."),
    ("Telugu", "te", "నా ఆర్డర్ ఎక్కడ ఉంది?", "మీ ఆర్డర్ రేపు వస్తుంది."),
    ("Kannada", "kn", "ನನ್ನ ಆರ್ಡರ್ ಎಲ್ಲಿದೆ?", "ನಿಮ್ಮ ಆರ್ಡರ್ ನಾಳೆ ಬರುತ್ತದೆ."),
    ("Bengali", "bn", "আমার অর্ডার কোথায়?", "আপনার অর্ডার আগামীকাল আসবে।"),
    ("Marathi", "mr", "माझी ऑर्डर कुठे आहे?", "तुमची ऑर्डर उद्या येईल."),
    ("Hinglish", "hi", "Mera order kahan hai?", "Aapka order kal aayega."),
]


def _memory():
    mem = MagicMock()
    mem.get_conversation_history = AsyncMock(return_value=[])
    mem.store_conversation_turn = AsyncMock()
    mem.get_session_context = AsyncMock(return_value=None)
    mem.set_session_context = AsyncMock()
    mem.get_cache = AsyncMock(return_value=None)
    mem.set_cache = AsyncMock()
    return mem


class TestLanguageCodeMapping:

    @pytest.mark.parametrize("display,code,_query,_reply", LANGUAGE_SAMPLES)
    def test_every_language_maps_to_its_bcp47_code(self, display, code, _query, _reply):
        """The display name the UI sends resolves to the code services expect."""
        assert LANGUAGE_CODES[display] == code

    def test_frontend_and_backend_language_lists_agree(self):
        """The two hardcoded language lists have not drifted apart.

        constants.py and frontend/src/lib/constants.ts are separate sources of
        truth. A language added to one and not the other fails at runtime, in
        the user's language, where nobody testing in English would notice.
        """
        import re
        from pathlib import Path

        frontend_constants = (
            Path(__file__).parents[3] / "frontend" / "src" / "lib" / "constants.ts"
        )
        source = frontend_constants.read_text(encoding="utf-8")

        block = re.search(r"export const LANGUAGES = \[(.*?)\] as const", source, re.S)
        assert block, "LANGUAGES array not found in frontend constants"
        frontend_languages = set(re.findall(r'"([^"]+)"', block.group(1)))

        assert frontend_languages == set(LANGUAGE_CODES.keys())

    def test_hinglish_is_served_by_the_hindi_voice(self):
        """Hinglish has no speech model of its own — Hindi is the deliberate choice."""
        assert LANGUAGE_CODES["Hinglish"] == LANGUAGE_CODES["Hindi"]

    def test_reverse_lookup_resolves_every_code(self):
        """Every code maps back to a display name for the UI and the ticket record."""
        for code in set(LANGUAGE_CODES.values()):
            assert LANGUAGE_NAMES[code] in LANGUAGE_CODES


class TestNativeScriptRoundTrip:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("display,code,query,reply", LANGUAGE_SAMPLES)
    async def test_reply_reaches_the_customer_in_their_own_script(
        self, display, code, query, reply
    ):
        """The native-script reply survives the pipeline byte for byte.

        Non-Latin scripts are where encoding bugs hide: they survive an English
        smoke test and corrupt every real customer interaction.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        gemini = MagicMock()
        gemini.generate_response = AsyncMock(
            return_value={
                "response_text": reply,
                "response_english": "Your order arrives tomorrow.",
                "tone": "empathetic",
            }
        )
        patches = patch_all_services(gemini, MagicMock(), MagicMock(), _memory())

        state = PipelineState(
            transcript_original=query,
            transcript_english="Where is my order?",
            language_detected=display,
            language_code=code,
            intent="order_status",
            recommended_action="Inform",
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.agent_response_generation(state)

        assert result.response_text == reply
        assert result.language_code == code

    @pytest.mark.asyncio
    @pytest.mark.parametrize("display,code,query,_reply", LANGUAGE_SAMPLES)
    async def test_intake_preserves_the_original_utterance(
        self, display, code, query, _reply
    ):
        """The customer's own words are kept alongside the English translation.

        transcript_original is what the support agent sees in the ticket; losing
        it means the human handling an escalation reads a paraphrase.
        """
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        patches = patch_all_services(MagicMock(), MagicMock(), MagicMock(), _memory())
        state = PipelineState(raw_text=query, language_detected=display, language_code=code)

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            result = await pipeline.agent_voice_intake(state)

        assert result.transcript_original == query
        assert result.has_error is False


class TestSpeechSynthesisRouting:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("display,code,_query,reply", LANGUAGE_SAMPLES)
    async def test_tts_is_asked_for_the_customers_language(
        self, display, code, _query, reply
    ):
        """Agent 8 requests speech in the detected language, never a default."""
        from app.agents.pipeline import VoiceCarePipeline
        from app.agents.state import PipelineState

        bhashini = MagicMock()
        bhashini.text_to_speech = AsyncMock(return_value="base64audio")
        patches = patch_all_services(MagicMock(), bhashini, MagicMock(), _memory())

        state = PipelineState(
            response_text=reply, language_detected=display, language_code=code
        )

        with patches[0], patches[1], patches[2], patches[3]:
            pipeline = VoiceCarePipeline(db=make_mock_db())
            await pipeline.agent_tts(state)

        bhashini.text_to_speech.assert_awaited_once()
        requested_language = bhashini.text_to_speech.await_args.args[1]
        assert requested_language == code


class TestBrowserTranscriptAcrossScripts:

    @pytest.mark.parametrize("display,code,query,_reply", LANGUAGE_SAMPLES)
    def test_native_script_utterances_clear_the_trust_threshold(
        self, display, code, query, _reply
    ):
        """The Whisper-skip length guard does not disadvantage dense scripts.

        Indic scripts pack far more meaning per character than Latin, so a
        character-count floor tuned on English could reject a perfectly good
        Tamil or Telugu transcript and force a needless STT round trip.
        """
        from app.agents.pipeline import _MIN_BROWSER_TRANSCRIPT_CHARS

        assert len(query.strip()) >= _MIN_BROWSER_TRANSCRIPT_CHARS

    def test_noise_fragments_are_still_rejected(self):
        """The floor exists to reject mis-heard noise, and still does."""
        from app.agents.pipeline import _MIN_BROWSER_TRANSCRIPT_CHARS

        for fragment in ("uh", "hmm", "a", "क"):
            assert len(fragment.strip()) < _MIN_BROWSER_TRANSCRIPT_CHARS
