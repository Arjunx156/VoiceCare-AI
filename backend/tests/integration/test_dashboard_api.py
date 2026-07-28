"""The support-agent dashboard API, against a real database.

These are the read paths a human agent actually uses to triage: the queue, the
escalation list, the analytics header, one ticket's full detail, and the
claim/release handover. They run the real routers over committing SQLite
sessions rather than mocks, so a broken query or a schema drift shows up here.
"""

import uuid

import pytest

from app.db.models import SupportResolution, SupportTicket, User


@pytest.fixture
def unique_phone():
    return "9" + uuid.uuid4().hex[:9]


async def _seed_ticket(sessionmaker_, *, phone, **overrides):
    """Commit one user + ticket and return their ids."""
    async with sessionmaker_() as session:
        user = User(name=overrides.pop("name", "Asha Rao"), phone=phone, preferred_language="Hindi")
        session.add(user)
        await session.flush()
        ticket = SupportTicket(
            user_id=user.user_id,
            ticket_type=overrides.pop("ticket_type", "Complaint"),
            priority=overrides.pop("priority", "High"),
            status=overrides.pop("status", "Open"),
            language="Hindi",
            summary=overrides.pop("summary", "Damaged product on arrival"),
            **overrides,
        )
        session.add(ticket)
        await session.commit()
        return {"user_id": str(user.user_id), "ticket_id": str(ticket.ticket_id)}


class TestTicketQueue:

    @pytest.mark.asyncio
    async def test_queue_returns_the_seeded_ticket(self, authed_client, seeded_ticket):
        """The list endpoint returns tickets with their summary fields."""
        response = await authed_client.get("/api/tickets/")

        assert response.status_code == 200
        ids = [t["ticket_id"] for t in response.json()]
        assert seeded_ticket["ticket_id"] in ids

    @pytest.mark.asyncio
    async def test_queue_filters_by_status(self, authed_client, sessionmaker_, unique_phone):
        """A status filter excludes tickets in other states."""
        resolved = await _seed_ticket(
            sessionmaker_, phone=unique_phone, status="Resolved", summary="Already handled"
        )

        response = await authed_client.get("/api/tickets/?status=Resolved")

        assert response.status_code == 200
        returned = response.json()
        assert resolved["ticket_id"] in [t["ticket_id"] for t in returned]
        assert all(t["status"] == "Resolved" for t in returned)

    @pytest.mark.asyncio
    async def test_queue_filters_by_priority(self, authed_client, sessionmaker_, unique_phone):
        """Priority filtering lets an agent work the critical queue first."""
        critical = await _seed_ticket(
            sessionmaker_, phone=unique_phone, priority="Critical", summary="Payment taken twice"
        )

        response = await authed_client.get("/api/tickets/?priority=Critical")

        assert response.status_code == 200
        returned = response.json()
        assert critical["ticket_id"] in [t["ticket_id"] for t in returned]
        assert all(t["priority"] == "Critical" for t in returned)

    @pytest.mark.asyncio
    async def test_queue_respects_the_limit(self, authed_client, sessionmaker_):
        """An unbounded queue would be a denial-of-service on the dashboard."""
        for _ in range(3):
            await _seed_ticket(sessionmaker_, phone="9" + uuid.uuid4().hex[:9])

        response = await authed_client.get("/api/tickets/?limit=2")

        assert response.status_code == 200
        assert len(response.json()) <= 2


class TestEscalationQueue:

    @pytest.mark.asyncio
    async def test_escalations_lists_only_escalated_tickets(
        self, authed_client, seeded_ticket, sessionmaker_, unique_phone
    ):
        """The escalation queue is the human-attention list — nothing else."""
        await _seed_ticket(sessionmaker_, phone=unique_phone, status="Open", summary="Routine")

        response = await authed_client.get("/api/tickets/escalations")

        assert response.status_code == 200
        returned = response.json()
        assert seeded_ticket["ticket_id"] in [t["ticket_id"] for t in returned]
        assert all(t["status"] == "Escalated" for t in returned)


class TestAnalytics:

    @pytest.mark.asyncio
    async def test_analytics_returns_the_dashboard_header_figures(
        self, authed_client, seeded_ticket
    ):
        """Every KPI the overview renders is present and numeric."""
        response = await authed_client.get("/api/tickets/analytics")

        assert response.status_code == 200
        body = response.json()
        for key in (
            "total_tickets",
            "open_tickets",
            "escalated_tickets",
            "resolved_tickets",
            "resolution_rate",
            "escalation_rate",
            "tickets_by_language",
            "tickets_by_priority",
            "tickets_over_time",
        ):
            assert key in body, f"missing analytics field: {key}"
        assert body["total_tickets"] >= 1

    @pytest.mark.asyncio
    async def test_analytics_survives_an_empty_database(self, authed_client):
        """Zero tickets must not divide by zero in the resolution rate."""
        response = await authed_client.get("/api/tickets/analytics")

        assert response.status_code == 200
        assert isinstance(response.json()["resolution_rate"], (int, float))


class TestTicketDetail:

    @pytest.mark.asyncio
    async def test_detail_includes_the_customer_and_agent_trace(
        self, authed_client, sessionmaker_, unique_phone
    ):
        """Detail carries the trace the replay tab renders."""
        seeded = await _seed_ticket(sessionmaker_, phone=unique_phone)
        async with sessionmaker_() as session:
            session.add(
                SupportResolution(
                    ticket_id=uuid.UUID(seeded["ticket_id"]),
                    recommended_action="Refund",
                    final_response_text="We have issued your refund.",
                    confidence_score=0.91,
                    agent_trace='[{"agent_name": "Voice Intake", "stage_number": 1}]',
                )
            )
            await session.commit()

        response = await authed_client.get(f"/api/tickets/{seeded['ticket_id']}")

        assert response.status_code == 200
        body = response.json()
        assert body["ticket_id"] == seeded["ticket_id"]
        assert body["user_name"] == "Asha Rao"
        assert isinstance(body["agent_trace"], list)
        assert body["agent_trace"][0]["agent_name"] == "Voice Intake"

    @pytest.mark.asyncio
    async def test_detail_rejects_a_malformed_id(self, authed_client):
        """A non-UUID path segment is a client error, never a 500."""
        response = await authed_client.get("/api/tickets/not-a-uuid")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_detail_404s_for_an_unknown_ticket(self, authed_client):
        """A well-formed id that does not exist is a clean 404."""
        response = await authed_client.get(f"/api/tickets/{uuid.uuid4()}")

        assert response.status_code == 404


class TestClaimAndRelease:

    @pytest.mark.asyncio
    async def test_claiming_assigns_the_ticket_to_the_agent(
        self, authed_client, seeded_ticket
    ):
        """Claiming records who owns the ticket, so two agents don't collide."""
        from tests.conftest import ADMIN_EMAIL

        response = await authed_client.patch(
            f"/api/tickets/{seeded_ticket['ticket_id']}/claim"
        )

        assert response.status_code == 200
        detail = await authed_client.get(f"/api/tickets/{seeded_ticket['ticket_id']}")
        assert detail.json()["assigned_to"] == ADMIN_EMAIL

    @pytest.mark.asyncio
    async def test_releasing_clears_the_assignment(self, authed_client, seeded_ticket):
        """Releasing returns the ticket to the shared queue."""
        ticket_id = seeded_ticket["ticket_id"]
        await authed_client.patch(f"/api/tickets/{ticket_id}/claim")

        response = await authed_client.patch(f"/api/tickets/{ticket_id}/release")

        assert response.status_code == 200
        detail = await authed_client.get(f"/api/tickets/{ticket_id}")
        assert not detail.json()["assigned_to"]

    @pytest.mark.asyncio
    async def test_claiming_an_unknown_ticket_404s(self, authed_client):
        """No silent success on a ticket that isn't there."""
        response = await authed_client.patch(f"/api/tickets/{uuid.uuid4()}/claim")

        assert response.status_code == 404


class TestHandoffNote:

    @pytest.mark.asyncio
    async def test_handoff_summarises_the_ticket_for_a_human(
        self, authed_client, seeded_ticket
    ):
        """The handoff note is what an agent reads before picking up the call."""
        response = await authed_client.get(
            f"/api/tickets/{seeded_ticket['ticket_id']}/handoff"
        )

        assert response.status_code == 200
        body = response.json()
        assert body["customer_name"] == "Asha Rao"
        assert body["issue_summary"]
        assert body["recommended_next_steps"]

    @pytest.mark.asyncio
    async def test_handoff_404s_for_an_unknown_ticket(self, authed_client):
        """Same clean 404 as the detail route."""
        response = await authed_client.get(f"/api/tickets/{uuid.uuid4()}/handoff")

        assert response.status_code == 404


class TestCustomerProfile:
    """The profile an agent opens mid-call: orders, tickets, sentiment history."""

    @pytest.mark.asyncio
    async def test_profile_resolves_by_internal_uuid(
        self, authed_client, sessionmaker_, unique_phone
    ):
        """Bookmarked links use the UUID and must keep working."""
        seeded = await _seed_ticket(sessionmaker_, phone=unique_phone)

        response = await authed_client.get(f"/api/customers/{seeded['user_id']}")

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Asha Rao"
        assert body["phone"] == unique_phone

    @pytest.mark.asyncio
    async def test_profile_resolves_by_short_customer_code(
        self, authed_client, sessionmaker_, unique_phone
    ):
        """Agents read the short CUST- code aloud; it has to resolve."""
        from sqlalchemy import select

        seeded = await _seed_ticket(sessionmaker_, phone=unique_phone)
        async with sessionmaker_() as session:
            user = (
                await session.execute(
                    select(User).where(User.user_id == uuid.UUID(seeded["user_id"]))
                )
            ).scalar_one()
            user.customer_code = "CUST-" + uuid.uuid4().hex[:4].upper()
            code = user.customer_code
            await session.commit()

        response = await authed_client.get(f"/api/customers/{code}")

        assert response.status_code == 200
        assert response.json()["name"] == "Asha Rao"

    @pytest.mark.asyncio
    async def test_the_code_lookup_is_case_insensitive(
        self, authed_client, sessionmaker_, unique_phone
    ):
        """A code typed in lower case still finds the customer."""
        from sqlalchemy import select

        seeded = await _seed_ticket(sessionmaker_, phone=unique_phone)
        async with sessionmaker_() as session:
            user = (
                await session.execute(
                    select(User).where(User.user_id == uuid.UUID(seeded["user_id"]))
                )
            ).scalar_one()
            user.customer_code = "CUST-" + uuid.uuid4().hex[:4].upper()
            code = user.customer_code
            await session.commit()

        response = await authed_client.get(f"/api/customers/{code.lower()}")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_profile_includes_the_ticket_history(
        self, authed_client, sessionmaker_, unique_phone
    ):
        """The agent needs to see prior contacts, not just this one."""
        seeded = await _seed_ticket(sessionmaker_, phone=unique_phone)

        response = await authed_client.get(f"/api/customers/{seeded['user_id']}")

        assert response.status_code == 200
        tickets = response.json()["tickets"]
        assert seeded["ticket_id"] in [t["ticket_id"] for t in tickets]

    @pytest.mark.asyncio
    async def test_a_malformed_id_is_a_client_error(self, authed_client):
        """Neither a UUID nor a CUST- code — reject cleanly, never 500."""
        response = await authed_client.get("/api/customers/not-an-id")

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_an_unknown_customer_404s(self, authed_client):
        """A well-formed id for someone who does not exist."""
        response = await authed_client.get(f"/api/customers/{uuid.uuid4()}")

        assert response.status_code == 404
