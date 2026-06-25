"""
CommerceMind VoiceCare AI — Voice Query API Routes
Handles text/voice queries and WebSocket streaming.
"""

import json
import uuid
import time
import structlog
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.core.errors import RateLimitError, ErrorMessages
from app.agents.state import PipelineState
from app.agents.pipeline import VoiceCarePipeline
from app.schemas.schemas import VoiceQueryRequest, VoiceQueryResponse
from app.services.memory_service import get_memory_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/voice", tags=["voice"])
settings = get_settings()


# ================================================================
# Rate-Limiting Dependency
# ================================================================

async def rate_limit_dependency(request: VoiceQueryRequest) -> None:
    """
    Simple in-memory rate limiter: max 5 voice queries/minute per phone.
    Uses the memory service (Redis) so it works across multiple workers.
    Falls back gracefully if Redis is unavailable.
    """
    phone = request.phone
    if not phone:
        return  # anonymous requests are not rate-limited here

    try:
        memory = await get_memory_service()
        limit = settings.voice_rate_limit_per_minute
        window = 60  # seconds
        key = f"rate_limit:voice:{phone}"

        # Increment the counter; set expiry on first hit
        count = await memory.increment_with_expiry(key, window)
        if count is not None and count > limit:
            logger.warning("rate_limit_exceeded", phone=phone, count=count)
            raise HTTPException(
                status_code=429,
                detail=ErrorMessages.RATE_LIMIT_VOICE,
                headers={"Retry-After": str(window)},
            )
    except HTTPException:
        raise
    except Exception as exc:
        # Redis unavailable — degrade gracefully, don't block the user
        logger.warning("rate_limit_check_failed", error=str(exc))


# ================================================================
# REST Endpoint
# ================================================================

@router.post("/query", response_model=VoiceQueryResponse)
async def process_voice_query(
    request: VoiceQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency),
):
    """Process a text or voice query through the 9-agent pipeline."""
    # Build initial pipeline state
    state = PipelineState(
        raw_text=request.text,
        raw_audio_base64=request.audio_base64,
        language_detected=request.language or "English",
        language_code=_lang_to_code(request.language) if request.language else "en",
        phone=request.phone,
        input_order_id=request.order_id,
    )

    # Load conversation history from Redis if multi-turn
    if request.session_id:
        state.session_id = request.session_id
        memory = await get_memory_service()
        history = await memory.get_conversation_history(request.session_id)
        state.conversation_history = history

    # Run the pipeline
    pipeline = VoiceCarePipeline(db=db)
    state = await pipeline.run(state)

    if state.has_error:
        raise HTTPException(status_code=500, detail=state.error)

    # Store conversation turn in memory
    memory = await get_memory_service()
    await memory.store_conversation_turn(
        state.session_id, "customer", state.transcript_original or request.text or ""
    )
    await memory.store_conversation_turn(
        state.session_id, "ai", state.response_english or state.response_text or ""
    )

    return VoiceQueryResponse(
        session_id=state.session_id,
        ticket_id=state.ticket_id or "",
        response_text=state.response_text or "",
        response_audio_base64=state.response_audio_base64,
        language=state.language_detected,
        intent=state.intent or "general_inquiry",
        sentiment=state.sentiment,
        priority=state.priority,
        recommended_action=state.recommended_action or "Inform",
        policy_reference=state.policy_reference,
        confidence_score=state.confidence_score,
        is_escalated=state.is_escalated,
        escalation_reason=state.escalation_reason,
        agent_trace=[step.model_dump(mode="json") for step in state.agent_trace],
    )


# ================================================================
# WebSocket Endpoint
# ================================================================

@router.websocket("/ws/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time pipeline status streaming."""
    await websocket.accept()

    async def on_stage_update(update: dict):
        await websocket.send_json(update)

    try:
        while True:
            data = await websocket.receive_json()

            # Get a fresh DB session for WebSocket
            from app.core.database import async_session
            async with async_session() as db:
                state = PipelineState(
                    session_id=session_id,
                    raw_text=data.get("text"),
                    raw_audio_base64=data.get("audio_base64"),
                    language_detected=data.get("language", "English"),
                    language_code=_lang_to_code(data.get("language", "English")),
                    phone=data.get("phone"),
                    input_order_id=data.get("order_id"),
                )

                # Load history
                if session_id:
                    memory = await get_memory_service()
                    history = await memory.get_conversation_history(session_id)
                    state.conversation_history = history

                pipeline = VoiceCarePipeline(db=db, on_stage_update=on_stage_update)
                state = await pipeline.run(state)

                # Send final response
                await websocket.send_json({
                    "type": "response",
                    "session_id": state.session_id,
                    "ticket_id": state.ticket_id,
                    "response_text": state.response_text,
                    "response_audio_base64": state.response_audio_base64,
                    "language": state.language_detected,
                    "intent": state.intent,
                    "sentiment": state.sentiment,
                    "is_escalated": state.is_escalated,
                    "is_complete": True,
                })

                # Store turns
                await memory.store_conversation_turn(
                    session_id, "customer", state.transcript_original or ""
                )
                await memory.store_conversation_turn(
                    session_id, "ai", state.response_english or ""
                )

                await db.commit()

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", session_id=session_id)
    except Exception as e:
        logger.error("websocket_error", session_id=session_id, error=str(e))
        await websocket.close(code=1011)


# ================================================================
# Helpers
# ================================================================

def _lang_to_code(language: str) -> str:
    """Convert language name to code."""
    mapping = {
        "Hindi": "hi", "English": "en", "Malayalam": "ml",
        "Tamil": "ta", "Telugu": "te", "Kannada": "kn",
        "Bengali": "bn", "Marathi": "mr", "Hinglish": "hi",
    }
    return mapping.get(language, "en")
