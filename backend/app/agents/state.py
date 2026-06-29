"""
CommerceMind VoiceCare AI — Pipeline State Schema
Shared state that flows through all 9 agents in the LangGraph pipeline.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AgentTraceStep(BaseModel):
    agent_name: str
    stage_number: int
    input_summary: str
    output_summary: str
    decision: Optional[str] = None
    reasoning: Optional[str] = None
    duration_ms: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineState(BaseModel):
    """Shared state flowing through the 9-agent LangGraph pipeline."""

    # Session
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = Field(default_factory=datetime.utcnow)

    # Input
    raw_audio_base64: Optional[str] = None
    raw_text: Optional[str] = None
    phone: Optional[str] = None
    input_order_id: Optional[str] = None

    # Stage 1: Voice Intake
    transcript_original: Optional[str] = None
    transcript_english: Optional[str] = None
    language_detected: str = "English"
    language_code: str = "en"

    # Stage 2: Intent + Sentiment + Priority
    intent: Optional[str] = None
    sub_intent: Optional[str] = None
    sentiment: str = "Neutral"
    priority: str = "Medium"
    summary_english: Optional[str] = None
    requires_order_lookup: bool = False
    extracted_order_id: Optional[str] = None
    extracted_phone: Optional[str] = None
    extracted_name: Optional[str] = None

    # Identity confirmation: set when a caller is matched only loosely (e.g. by
    # name) and must confirm their order number / phone before we share details.
    identity_needs_confirmation: bool = False

    # Stage 3: Order Lookup
    user_data: Optional[dict] = None
    order_data: Optional[dict] = None
    shipment_data: Optional[dict] = None
    return_data: Optional[dict] = None
    refund_data: Optional[dict] = None
    payment_data: Optional[dict] = None
    lookup_successful: bool = False

    # Stage 4: Policy RAG
    policy_context: Optional[str] = None
    retrieved_policies: List[dict] = Field(default_factory=list)
    rag_retrieved_count: int = 0       # 0 means no policy grounding — resolution confidence is capped

    # Stage 5: Resolution
    recommended_action: Optional[str] = None
    resolution_summary: Optional[str] = None
    policy_reference: Optional[str] = None
    internal_note: Optional[str] = None
    confidence_score: float = 0.0
    requires_human_review: bool = False

    # Stage 6: Escalation Check
    is_escalated: bool = False
    escalation_reason: Optional[str] = None
    escalation_rules_triggered: List[str] = Field(default_factory=list)

    # Stage 7: Response Generation
    response_text: Optional[str] = None
    response_english: Optional[str] = None
    response_tone: Optional[str] = None

    # Stage 8: TTS
    response_audio_base64: Optional[str] = None

    # Stage 9: Ticket Creation
    ticket_id: Optional[str] = None
    ticket_number: Optional[str] = None       # short, customer-facing code (TKT-xxxxx)
    ticket_created: bool = False

    # Trace
    agent_trace: List[AgentTraceStep] = Field(default_factory=list)
    current_stage: int = 0
    total_stages: int = 9

    # Error Handling
    error: Optional[str] = None
    has_error: bool = False

    # Multi-turn
    conversation_history: List[dict] = Field(default_factory=list)

    def add_trace(self, agent_name, stage_number, input_summary, output_summary,
                  decision=None, reasoning=None, duration_ms=None):
        self.agent_trace.append(AgentTraceStep(
            agent_name=agent_name, stage_number=stage_number,
            input_summary=input_summary, output_summary=output_summary,
            decision=decision, reasoning=reasoning, duration_ms=duration_ms,
        ))
        self.current_stage = stage_number
