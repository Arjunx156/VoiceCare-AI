"""
CommerceMind VoiceCare AI — Anonymous Customer Cleanup

Deletes junk placeholder User rows created when callers didn't identify
themselves (phone starts with 'anon-' or 'temp-', or name is 'Anonymous Customer').
Their dependent rows are removed first so FK constraints aren't violated.

Usage:
    python -m app.utils.cleanup_anonymous
    python -m app.utils.cleanup_anonymous --dry-run  # preview without deleting
"""

import asyncio
import argparse

from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.db.models import (
    User, VoiceSession, SupportTicket, SupportMessage,
    SupportResolution, CustomerSentiment,
)


async def cleanup(dry_run: bool = False) -> None:
    async with async_session() as db:
        # Find all junk users
        junk = (await db.execute(
            select(User).where(
                or_(
                    User.phone.like("anon-%"),
                    User.phone.like("temp-%"),
                    User.name == "Anonymous Customer",
                    User.customer_segment == "Anonymous",
                )
            )
        )).scalars().all()

        if not junk:
            print("✅ No anonymous/temporary customers found. Nothing to delete.")
            return

        junk_ids = [u.user_id for u in junk]
        print(f"Found {len(junk)} junk customer row(s):")
        for u in junk:
            print(f"  • {u.name!r}  phone={u.phone}  segment={u.customer_segment}")

        if dry_run:
            print("\nDry-run mode — no changes made.")
            return

        # Gather associated tickets
        tickets = (await db.execute(
            select(SupportTicket).where(SupportTicket.user_id.in_(junk_ids))
        )).scalars().all()
        ticket_ids = [t.ticket_id for t in tickets]

        # Delete in FK-safe order
        if ticket_ids:
            await db.execute(delete(CustomerSentiment).where(CustomerSentiment.ticket_id.in_(ticket_ids)))
            await db.execute(delete(SupportResolution).where(SupportResolution.ticket_id.in_(ticket_ids)))
            await db.execute(delete(SupportMessage).where(SupportMessage.ticket_id.in_(ticket_ids)))
            await db.execute(delete(SupportTicket).where(SupportTicket.ticket_id.in_(ticket_ids)))
            print(f"  Deleted {len(ticket_ids)} ticket(s) and their messages/resolutions.")

        await db.execute(delete(VoiceSession).where(VoiceSession.user_id.in_(junk_ids)))
        await db.execute(delete(User).where(User.user_id.in_(junk_ids)))
        await db.commit()

        print(f"\n✅ Deleted {len(junk)} anonymous user(s) and all dependent rows.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete anonymous/temporary customer rows.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without deleting")
    args = parser.parse_args()
    asyncio.run(cleanup(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
