"""
CommerceMind VoiceCare AI — Gemini LLM Service
Handles all 3 LLM calls: Intent+Sentiment+Priority, Resolution, Response.
Includes retry with exponential backoff and structured output.
"""

import json
import time
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

# On every thinking-capable Gemini model (2.5 and 3.x alike) thinking tokens are
# drawn from max_output_tokens — they are
# spent BEFORE the first character of JSON is written. So the two numbers are
# not independent: the ceiling must cover the reasoning AND the whole payload.
#
# Every ceiling below is therefore *derived* from a thinking budget plus an
# explicit reserve for the JSON itself, so the invariant
# `max_output_tokens > thinking_budget` cannot silently drift again. It drifted
# once: intent ran with a 768 ceiling against a 1024 budget, which left nothing
# for output — every intent call came back truncated, fell through to the
# fallback dict, and returned extracted_order_id=None. That is what made agent 3
# skip the DB entirely and report 0 ms even when the customer spoke an order
# number.
#
# The ceilings are blast-radius guardrails, not a speed dial — a well-behaved
# model stops at its stop token regardless, and an unused ceiling costs nothing.
# Call 3's reserve is the largest because it emits BOTH the native-script reply
# and its English translation, and Devanagari/Tamil cost 3-4x more tokens per
# character.

# Reasoning allowance per call. Resolution gets the most: it is the one call
# that must weigh order state, policy text, and sentiment against each other
# (e.g. damaged product + refund eligibility + return window).
_THINKING_BUDGET_INTENT = 512
_THINKING_BUDGET_RESOLUTION = 1024
_THINKING_BUDGET_RESPONSE = 512

# Room for the JSON payload itself, on top of the reasoning above.
_OUTPUT_RESERVE_INTENT = 1024
_OUTPUT_RESERVE_RESOLUTION = 2048
_OUTPUT_RESERVE_RESPONSE = 3072

_MAX_TOKENS_INTENT = _THINKING_BUDGET_INTENT + _OUTPUT_RESERVE_INTENT
_MAX_TOKENS_RESOLUTION = _THINKING_BUDGET_RESOLUTION + _OUTPUT_RESERVE_RESOLUTION
_MAX_TOKENS_RESPONSE = _THINKING_BUDGET_RESPONSE + _OUTPUT_RESERVE_RESPONSE

# Per-attempt wall clock. Generous on purpose: a call that reasons before
# answering legitimately takes longer than one that does not, and a timeout here
# costs the customer a canned apology — far worse than a few extra seconds.
_REQUEST_TIMEOUT_MS = 25_000

# Cap on a single history turn's text inside a prompt.
_MAX_HISTORY_CHARS_PER_TURN = 300


def _is_gemini_retryable(exc: Exception) -> bool:
    """Return True only for transient errors that are worth retrying.

    Skip retrying every 4xx — auth, bad-request, model-not-found, and 429. The
    free-tier limit that actually bites here is a per-DAY request quota, so a
    backed-off retry cannot clear it and only adds dead air to the customer's
    critical path.
    """
    code = getattr(exc, "code", None)
    if not isinstance(code, int):
        code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code >= 500
    return True


class GeminiService:
    """Service for interacting with Google Gemini."""

    MODEL = settings.gemini_model

    # Outcome of the most recent call, so /health can report an LLM that is
    # failing without spending generation quota to probe it. Class-level
    # defaults, not just __init__, because a 404 here degrades every reply to a
    # canned apology and nothing else in the system notices — the pipeline
    # catches the exception by design and answers the customer anyway.
    _last_error: Optional[str] = None
    _last_success_at: Optional[float] = None
    _consecutive_failures: int = 0

    def status(self) -> dict:
        """Snapshot of LLM reachability for the health endpoint."""
        return {
            "model": self.MODEL,
            "configured": bool(settings.gemini_api_key),
            "last_success_at": self._last_success_at,
            "consecutive_failures": self._consecutive_failures,
            "last_error": self._last_error,
        }

    def __init__(self):
        # google-genai, not the retired google-generativeai package: the latter
        # has no thinking_config field at all, so the budget below could never
        # be applied and every call silently ran with thinking enabled.
        self.client = genai.Client(api_key=settings.gemini_api_key)

    # 2 attempts, not 3: the per-attempt timeout is now 25s (up from 12s) to give
    # a reasoning call room to finish, so the retry count comes down to keep the
    # worst-case dead air on the customer's critical path bounded at ~52s.
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
        self,
        prompt: str,
        system_instruction: str = "",
        max_output_tokens: int = 2048,
        thinking_budget: int = 0,
    ) -> str:
        """Make a Gemini API call with retry logic."""
        try:
            # Last line of defence for the invariant the module constants
            # encode: thinking is spent out of max_output_tokens, so a budget
            # that crowds out the payload truncates every response. Clamp rather
            # than raise — a slightly shallower reasoning pass still answers the
            # customer; a truncated one never does.
            if thinking_budget >= max_output_tokens:
                logger.warning(
                    "gemini_thinking_budget_clamped",
                    requested=thinking_budget,
                    max_output_tokens=max_output_tokens,
                )
                thinking_budget = max_output_tokens // 4

            config = genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
                # Thinking tokens are drawn from max_output_tokens, so leaving
                # this unset burns the whole budget before any JSON is written.
                thinking_config=genai_types.ThinkingConfig(
                    thinking_budget=thinking_budget
                ),
                http_options=genai_types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS),
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
                    thinking_budget=thinking_budget,
                    usage=str(getattr(response, "usage_metadata", None)),
                )

            GeminiService._last_success_at = time.time()
            GeminiService._last_error = None
            GeminiService._consecutive_failures = 0
            return response.text
        except Exception as e:
            GeminiService._last_error = f"{type(e).__name__}: {str(e)[:200]}"
            GeminiService._consecutive_failures += 1
            logger.error("gemini_call_failed", model=self.MODEL, error=str(e))
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
        text = (text or "").strip()
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
            pass

        # Decode just the first JSON value and ignore whatever follows. Models
        # do sometimes append a second object or a stray line after the answer,
        # and json.loads rejects the whole payload for it ("Extra data") — which
        # threw away a complete, usable resolution. Leading prose is skipped the
        # same way.
        start = text.find("{")
        if start != -1:
            try:
                value, _ = json.JSONDecoder().raw_decode(text[start:])
                if isinstance(value, dict):
                    logger.warning("gemini_json_recovered", chars=len(text))
                    return value
            except json.JSONDecodeError:
                pass

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
    "extracted_order_id": "<order number if mentioned, null otherwise>",
    "extracted_phone": "<phone number if mentioned, null otherwise>",
    "extracted_name": "<customer name if mentioned, null otherwise>"
}}

Rules:
- If the customer sounds frustrated, set sentiment to Angry or Very Angry
- If the issue involves money (refund, payment) or damaged/wrong product, set priority to High
- If the customer mentions urgency or repeated complaints, set priority to Critical
- Always provide a concise summary_english regardless of input language

Extracting extracted_order_id — read this carefully, the order lookup depends on it:
- Order numbers look like "ORD-7K3F": the literal prefix ORD, a hyphen, then 4
  characters from A-Z and 2-9 (never the letters O, I, L or the digits 0, 1).
- The query is a speech transcript, so the number arrives spelled out, spaced,
  or mis-cased: "order I D O R D dash seven K three F", "ord 7k3f", "ORD 7K 3F".
  Reassemble it and return the canonical form "ORD-7K3F" — uppercase, one hyphen.
- If the customer gives only the 4-character body ("my order is 7K3F"), return
  it with the prefix added: "ORD-7K3F".
- If they read out a long UUID, return it verbatim.
- Never invent, complete, or guess an order number. If none was spoken, return null.
- A tracking number, ticket number (TKT-...), or customer code (CUST-...) is NOT
  an order number — return null for extracted_order_id in those cases."""

        try:
            result = await self._call_gemini(
                prompt,
                max_output_tokens=_MAX_TOKENS_INTENT,
                thinking_budget=_THINKING_BUDGET_INTENT,
            )
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

    @staticmethod
    def _account_context(
        order_data: Optional[dict],
        shipment_data: Optional[dict],
        return_data: Optional[dict],
        refund_data: Optional[dict],
        payment_data: Optional[dict],
        order_not_found: bool,
        order_reference: Optional[str],
    ) -> str:
        """Everything agent 3 pulled out of Postgres, as prompt context.

        Agent 3 loads shipment, return, refund and payment rows on every
        verified lookup, but only `order_data` used to reach this call — so the
        model decided "where is my refund" without ever seeing the refund row and
        answered from the policy text alone. All of it goes in now.
        """
        sections = []
        for label, payload in (
            ("Order", order_data),
            ("Shipment / tracking", shipment_data),
            ("Return request", return_data),
            ("Refund", refund_data),
            ("Payments", payment_data),
        ):
            if payload:
                body = json.dumps(payload, separators=(",", ":"), default=str)
                sections.append(f"{label}: {body}")

        if not sections:
            if order_not_found and order_reference:
                return (
                    f'The customer referred to order "{order_reference}", but no such '
                    "order exists on this account. Do not guess at its contents — ask "
                    "them to re-read the order number, or offer to look it up another way."
                )
            return "No account or order data available for this customer."

        if order_not_found and order_reference:
            sections.append(
                f'Note: the order number the customer gave ("{order_reference}") did '
                "not match this account; the data above is what we do hold."
            )
        return "Customer account data retrieved from our systems:\n" + "\n".join(sections)

    async def generate_resolution(
        self,
        query: str,
        intent: str,
        order_data: Optional[dict],
        policy_context: str,
        sentiment: str,
        conversation_history: list = None,
        shipment_data: Optional[dict] = None,
        return_data: Optional[dict] = None,
        refund_data: Optional[dict] = None,
        payment_data: Optional[dict] = None,
        order_not_found: bool = False,
        order_reference: Optional[str] = None,
    ) -> dict:
        """
        LLM Call 2: Determine the resolution based on order data + policy.
        This is where policy-groundedness matters most.
        """
        order_context = self._account_context(
            order_data,
            shipment_data,
            return_data,
            refund_data,
            payment_data,
            order_not_found,
            order_reference,
        )

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
- Ground the decision in the account data above FIRST, then the policy. The
  order status, shipment status, return status and refund status are facts —
  never contradict them, and never state a fact that is not in that block.
- Answer the question the customer actually asked. If they asked where their
  order is, the resolution must turn on the shipment status and expected
  delivery date; if they asked about a refund, on the refund status and amount.
- If the data needed to answer is simply absent, say so in resolution_summary
  and choose an action that gets it (ask for the order number, or Track).
- If no specific policy covers this case, use standard e-commerce best practices (e.g., apologize, inform, track).
- Set confidence_score high (0.8+) if you can reasonably address the query, even without strict policy.
  Set it below 0.4 only when you genuinely cannot tell what the customer needs.
- ONLY set recommended_action to "Escalate" and requires_human_review to true if the issue is highly sensitive, involves fraud, or strictly requires a human manager.
- When referring to the order, use the short "order_number" (e.g. ORD-7K3F). NEVER use the long internal "order_id" UUID."""

        try:
            result = await self._call_gemini(
                prompt,
                max_output_tokens=_MAX_TOKENS_RESOLUTION,
                thinking_budget=_THINKING_BUDGET_RESOLUTION,
            )
            return self._parse_json(result)
        except Exception as e:
            logger.error("generate_resolution_fallback", error=str(e))
            return {
                "recommended_action": "Escalate",
                "resolution_summary": "Your request has been noted and will be handled by a support agent shortly.",
                "policy_reference": "Standard Practice",
                "internal_note": f"Gemini LLM unavailable — auto-escalating to human agent. Error: {e}",
                # Honest low confidence: the LLM never ran, so the value must
                # trip escalation Rule 5 (< 0.4) instead of masking the outage.
                "confidence_score": 0.2,
                "requires_human_review": True,
                "reason_for_action": "LLM unavailable — automatic escalation"
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
            result = await self._call_gemini(
                prompt,
                max_output_tokens=_MAX_TOKENS_RESPONSE,
                thinking_budget=_THINKING_BUDGET_RESPONSE,
            )
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
