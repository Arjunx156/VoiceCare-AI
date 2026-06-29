"""
CommerceMind VoiceCare AI — Customer 360 API Routes

Surfaces customer profiles (orders, ticket history, sentiment timeline) built
from data the platform already captures but never exposed in the dashboard.
"""

import uuid
import structlog
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.auth import require_admin
from app.db.models import (
    User, Order, Shipment, SupportTicket, CustomerSentiment,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/customers",
    tags=["customers"],
    dependencies=[Depends(require_admin)],
)


@router.get("/")
async def list_customers(
    search: Optional[str] = Query(None, description="Match name, phone, or email"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """List/search customers with ticket counts and last contact time."""
    query = select(User).order_by(User.created_at.desc())
    if search:
        like = f"%{search.strip()}%"
        query = query.where(
            or_(
                User.name.ilike(like),
                User.phone.ilike(like),
                User.email.ilike(like),
            )
        )
    query = query.limit(limit).offset(offset)
    users = (await db.execute(query)).scalars().all()

    if not users:
        return []

    user_ids = [u.user_id for u in users]
    # One aggregate round-trip for ticket counts + last contact per user.
    agg_rows = (await db.execute(
        select(
            SupportTicket.user_id,
            func.count(SupportTicket.ticket_id).label("ticket_count"),
            func.max(SupportTicket.created_at).label("last_contact"),
        )
        .where(SupportTicket.user_id.in_(user_ids), SupportTicket.deleted_at.is_(None))
        .group_by(SupportTicket.user_id)
    )).all()
    agg = {row.user_id: (row.ticket_count, row.last_contact) for row in agg_rows}

    return [
        {
            "user_id": str(u.user_id),
            "name": u.name,
            "phone": u.phone,
            "email": u.email,
            "city": u.city,
            "customer_segment": u.customer_segment,
            "preferred_language": u.preferred_language,
            "ticket_count": agg.get(u.user_id, (0, None))[0],
            "last_contact": (agg.get(u.user_id, (0, None))[1] or None)
            and agg[u.user_id][1].isoformat(),
        }
        for u in users
    ]


@router.get("/{customer_id}")
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    """Full customer profile: orders, ticket history, and sentiment timeline."""
    try:
        uid = uuid.UUID(customer_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid customer ID")

    user = (await db.execute(select(User).where(User.user_id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Orders with their shipment, most recent first.
    orders = (await db.execute(
        select(Order)
        .options(selectinload(Order.shipment))
        .where(Order.user_id == uid)
        .order_by(Order.order_date.desc())
        .limit(50)
    )).scalars().all()

    # Tickets for this customer.
    tickets = (await db.execute(
        select(SupportTicket)
        .where(SupportTicket.user_id == uid, SupportTicket.deleted_at.is_(None))
        .order_by(SupportTicket.created_at.desc())
        .limit(50)
    )).scalars().all()

    # Sentiment timeline across all of this customer's tickets.
    ticket_ids = [t.ticket_id for t in tickets]
    sentiment_rows = []
    if ticket_ids:
        sentiment_rows = (await db.execute(
            select(CustomerSentiment)
            .where(CustomerSentiment.ticket_id.in_(ticket_ids))
            .order_by(CustomerSentiment.recorded_at.asc())
        )).scalars().all()

    def _shipment(o: Order):
        s = o.shipment
        if not s:
            return None
        return {
            "status": s.shipment_status,
            "courier": s.courier_partner,
            "tracking_number": s.tracking_number,
            "expected_delivery": s.expected_delivery_date.isoformat() if s.expected_delivery_date else None,
        }

    return {
        "user_id": str(user.user_id),
        "name": user.name,
        "phone": user.phone,
        "email": user.email,
        "city": user.city,
        "customer_segment": user.customer_segment,
        "preferred_language": user.preferred_language,
        "created_at": user.created_at.isoformat(),
        "orders": [
            {
                "order_id": str(o.order_id),
                "order_date": o.order_date.isoformat(),
                "status": o.status,
                "total_amount": float(o.total_amount),
                "shipment": _shipment(o),
            }
            for o in orders
        ],
        "tickets": [
            {
                "ticket_id": str(t.ticket_id),
                "ticket_type": t.ticket_type,
                "status": t.status,
                "priority": t.priority,
                "sentiment": t.sentiment,
                "summary": t.summary,
                "created_at": t.created_at.isoformat(),
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            }
            for t in tickets
        ],
        "sentiment_timeline": [
            {
                "label": s.sentiment_label,
                "confidence": s.confidence_score,
                "recorded_at": s.recorded_at.isoformat(),
            }
            for s in sentiment_rows
        ],
    }
