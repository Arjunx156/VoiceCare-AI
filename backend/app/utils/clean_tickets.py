"""
VoiceCare AI — Ticket Cleanup Utility
Soft-deletes excess tickets from the DB, keeping a curated representative set.

Strategy:
  • Keep 2 tickets per priority tier (Critical / High / Medium / Low).
  • Among those kept, prefer Escalated and Open statuses so the dashboard
    has useful data to show.
  • Soft-delete everything else (sets deleted_at — reversible).

Run:
  cd backend
  python -m app.utils.clean_tickets
"""

import asyncio
from datetime import datetime
from collections import defaultdict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session


KEEP_PER_PRIORITY = 2

# Statuses ordered by how interesting they are for the dashboard
STATUS_PRIORITY = ["Escalated", "Open", "In Progress", "Resolved", "Closed"]


async def clean_tickets() -> None:
    from app.db.models import SupportTicket

    async with async_session() as db:
        result = await db.execute(
            select(SupportTicket)
            .where(SupportTicket.deleted_at.is_(None))
            .order_by(SupportTicket.priority, SupportTicket.created_at.asc())
        )
        all_tickets = result.scalars().all()

        print(f"Total active tickets: {len(all_tickets)}")

        # Group by priority
        by_priority: dict[str, list] = defaultdict(list)
        for t in all_tickets:
            by_priority[t.priority].append(t)

        keep_ids: set = set()

        for priority, tickets in by_priority.items():
            # Sort so more interesting statuses come first
            tickets.sort(key=lambda t: (
                STATUS_PRIORITY.index(t.status) if t.status in STATUS_PRIORITY else 99,
                t.created_at,
            ))
            kept = tickets[:KEEP_PER_PRIORITY]
            for t in kept:
                keep_ids.add(t.ticket_id)
            print(f"  {priority}: keeping {len(kept)} of {len(tickets)}")

        # Soft-delete everything not in keep_ids
        to_delete = [t for t in all_tickets if t.ticket_id not in keep_ids]
        if not to_delete:
            print("Nothing to delete.")
            return

        now = datetime.utcnow()
        for t in to_delete:
            t.deleted_at = now
        await db.commit()

        print(f"Soft-deleted {len(to_delete)} tickets. {len(keep_ids)} tickets remain active.")
        print("\nKept tickets:")
        for t in all_tickets:
            if t.ticket_id in keep_ids:
                print(f"  [{t.priority}] {t.status} — {t.ticket_type} — {t.ticket_id}")


if __name__ == "__main__":
    asyncio.run(clean_tickets())
