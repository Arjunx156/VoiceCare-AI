"""
VoiceCare AI — Demo Ticket Curation Script

Covers app/utils/curate_demo_tickets.py: the operator CLI that soft-deletes a
named set of non-representative demo tickets. The script writes to the database
and is run by hand before a demo, so the properties that matter are that a dry
run changes nothing, an apply only ever sets deleted_at (never destroys), it is
idempotent, and --restore is a true inverse.
"""

import sys
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select

import app.utils.curate_demo_tickets as curate_module
from app.db.models import SupportTicket, User

# One ticket from each reason group, plus one the script must never touch.
LISTED = {
    "TKT-B29FQ": "load-test artifact",
    "TKT-GDUTG": "API quota exhausted / LLM failure",
    "TKT-QVBD2": "off-topic or nonsensical",
    "TKT-NA877": "presentation defect",
}
UNLISTED = "TKT-KEEP1"


async def _fetch(sessionmaker_, ticket_number):
    async with sessionmaker_() as s:
        return (await s.execute(
            select(SupportTicket).where(SupportTicket.ticket_number == ticket_number)
        )).scalars().first()


@pytest_asyncio.fixture
async def demo_tickets(sessionmaker_):
    """Commit one ticket per removal reason plus an unlisted control, then clean up.

    The suite shares a single in-memory database, so these rows are deleted on
    teardown — a soft-deleted ticket left behind would skew any later test that
    counts tickets.
    """
    numbers = list(LISTED) + [UNLISTED]
    async with sessionmaker_() as s:
        user = User(
            name="Demo Curation",
            phone="9" + uuid.uuid4().hex[:9],
            preferred_language="English",
        )
        s.add(user)
        await s.flush()
        for number in numbers:
            s.add(SupportTicket(
                ticket_number=number,
                user_id=user.user_id,
                ticket_type="General",
                priority="Medium",
                status="Open",
                language="English",
            ))
        await s.commit()
        user_id = user.user_id

    with patch.object(curate_module, "async_session", sessionmaker_):
        yield numbers

    async with sessionmaker_() as s:
        for number in numbers:
            row = (await s.execute(
                select(SupportTicket).where(SupportTicket.ticket_number == number)
            )).scalars().first()
            if row:
                await s.delete(row)
        await s.delete(await s.get(User, user_id))
        await s.commit()


# ---------------------------------------------------------------------------
# _reason_for — pure lookup, no database
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ticket_number,expected", list(LISTED.items()))
def test_reason_for_maps_each_ticket_to_its_removal_group(ticket_number, expected):
    """Every listed ticket reports the reason group it was filed under."""
    assert curate_module._reason_for(ticket_number) == expected


def test_reason_for_returns_unspecified_for_unlisted_ticket():
    """A ticket outside every group falls back to 'unspecified' rather than raising."""
    assert curate_module._reason_for(UNLISTED) == "unspecified"


def test_every_listed_ticket_appears_in_exactly_one_group():
    """TO_HIDE is the union of the reason groups with no ticket double-listed."""
    counted = sum(len(group) for _, group in curate_module.REASONS)
    assert counted == len(curate_module.TO_HIDE)


# ---------------------------------------------------------------------------
# curate() — dry run
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_dry_run_leaves_every_ticket_visible(demo_tickets, sessionmaker_, capsys):
    """A dry run reports what it would hide and writes nothing to the database."""
    await curate_module.curate(dry_run=True)

    assert "Dry run" in capsys.readouterr().out
    for number in demo_tickets:
        assert (await _fetch(sessionmaker_, number)).deleted_at is None


@pytest.mark.asyncio
async def test_dry_run_warns_about_tickets_absent_from_this_database(demo_tickets, capsys):
    """Listed tickets missing from the database are named, not silently skipped."""
    await curate_module.curate(dry_run=True)

    out = capsys.readouterr().out
    missing = len(curate_module.TO_HIDE) - len(LISTED)
    assert f"{missing} listed ticket(s) not in this database" in out


# ---------------------------------------------------------------------------
# curate() — apply
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_apply_soft_deletes_only_the_listed_tickets(demo_tickets, sessionmaker_):
    """Applying sets deleted_at on every listed ticket and leaves unlisted ones alone."""
    await curate_module.curate()

    for number in LISTED:
        row = await _fetch(sessionmaker_, number)
        assert row.deleted_at is not None
        assert row.updated_by == "curate_demo_tickets"

    assert (await _fetch(sessionmaker_, UNLISTED)).deleted_at is None


@pytest.mark.asyncio
async def test_apply_never_deletes_a_row(demo_tickets, sessionmaker_):
    """Curation is soft-delete only — every hidden ticket is still retrievable."""
    await curate_module.curate()

    for number in demo_tickets:
        assert await _fetch(sessionmaker_, number) is not None


@pytest.mark.asyncio
async def test_apply_prints_the_remaining_escalation_ratio(demo_tickets, capsys):
    """The apply summary reports how many tickets remain active and the escalated share."""
    await curate_module.curate()

    out = capsys.readouterr().out
    assert f"Hid {len(LISTED)} ticket(s)." in out
    assert "Active tickets now" in out
    assert "Escalated" in out


@pytest.mark.asyncio
async def test_second_apply_is_a_no_op(demo_tickets, sessionmaker_, capsys):
    """Re-running after a successful apply changes nothing — the script is idempotent."""
    await curate_module.curate()
    hidden_at = {n: (await _fetch(sessionmaker_, n)).deleted_at for n in LISTED}
    capsys.readouterr()

    await curate_module.curate()

    assert "Nothing to do." in capsys.readouterr().out
    for number, first_timestamp in hidden_at.items():
        assert (await _fetch(sessionmaker_, number)).deleted_at == first_timestamp


# ---------------------------------------------------------------------------
# curate() — restore
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_restore_undoes_an_apply(demo_tickets, sessionmaker_):
    """--restore clears deleted_at on the listed tickets, returning them to the dashboard."""
    await curate_module.curate()
    await curate_module.curate(restore=True)

    for number in demo_tickets:
        assert (await _fetch(sessionmaker_, number)).deleted_at is None


@pytest.mark.asyncio
async def test_restore_dry_run_leaves_tickets_hidden(demo_tickets, sessionmaker_, capsys):
    """--restore --dry-run reports the restore it would perform without writing."""
    await curate_module.curate()
    capsys.readouterr()

    await curate_module.curate(dry_run=True, restore=True)

    assert "Dry run" in capsys.readouterr().out
    for number in LISTED:
        assert (await _fetch(sessionmaker_, number)).deleted_at is not None


# ---------------------------------------------------------------------------
# main() — argument parsing
# ---------------------------------------------------------------------------
# Sync tests on purpose: main() calls asyncio.run, which raises if a loop is
# already running.
@pytest.mark.parametrize("argv,expected", [
    ([], {"dry_run": False, "restore": False}),
    (["--dry-run"], {"dry_run": True, "restore": False}),
    (["--restore"], {"dry_run": False, "restore": True}),
    (["--dry-run", "--restore"], {"dry_run": True, "restore": True}),
])
def test_main_forwards_its_flags_to_curate(argv, expected):
    """Each CLI flag combination reaches curate() as the matching keyword argument."""
    with patch.object(curate_module, "curate", new=AsyncMock()) as mock_curate, \
         patch.object(sys, "argv", ["curate_demo_tickets", *argv]):
        curate_module.main()

    mock_curate.assert_awaited_once_with(**expected)
