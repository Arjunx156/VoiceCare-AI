"""
CommerceMind VoiceCare AI — SQLAlchemy Models
All 15 tables across 3 clusters: Customer & Catalog, Fulfillment & Payments, Support & AI.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, ForeignKey,
    Enum as SQLEnum, Numeric, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


# ============================================================
# Cluster 1: Customer & Catalog
# ============================================================

class User(Base):
    """Customer accounts."""
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str] = mapped_column(
        String(20), default="Hindi", nullable=False
    )
    customer_segment: Mapped[str] = mapped_column(
        String(20), default="Regular", nullable=False  # Regular / Premium / New
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    # Audit fields
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # system / admin / pipeline
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    orders: Mapped[List["Order"]] = relationship(back_populates="user", lazy="selectin")
    voice_sessions: Mapped[List["VoiceSession"]] = relationship(back_populates="user", lazy="selectin")
    support_tickets: Mapped[List["SupportTicket"]] = relationship(back_populates="user", lazy="selectin")


class Product(Base):
    """Product catalog."""
    __tablename__ = "products"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="product", lazy="selectin")


class Order(Base):
    """Customer orders."""
    __tablename__ = "orders"

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Short, customer-facing order code (e.g. "ORD-7K3F"). The UUID stays the PK.
    order_number: Mapped[Optional[str]] = mapped_column(String(16), unique=True, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="Placed", nullable=False
        # Placed / Confirmed / Shipped / Out for Delivery / Delivered / Cancelled
    )
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    # Audit fields
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    order_items: Mapped[List["OrderItem"]] = relationship(back_populates="order", lazy="selectin")
    shipment: Mapped[Optional["Shipment"]] = relationship(back_populates="order", uselist=False, lazy="selectin")
    return_request: Mapped[Optional["Return"]] = relationship(back_populates="order", uselist=False, lazy="selectin")
    payments: Mapped[List["Payment"]] = relationship(back_populates="order", lazy="selectin")
    support_tickets: Mapped[List["SupportTicket"]] = relationship(back_populates="order", lazy="selectin")

    __table_args__ = (
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_status", "status"),
    )


class OrderItem(Base):
    """Individual items within an order."""
    __tablename__ = "order_items"

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_at_purchase: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="order_items")
    product: Mapped["Product"] = relationship(back_populates="order_items")


# ============================================================
# Cluster 2: Fulfillment & Payments
# ============================================================

class Shipment(Base):
    """Shipment tracking for orders."""
    __tablename__ = "shipments"

    shipment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), unique=True, nullable=False
    )
    courier_partner: Mapped[str] = mapped_column(String(100), nullable=False)
    shipment_status: Mapped[str] = mapped_column(
        String(30), default="Pending", nullable=False
        # Pending / Picked Up / In Transit / Out for Delivery / Delivered / RTO
    )
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="shipment")


class Return(Base):
    """Return requests."""
    __tablename__ = "returns"

    return_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), unique=True, nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="Requested", nullable=False
        # Requested / Approved / Rejected / Pickup Scheduled / Completed
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    eligibility_window_days: Mapped[int] = mapped_column(
        Integer, default=7, nullable=False
    )
    # Audit fields
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="return_request")
    refund: Mapped[Optional["Refund"]] = relationship(back_populates="return_request", uselist=False, lazy="selectin")


class Refund(Base):
    """Refund records."""
    __tablename__ = "refunds"

    refund_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    return_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("returns.return_id"), nullable=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="Pending", nullable=False
        # Pending / Approved / Processing / Credited / Rejected
    )
    credited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    # Audit fields
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    return_request: Mapped[Optional["Return"]] = relationship(back_populates="refund")


class Payment(Base):
    """Payment transactions."""
    __tablename__ = "payments"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="Pending", nullable=False
        # Pending / Success / Failed / Refunded
    )
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False  # UPI / Credit Card / Debit Card / Net Banking / COD
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship(back_populates="payments")

    __table_args__ = (
        Index("idx_payments_order_id", "order_id"),
        Index("idx_payments_status", "status"),
    )


# ============================================================
# Cluster 3: Support & AI
# ============================================================

class VoiceSession(Base):
    """Voice interaction sessions."""
    __tablename__ = "voice_sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )
    language_detected: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    audio_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    transcript_original: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript_english: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="voice_sessions")
    messages: Mapped[List["SupportMessage"]] = relationship(back_populates="voice_session", lazy="selectin")


class SupportTicket(Base):
    """Support tickets generated from voice interactions."""
    __tablename__ = "support_tickets"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Short, customer-facing ticket code (e.g. "TKT-9QXM2"). The UUID stays the PK.
    ticket_number: Mapped[Optional[str]] = mapped_column(String(16), unique=True, nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False
    )
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=True
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("voice_sessions.session_id"), nullable=True
    )
    ticket_type: Mapped[str] = mapped_column(
        String(30), nullable=False
        # Delay / Refund / Return / Payment / Complaint / General
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="Medium", nullable=False
        # Low / Medium / High / Critical
    )
    status: Mapped[str] = mapped_column(
        String(20), default="Open", nullable=False
        # Open / In Progress / Resolved / Escalated / Closed
    )
    language: Mapped[str] = mapped_column(String(20), default="English", nullable=False)
    sentiment: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True  # Neutral / Negative / Angry
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # agent email who claimed
    # Audit fields
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="support_tickets")
    order: Mapped[Optional["Order"]] = relationship(back_populates="support_tickets")
    messages: Mapped[List["SupportMessage"]] = relationship(back_populates="ticket", lazy="selectin")
    resolution: Mapped[Optional["SupportResolution"]] = relationship(
        back_populates="ticket", uselist=False, lazy="selectin"
    )
    sentiment_records: Mapped[List["CustomerSentiment"]] = relationship(
        back_populates="ticket", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_tickets_user_id", "user_id"),
        Index("idx_tickets_status", "status"),
        Index("idx_tickets_priority", "priority"),
        Index("idx_tickets_created_at", "created_at"),
    )


class SupportMessage(Base):
    """Individual messages within a support conversation."""
    __tablename__ = "support_messages"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("support_tickets.ticket_id"), nullable=False
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("voice_sessions.session_id"), nullable=True
    )
    sender_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # Customer / AI / Human
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="English", nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    # Audit fields
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    ticket: Mapped["SupportTicket"] = relationship(back_populates="messages")
    voice_session: Mapped[Optional["VoiceSession"]] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_messages_ticket_id", "ticket_id"),
        Index("idx_messages_timestamp", "timestamp"),
    )


class SupportResolution(Base):
    """AI-generated resolution for a support ticket."""
    __tablename__ = "support_resolutions"

    resolution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("support_tickets.ticket_id"), unique=True, nullable=False
    )
    recommended_action: Mapped[str] = mapped_column(
        String(30), nullable=False
        # Inform / Refund / Replace / Escalate / Reject / Apologize
    )
    policy_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_response_text: Mapped[str] = mapped_column(Text, nullable=False)
    final_response_audio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    internal_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    agent_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON trace of agent decisions
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    # Audit fields
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    ticket: Mapped["SupportTicket"] = relationship(back_populates="resolution")


class PolicyDocument(Base):
    """Company policy documents used for RAG retrieval."""
    __tablename__ = "policy_documents"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
        # Shipping / Return / Refund / Cancellation / Replacement / Warranty /
        # Compensation / Escalation SOP / Payment Failure SOP
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class EscalationRule(Base):
    """Deterministic escalation rules (code, not LLM)."""
    __tablename__ = "escalation_rules"

    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    condition_description: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority_level: Mapped[str] = mapped_column(String(20), default="High", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


class CustomerSentiment(Base):
    """Sentiment tracking per ticket interaction."""
    __tablename__ = "customer_sentiment"

    sentiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("support_tickets.ticket_id"), nullable=False
    )
    sentiment_label: Mapped[str] = mapped_column(
        String(30), nullable=False
        # Calm / Confused / Dissatisfied / Angry / Very Angry / High-risk Escalation
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    ticket: Mapped["SupportTicket"] = relationship(back_populates="sentiment_records")
