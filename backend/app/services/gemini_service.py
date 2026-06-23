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
    retry_if_exception_type,
)
import google.generativeai as genai

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class GeminiService:
    """Service for interacting with Google Gemini 2.5 Flash-Lite."""

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=lambda retry_state: logger.warning(
            "gemini_retry",
            attempt=retry_state.attempt_number,
            wait=retry_state.next_action.sleep,
        ),
    )
    async def _call_gemini(self, prompt: str, system_instruction: str = "") -> str:
        """Make a Gemini API call with retry logic."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                ),
            )
            return response.text
        except Exception as e:
            logger.error("gemini_call_failed", error=str(e))
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
    "extracted_phone": "<phone number if mentioned, null otherwise>"
}}

Rules:
- If the customer sounds frustrated, set sentiment to Angry or Very Angry
- If the issue involves money (refund, payment) or damaged/wrong product, set priority to High
- If the customer mentions urgency or repeated complaints, set priority to Critical
- Always provide a concise summary_english regardless of input language"""

        result = await self._call_gemini(prompt)
        return json.loads(result)

    async def generate_resolution(
        self,
        query: str,
        intent: str,
        order_data: Optional[dict],
        policy_context: str,
        sentiment: str,
    ) -> dict:
        """
        LLM Call 2: Determine the resolution based on order data + policy.
        This is where policy-groundedness matters most.
        """
        order_context = "No order data available."
        if order_data:
            order_context = f"Order details:\n{json.dumps(order_data, indent=2, default=str)}"

        prompt = f"""You are an e-commerce customer support AI making a resolution decision.
You MUST ground your resolution ONLY in the provided company policy. Never invent resolutions.

Customer issue: "{query}"
Detected intent: {intent}
Customer sentiment: {sentiment}

{order_context}

Relevant company policy sections:
{policy_context}

Return a JSON object with exactly these fields:
{{
    "recommended_action": "<one of: Inform, Refund, Replace, Escalate, Reject, Apologize, Track>",
    "resolution_summary": "<what you're recommending and why>",
    "policy_reference": "<exact quote or reference from the policy that supports this decision>",
    "internal_note": "<note for the support team about this resolution>",
    "confidence_score": <0.0 to 1.0>,
    "requires_human_review": <true/false>,
    "reason_for_action": "<brief explanation of why this specific action was chosen>"
}}

Rules:
- ONLY recommend actions supported by the provided policy
- If the policy doesn't cover this case, set recommended_action to "Escalate"
- If you're uncertain, set confidence_score below 0.6 and requires_human_review to true
- Always cite the specific policy section that supports your decision"""

        result = await self._call_gemini(prompt)
        return json.loads(result)

    async def generate_response(
        self,
        query: str,
        resolution: dict,
        language: str,
        customer_name: str = "Customer",
    ) -> dict:
        """
        LLM Call 3: Generate the final customer-facing response in their language.
        """
        prompt = f"""You are a friendly, empathetic e-commerce customer support assistant.
Generate a natural, helpful response to the customer.

Original customer query: "{query}"
Customer name: {customer_name}
Target language: {language}
Resolution decided: {json.dumps(resolution, indent=2)}

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
- Don't use markdown, bullet points, or formatting — use natural spoken language"""

        result = await self._call_gemini(prompt)
        return json.loads(result)


# Singleton
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
