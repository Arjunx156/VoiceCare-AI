"""
Mock fixtures for Gemini LLM responses.
Import these from conftest.py or use directly in unit tests.
"""

import json

# Intent analysis mock responses
INTENT_RESPONSES = {
    "order_status": {
        "intent": "order_status",
        "sub_intent": "customer wants to know delivery status",
        "sentiment": "Neutral",
        "priority": "Medium",
        "summary_english": "Customer asking about order status",
        "requires_order_lookup": True,
        "extracted_order_id": None,
        "extracted_phone": "9876543210",
        "extracted_name": None,
    },
    "refund_angry": {
        "intent": "refund_status",
        "sub_intent": "customer demanding refund for delayed product",
        "sentiment": "Angry",
        "priority": "High",
        "summary_english": "Customer angry about delayed refund",
        "requires_order_lookup": True,
        "extracted_order_id": None,
        "extracted_phone": "9876543210",
        "extracted_name": "Raj",
    },
    "general_inquiry": {
        "intent": "general_inquiry",
        "sub_intent": "product availability question",
        "sentiment": "Neutral",
        "priority": "Low",
        "summary_english": "Customer asking about product availability",
        "requires_order_lookup": False,
        "extracted_order_id": None,
        "extracted_phone": None,
        "extracted_name": None,
    },
}

RESOLUTION_RESPONSES = {
    "inform": {
        "recommended_action": "Inform",
        "resolution_summary": "Order is in transit.",
        "policy_reference": "Standard shipping policy",
        "internal_note": "No escalation needed.",
        "confidence_score": 0.9,
        "requires_human_review": False,
        "reason_for_action": "Order status clear from DB.",
    },
    "escalate": {
        "recommended_action": "Escalate",
        "resolution_summary": "Complex refund case requiring manager approval.",
        "policy_reference": "Refund policy section 3.2",
        "internal_note": "High-value order with dispute.",
        "confidence_score": 0.3,
        "requires_human_review": True,
        "reason_for_action": "Dispute amount exceeds automated threshold.",
    },
    "refund": {
        "recommended_action": "Refund",
        "resolution_summary": "Eligible for full refund per return policy.",
        "policy_reference": "Return window: 7 days from delivery.",
        "internal_note": "Process refund within 5 business days.",
        "confidence_score": 0.85,
        "requires_human_review": False,
        "reason_for_action": "Within return window, product not delivered.",
    },
}

RESPONSE_TEXT_EXAMPLES = {
    "english_professional": {
        "response_text": "Your order is currently in transit and will be delivered within 2 days.",
        "response_english": "Your order is currently in transit and will be delivered within 2 days.",
        "tone": "Professional",
    },
    "hindi_empathetic": {
        "response_text": "आपका ऑर्डर रास्ते में है और 2 दिन में पहुंच जाएगा।",
        "response_english": "Your order is on its way and will arrive in 2 days.",
        "tone": "Empathetic",
    },
    "escalation_notice": {
        "response_text": "I'm connecting you to a human agent who will assist you shortly.",
        "response_english": "I'm connecting you to a human agent who will assist you shortly.",
        "tone": "Apologetic",
    },
}
