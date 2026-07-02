"""
Table-driven tests for the six deterministic escalation rules
(agent_escalation_check) — the product's core differentiator, previously
untested. Pure state-in/state-out: no DB or LLM involved.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.state import PipelineState


def _pipeline():
    from app.agents.pipeline import VoiceCarePipeline

    with (
        patch("app.agents.pipeline.get_gemini_service", return_value=MagicMock()),
        patch("app.agents.pipeline.get_bhashini_service", return_value=MagicMock()),
        patch("app.agents.pipeline.get_chroma_service", return_value=MagicMock()),
        patch("app.agents.pipeline.get_memory_service", new=AsyncMock(return_value=MagicMock())),
    ):
        return VoiceCarePipeline(db=MagicMock())


# (case id, state kwargs, expect_escalated, expected rule substring)
RULE_CASES = [
    (
        "rule1_angry_sentiment",
        {"sentiment": "Angry", "confidence_score": 0.9},
        True,
        "Angry customer",
    ),
    (
        "rule1_very_angry_sentiment",
        {"sentiment": "Very Angry", "confidence_score": 0.9},
        True,
        "Angry customer",
    ),
    (
        "rule2_high_value_negative",
        {
            "sentiment": "Negative",
            "confidence_score": 0.9,
            "order_data": {"total_amount": 6000},
        },
        True,
        "High-value order",
    ),
    (
        "rule2_high_value_neutral_not_escalated",
        {
            "sentiment": "Neutral",
            "confidence_score": 0.9,
            "order_data": {"total_amount": 6000},
        },
        False,
        None,
    ),
    (
        "rule2_low_value_negative_not_escalated",
        {
            "sentiment": "Negative",
            "confidence_score": 0.9,
            "order_data": {"total_amount": 500},
        },
        False,
        None,
    ),
    (
        "rule3_pending_refund",
        {
            "confidence_score": 0.9,
            "refund_data": {"status": "Pending", "amount": 1200.0},
        },
        True,
        "Refund delayed",
    ),
    (
        "rule4_failed_payment",
        {
            "confidence_score": 0.9,
            "intent": "payment_issue",
            "payment_data": {"payments": [{"status": "Failed", "amount": 999.0}]},
        },
        True,
        "Payment deducted",
    ),
    (
        "rule4_success_payment_cancelled_order",
        {
            "confidence_score": 0.9,
            "intent": "payment_issue",
            "order_data": {"status": "Cancelled", "total_amount": 999},
            "payment_data": {"payments": [{"status": "Success", "amount": 999.0}]},
        },
        True,
        "Payment deducted",
    ),
    (
        "rule5_low_confidence_boundary_below",
        {"confidence_score": 0.39},
        True,
        "Low AI confidence",
    ),
    (
        "rule5_low_confidence_boundary_at",
        {"confidence_score": 0.40},
        False,
        None,
    ),
    (
        "rule6_llm_escalate",
        {"confidence_score": 0.9, "recommended_action": "Escalate"},
        True,
        "human escalation",
    ),
    (
        "no_rules_triggered",
        {
            "sentiment": "Positive",
            "confidence_score": 0.95,
            "recommended_action": "Inform",
        },
        False,
        None,
    ),
]


class TestEscalationRules:

    @pytest.mark.parametrize(
        "case_id, state_kwargs, expect_escalated, rule_substring",
        RULE_CASES,
        ids=[c[0] for c in RULE_CASES],
    )
    @pytest.mark.asyncio
    async def test_rule(self, case_id, state_kwargs, expect_escalated, rule_substring):
        state = PipelineState(raw_text="query", **state_kwargs)
        result = await _pipeline().agent_escalation_check(state)

        assert result.is_escalated is expect_escalated
        if expect_escalated:
            assert rule_substring in result.escalation_reason
            assert result.escalation_rules_triggered
        else:
            assert result.escalation_reason is None
            assert result.escalation_rules_triggered == []

    @pytest.mark.asyncio
    async def test_multiple_rules_all_recorded(self):
        """Every triggered rule appears in the joined reason."""
        state = PipelineState(
            raw_text="query",
            sentiment="Very Angry",
            confidence_score=0.2,
            refund_data={"status": "Pending"},
        )
        result = await _pipeline().agent_escalation_check(state)

        assert result.is_escalated is True
        assert len(result.escalation_rules_triggered) == 3
        for fragment in ("Angry customer", "Refund delayed", "Low AI confidence"):
            assert fragment in result.escalation_reason

    @pytest.mark.asyncio
    async def test_llm_outage_fallback_escalates(self):
        """The Gemini fallback resolution (confidence 0.3) must trip Rule 5."""
        from app.services.gemini_service import GeminiService

        with patch("app.services.gemini_service.genai"):
            svc = GeminiService.__new__(GeminiService)
            svc._call_gemini = AsyncMock(side_effect=Exception("LLM down"))
            fallback = await svc.generate_resolution(
                query="q", intent="general_inquiry",
                order_data=None, policy_context="", sentiment="Neutral",
            )

        state = PipelineState(raw_text="q", confidence_score=fallback["confidence_score"])
        result = await _pipeline().agent_escalation_check(state)

        assert result.is_escalated is True
        assert "Low AI confidence" in result.escalation_reason
