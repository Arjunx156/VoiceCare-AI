"""
Mock fixtures for ChromaDB vector store responses.
"""

POLICY_CONTEXTS = {
    "shipping": (
        "Standard Shipping Policy: Orders are delivered within 5-7 business days. "
        "Express shipping (1-2 days) is available for an additional fee."
    ),
    "return": (
        "Return Policy: Items can be returned within 7 days of delivery. "
        "The item must be unused and in original packaging."
    ),
    "refund": (
        "Refund Policy: Approved refunds are processed within 5-7 business days. "
        "Refunds are credited to the original payment method."
    ),
    "empty": "No policy documents available.",
}

POLICY_QUERY_RESULTS = {
    "order_status": [
        {
            "id": "policy_ship_1",
            "content": POLICY_CONTEXTS["shipping"],
            "category": "Shipping",
            "score": 0.92,
        }
    ],
    "refund": [
        {
            "id": "policy_refund_1",
            "content": POLICY_CONTEXTS["refund"],
            "category": "Refund",
            "score": 0.95,
        },
        {
            "id": "policy_return_1",
            "content": POLICY_CONTEXTS["return"],
            "category": "Return",
            "score": 0.87,
        },
    ],
    "empty": [],
}
