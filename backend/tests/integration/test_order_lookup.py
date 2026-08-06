"""
Integration tests for agent 3's order resolution.

Customers speak the short order code ("ORD-7K3F") — it is the only form they
are ever shown. These tests pin the two ways that used to fail silently: the
code being parsed as a UUID and discarded, and the whole lookup being skipped
when no phone number accompanied it.
"""

from datetime import datetime

import pytest

from app.agents.pipeline import VoiceCarePipeline
from app.agents.state import PipelineState
from app.db.models import Order, Payment, Shipment, User

PHONE = "9812345670"
CUSTOMER_NAME = "Meera Iyer"
ORDER_NUMBER = "ORD-7K3F"


@pytest.fixture
async def seeded_order(db_session):
    user = User(
        name=CUSTOMER_NAME,
        phone=PHONE,
        preferred_language="Tamil",
        customer_segment="Premium",
        created_by="test",
    )
    db_session.add(user)
    await db_session.flush()

    order = Order(
        user_id=user.user_id,
        order_number=ORDER_NUMBER,
        order_date=datetime(2026, 7, 2),
        status="Shipped",
        total_amount=3499.0,
        created_by="test",
    )
    db_session.add(order)
    await db_session.flush()

    db_session.add(Shipment(
        order_id=order.order_id,
        shipment_status="In Transit",
        courier_partner="BlueDart",
        tracking_number="BD123456789",
        expected_delivery_date=datetime(2026, 7, 9),
    ))
    db_session.add(Payment(
        order_id=order.order_id,
        amount=3499.0,
        status="Success",
        payment_method="UPI",
        transaction_date=datetime(2026, 7, 2),
    ))
    await db_session.flush()
    return user, order


class TestSpokenOrderNumber:

    @pytest.mark.asyncio
    async def test_order_number_alone_resolves_the_account(self, db_session, seeded_order):
        """A spoken order number with no phone finds the order and its owner."""
        state = PipelineState(extracted_order_id=ORDER_NUMBER)

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.lookup_successful is True
        assert result.order_data["order_number"] == ORDER_NUMBER
        assert result.user_data["name"] == CUSTOMER_NAME
        assert result.identity_verified is True
        assert result.order_not_found is False

    @pytest.mark.asyncio
    async def test_order_number_lookup_loads_shipment_and_payments(
        self, db_session, seeded_order
    ):
        """The order's shipment and payment rows load alongside it, for agent 5."""
        state = PipelineState(extracted_order_id=ORDER_NUMBER)

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.shipment_data["tracking_number"] == "BD123456789"
        assert result.payment_data["payments"][0]["status"] == "Success"

    @pytest.mark.parametrize(
        "spoken",
        ["ord-7k3f", "ORD 7K3F", "ORD 7K 3F", "7K3F", "ord.7k3f"],
        ids=["lowercase", "spaced", "spaced-body", "no-prefix", "dotted"],
    )
    @pytest.mark.asyncio
    async def test_transcription_variants_match_the_same_order(
        self, db_session, seeded_order, spoken
    ):
        """Speech-recognition spacing, casing and a dropped prefix all still match."""
        state = PipelineState(extracted_order_id=spoken)

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.order_data is not None, f"{spoken!r} failed to match"
        assert result.order_data["order_number"] == ORDER_NUMBER

    @pytest.mark.asyncio
    async def test_order_uuid_still_resolves(self, db_session, seeded_order):
        """The internal UUID keeps working — the REST order_id field sends it."""
        _, order = seeded_order
        state = PipelineState(input_order_id=str(order.order_id))

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.order_data["order_number"] == ORDER_NUMBER


class TestUnmatchedOrderNumber:

    @pytest.mark.asyncio
    async def test_unknown_order_number_is_reported_not_swallowed(
        self, db_session, seeded_order
    ):
        """An order number that matches nothing sets order_not_found."""
        state = PipelineState(extracted_order_id="ORD-ZZZZ")

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.order_not_found is True
        assert result.order_data is None
        assert result.user_data is None

    @pytest.mark.asyncio
    async def test_fragment_too_short_to_match_is_ignored(self, db_session, seeded_order):
        """A 3-character transcription fragment must not match anyone's order."""
        state = PipelineState(extracted_order_id="7K3")

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.order_data is None
        assert result.order_not_found is True

    @pytest.mark.asyncio
    async def test_no_identifier_at_all_is_not_an_order_error(self, db_session):
        """Saying nothing identifying is not the same as naming a bad order."""
        state = PipelineState(raw_text="What is your return policy?")

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.order_not_found is False
        assert result.order_data is None


class TestOrderNumberOwnership:

    @pytest.mark.asyncio
    async def test_order_belonging_to_another_account_is_not_attached(
        self, db_session, seeded_order
    ):
        """A phone that matches one account cannot pull in another's order."""
        stranger = User(
            name="Other Person",
            phone="9812345671",
            preferred_language="Hindi",
            customer_segment="Regular",
            created_by="test",
        )
        db_session.add(stranger)
        await db_session.flush()

        state = PipelineState(phone="9812345671", extracted_order_id=ORDER_NUMBER)

        result = await VoiceCarePipeline(db=db_session).agent_order_lookup(state)

        assert result.order_data is None
        assert result.order_not_found is True
        assert result.identity_needs_confirmation is True
        assert result.user_data["name"] == "Other Person"
