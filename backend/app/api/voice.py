"""
CommerceMind VoiceCare AI — Voice Query API Routes
Handles text/voice queries and WebSocket streaming.
"""

import json
import re
import uuid
import time
import structlog
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.database import get_db
from app.core.config import get_settings
from app.core.errors import RateLimitError, ErrorMessages
from app.core.constants import LANGUAGE_CODES, MAX_AUDIO_B64_LEN, MAX_TEXT_LEN
from app.core.rate_limit import (
    enforce as enforce_rate_limit,
    get_client_ip,
    is_within_limit,
)
from app.agents.state import PipelineState
from app.agents.pipeline import VoiceCarePipeline
from pydantic import ValidationError

from app.schemas.schemas import VoiceQueryRequest, VoiceQueryResponse
from app.services.memory_service import get_memory_service

logger = structlog.get_logger()
router = APIRouter(prefix="/api/voice", tags=["voice"])
settings = get_settings()

_RATE_WINDOW_SECONDS = 60
_VERCEL_ORIGIN_RE = re.compile(r"^https://[a-z0-9.-]+\.vercel\.app$", re.IGNORECASE)

# Live voice WebSocket connections per client IP (per-worker; enough to stop
# a single host from opening unbounded pipeline connections).
_ws_connections: dict[str, int] = {}

# ================================================================
# Rate-Limiting Dependency
# ================================================================

async def rate_limit_dependency(request: Request, body: VoiceQueryRequest) -> None:
    """Per-IP limit for every caller (anonymous included), plus the tighter
    per-phone limit when a phone number is supplied. Degrades to an in-process
    counter when the shared store is unavailable (see app/core/rate_limit.py)."""
    await enforce_rate_limit(
        key=f"rate_limit:voice:ip:{get_client_ip(request)}",
        limit=settings.voice_rate_limit_ip_per_minute,
        window_seconds=_RATE_WINDOW_SECONDS,
        detail=ErrorMessages.RATE_LIMIT_VOICE,
    )
    if body.phone:
        await enforce_rate_limit(
            key=f"rate_limit:voice:{body.phone}",
            limit=settings.voice_rate_limit_per_minute,
            window_seconds=_RATE_WINDOW_SECONDS,
            detail=ErrorMessages.RATE_LIMIT_VOICE,
        )


def _build_voice_response(state: PipelineState) -> dict:
    """Single source of truth for the client-facing pipeline result.

    Used by both the REST endpoint (wrapped in VoiceQueryResponse) and the
    WebSocket final message, so the two transports can never drift apart.
    """
    return {
        "session_id": state.session_id,
        "ticket_id": state.ticket_id or "",
        "ticket_number": state.ticket_number,
        "ticket_created": state.ticket_created,
        "order_number": (state.order_data or {}).get("order_number"),
        "response_text": state.response_text or "",
        "response_audio_base64": state.response_audio_base64,
        "language": state.language_detected,
        "intent": state.intent or "general_inquiry",
        "sentiment": state.sentiment,
        "priority": state.priority,
        "recommended_action": state.recommended_action or "Inform",
        "policy_reference": state.policy_reference,
        "confidence_score": state.confidence_score,
        "is_escalated": state.is_escalated,
        "escalation_reason": state.escalation_reason,
        "agent_trace": [step.model_dump(mode="json") for step in state.agent_trace],
    }


# ================================================================
# REST Endpoint
# ================================================================

@router.post("/query", response_model=VoiceQueryResponse)
async def process_voice_query(
    body: VoiceQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit_dependency),
):
    """Process a text or voice query through the 9-agent pipeline."""
    # Build initial pipeline state
    state = PipelineState(
        raw_text=body.text,
        raw_audio_base64=body.audio_base64,
        language_detected=body.language or "English",
        language_code=_language_to_code(body.language) if body.language else "en",
        phone=body.phone,
        input_order_id=body.order_id,
    )

    # Load conversation history from Redis if multi-turn
    if body.session_id:
        state.session_id = body.session_id
        memory = await get_memory_service()
        history = await memory.get_conversation_history(body.session_id)
        state.conversation_history = history

    # Run the pipeline
    pipeline = VoiceCarePipeline(db=db)
    state = await pipeline.run(state)

    if state.has_error:
        # Log the real failure server-side; never echo internals to the client.
        logger.error("voice_query_failed", session_id=state.session_id, error=state.error)
        raise HTTPException(
            status_code=500,
            detail="Voice query processing failed. Please try again.",
        )

    # Store conversation turn in memory
    memory = await get_memory_service()
    await memory.store_conversation_turn(
        state.session_id, "customer", state.transcript_original or body.text or ""
    )
    await memory.store_conversation_turn(
        state.session_id,
        "ai",
        state.response_english or state.response_text or "",
        display_content=state.response_text or "",
    )

    return VoiceQueryResponse(**_build_voice_response(state))


# ================================================================
# WebSocket Endpoint
# ================================================================

def _origin_allowed(origin: str) -> bool:
    """Mirror of the CORS policy for WebSocket handshakes.

    Browsers always send Origin; a mismatched one is rejected. A missing
    Origin (non-browser client) is allowed — those callers are still bounded
    by the per-IP connection cap and message budget.
    """
    normalized = origin.rstrip("/")
    if normalized in settings.allowed_origins:
        return True
    allow_vercel = (not settings.is_production) or settings.cors_allow_vercel_previews
    return bool(allow_vercel and _VERCEL_ORIGIN_RE.match(normalized))


@router.websocket("/ws/{session_id}")
async def voice_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time pipeline status streaming."""
    import asyncio as _asyncio

    origin = websocket.headers.get("origin")
    if origin and not _origin_allowed(origin):
        logger.warning("websocket_origin_rejected", session_id=session_id)
        await websocket.close(code=4403)
        return

    client_ip = get_client_ip(websocket)
    if _ws_connections.get(client_ip, 0) >= settings.ws_max_connections_per_ip:
        logger.warning("websocket_connection_cap", client_ip=client_ip)
        await websocket.close(code=4429)
        return
    _ws_connections[client_ip] = _ws_connections.get(client_ip, 0) + 1

    await websocket.accept()

    async def on_stage_update(update: dict):
        await websocket.send_json(update)

    # Keep-alive: send a server-side ping every 20 s so the connection is never
    # idle long enough for Render / load balancers to tear it down mid-pipeline.
    async def _keep_alive():
        try:
            while True:
                await _asyncio.sleep(20)
                await websocket.send_json({"type": "ping"})
        except Exception:
            pass

    ping_task = _asyncio.create_task(_keep_alive())

    try:
        while True:
            data = await websocket.receive_json()

            # Validate incoming payload with Pydantic schema. Only field-level
            # locations/messages are returned — never the submitted values.
            try:
                ws_request = VoiceQueryRequest(**data)
            except ValidationError as ve:
                await websocket.send_json({
                    "error": "VALIDATION_ERROR",
                    "detail": [
                        {
                            "field": ".".join(str(loc) for loc in err.get("loc", [])),
                            "message": err.get("msg", "Invalid value"),
                        }
                        for err in ve.errors()
                    ],
                })
                continue
            except TypeError:
                await websocket.send_json({
                    "error": "VALIDATION_ERROR",
                    "detail": "Message must be a JSON object.",
                })
                continue

            # Reject oversized inputs before any processing
            if ws_request.text and len(ws_request.text) > MAX_TEXT_LEN:
                await websocket.send_json({
                    "error": "VALIDATION_ERROR",
                    "detail": f"Text input exceeds {MAX_TEXT_LEN} character limit.",
                })
                continue
            if ws_request.audio_base64 and len(ws_request.audio_base64) > MAX_AUDIO_B64_LEN:
                await websocket.send_json({
                    "error": "VALIDATION_ERROR",
                    "detail": "Audio payload exceeds 10 MB limit.",
                })
                continue

            # Message budget — shares the per-IP counter with the REST
            # endpoint so switching transports cannot double the allowance.
            within_ip_budget = await is_within_limit(
                f"rate_limit:voice:ip:{client_ip}",
                settings.voice_rate_limit_ip_per_minute,
                _RATE_WINDOW_SECONDS,
            )
            within_phone_budget = not ws_request.phone or await is_within_limit(
                f"rate_limit:voice:{ws_request.phone}",
                settings.voice_rate_limit_per_minute,
                _RATE_WINDOW_SECONDS,
            )
            if not (within_ip_budget and within_phone_budget):
                await websocket.send_json({
                    "error": "RATE_LIMITED",
                    "detail": ErrorMessages.RATE_LIMIT_VOICE,
                    "retry_after": _RATE_WINDOW_SECONDS,
                })
                continue

            # Get a fresh DB session for WebSocket
            from app.core.database import async_session
            async with async_session() as db:
                state = PipelineState(
                    session_id=session_id,
                    raw_text=ws_request.text,
                    raw_audio_base64=ws_request.audio_base64,
                    language_detected=ws_request.language or "English",
                    language_code=_language_to_code(ws_request.language or "English"),
                    phone=ws_request.phone,
                    input_order_id=ws_request.order_id,
                )

                # Load history
                if session_id:
                    memory = await get_memory_service()
                    history = await memory.get_conversation_history(session_id)
                    state.conversation_history = history

                pipeline = VoiceCarePipeline(db=db, on_stage_update=on_stage_update)
                state = await pipeline.run(state)

                # Send final response — all VoiceQueryResponse fields plus the
                # WS framing keys, built from the shared response builder.
                await websocket.send_json({
                    "type": "response",
                    "is_complete": True,
                    **_build_voice_response(state),
                })

                # Store turns
                await memory.store_conversation_turn(
                    session_id, "customer", state.transcript_original or ""
                )
                await memory.store_conversation_turn(
                    session_id,
                    "ai",
                    state.response_english or "",
                    display_content=state.response_text or "",
                )

                try:
                    await db.commit()
                except Exception as db_exc:
                    # Catch all SQLAlchemy errors — PendingRollbackError,
                    # IntegrityError, OperationalError, etc. — so the WS
                    # handler never crashes after a failed commit.
                    try:
                        await db.rollback()
                    except Exception as rb_exc:
                        logger.warning(
                            "websocket_db_rollback_failed",
                            session_id=session_id,
                            error=str(rb_exc),
                        )
                    logger.error(
                        "websocket_db_commit_failed",
                        session_id=session_id,
                        error=str(db_exc),
                        exc_info=True,
                    )

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", session_id=session_id)
    except Exception as e:
        logger.error("websocket_error", session_id=session_id, error=str(e))
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
    finally:
        ping_task.cancel()
        remaining = _ws_connections.get(client_ip, 1) - 1
        if remaining > 0:
            _ws_connections[client_ip] = remaining
        else:
            _ws_connections.pop(client_ip, None)


# ================================================================
# Session Reset (clears multi-turn memory for a session)
# ================================================================

@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, request: Request):
    """Return the stored turns for a session so a reloaded page can restore
    its conversation thread. Same trust model as DELETE below: the session id
    is an unguessable client-generated UUIDv4, and history expires after 2h.
    """
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    await enforce_rate_limit(
        key=f"rate_limit:session_history:{get_client_ip(request)}",
        limit=settings.voice_rate_limit_ip_per_minute,
        window_seconds=_RATE_WINDOW_SECONDS,
        detail="Too many requests. Please slow down.",
    )

    memory = await get_memory_service()
    history = await memory.get_conversation_history(session_id, max_turns=50)
    # Expose only the documented fields — never whatever else lands in memory.
    # Roles as stored by the pipeline: "customer" and "ai". Prefer the
    # customer-language display text over the English LLM-context copy.
    turns = [
        {
            "role": t.get("role"),
            "content": t.get("display_content") or t.get("content"),
            "timestamp": t.get("timestamp"),
        }
        for t in history
        if t.get("role") in ("customer", "ai") and (t.get("display_content") or t.get("content"))
    ]
    return {"session_id": session_id, "turns": turns}


@router.delete("/session/{session_id}")
async def clear_session(session_id: str, request: Request):
    """Clear conversation history and identity context for a session (new conversation)."""
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format.")

    await enforce_rate_limit(
        key=f"rate_limit:session_clear:{get_client_ip(request)}",
        limit=settings.voice_rate_limit_ip_per_minute,
        window_seconds=_RATE_WINDOW_SECONDS,
        detail="Too many requests. Please slow down.",
    )

    try:
        memory = await get_memory_service()
        await memory.clear_conversation(session_id)
        logger.info("session_cleared", session_id=session_id)
        return {"cleared": True, "session_id": session_id}
    except Exception as exc:
        logger.error("session_clear_failed", session_id=session_id, error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to clear session")


# ================================================================
# Helpers
# ================================================================

def _language_to_code(language: str) -> str:
    """Convert language display name to BCP-47 code via shared LANGUAGE_CODES constant."""
    return LANGUAGE_CODES.get(language, "en")
