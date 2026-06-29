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

ADMIN_EMAIL = "agent@test.com"


@pytest_asyncio.fixture
async def sessionmaker_(engine):
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def authed_client(sessionmaker_):
    """ASGI client with committing DB sessions and admin auth stubbed."""
    from main import app

    async def override_get_db():
        async with sessionmaker_() as s:
            yield s

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = lambda: ADMIN_EMAIL

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(require_admin, None)


@pytest_asyncio.fixture
async def seeded_ticket(sessionmaker_):
    """A user + one escalated ticket committed to the shared test DB."""
    phone = "9" + uuid.uuid4().hex[:9]
    async with sessionmaker_() as s:
        user = User(name="Asha Rao", phone=phone, preferred_language="Hindi")
        s.add(user)
        await s.flush()
        ticket = SupportTicket(
            user_id=user.user_id,
            ticket_type="Complaint",
            priority="High",
            status="Escalated",
            language="Hindi",
            summary="Damaged product on arrival",
        )
        s.add(ticket)
        await s.commit()
        return {"user_id": str(user.user_id), "ticket_id": str(ticket.ticket_id), "phone": phone}


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
