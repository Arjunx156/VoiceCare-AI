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
from google import genai
from google.genai import types as genai_types

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Per-call output ceilings. These are blast-radius guardrails, not a speedup —
# a well-behaved model stops at its stop token regardless. Call 3 stays generous
# because it emits BOTH the native-script reply and its English translation, and
# Devanagari/Tamil cost 3-4x more tokens per character; a truncated response
# fails JSON parsing and falls through to the apologetic fallback, which is far
# worse for the customer than a few hundred extra milliseconds.
#
# These ceilings only hold while thinking is off (see _THINKING_BUDGET). On
# gemini-2.5-* thinking tokens are drawn from max_output_tokens, and an
# unbudgeted call spends 500-600 of them before writing a single character of
# JSON — which silently truncated every resolution call at 640.
_MAX_TOKENS_INTENT = 512
_MAX_TOKENS_RESOLUTION = 640
_MAX_TOKENS_RESPONSE = 2048

# 0 disables thinking outright. Every prompt here asks for a fixed JSON shape
# from a short context; none of them benefit from a reasoning budget, and all of
# them sit on the customer's critical path.
_THINKING_BUDGET = 0

# Cap on a single history turn's text inside a prompt.
_MAX_HISTORY_CHARS_PER_TURN = 300


def _is_gemini_retryable(exc: Exception) -> bool:
    """Return True only for transient errors that are worth retrying.

    Skip retrying every 4xx — auth, bad-request, model-not-found, and 429. The
    free-tier limit that actually bites here is a per-DAY request quota, so a
    backed-off retry cannot clear it and only adds dead air to the customer's
    critical path. Quota exhaustion is already handled by the Groq fallback in
    _call_gemini, which runs before this predicate is ever consulted.
    """
    code = getattr(exc, "code", None)
    if not isinstance(code, int):
        code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code >= 500
    return True


class GeminiService:
    """Service for interacting with Google Gemini 2.5 Flash-Lite."""

    MODEL = "gemini-2.5-flash"

    def __init__(self):
        # google-genai, not the retired google-generativeai package: the latter
        # has no thinking_config field at all, so the budget below could never
        # be applied and every call silently ran with thinking enabled.
        self.client = genai.Client(api_key=settings.gemini_api_key)

    # 2 attempts, not 3: each attempt carries a 12s timeout plus an inline Groq
    # fallback, so 3 attempts meant ~90s of dead air before the caller gave up.
    @retry(
        stop=stop_after_attempt(2),
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
            config = genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
                # Thinking tokens are drawn from max_output_tokens, so leaving
                # this unset burns the whole budget before any JSON is written.
                thinking_config=genai_types.ThinkingConfig(
                    thinking_budget=_THINKING_BUDGET
                ),
                http_options=genai_types.HttpOptions(timeout=12_000),
            )

            # client.aio, NOT the sync client: the sync method blocks the uvicorn
            # event loop for the whole call (1.5-5s x3 per turn), which stalls the
            # WS keep-alive ping and makes the asyncio.gather in pipeline.run()
            # fake parallelism.
            response = await self.client.aio.models.generate_content(
                model=self.MODEL, contents=prompt, config=config
            )

            # A truncated candidate still returns 200 with partial JSON, which
            # fails downstream in _parse_json as an opaque "Unterminated string"
            # and degrades the turn to a canned fallback. Name it here instead.
            candidate = (response.candidates or [None])[0]
            finish_reason = getattr(candidate, "finish_reason", None)
            if finish_reason is not None and str(finish_reason).endswith("MAX_TOKENS"):
                logger.warning(
                    "gemini_response_truncated",
                    max_output_tokens=max_output_tokens,
                    usage=str(getattr(response, "usage_metadata", None)),
                )
            return response.text
        except Exception as e:
            logger.error("gemini_call_failed", error=str(e))
            if settings.groq_api_key:
                logger.info("falling_back_to_groq_llm")
                from app.core.http import get_http_client
                try:
                    client = get_http_client()
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                        json={
                            # llama3-70b-8192 was decommissioned by Groq; use the
                            # current 70B model so this fallback actually works when
                            # Gemini hits its free-tier quota (429).
                            "model": "llama-3.3-70b-versatile",
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.3,
                            "response_format": {"type": "json_object"}
                        },
                        timeout=15.0,
                    )
                    if resp.status_code == 200:
                        return resp.json()["choices"][0]["message"]["content"]
                    else:
                        logger.error("groq_fallback_failed", status=resp.status_code, text=resp.text)
                except Exception as groq_err:
                    logger.error("groq_fallback_exception", error=str(groq_err))
            raise

    @staticmethod
    def _compact_history(history: list, max_turns: int) -> str:
        """Serialise the last N conversation turns as compact JSON.

        Every token of prompt input costs time-to-first-token. The history was
        previously dumped with indent=2 (20-40% pure whitespace) and, in
        analyze_intent, entirely unbounded — a long session could push thousands
        of stale tokens into every single call.
        """
        if not history:
            return ""
        trimmed = [
            {**turn, "content": str(turn.get("content", ""))[:_MAX_HISTORY_CHARS_PER_TURN]}
            if isinstance(turn, dict) else turn
            for turn in history[-max_turns:]
        ]
        return json.dumps(trimmed, separators=(",", ":"), default=str)

    def _parse_json(self, text: str) -> dict:
        """Safely parse JSON from Gemini, stripping markdown if present."""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # The callers turn this into a canned fallback answer, so without the
            # offending payload a truncation looks identical to an outage.
            logger.error("gemini_json_parse_failed", chars=len(text), preview=text[:200])
            raise

    async def analyze_intent(
        self, query: str, language: str, conversation_history: list = None
    ) -> dict:
        """
        LLM Call 1: Extract intent, sentiment, and priority from customer query.
        Returns structured JSON with intent, sentiment, priority, and summary.
        """
        history_context = ""
        if conversation_history:
            history_context = f"\n\nConversation history:\n{self._compact_history(conversation_history, 4)}"

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
            result = await self._call_gemini(prompt, max_output_tokens=_MAX_TOKENS_INTENT)
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
            order_context = f"Order details:\n{json.dumps(order_data, separators=(',', ':'), default=str)}"

        history_context = ""
        if conversation_history:
            history_context = f"\n\nConversation history (earlier turns in this session):\n{self._compact_history(conversation_history, 4)}"

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
- ONLY set recommended_action to "Escalate" and requires_human_review to true if the issue is highly sensitive, involves fraud, or strictly requires a human manager.
- When referring to the order, use the short "order_number" (e.g. ORD-7K3F). NEVER use the long internal "order_id" UUID."""

        try:
            result = await self._call_gemini(prompt, max_output_tokens=_MAX_TOKENS_RESOLUTION)
            return self._parse_json(result)
        except Exception as e:
            logger.error("generate_resolution_fallback", error=str(e))
            return {
                "recommended_action": "Inform",
                "resolution_summary": "We are experiencing high traffic, but your request is noted.",
                "policy_reference": "Standard Practice",
                "internal_note": "AI rate limit hit, defaulted to basic resolution.",
                # Honest low confidence: the LLM never ran, so the value must
                # trip escalation Rule 5 (< 0.4) instead of masking the outage.
                "confidence_score": 0.3,
                "requires_human_review": True,
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
            history_context = f"\nConversation history (for context):\n{self._compact_history(conversation_history, 2)}\n"

        prompt = f"""You are a friendly, empathetic e-commerce customer support assistant.
Generate a natural, helpful response to the customer.

Original customer query: "{query}"
Customer name: {customer_name}
Target language: {language}
{history_context}Resolution decided: {json.dumps(resolution, separators=(',', ':'), default=str)}

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
- Lead with the answer/resolution, then ONE key detail (short order number like ORD-7K3F, date, or amount), then the next step.
- When referencing an order use the short "order_number" field (e.g. ORD-7K3F). NEVER read the long internal UUID order_id.
- No filler, no repetition, no restating the question back. Every sentence must add information."""

        try:
            result = await self._call_gemini(prompt, max_output_tokens=_MAX_TOKENS_RESPONSE)
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
