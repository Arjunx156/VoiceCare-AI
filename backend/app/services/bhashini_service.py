"""
CommerceMind VoiceCare AI — Bhashini STT/TTS Service
Handles speech-to-text and text-to-speech via Bhashini API
for 8 Indian languages + Hinglish.
"""

import base64
import httpx
import structlog
from typing import Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Language code mapping for Bhashini
LANGUAGE_CODES = {
    "Hindi": "hi",
    "English": "en",
    "Malayalam": "ml",
    "Tamil": "ta",
    "Telugu": "te",
    "Kannada": "kn",
    "Bengali": "bn",
    "Marathi": "mr",
    "Hinglish": "hi",  # Treated as Hindi for STT/TTS
}

LANGUAGE_NAMES = {v: k for k, v in LANGUAGE_CODES.items()}


class BhashiniService:
    """Service for Bhashini Speech-to-Text and Text-to-Speech."""

    def __init__(self):
        self.user_id = settings.bhashini_user_id
        self.api_key = settings.bhashini_api_key
        self.pipeline_url = settings.bhashini_pipeline_url
        self.timeout = settings.bhashini_timeout

    async def _get_pipeline_config(
        self, task_type: str, source_lang: str, target_lang: str = None
    ) -> dict:
        """Fetch pipeline configuration from Bhashini."""
        payload = {
            "pipelineTasks": [{"taskType": task_type, "config": {"language": {"sourceLanguage": source_lang}}}],
            "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"},
        }

        if target_lang:
            payload["pipelineTasks"][0]["config"]["language"]["targetLanguage"] = target_lang

        headers = {
            "userID": self.user_id,
            "ulcaApiKey": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline",
                json=payload,
                headers=headers,
            )
            if response.status_code != 200:
                logger.error("bhashini_pipeline_error", status_code=response.status_code, text=response.text, payload=payload)
            response.raise_for_status()
            return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
    )
    async def speech_to_text(
        self, audio_base64: str, source_language: str = "hi"
    ) -> Tuple[str, str]:
        """
        Convert speech to text using Bhashini STT.

        Args:
            audio_base64: Base64 encoded audio data
            source_language: Language code (hi, en, ta, etc.)

        Returns:
            Tuple of (transcript, detected_language_code)
        """
        try:
            # Get pipeline config for ASR
            config = await self._get_pipeline_config("asr", source_language)

            pipeline_config = config.get("pipelineResponseConfig", [{}])[0]
            service_id = pipeline_config.get("config", [{}])[0].get("serviceId", "")
            callback_url = config.get("pipelineInferenceAPIEndPoint", {}).get(
                "callbackUrl", self.pipeline_url
            )
            inference_key = config.get("pipelineInferenceAPIEndPoint", {}).get(
                "inferenceApiKey", {}).get("value", self.api_key
            )

            # Make STT request
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {"sourceLanguage": source_language},
                            "serviceId": service_id,
                            "audioFormat": "wav",
                            "samplingRate": 16000,
                        },
                    }
                ],
                "inputData": {
                    "audio": [{"audioContent": audio_base64}]
                },
            }

            headers = {
                "Authorization": inference_key,
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    callback_url, json=payload, headers=headers
                )
                response.raise_for_status()
                result = response.json()

            transcript = (
                result.get("pipelineResponse", [{}])[0]
                .get("output", [{}])[0]
                .get("source", "")
            )

            logger.info(
                "stt_success",
                language=source_language,
                transcript_length=len(transcript),
            )
            return transcript, source_language

        except Exception as e:
            logger.error("stt_failed", error=str(e), language=source_language)
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
    )
    async def text_to_speech(
        self, text: str, target_language: str = "hi", gender: str = "female"
    ) -> str:
        """
        Convert text to speech using Bhashini TTS.

        Args:
            text: Text to convert to speech
            target_language: Language code
            gender: Voice gender (male/female)

        Returns:
            Base64 encoded audio
        """
        try:
            config = await self._get_pipeline_config("tts", target_language)

            pipeline_config = config.get("pipelineResponseConfig", [{}])[0]
            service_id = pipeline_config.get("config", [{}])[0].get("serviceId", "")
            callback_url = config.get("pipelineInferenceAPIEndPoint", {}).get(
                "callbackUrl", self.pipeline_url
            )
            inference_key = config.get("pipelineInferenceAPIEndPoint", {}).get(
                "inferenceApiKey", {}).get("value", self.api_key
            )

            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {"sourceLanguage": target_language},
                            "serviceId": service_id,
                            "gender": gender,
                            "samplingRate": 16000,
                        },
                    }
                ],
                "inputData": {
                    "input": [{"source": text}]
                },
            }

            headers = {
                "Authorization": inference_key,
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    callback_url, json=payload, headers=headers
                )
                response.raise_for_status()
                result = response.json()

            audio_base64 = (
                result.get("pipelineResponse", [{}])[0]
                .get("audio", [{}])[0]
                .get("audioContent", "")
            )

            logger.info(
                "tts_success",
                language=target_language,
                text_length=len(text),
            )
            return audio_base64

        except Exception as e:
            logger.error("tts_failed", error=str(e), language=target_language)
            raise

    async def translate_text(
        self, text: str, source_lang: str, target_lang: str = "en"
    ) -> str:
        """Translate text between languages using Bhashini NMT."""
        if source_lang == target_lang:
            return text

        try:
            config = await self._get_pipeline_config("translation", source_lang, target_lang)

            pipeline_config = config.get("pipelineResponseConfig", [{}])[0]
            service_id = pipeline_config.get("config", [{}])[0].get("serviceId", "")
            callback_url = config.get("pipelineInferenceAPIEndPoint", {}).get(
                "callbackUrl", self.pipeline_url
            )
            inference_key = config.get("pipelineInferenceAPIEndPoint", {}).get(
                "inferenceApiKey", {}).get("value", self.api_key
            )

            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": source_lang,
                                "targetLanguage": target_lang,
                            },
                            "serviceId": service_id,
                        },
                    }
                ],
                "inputData": {
                    "input": [{"source": text}]
                },
            }

            headers = {
                "Authorization": inference_key,
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    callback_url, json=payload, headers=headers
                )
                response.raise_for_status()
                result = response.json()

            translated = (
                result.get("pipelineResponse", [{}])[0]
                .get("output", [{}])[0]
                .get("target", text)
            )

            logger.info(
                "translation_success",
                source=source_lang,
                target=target_lang,
            )
            return translated

        except Exception as e:
            logger.error("translation_failed", error=str(e))
            return text  # Fallback to original text


# Singleton
_bhashini_service: Optional[BhashiniService] = None


def get_bhashini_service() -> BhashiniService:
    global _bhashini_service
    if _bhashini_service is None:
        _bhashini_service = BhashiniService()
    return _bhashini_service
