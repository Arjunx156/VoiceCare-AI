"""
CommerceMind VoiceCare AI — Ticket & Dashboard API Routes
"""

import json
import uuid
import structlog
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.db.models import (
    SupportTicket, SupportResolution, SupportMessage,
    User, Order, CustomerSentiment,
)
from app.schemas.schemas import (
    TicketSummary, TicketDetail, HandoffNote, AnalyticsOverview,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("/", response_model=List[TicketSummary])
async def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List support tickets with optional filters."""
    # Eager-load user to avoid N+1 queries
    query = (
        select(SupportTicket)
        .options(selectinload(SupportTicket.user))
        .order_by(SupportTicket.created_at.desc())
    )

    if status:
        query = query.where(SupportTicket.status == status)
    if priority:
        query = query.where(SupportTicket.priority == priority)
    if language:
        query = query.where(SupportTicket.language == language)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    tickets = result.scalars().all()

    return [
        TicketSummary(
            ticket_id=t.ticket_id,
            user_name=t.user.name if t.user else "Unknown",
            phone=t.user.phone if t.user else "",
            ticket_type=t.ticket_type,
            priority=t.priority,
            status=t.status,
            language=t.language,
            sentiment=t.sentiment,
            summary=t.summary,
            created_at=t.created_at,
            resolved_at=t.resolved_at,
        )
        for t in tickets
    ]


@router.get("/escalations", response_model=List[TicketSummary])
async def list_escalations(
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List escalated tickets for the escalation queue."""
    # Eager-load user to avoid N+1 queries
    query = (
        select(SupportTicket)
        .options(selectinload(SupportTicket.user))
        .where(SupportTicket.status == "Escalated")
        .order_by(SupportTicket.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    tickets = result.scalars().all()

    return [
        TicketSummary(
            ticket_id=t.ticket_id,
            user_name=t.user.name if t.user else "Unknown",
            phone=t.user.phone if t.user else "",
            ticket_type=t.ticket_type,
            priority=t.priority,
            status=t.status,
            language=t.language,
            sentiment=t.sentiment,
            summary=t.summary,
            created_at=t.created_at,
            resolved_at=t.resolved_at,
        )
        for t in tickets
    ]


@router.get("/analytics", response_model=AnalyticsOverview)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Dashboard analytics overview."""
    # Total counts
    total = await db.scalar(select(func.count(SupportTicket.ticket_id)))
    open_count = await db.scalar(
        select(func.count(SupportTicket.ticket_id)).where(SupportTicket.status == "Open")
    )
    escalated = await db.scalar(
        select(func.count(SupportTicket.ticket_id)).where(SupportTicket.status == "Escalated")
    )
    resolved = await db.scalar(
        select(func.count(SupportTicket.ticket_id)).where(SupportTicket.status == "Resolved")
    )

    # By language
    lang_result = await db.execute(
        select(SupportTicket.language, func.count(SupportTicket.ticket_id))
        .group_by(SupportTicket.language)
    )
    by_language = {row[0]: row[1] for row in lang_result.all()}

    # By category
    cat_result = await db.execute(
        select(SupportTicket.ticket_type, func.count(SupportTicket.ticket_id))
        .group_by(SupportTicket.ticket_type)
    )
    by_category = {row[0]: row[1] for row in cat_result.all()}

    # By priority
    pri_result = await db.execute(
        select(SupportTicket.priority, func.count(SupportTicket.ticket_id))
        .group_by(SupportTicket.priority)
    )
    by_priority = {row[0]: row[1] for row in pri_result.all()}

    # By sentiment
    sent_result = await db.execute(
        select(SupportTicket.sentiment, func.count(SupportTicket.ticket_id))
        .where(SupportTicket.sentiment.isnot(None))
        .group_by(SupportTicket.sentiment)
    )
    by_sentiment = {row[0]: row[1] for row in sent_result.all()}

    total = total or 0
    resolved = resolved or 0
    escalated = escalated or 0

    return AnalyticsOverview(
        total_tickets=total,
        open_tickets=open_count or 0,
        escalated_tickets=escalated,
        resolved_tickets=resolved,
        avg_resolution_time_minutes=None,
        tickets_by_language=by_language,
        tickets_by_category=by_category,
        tickets_by_priority=by_priority,
        tickets_by_sentiment=by_sentiment,
        tickets_over_time=[],
        resolution_rate=round(resolved / total * 100, 1) if total > 0 else 0,
        escalation_rate=round(escalated / total * 100, 1) if total > 0 else 0,
    )


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Get full ticket detail with resolution, messages, and agent trace."""
    try:
        tid = uuid.UUID(ticket_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket ID")

    result = await db.execute(
        select(SupportTicket).where(SupportTicket.ticket_id == tid)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Get user
    user = None
    if ticket.user_id:
        user_result = await db.execute(select(User).where(User.user_id == ticket.user_id))
        user = user_result.scalar_one_or_none()

    # Get order
    order = None
    if ticket.order_id:
        order_result = await db.execute(select(Order).where(Order.order_id == ticket.order_id))
        order = order_result.scalar_one_or_none()

    # Get resolution
    res_result = await db.execute(
        select(SupportResolution).where(SupportResolution.ticket_id == tid)
    )
    resolution = res_result.scalar_one_or_none()

    # Get messages
    msg_result = await db.execute(
        select(SupportMessage)
        .where(SupportMessage.ticket_id == tid)
        .order_by(SupportMessage.timestamp)
    )
    messages = msg_result.scalars().all()

    # Parse agent trace
    agent_trace = []
    if resolution and resolution.agent_trace:
        try:
            agent_trace = json.loads(resolution.agent_trace)
        except (json.JSONDecodeError, TypeError):
            agent_trace = []

    return TicketDetail(
        ticket_id=ticket.ticket_id,
        user_name=user.name if user else "Unknown",
        phone=user.phone if user else "",
        ticket_type=ticket.ticket_type,
        priority=ticket.priority,
        status=ticket.status,
        language=ticket.language,
        sentiment=ticket.sentiment,
        summary=ticket.summary,
        created_at=ticket.created_at,
        resolved_at=ticket.resolved_at,
        escalated_at=ticket.escalated_at,
        order_id=ticket.order_id,
        order_status=order.status if order else None,
        order_amount=float(order.total_amount) if order else None,
        order_date=order.order_date if order else None,
        recommended_action=resolution.recommended_action if resolution else None,
        policy_reference=resolution.policy_reference if resolution else None,
        response_text=resolution.final_response_text if resolution else None,
        internal_note=resolution.internal_note if resolution else None,
        confidence_score=resolution.confidence_score if resolution else None,
        agent_trace=agent_trace,
        messages=[
            {
                "message_id": str(m.message_id),
                "sender_type": m.sender_type,
                "message_text": m.message_text,
                "language": m.language,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in messages
        ],
    )


@router.get("/{ticket_id}/handoff", response_model=HandoffNote)
async def get_handoff_note(ticket_id: str, db: AsyncSession = Depends(get_db)):
    """Get auto-generated handoff note for an escalated ticket."""
    try:
        tid = uuid.UUID(ticket_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket ID")

    result = await db.execute(
        select(SupportTicket).where(SupportTicket.ticket_id == tid)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Gather all context
    user = None
    if ticket.user_id:
        u = await db.execute(select(User).where(User.user_id == ticket.user_id))
        user = u.scalar_one_or_none()

    res = await db.execute(
        select(SupportResolution).where(SupportResolution.ticket_id == tid)
    )
    resolution = res.scalar_one_or_none()

    msgs = await db.execute(
        select(SupportMessage).where(SupportMessage.ticket_id == tid).order_by(SupportMessage.timestamp)
    )
    messages = msgs.scalars().all()

    # Determine escalation reason from agent trace
    escalation_reason = "Unknown"
    if resolution and resolution.agent_trace:
        try:
            trace = json.loads(resolution.agent_trace)
            for step in trace:
                if step.get("agent_name") == "Escalation Check" and step.get("decision") == "ESCALATED":
                    escalation_reason = step.get("reasoning", "Escalation rules triggered")
        except (json.JSONDecodeError, TypeError):
            pass

    return HandoffNote(
        ticket_id=ticket.ticket_id,
        customer_name=user.name if user else "Unknown",
        customer_phone=user.phone if user else "",
        language=ticket.language,
        issue_summary=ticket.summary or "No summary available",
        sentiment=ticket.sentiment or "Neutral",
        priority=ticket.priority,
        order_details=f"Order status: {ticket.order_id}" if ticket.order_id else None,
        ai_attempted_resolution=resolution.final_response_text if resolution else "No AI resolution",
        policy_referenced=resolution.policy_reference if resolution else None,
        escalation_reason=escalation_reason,
        recommended_next_steps=resolution.internal_note if resolution else "Review the ticket manually",
        conversation_history=[
            {"sender": m.sender_type, "text": m.message_text, "time": m.timestamp.isoformat()}
            for m in messages
        ],
        generated_at=datetime.utcnow(),
    )
