"""
CommerceMind VoiceCare AI — Bhashini STT/TTS Service
Handles speech-to-text and text-to-speech via Bhashini API
for 8 Indian languages + Hinglish.
"""

import asyncio
import base64
import time
import httpx
import structlog
from typing import Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.constants import LANGUAGE_CODES, LANGUAGE_NAMES
from app.core.http import get_http_client

logger = structlog.get_logger()
settings = get_settings()

# The ULCA model-pipeline response is static per (task, language) — the same
# serviceId, callbackUrl and inference key every time — yet it was re-fetched
# over HTTPS before every single STT/TTS call, doubling the round trips.
# Cached with a TTL rather than forever so a rotated inference key eventually
# heals on its own; the 401/403 force-refresh below handles it immediately.
_PIPELINE_CONFIG_CACHE: dict[tuple, tuple[float, dict]] = {}
_PIPELINE_CONFIG_TTL_SECONDS = 6 * 3600
_config_lock = asyncio.Lock()


def reset_pipeline_config_cache() -> None:
    """Clear the config cache. Used by tests to prevent cross-test bleed."""
    _PIPELINE_CONFIG_CACHE.clear()


class BhashiniService:
    """Service for Bhashini Speech-to-Text and Text-to-Speech."""

    def __init__(self):
        self.user_id = settings.bhashini_user_id
        self.api_key = settings.bhashini_api_key
        self.pipeline_url = settings.bhashini_pipeline_url
        self.timeout = settings.bhashini_timeout

    async def _get_pipeline_config(
        self,
        task_type: str,
        source_lang: str,
        target_lang: str = None,
        *,
        force_refresh: bool = False,
    ) -> dict:
        """Fetch pipeline configuration from Bhashini, cached per (task, language)."""
        cache_key = (task_type, source_lang, target_lang)
        now = time.monotonic()

        if not force_refresh:
            hit = _PIPELINE_CONFIG_CACHE.get(cache_key)
            if hit and now - hit[0] < _PIPELINE_CONFIG_TTL_SECONDS:
                return hit[1]

        # Serialise misses so a cold start with several concurrent turns issues
        # one config fetch, not one per turn.
        async with _config_lock:
            if not force_refresh:
                hit = _PIPELINE_CONFIG_CACHE.get(cache_key)
                if hit and time.monotonic() - hit[0] < _PIPELINE_CONFIG_TTL_SECONDS:
                    return hit[1]

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

            client = get_http_client()
            response = await client.post(
                "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code != 200:
                logger.error("bhashini_pipeline_error", status_code=response.status_code, text=response.text, payload=payload)
            response.raise_for_status()
            config = response.json()
            _PIPELINE_CONFIG_CACHE[cache_key] = (time.monotonic(), config)
            return config

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

            client = get_http_client()
            response = await client.post(
                callback_url, json=payload, headers=headers, timeout=self.timeout
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

    async def _tts_inference(
        self, text: str, target_language: str, gender: str, *, force_refresh: bool = False
    ) -> str:
        """One config lookup (usually cached) + one inference call."""
        config = await self._get_pipeline_config(
            "tts", target_language, force_refresh=force_refresh
        )

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

        client = get_http_client()
        response = await client.post(
            callback_url, json=payload, headers=headers, timeout=self.timeout
        )
        response.raise_for_status()
        result = response.json()

        return (
            result.get("pipelineResponse", [{}])[0]
            .get("audio", [{}])[0]
            .get("audioContent", "")
        )

    # 2 attempts, not 3: each carries a 30s timeout plus a chunked gTTS fallback,
    # so 3 attempts could keep a background task alive for minutes.
    @retry(
        stop=stop_after_attempt(2),
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
            try:
                audio_base64 = await self._tts_inference(text, target_language, gender)
            except httpx.HTTPStatusError as auth_exc:
                # A cached inference key that has since rotated would otherwise
                # break audio for the full 6h cache TTL. Refetch once and retry.
                if auth_exc.response.status_code not in (401, 403):
                    raise
                logger.warning("bhashini_key_stale_refreshing", language=target_language)
                audio_base64 = await self._tts_inference(
                    text, target_language, gender, force_refresh=True
                )

            logger.info(
                "tts_success",
                language=target_language,
                text_length=len(text),
            )
            return audio_base64

        except Exception as e:
            logger.error("tts_failed", error=str(e), language=target_language)
            # The gTTS fallback ships the customer-facing response text (which
            # can include names, order codes, amounts) to translate.google.com.
            # Privacy-sensitive deployments disable it via ALLOW_GTTS_FALLBACK
            # and deliver the answer text-only when Bhashini TTS is down.
            from app.core.config import get_settings
            if not get_settings().allow_gtts_fallback:
                logger.info("gtts_fallback_disabled", reason="allow_gtts_fallback=false")
                return None  # Let frontend fall back to browser TTS

            # Fallback: split text into ≤200-char chunks (Google TTS URL limit),
            # fetch each chunk as MP3, concatenate the raw bytes, and return
            # the result base64-encoded with a "mp3" marker so the frontend
            # can use the right MIME type.
            logger.info("falling_back_to_gtts")
            try:
                import urllib.parse
                import base64 as b64mod
                lang_code = target_language if target_language != "en" else "en"

                # Split on sentence boundaries first, then hard-chunk at 200 chars.
                chunks: list[str] = []
                for sentence in text.replace("।", ".").split("."):
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    while len(sentence) > 200:
                        chunks.append(sentence[:200])
                        sentence = sentence[200:]
                    if sentence:
                        chunks.append(sentence)

                audio_parts: list[bytes] = []
                client = get_http_client()
                for chunk in chunks:
                    encoded = urllib.parse.quote(chunk)
                    url = (
                        f"https://translate.google.com/translate_tts"
                        f"?ie=UTF-8&total=1&idx=0&textlen={len(chunk)}"
                        f"&client=tw-ob&q={encoded}&tl={lang_code}"
                    )
                    resp = await client.get(url, timeout=10.0)
                    resp.raise_for_status()
                    audio_parts.append(resp.content)

                combined = b"".join(audio_parts)
                # Prefix with "mp3:" so the frontend knows the MIME type.
                return "mp3:" + b64mod.b64encode(combined).decode("utf-8")
            except Exception as fallback_e:
                logger.error("gtts_fallback_failed", error=str(fallback_e))
                return None  # Let frontend fall back to browser TTS

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

            client = get_http_client()
            response = await client.post(
                callback_url, json=payload, headers=headers, timeout=self.timeout
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
