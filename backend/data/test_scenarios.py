"""
CommerceMind VoiceCare AI — QA Test Scenario Catalog
Static, code-defined scenarios for the Test Runs tab. Each one drives the real
pipeline (agents 1-7 only, via VoiceCarePipeline.run_critical) against a seeded
demo user so order/refund/payment lookups have real data to work with.

Expectations are optional: a scenario with none of expected_intent /
expected_escalated / expected_min_confidence set is "observed" only — it never
fails, it just shows what the pipeline actually did with that query.
"""

from dataclasses import dataclass
from typing import Optional

from data.seed.seed_data import SEED_USERS


@dataclass(frozen=True)
class TestScenario:
    __test__ = False  # not a pytest test class — name collides with "Test*"
    id: str
    label: str
    query_text: str
    language: str
    phone: Optional[str] = None
    order_id: Optional[str] = None
    expected_intent: Optional[str] = None
    expected_escalated: Optional[bool] = None
    expected_min_confidence: Optional[float] = None


# Demo phones, indexed the same way as SEED_USERS in seed_data.py:
# 0 Rajesh (Hindi) · 1 Priya (Malayalam) · 2 Muthu (Tamil) · 3 Ananya (Telugu)
# 4 Kavitha (Kannada) · 5 Sourav (Bengali) · 6 Sneha (Marathi) · 7 Amit (Hinglish)
_PHONE = {u["name"].split()[0]: u["phone"] for u in SEED_USERS}

TEST_SCENARIOS: list[TestScenario] = [
    TestScenario(
        id="order-status-hindi",
        label="Order status — Hindi",
        query_text="Mera order kab tak deliver hoga?",
        language="Hindi",
        phone=_PHONE["Rajesh"],
        expected_intent="order_status",
        expected_min_confidence=0.5,
    ),
    TestScenario(
        id="refund-status-malayalam",
        label="Refund status — Malayalam",
        query_text="Ente refund engott aayi?",
        language="Malayalam",
        phone=_PHONE["Priya"],
        expected_intent="refund_status",
    ),
    TestScenario(
        id="damaged-product-tamil",
        label="Damaged product — Tamil",
        query_text="Enaku vantha product damage aagiruku, replace pannunga.",
        language="Tamil",
        phone=_PHONE["Muthu"],
        expected_intent="damaged_product",
        expected_min_confidence=0.5,
    ),
    TestScenario(
        id="payment-issue-telugu",
        label="Payment deducted, order cancelled — Telugu",
        query_text="Naa order cancel ayyindi kani money debit ayyindi.",
        language="Telugu",
        phone=_PHONE["Ananya"],
        expected_intent="payment_issue",
        expected_escalated=True,
    ),
    TestScenario(
        id="cancellation-kannada",
        label="Cancellation request — Kannada",
        query_text="Nanna order cancel maadbeku.",
        language="Kannada",
        phone=_PHONE["Kavitha"],
        expected_intent="cancellation",
    ),
    TestScenario(
        id="delivery-delay-bengali",
        label="Delivery delay — Bengali",
        query_text="Amar order onek deri hocche, ki hoyeche?",
        language="Bengali",
        phone=_PHONE["Sourav"],
        expected_intent="delivery_delay",
    ),
    TestScenario(
        id="return-request-marathi",
        label="Return request — Marathi",
        query_text="Mala ha product parat karaycha aahe.",
        language="Marathi",
        phone=_PHONE["Sneha"],
        expected_intent="return_request",
    ),
    TestScenario(
        id="wrong-product-angry-hinglish",
        label="Wrong product, angry — Hinglish (escalation)",
        query_text="Yeh bilkul galat product bheja hai, third time complain kar raha hoon, bohot bura service hai!",
        language="Hinglish",
        phone=_PHONE["Amit"],
        expected_intent="wrong_product",
        expected_escalated=True,
    ),
    TestScenario(
        id="general-inquiry-english",
        label="General inquiry — English",
        query_text="What is your return policy for electronics?",
        language="English",
        expected_intent="general_inquiry",
    ),
    TestScenario(
        id="exchange-english",
        label="Exchange request — English",
        query_text="I'd like to exchange this for a different size, is that possible?",
        language="English",
        phone=_PHONE["Rajesh"],
        expected_intent="exchange",
    ),
]
