"""
CommerceMind VoiceCare AI — LangGraph Agent Pipeline
9-agent state machine: STT → Intent → Lookup → RAG → Resolution →
Escalation → Response → TTS → Ticket
Maps to only 3 real LLM calls — everything else is deterministic code.
"""

import json
import time
import uuid
import structlog
import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.state import PipelineState
from app.services.gemini_service import get_gemini_service
from app.services.bhashini_service import get_bhashini_service
from app.core.constants import LANGUAGE_CODES, LANGUAGE_NAMES
from app.services.chroma_service import get_chroma_service
from app.services.memory_service import get_memory_service
from app.db.models import (
    User, Order, OrderItem, Shipment, Return, Refund, Payment,
    VoiceSession, SupportTicket, SupportMessage, SupportResolution,
    CustomerSentiment,
)

logger = structlog.get_logger()


class VoiceCarePipeline:
    """
    The 9-agent pipeline orchestrator.
    Each agent is a method that takes PipelineState, mutates it, and returns it.
    """

    def __init__(self, db: AsyncSession, on_stage_update: Callable = None):
        self.db = db
        self.gemini = get_gemini_service()
        self.bhashini = get_bhashini_service()
        self.chroma = get_chroma_service()
        self.on_stage_update = on_stage_update  # WebSocket callback

    async def _notify_stage(self, stage: int, message: str, is_complete: bool = False):
        """Send stage update via WebSocket callback."""
        if self.on_stage_update:
            await self.on_stage_update({
                "stage_number": stage,
                "total_stages": 9,
                "message": message,
                "is_complete": is_complete,
            })

    # ================================================================
    # Agent 1: Voice Intake (Bhashini STT) — deterministic/code
    # ================================================================
    async def agent_voice_intake(self, state: PipelineState) -> PipelineState:
        """Convert audio to text using Bhashini STT, or pass through text input."""
        start = time.time()
        await self._notify_stage(1, "Listening...")

        try:
            if state.raw_audio_base64:
                # Detect language and transcribe
                lang_code = state.language_code or "hi"
                try:
                    """
                    # --- BHASHINI STT (COMMENTED OUT FOR FUTURE USE) ---
                    transcript, detected_lang = await self.bhashini.speech_to_text(
                        state.raw_audio_base64, lang_code
                    )
                    state.transcript_original = transcript
                    state.language_code = detected_lang

                    # Get language name
                    lang_names = {v: k for k, v in LANGUAGE_CODES.items()}
                    state.language_detected = lang_names.get(detected_lang, "Hindi")

                    # Translate to English for downstream processing
                    if detected_lang != "en":
                        state.transcript_english = await self.bhashini.translate_text(
                            transcript, detected_lang, "en"
                        )
                    else:
                        state.transcript_english = transcript

                    decision = "Bhashini STT transcription"
                    """
                    # --- GROQ WHISPER STT (FAST, FREE API) ---
                    import base64
                    import httpx
                    from app.core.config import get_settings
                    
                    settings = get_settings()
                    if not settings.groq_api_key:
                        raise Exception("GROQ_API_KEY is not set. Please add it to your environment variables.")

                    # Decode base64 audio
                    # Strip data URI scheme if present
                    audio_b64 = state.raw_audio_base64
                    if "base64," in audio_b64:
                        audio_b64 = audio_b64.split("base64,")[1]
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    async with httpx.AsyncClient() as client:
                        # We use 'audio.webm' as a generic extension, Groq handles most formats automatically
                        files = {"file": ("audio.webm", audio_bytes, "audio/webm")}
                        data = {"model": "whisper-large-v3", "language": lang_code if lang_code != "en" else "en"}
                        
                        response = await client.post(
                            "https://api.groq.com/openai/v1/audio/transcriptions",
                            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                            files=files,
                            data=data,
                            timeout=15.0
                        )
                        response.raise_for_status()
                        transcript = response.json().get("text", "")

                    state.transcript_original = transcript
                    state.language_code = lang_code
                    state.language_detected = LANGUAGE_NAMES.get(lang_code, "Hindi")

                    # Note: We rely on the downstream Gemini Agent (Agent 2) to handle English translation
                    # if needed, since Groq Whisper STT only returns the original language transcription here.
                    state.transcript_english = transcript 

                    decision = "Groq Whisper STT transcription"

                except Exception as bhashini_err:
                    logger.warning(
                        "bhashini_stt_unavailable",
                        error=str(bhashini_err),
                        fallback="raw_text" if state.raw_text else "none",
                    )
                    # ── Graceful fallback ──────────────────────────────────────
                    # If the caller also sent raw_text (e.g. typed query), use it.
                    # Otherwise surface a clear error instead of a generic crash.
                    if state.raw_text:
                        state.transcript_original = state.raw_text
                        state.transcript_english = state.raw_text
                        state.language_detected = state.language_detected or "English"
                        state.language_code = state.language_code or "en"
                        decision = "Text fallback (Bhashini STT unavailable)"
                    else:
                        state.error = (
                            "Voice recognition is temporarily unavailable. "
                            "Please use the \"Switch to Text\" option to type your query."
                        )
                        state.has_error = True
                        return state

            elif state.raw_text:
                state.transcript_original = state.raw_text
                state.transcript_english = state.raw_text
                state.language_detected = state.language_detected or "English"
                state.language_code = state.language_code or "en"
                decision = "Text input passthrough"
            else:
                state.error = "No audio or text input provided"
                state.has_error = True
                return state

            state.add_trace(
                agent_name="Voice Intake",
                stage_number=1,
                input_summary=f"Audio: {'yes' if state.raw_audio_base64 else 'no'}, Text: {'yes' if state.raw_text else 'no'}",
                output_summary=f"Transcript: {(state.transcript_english or '')[:100]}...",
                decision=decision,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("voice_intake_failed", error=str(e))
            state.error = f"Voice intake failed: {str(e)}"
            state.has_error = True

        return state

    # ================================================================
    # Agent 2: Intent + Sentiment + Priority (LLM Call 1)
    # ================================================================
    async def agent_intent_analysis(self, state: PipelineState) -> PipelineState:
        """Analyze intent, sentiment, and priority using Gemini."""
        start = time.time()
        await self._notify_stage(2, "Understanding your issue...")

        try:
            query = state.transcript_english or state.transcript_original
            result = await self.gemini.analyze_intent(
                query=query,
                language=state.language_detected,
                conversation_history=state.conversation_history,
            )

            state.intent = result.get("intent", "general_inquiry")
            state.sub_intent = result.get("sub_intent", "")
            state.sentiment = result.get("sentiment", "Neutral")
            state.priority = result.get("priority", "Medium")
            state.summary_english = result.get("summary_english", query)
            state.requires_order_lookup = result.get("requires_order_lookup", False)
            state.extracted_order_id = result.get("extracted_order_id")
            state.extracted_phone = result.get("extracted_phone")
            state.extracted_name = result.get("extracted_name")

            state.add_trace(
                agent_name="Intent Analysis",
                stage_number=2,
                input_summary=f"Query: {query[:100]}...",
                output_summary=f"Intent: {state.intent}, Sentiment: {state.sentiment}, Priority: {state.priority}",
                decision=f"Classified as {state.intent} with {state.priority} priority",
                reasoning=f"Sentiment detected: {state.sentiment}",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("intent_analysis_failed", error=str(e))
            state.intent = "general_inquiry"
            state.sentiment = "Neutral"
            state.priority = "Medium"
            state.summary_english = state.transcript_english

        return state

    # ================================================================
    # Agent 3: Order / Transaction Lookup (DB) — deterministic/code
    # ================================================================
    async def agent_order_lookup(self, state: PipelineState) -> PipelineState:
        """Look up order, shipment, return, refund, payment data from Postgres."""
        start = time.time()
        await self._notify_stage(3, "Checking your order...")

        try:
            # Find user by phone
            phone = state.phone or state.extracted_phone
            if phone:
                user_result = await self.db.execute(
                    select(User).where(User.phone == phone)
                )
                user = user_result.scalar_one_or_none()

                if user:
                    state.user_data = {
                        "user_id": str(user.user_id),
                        "name": user.name,
                        "phone": user.phone,
                        "preferred_language": user.preferred_language,
                        "customer_segment": user.customer_segment,
                    }

                    # Find order
                    order_id = state.input_order_id or state.extracted_order_id
                    if order_id:
                        try:
                            order_uuid = uuid.UUID(order_id)
                            order_result = await self.db.execute(
                                select(Order).where(
                                    Order.order_id == order_uuid,
                                    Order.user_id == user.user_id
                                )
                            )
                            order = order_result.scalar_one_or_none()
                        except ValueError:
                            logger.warning("invalid_order_uuid_format", order_id=order_id)
                            order = None
                        except Exception as db_exc:
                            logger.error("order_lookup_db_error", order_id=order_id, error=str(db_exc))
                            raise
                    else:
                        # Get most recent order
                        order_result = await self.db.execute(
                            select(Order)
                            .where(Order.user_id == user.user_id)
                            .order_by(Order.order_date.desc())
                            .limit(1)
                        )
                        order = order_result.scalar_one_or_none()

                    if order:
                        state.order_data = {
                            "order_id": str(order.order_id),
                            "order_date": str(order.order_date),
                            "status": order.status,
                            "total_amount": float(order.total_amount),
                        }

                        # Shipment
                        ship_result = await self.db.execute(
                            select(Shipment).where(Shipment.order_id == order.order_id)
                        )
                        shipment = ship_result.scalar_one_or_none()
                        if shipment:
                            state.shipment_data = {
                                "shipment_status": shipment.shipment_status,
                                "courier_partner": shipment.courier_partner,
                                "expected_delivery": str(shipment.expected_delivery_date),
                                "actual_delivery": str(shipment.actual_delivery_date) if shipment.actual_delivery_date else None,
                                "tracking_number": shipment.tracking_number,
                            }

                        # Return
                        ret_result = await self.db.execute(
                            select(Return).where(Return.order_id == order.order_id)
                        )
                        ret = ret_result.scalar_one_or_none()
                        if ret:
                            state.return_data = {
                                "return_id": str(ret.return_id),
                                "reason": ret.reason,
                                "status": ret.status,
                                "requested_at": str(ret.requested_at),
                            }

                            # Refund linked to return
                            ref_result = await self.db.execute(
                                select(Refund).where(Refund.return_id == ret.return_id)
                            )
                            refund = ref_result.scalar_one_or_none()
                            if refund:
                                state.refund_data = {
                                    "refund_id": str(refund.refund_id),
                                    "amount": float(refund.amount),
                                    "status": refund.status,
                                    "credited_at": str(refund.credited_at) if refund.credited_at else None,
                                }

                        # Payment
                        pay_result = await self.db.execute(
                            select(Payment).where(Payment.order_id == order.order_id)
                        )
                        payments = pay_result.scalars().all()
                        if payments:
                            state.payment_data = {
                                "payments": [
                                    {
                                        "payment_id": str(p.payment_id),
                                        "amount": float(p.amount),
                                        "status": p.status,
                                        "method": p.payment_method,
                                        "date": str(p.transaction_date),
                                    }
                                    for p in payments
                                ]
                            }

                        state.lookup_successful = True

            state.add_trace(
                agent_name="Order Lookup",
                stage_number=3,
                input_summary=f"Phone: {phone}, Order: {state.input_order_id or state.extracted_order_id}",
                output_summary=f"Found: user={state.user_data is not None}, order={state.order_data is not None}",
                decision="Data retrieved from Postgres" if state.lookup_successful else "No matching records",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("order_lookup_failed", error=str(e))
            state.lookup_successful = False

        return state

    # ================================================================
    # Agent 4: Policy RAG Retrieval (Chroma) — deterministic/code
    # ================================================================
    async def agent_policy_rag(self, state: PipelineState) -> PipelineState:
        """Retrieve relevant policy documents from Chroma vector store."""
        start = time.time()
        await self._notify_stage(4, "Finding the right policy...")

        try:
            import hashlib
            query = state.summary_english or state.transcript_english or ""
            cache_key = f"rag:{hashlib.md5(query.encode()).hexdigest()}"

            memory = await get_memory_service()
            cached = await memory.get_cache(cache_key)
            if cached:
                state.policy_context = cached.get("policy_context", "")
                state.retrieved_policies = cached.get("retrieved_policies", [])
                logger.info("policy_rag_cache_hit", query_len=len(query))
            else:
                state.policy_context = self.chroma.get_policy_context(query, n_results=3)
                state.retrieved_policies = self.chroma.query_policies(query, n_results=3)
                await memory.set_cache(
                    cache_key,
                    {
                        "policy_context": state.policy_context,
                        "retrieved_policies": state.retrieved_policies,
                    },
                    ttl_seconds=3600,
                )

            state.rag_retrieved_count = len(state.retrieved_policies)
            if state.rag_retrieved_count == 0:
                logger.warning("rag_no_policies_retrieved", query_preview=query[:80])
                state.policy_context = (
                    "No matching policy documents found. Apply standard e-commerce best practices."
                )

            state.add_trace(
                agent_name="Policy RAG",
                stage_number=4,
                input_summary=f"Query: {query[:100]}...",
                output_summary=f"Retrieved {state.rag_retrieved_count} policy documents",
                decision="Vector similarity search on policy collection" if state.rag_retrieved_count else "No matching policies — using best-practice fallback",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("policy_rag_failed", error=str(e))
            state.policy_context = "No policy documents available."

        return state

    # ================================================================
    # Agent 5: Resolution Decision (LLM Call 2)
    # ================================================================
    async def agent_resolution(self, state: PipelineState) -> PipelineState:
        """Generate resolution decision using Gemini — policy-grounded."""
        start = time.time()
        await self._notify_stage(5, "Determining the best resolution...")

        try:
            query = state.transcript_english or state.transcript_original
            result = await self.gemini.generate_resolution(
                query=query,
                intent=state.intent,
                order_data=state.order_data,
                policy_context=state.policy_context or "",
                sentiment=state.sentiment,
                conversation_history=state.conversation_history,
            )

            state.recommended_action = result.get("recommended_action", "Inform")
            state.resolution_summary = result.get("resolution_summary", "")
            state.policy_reference = result.get("policy_reference", "")
            state.internal_note = result.get("internal_note", "")
            raw_confidence = result.get("confidence_score", 0.5)
            # If no policies were retrieved, cap confidence so escalation rules can trigger
            # correctly — LLM can't be highly confident without policy grounding.
            if state.rag_retrieved_count == 0:
                raw_confidence = min(raw_confidence, 0.65)
            state.confidence_score = raw_confidence
            state.requires_human_review = result.get("requires_human_review", False)

            state.add_trace(
                agent_name="Resolution",
                stage_number=5,
                input_summary=f"Intent: {state.intent}, Order: {state.order_data is not None}",
                output_summary=f"Action: {state.recommended_action}, Confidence: {state.confidence_score}",
                decision=f"Recommended: {state.recommended_action}",
                reasoning=state.resolution_summary,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("resolution_failed", error=str(e))
            state.recommended_action = "Escalate"
            state.confidence_score = 0.0
            state.internal_note = f"Resolution failed: {str(e)}"

        return state

    # ================================================================
    # Agent 6: Escalation Check (Deterministic Rules) — code only
    # ================================================================
    async def agent_escalation_check(self, state: PipelineState) -> PipelineState:
        """Check 5 deterministic escalation rules — no LLM call."""
        start = time.time()
        await self._notify_stage(6, "Checking if escalation needed...")

        rules_triggered = []

        # Rule 1: Angry or Very Angry sentiment
        if state.sentiment in ("Angry", "Very Angry"):
            rules_triggered.append("Angry customer detected")

        # Rule 2: High-value order (>₹5000)
        if state.order_data and state.order_data.get("total_amount", 0) > 5000:
            if state.sentiment in ("Negative", "Angry", "Very Angry"):
                rules_triggered.append("High-value order with negative sentiment")

        # Rule 3: Refund delayed beyond SLA
        if state.refund_data and state.refund_data.get("status") == "Pending":
            rules_triggered.append("Refund delayed beyond SLA")

        # Rule 4: Payment deducted but order not created
        if state.intent == "payment_issue" and state.payment_data:
            payments = state.payment_data.get("payments", [])
            has_failed = any(p.get("status") == "Failed" for p in payments)
            has_success = any(p.get("status") == "Success" for p in payments)
            if has_failed or (has_success and state.order_data and state.order_data.get("status") == "Cancelled"):
                rules_triggered.append("Payment deducted but order issue detected")

        # Rule 5: Low AI confidence
        if state.confidence_score < 0.4:
            rules_triggered.append(f"Low AI confidence: {state.confidence_score:.2f}")

        # Rule 6: LLM specifically recommended escalation
        if state.recommended_action == "Escalate":
            rules_triggered.append("LLM determined human escalation is required")

        if rules_triggered:
            state.is_escalated = True
            state.escalation_reason = "; ".join(rules_triggered)
            state.escalation_rules_triggered = rules_triggered

        state.add_trace(
            agent_name="Escalation Check",
            stage_number=6,
            input_summary=f"Sentiment: {state.sentiment}, Confidence: {state.confidence_score}",
            output_summary=f"Escalated: {state.is_escalated}",
            decision="ESCALATED" if state.is_escalated else "Not escalated",
            reasoning=state.escalation_reason if state.is_escalated else "No escalation rules triggered",
            duration_ms=(time.time() - start) * 1000,
        )
        return state

    # ================================================================
    # Agent 7: Response Generation (LLM Call 3)
    # ================================================================
    async def agent_response_generation(self, state: PipelineState) -> PipelineState:
        """Generate final customer-facing response in their language."""
        start = time.time()
        await self._notify_stage(7, "Preparing your response...")

        try:
            query = state.transcript_original or state.transcript_english
            customer_name = state.user_data.get("name") if state.user_data else (state.extracted_name or "Customer")

            resolution_data = {
                "recommended_action": state.recommended_action,
                "resolution_summary": state.resolution_summary,
                "policy_reference": state.policy_reference,
                "is_escalated": state.is_escalated,
                "escalation_reason": state.escalation_reason,
                "order_data": state.order_data,
                "shipment_data": state.shipment_data,
                "refund_data": state.refund_data,
            }

            result = await self.gemini.generate_response(
                query=query,
                resolution=resolution_data,
                language=state.language_detected,
                customer_name=customer_name,
                conversation_history=state.conversation_history,
            )

            state.response_text = result.get("response_text", "")
            state.response_english = result.get("response_english", "")
            state.response_tone = result.get("tone", "Professional")

            state.add_trace(
                agent_name="Response Generation",
                stage_number=7,
                input_summary=f"Language: {state.language_detected}, Escalated: {state.is_escalated}",
                output_summary=f"Response length: {len(state.response_text or '')} chars, Tone: {state.response_tone}",
                decision=f"Generated {state.language_detected} response",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("response_generation_failed", error=str(e))
            state.response_text = "I apologize, but I'm having trouble generating a response. Let me connect you with a human agent."
            state.response_english = state.response_text
            state.is_escalated = True

        return state

    # ================================================================
    # Agent 8: Text-to-Speech (Bhashini TTS) — deterministic/code
    # ================================================================
    async def agent_tts(self, state: PipelineState) -> PipelineState:
        """Convert response text to speech using Bhashini TTS."""
        start = time.time()
        await self._notify_stage(8, "Converting to speech...")

        try:
            if state.response_text and state.language_code != "en":
                state.response_audio_base64 = await self.bhashini.text_to_speech(
                    state.response_text, state.language_code
                )
            elif state.response_text:
                # For English, use Bhashini TTS as well
                state.response_audio_base64 = await self.bhashini.text_to_speech(
                    state.response_text, "en"
                )

            state.add_trace(
                agent_name="TTS",
                stage_number=8,
                input_summary=f"Text length: {len(state.response_text or '')} chars",
                output_summary=f"Audio generated: {state.response_audio_base64 is not None}",
                decision="Bhashini TTS conversion",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.error("tts_failed", error=str(e))
            # TTS failure is non-fatal — text response still works

        return state

    # ================================================================
    # Agent 9: Ticket Creation (DB) — deterministic/code
    # ================================================================
    async def agent_ticket_creation(self, state: PipelineState) -> PipelineState:
        """Create support ticket, messages, and resolution in Postgres."""
        start = time.time()
        await self._notify_stage(9, "Creating your support ticket...")

        # Wrap everything in a SAVEPOINT so that any flush/constraint failure
        # rolls back only this agent's writes — the outer transaction stays
        # alive and db.commit() succeeds (committing nothing) rather than
        # raising PendingRollbackError and losing the whole session.
        try:
            async with self.db.begin_nested():
                user_id = None
                if state.user_data:
                    user_id = uuid.UUID(state.user_data["user_id"])
                else:
                    # Get-or-create: if Gemini extracted a phone that already
                    # exists in the DB, look it up instead of inserting a
                    # duplicate (which would raise a UniqueViolation).
                    phone_val = state.extracted_phone or f"temp-{uuid.uuid4().hex[:10]}"
                    existing = (await self.db.execute(
                        select(User).where(User.phone == phone_val)
                    )).scalar_one_or_none()
                    if existing:
                        user_id = existing.user_id
                    else:
                        new_user = User(
                            name=state.extracted_name or "Anonymous Customer",
                            phone=phone_val,
                        )
                        self.db.add(new_user)
                        await self.db.flush()
                        user_id = new_user.user_id

                order_id = None
                if state.order_data:
                    order_id = uuid.UUID(state.order_data["order_id"])

                # VoiceSession.session_id is the PK — always use a fresh UUID.
                # state.session_id is only for conversation-memory lookups.
                session = VoiceSession(
                    session_id=uuid.uuid4(),
                    user_id=user_id,
                    language_detected=state.language_detected,
                    transcript_original=state.transcript_original,
                    transcript_english=state.transcript_english,
                    started_at=state.started_at,
                    ended_at=datetime.utcnow(),
                )
                self.db.add(session)
                await self.db.flush()

                ticket = SupportTicket(
                    user_id=user_id,
                    order_id=order_id,
                    session_id=session.session_id,
                    ticket_type=self._intent_to_ticket_type(state.intent),
                    priority=state.priority,
                    status="Escalated" if state.is_escalated else "Resolved",
                    language=state.language_detected,
                    sentiment=state.sentiment,
                    summary=state.summary_english,
                    escalated_at=datetime.utcnow() if state.is_escalated else None,
                    resolved_at=datetime.utcnow() if not state.is_escalated else None,
                )
                self.db.add(ticket)
                await self.db.flush()

                state.ticket_id = str(ticket.ticket_id)

                self.db.add(SupportMessage(
                    ticket_id=ticket.ticket_id,
                    session_id=session.session_id,
                    sender_type="Customer",
                    message_text=state.transcript_original or "",
                    language=state.language_detected,
                ))
                self.db.add(SupportMessage(
                    ticket_id=ticket.ticket_id,
                    session_id=session.session_id,
                    sender_type="AI",
                    message_text=state.response_english or state.response_text or "",
                    language="English",
                ))

                trace_json = json.dumps(
                    [step.model_dump(mode="json") for step in state.agent_trace],
                    default=str,
                )
                self.db.add(SupportResolution(
                    ticket_id=ticket.ticket_id,
                    recommended_action=state.recommended_action or "Inform",
                    policy_reference=state.policy_reference,
                    final_response_text=state.response_text or "",
                    internal_note=state.internal_note,
                    confidence_score=state.confidence_score,
                    agent_trace=trace_json,
                ))
                self.db.add(CustomerSentiment(
                    ticket_id=ticket.ticket_id,
                    sentiment_label=state.sentiment,
                    confidence_score=state.confidence_score,
                ))

                await self.db.flush()
                state.ticket_created = True

                state.add_trace(
                    agent_name="Ticket Creation",
                    stage_number=9,
                    input_summary=f"User: {user_id}, Escalated: {state.is_escalated}",
                    output_summary=f"Ticket {state.ticket_id} created",
                    decision="Ticket persisted to Postgres",
                    duration_ms=(time.time() - start) * 1000,
                )

            await self._notify_stage(9, "Done!", is_complete=True)

        except Exception as e:
            logger.error("ticket_creation_failed", error=str(e), exc_info=True)
            state.error = f"Ticket creation failed: {str(e)}"
            # Savepoint already rolled back — outer transaction is clean.

        return state

    # ================================================================
    # Pipeline Executor
    # ================================================================
    async def run(self, state: PipelineState) -> PipelineState:
        """Execute the full 9-agent pipeline."""
        # Part B: Hydrate identity from prior turns so customers don't re-identify
        memory = await get_memory_service()
        if state.session_id:
            try:
                ctx = await memory.get_session_context(state.session_id)
                if ctx:
                    if not state.phone and ctx.get("phone"):
                        state.phone = ctx["phone"]
                    if not state.input_order_id and ctx.get("order_id"):
                        state.input_order_id = ctx["order_id"]
            except Exception as ctx_err:
                logger.warning("session_context_load_failed", error=str(ctx_err))

        if state.has_error:
            return state
        state = await self.agent_voice_intake(state)

        if state.has_error:
            return state
        state = await self.agent_intent_analysis(state)

        if state.has_error:
            return state
        # Run Order Lookup and Policy RAG in parallel
        await asyncio.gather(
            self.agent_order_lookup(state),
            self.agent_policy_rag(state)
        )

        if state.has_error:
            return state
        state = await self.agent_resolution(state)

        if state.has_error:
            return state
        state = await self.agent_escalation_check(state)

        if state.has_error:
            return state
        state = await self.agent_response_generation(state)

        if state.has_error:
            return state
        state = await self.agent_tts(state)

        if state.has_error:
            return state
        state = await self.agent_ticket_creation(state)

        # Part B: Persist identity context so the next turn can reuse phone/order_id
        if not state.has_error and state.session_id:
            try:
                phone = (state.user_data or {}).get("phone") or state.extracted_phone
                order_id = (state.order_data or {}).get("order_id") or state.extracted_order_id
                if phone or order_id:
                    await memory.set_session_context(state.session_id, {
                        "phone": phone,
                        "user_id": (state.user_data or {}).get("user_id"),
                        "order_id": order_id,
                        "intent": state.intent,
                        "last_summary": state.summary_english,
                    })
            except Exception as ctx_save_err:
                logger.warning("session_context_save_failed", error=str(ctx_save_err))

        return state

    @staticmethod
    def _intent_to_ticket_type(intent: str) -> str:
        """Map intent to ticket type."""
        mapping = {
            "order_status": "Delay",
            "delivery_delay": "Delay",
            "refund_status": "Refund",
            "return_request": "Return",
            "payment_issue": "Payment",
            "damaged_product": "Complaint",
            "wrong_product": "Complaint",
            "cancellation": "Return",
            "exchange": "Return",
            "general_inquiry": "General",
        }
        return mapping.get(intent, "General")
