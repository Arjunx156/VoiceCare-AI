"""
Unit tests for the new dashboard action endpoints:
  - POST  /api/tickets/{id}/reply
  - PATCH /api/tickets/{id}/resolve
  - PATCH /api/tickets/{id}/reassign
  - GET   /api/customers/  and  /api/customers/{id}

These exercise the real routers against the in-memory SQLite DB. Because the
endpoints commit, we override get_db with independent committing sessions
(rather than the shared rollback-per-test session) and isolate tests by giving
each seeded customer a unique phone number.
"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import User, SupportTicket
from app.api.auth import require_admin
from app.core.database import get_db

# sessionmaker_, authed_client and seeded_ticket now live in tests/conftest.py
# so the dashboard-API integration tests can share them.
from tests.conftest import ADMIN_EMAIL


@pytest.mark.asyncio
async def test_reply_posts_human_message_and_progresses_status(authed_client, seeded_ticket):
    tid = seeded_ticket["ticket_id"]
    resp = await authed_client.post(f"/api/tickets/{tid}/reply", json={"message_text": "We are refunding you now."})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["sender_type"] == "Human"
    assert body["message_text"] == "We are refunding you now."
    # An agent replying moves an escalated ticket into progress.
    assert body["ticket_status"] == "In Progress"


@pytest.mark.asyncio
async def test_reply_rejects_empty_message(authed_client, seeded_ticket):
    tid = seeded_ticket["ticket_id"]
    resp = await authed_client.post(f"/api/tickets/{tid}/reply", json={"message_text": ""})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_resolve_sets_status_then_conflicts(authed_client, seeded_ticket):
    tid = seeded_ticket["ticket_id"]
    resp = await authed_client.patch(f"/api/tickets/{tid}/resolve")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "Resolved"
    again = await authed_client.patch(f"/api/tickets/{tid}/resolve")
    assert again.status_code == 409


@pytest.mark.asyncio
async def test_reassign_updates_assignee(authed_client, seeded_ticket):
    tid = seeded_ticket["ticket_id"]
    resp = await authed_client.patch(f"/api/tickets/{tid}/reassign", json={"assigned_to": "lead@test.com"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["assigned_to"] == "lead@test.com"


@pytest.mark.asyncio
async def test_action_on_missing_ticket_404(authed_client):
    resp = await authed_client.patch(f"/api/tickets/{uuid.uuid4()}/resolve")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_customers_list_and_profile(authed_client, seeded_ticket):
    phone = seeded_ticket["phone"]
    # Search narrows to exactly the seeded customer.
    found = await authed_client.get("/api/customers/", params={"search": phone})
    assert found.status_code == 200, found.text
    rows = found.json()
    assert len(rows) == 1
    assert rows[0]["name"] == "Asha Rao"
    assert rows[0]["ticket_count"] >= 1

    # Profile returns the customer's ticket history.
    prof = await authed_client.get(f"/api/customers/{seeded_ticket['user_id']}")
    assert prof.status_code == 200, prof.text
    data = prof.json()
    assert data["name"] == "Asha Rao"
    assert len(data["tickets"]) >= 1


@pytest.mark.asyncio
async def test_customer_profile_invalid_id_400(authed_client):
    resp = await authed_client.get("/api/customers/not-a-uuid")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/tickets/?search=  (free-text ticket search)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ticket_search_by_customer_phone(authed_client, seeded_ticket):
    # Phone is unique per seeded fixture, so this narrows to exactly one row.
    resp = await authed_client.get("/api/tickets/", params={"search": seeded_ticket["phone"]})
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["ticket_id"] == seeded_ticket["ticket_id"]
    assert rows[0]["user_name"] == "Asha Rao"


@pytest.mark.asyncio
async def test_ticket_search_matches_summary_case_insensitively(authed_client, sessionmaker_):
    token = f"zebra{uuid.uuid4().hex[:8]}"  # unique so the shared DB can't collide
    async with sessionmaker_() as s:
        user = User(name="Sam Iyer", phone="8" + uuid.uuid4().hex[:9], preferred_language="Tamil")
        s.add(user)
        await s.flush()
        s.add(SupportTicket(
            user_id=user.user_id,
            ticket_type="Refund",
            priority="Medium",
            status="Open",
            language="Tamil",
            summary=f"Refund pending for order {token.upper()}",
        ))
        await s.commit()

    resp = await authed_client.get("/api/tickets/", params={"search": token})
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) == 1
    assert token.upper() in rows[0]["summary"]


@pytest.mark.asyncio
async def test_ticket_search_escapes_like_wildcards(authed_client, seeded_ticket):
    # A bare '%' must be treated as a literal, not a match-everything wildcard.
    resp = await authed_client.get("/api/tickets/", params={"search": "%"})
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


@pytest.mark.asyncio
async def test_ticket_search_no_match_returns_empty(authed_client, seeded_ticket):
    resp = await authed_client.get("/api/tickets/", params={"search": "no-such-customer-xyz"})
    assert resp.status_code == 200
    assert resp.json() == []
