"""
CommerceMind VoiceCare AI — Pydantic Schemas
Request/Response models for the API layer.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================================
# Voice Query Schemas
# ============================================================

class VoiceQueryRequest(BaseModel):
    """Request to process a voice/text query."""
    text: Optional[str] = Field(None, description="Text query (for text-only mode)")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded audio")
    language: Optional[str] = Field(None, description="Language hint (auto-detected if empty)")
    phone: Optional[str] = Field(None, description="Customer phone for lookup")
    order_id: Optional[str] = Field(None, description="Specific order ID to check")
    session_id: Optional[str] = Field(None, description="Existing session ID for multi-turn")


class PipelineStageUpdate(BaseModel):
    """WebSocket message for pipeline stage progress."""
    stage: str  # listening / understanding / checking_order / finding_policy / responding
    stage_number: int
    total_stages: int
    message: str
    is_complete: bool = False


class VoiceQueryResponse(BaseModel):
    """Response from the voice query pipeline."""
    session_id: str
    ticket_id: str
    response_text: str
    response_audio_base64: Optional[str] = None
    language: str
    intent: str
    sentiment: str
    priority: str
    recommended_action: str
    policy_reference: Optional[str] = None
    confidence_score: float
    is_escalated: bool
    escalation_reason: Optional[str] = None
    agent_trace: List[dict] = []


# ============================================================
# Ticket Schemas
# ============================================================

class TicketSummary(BaseModel):
    """Ticket list item."""
    ticket_id: uuid.UUID
    user_name: str
    phone: str
    ticket_type: str
    priority: str
    status: str
    language: str
    sentiment: Optional[str]
    summary: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class TicketDetail(BaseModel):
    """Full ticket detail with resolution and messages."""
    ticket_id: uuid.UUID
    user_name: str
    phone: str
    ticket_type: str
    priority: str
    status: str
    language: str
    sentiment: Optional[str]
    summary: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    escalated_at: Optional[datetime]

    # Order info
    order_id: Optional[uuid.UUID]
    order_status: Optional[str]
    order_amount: Optional[float]
    order_date: Optional[datetime]

    # Resolution
    recommended_action: Optional[str]
    policy_reference: Optional[str]
    response_text: Optional[str]
    internal_note: Optional[str]
    confidence_score: Optional[float]
    agent_trace: Optional[List[dict]] = []

    # Messages
    messages: List[dict] = []

    class Config:
        from_attributes = True


class HandoffNote(BaseModel):
    """Auto-generated handoff note for escalated tickets."""
    ticket_id: uuid.UUID
    customer_name: str
    customer_phone: str
    language: str
    issue_summary: str
    sentiment: str
    priority: str
    order_details: Optional[str]
    ai_attempted_resolution: str
    policy_referenced: Optional[str]
    escalation_reason: str
    recommended_next_steps: str
    conversation_history: List[dict]
    generated_at: datetime


# ============================================================
# Analytics Schemas
# ============================================================

class AnalyticsOverview(BaseModel):
    """Dashboard analytics overview."""
    total_tickets: int
    open_tickets: int
    escalated_tickets: int
    resolved_tickets: int
    avg_resolution_time_minutes: Optional[float]
    tickets_by_language: dict
    tickets_by_category: dict
    tickets_by_priority: dict
    tickets_by_sentiment: dict
    tickets_over_time: List[dict]
    resolution_rate: float
    escalation_rate: float


# ============================================================
# User Lookup Schemas
# ============================================================

class CustomerLookupRequest(BaseModel):
    """Customer identification by phone + order ID."""
    phone: str
    order_id: Optional[str] = None


class CustomerLookupResponse(BaseModel):
    """Customer data with recent orders."""
    user_id: uuid.UUID
    name: str
    phone: str
    preferred_language: str
    customer_segment: str
    recent_orders: List[dict] = []


# ============================================================
# Admin Auth Schemas
# ============================================================

class AdminLoginRequest(BaseModel):
    """Admin login credentials."""
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    """Admin login response with token."""
    access_token: str
    token_type: str = "bearer"
    admin_email: str
