"""
CommerceMind VoiceCare AI — Gemini LLM Service
Handles all 3 LLM calls: Intent+Sentiment+Priority, Resolution, Response.
Includes retry with exponential backoff and structured output.
"""

import json
import structlog
from typing import Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
)
import google.generativeai as genai

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


def _is_gemini_retryable(exc: Exception) -> bool:
    """Return True only for transient errors that are worth retrying.

    Skip retrying permanent failures (auth, bad-request, quota hard-limit) —
    they will keep failing and only waste time and quota.
    """
    try:
        import google.api_core.exceptions as _gapi
        if isinstance(exc, (_gapi.InvalidArgument, _gapi.PermissionDenied,
                             _gapi.NotFound, _gapi.Unauthenticated)):
            return False
    except ImportError:
        pass
    # Retry server-side / transient errors
    if hasattr(exc, "status_code") and exc.status_code < 500:  # type: ignore[attr-defined]
        return False
    return True


class GeminiService:
    """Service for interacting with Google Gemini 2.5 Flash-Lite."""

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception(_is_gemini_retryable),
        before_sleep=lambda retry_state: logger.warning(
            "gemini_retry",
            attempt=retry_state.attempt_number,
            wait=retry_state.next_action.sleep,
        ),
    )
    async def _call_gemini(
        self, prompt: str, system_instruction: str = "", max_output_tokens: int = 2048
    ) -> str:
        """Make a Gemini API call with retry logic and Groq fallback."""
        try:
            import google.api_core.exceptions as _gapi_exc
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=max_output_tokens,
                    response_mime_type="application/json",
                ),
                request_options={"timeout": 30},
            )
            return response.text
        except Exception as e:
            logger.error("gemini_call_failed", error=str(e))
            if settings.groq_api_key:
                logger.info("falling_back_to_groq_llm")
                import httpx
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                            json={
                                "model": "llama3-70b-8192",
                                "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.3,
                                "response_format": {"type": "json_object"}
                            }
                        )
                        if resp.status_code == 200:
                            return resp.json()["choices"][0]["message"]["content"]
                        else:
                            logger.error("groq_fallback_failed", status=resp.status_code, text=resp.text)
                except Exception as groq_err:
                    logger.error("groq_fallback_exception", error=str(groq_err))
            raise

    def _parse_json(self, text: str) -> dict:
        """Safely parse JSON from Gemini, stripping markdown if present."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    async def analyze_intent(
        self, query: str, language: str, conversation_history: list = None
    ) -> dict:
        """
        LLM Call 1: Extract intent, sentiment, and priority from customer query.
        Returns structured JSON with intent, sentiment, priority, and summary.
        """
        history_context = ""
        if conversation_history:
            history_context = f"\n\nConversation history:\n{json.dumps(conversation_history, indent=2)}"

        prompt = f"""You are an e-commerce customer support AI analyzing a customer query.
The customer speaks {language}. Analyze the following query and extract structured information.

Customer query: "{query}"{history_context}

Return a JSON object with exactly these fields:
{{
    "intent": "<one of: order_status, refund_status, return_request, payment_issue, delivery_delay, damaged_product, wrong_product, cancellation, exchange, general_inquiry>",
    "sub_intent": "<more specific description of what the customer wants>",
    "sentiment": "<one of: Neutral, Negative, Angry, Very Angry>",
    "priority": "<one of: Low, Medium, High, Critical>",
    "summary_english": "<brief English summary of the customer's issue>",
    "requires_order_lookup": <true/false>,
    "extracted_order_id": "<order ID if mentioned, null otherwise>",
    "extracted_phone": "<phone number if mentioned, null otherwise>",
    "extracted_name": "<customer name if mentioned, null otherwise>"
}}

Rules:
- If the customer sounds frustrated, set sentiment to Angry or Very Angry
- If the issue involves money (refund, payment) or damaged/wrong product, set priority to High
- If the customer mentions urgency or repeated complaints, set priority to Critical
- Always provide a concise summary_english regardless of input language"""

        try:
            result = await self._call_gemini(prompt)
            return self._parse_json(result)
        except Exception as e:
            logger.error("analyze_intent_fallback", error=str(e))
            return {
                "intent": "general_inquiry",
                "sub_intent": "user query fallback",
                "sentiment": "Neutral",
                "priority": "Medium",
                "summary_english": query,
                "requires_order_lookup": False,
                "extracted_order_id": None,
                "extracted_phone": None,
                "extracted_name": None
            }

    async def generate_resolution(
        self,
        query: str,
        intent: str,
        order_data: Optional[dict],
        policy_context: str,
        sentiment: str,
        conversation_history: list = None,
    ) -> dict:
        """
        LLM Call 2: Determine the resolution based on order data + policy.
        This is where policy-groundedness matters most.
        """
        order_context = "No order data available."
        if order_data:
            order_context = f"Order details:\n{json.dumps(order_data, indent=2, default=str)}"

        history_context = ""
        if conversation_history:
            history_context = f"\n\nConversation history (earlier turns in this session):\n{json.dumps(conversation_history[-6:], indent=2)}"

        prompt = f"""You are an e-commerce customer support AI making a resolution decision.

Customer issue: "{query}"
Detected intent: {intent}
Customer sentiment: {sentiment}

{order_context}

Relevant company policy sections:
{policy_context}{history_context}

Return a JSON object with exactly these fields:
{{
    "recommended_action": "<one of: Inform, Refund, Replace, Escalate, Reject, Apologize, Track>",
    "resolution_summary": "<ONE concise sentence: what you're recommending and why>",
    "policy_reference": "<exact quote or reference from the policy, or 'Standard Practice' if none provided>",
    "internal_note": "<note for the support team about this resolution>",
    "confidence_score": <0.0 to 1.0>,
    "requires_human_review": <true/false>,
    "reason_for_action": "<brief explanation of why this specific action was chosen>"
}}

Rules:
- Base your decision on the provided policy if relevant.
- If no specific policy covers this case, use standard e-commerce best practices (e.g., apologize, inform, track).
- Set confidence_score high (0.8+) if you can reasonably address the query, even without strict policy.
- ONLY set recommended_action to "Escalate" and requires_human_review to true if the issue is highly sensitive, involves fraud, or strictly requires a human manager."""

        try:
            result = await self._call_gemini(prompt)
            return self._parse_json(result)
        except Exception as e:
            logger.error("generate_resolution_fallback", error=str(e))
            return {
                "recommended_action": "Inform",
                "resolution_summary": "We are experiencing high traffic, but your request is noted.",
                "policy_reference": "Standard Practice",
                "internal_note": "AI rate limit hit, defaulted to basic resolution.",
                "confidence_score": 0.8,
                "requires_human_review": False,
                "reason_for_action": "System fallback"
            }

    async def generate_response(
        self,
        query: str,
        resolution: dict,
        language: str,
        customer_name: str = "Customer",
        conversation_history: list = None,
    ) -> dict:
        """
        LLM Call 3: Generate the final customer-facing response in their language.
        """
        history_context = ""
        if conversation_history:
            history_context = f"\nConversation history (for context):\n{json.dumps(conversation_history[-4:], indent=2)}\n"

        prompt = f"""You are a friendly, empathetic e-commerce customer support assistant.
Generate a natural, helpful response to the customer.

Original customer query: "{query}"
Customer name: {customer_name}
Target language: {language}
{history_context}Resolution decided: {json.dumps(resolution, indent=2, default=str)}

Return a JSON object with exactly these fields:
{{
    "response_text": "<the full response in {language} that the customer will hear>",
    "response_english": "<English translation of the response>",
    "tone": "<Professional / Empathetic / Apologetic / Reassuring>"
}}

Rules:
- Respond in {language} naturally, as a native speaker would
- Be empathetic and professional
- Reference specific details (order ID, dates, amounts) when available
- If the resolution involves tracking, provide the tracking details
- If escalating, explain that a human agent will follow up soon
- Keep the response conversational since it will be spoken aloud (TTS)
- Don't use markdown, bullet points, or formatting — use natural spoken language
- LENGTH: Be concise and adaptive. Simple queries (order status, tracking) → 1-2 sentences.
  Complex complaints (damaged/wrong product, refund disputes) → at most 3-4 sentences (~120 words max).
- Lead with the answer/resolution, then ONE key detail (order ID, date, or amount), then the next step.
- No filler, no repetition, no restating the question back. Every sentence must add information."""

        try:
            result = await self._call_gemini(prompt, max_output_tokens=768)
            return self._parse_json(result)
        except Exception as e:
            logger.error("generate_response_fallback", error=str(e))
            return {
                "response_text": "I apologize, but I am currently experiencing technical difficulties processing your request. Please hold on or try again later.",
                "response_english": "I apologize, but I am currently experiencing technical difficulties.",
                "tone": "Apologetic"
            }


# Singleton
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
