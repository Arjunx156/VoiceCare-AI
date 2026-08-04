"""
VoiceCare AI — Demo Ticket Curation

Soft-deletes a specific, named set of tickets that misrepresent the product:
load-test artifacts, responses produced while the Gemini quota was exhausted,
off-topic noise, and one row with a mismatched customer name.

Why an explicit list rather than a rule (cf. clean_tickets.py, which keeps N per
priority): the tickets worth removing are bad for *different* reasons, and a
rule that captured all of them would also catch legitimate ones. Listing them
by ticket number keeps the decision auditable and makes the script idempotent —
re-running it will never touch tickets created after this was written, so it is
safe to run before a demo without eating the tickets the demo itself creates.

Soft-delete only: sets deleted_at, which every dashboard query filters on
(`WHERE deleted_at IS NULL`). Nothing is destroyed, and --restore undoes it.

Run:
    cd backend
    python -m app.utils.curate_demo_tickets --dry-run   # preview
    python -m app.utils.curate_demo_tickets             # apply
    python -m app.utils.curate_demo_tickets --restore   # undo
"""

import argparse
import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import noload

from app.core.database import async_session
from app.db.models import SupportTicket

# ---------------------------------------------------------------------------
# Tickets to hide, grouped by why. Ticket numbers, not UUIDs, so this stays
# readable against what the dashboard actually displays.
# ---------------------------------------------------------------------------

LOAD_TEST_ARTIFACTS = {
    # Cold/warm-start probe runs on 2026-07-28, users anon-probecold/warm/warm2.
    # Never real conversations. TKT-MZC56 and TKT-YEPDT are an exact duplicate
    # pair ("Where is my order?"), which is what made the duplication visible.
    "TKT-B29FQ", "TKT-PQCP8", "TKT-YUCKM", "TKT-MZC56", "TKT-FSTTV",
    "TKT-VU92H", "TKT-YEPDT", "TKT-YJR4B", "TKT-RE2NX",
}

QUOTA_EXHAUSTED = {
    # confidence 0.00 — hard LLM failure. Response is the canned
    # "I'm having trouble generating a response" fallback.
    "TKT-GDUTG", "TKT-DZSQV",
}

OFF_TOPIC = {
    # "a new knee", its follow-up, an order ID of 'one', and a confidence-0.00
    # Malayalam ticket about "an investment in a subscription".
    "TKT-QVBD2", "TKT-CQ8ZM", "TKT-6RH9F", "TKT-TG5Y8",
}

PRESENTATION = {
    # TKT-NA877: filed under Ananya Reddy, summary says "Priya Nair wants to
    #            return a product" — wrong name renders on the ticket row.
    # TKT-45VQJ: an "Anonymous Customer" holding a Critical escalation, which
    #            skews the escalation ratio without adding anything.
    "TKT-NA877", "TKT-45VQJ",
}

REASONS = [
    ("load-test artifact", LOAD_TEST_ARTIFACTS),
    ("API quota exhausted / LLM failure", QUOTA_EXHAUSTED),
    ("off-topic or nonsensical", OFF_TOPIC),
    ("presentation defect", PRESENTATION),
]

TO_HIDE = {n for _, group in REASONS for n in group}


def _reason_for(ticket_number: str) -> str:
    for reason, group in REASONS:
        if ticket_number in group:
            return reason
    return "unspecified"


async def curate(dry_run: bool = False, restore: bool = False) -> None:
    async with async_session() as db:
        targets = (await db.execute(
            select(SupportTicket)
            .options(noload("*"))
            .where(SupportTicket.ticket_number.in_(TO_HIDE))
        )).scalars().all()

        found = {t.ticket_number for t in targets}
        missing = TO_HIDE - found
        if missing:
            print(f"! {len(missing)} listed ticket(s) not in this database: {sorted(missing)}")

        if restore:
            restored = [t for t in targets if t.deleted_at is not None]
            print(f"Restoring {len(restored)} ticket(s)...")
            if not dry_run:
                for t in restored:
                    t.deleted_at = None
                await db.commit()
                print(f"Restored {len(restored)}.")
            else:
                print("Dry run — no changes.")
            return

        pending = [t for t in targets if t.deleted_at is None]
        already = len(targets) - len(pending)

        print(f"Listed for removal : {len(TO_HIDE)}")
        print(f"Found in database  : {len(targets)}")
        print(f"Already hidden     : {already}")
        print(f"To hide now        : {len(pending)}\n")

        for reason, _ in REASONS:
            rows = [t for t in pending if _reason_for(t.ticket_number) == reason]
            if rows:
                print(f"  {reason} ({len(rows)})")
                for t in sorted(rows, key=lambda x: x.ticket_number):
                    print(f"    {t.ticket_number}  {t.status:<12} {t.priority:<9} {t.language}")

        if not pending:
            print("Nothing to do.")
            return

        if dry_run:
            print("\nDry run — no changes made.")
            return

        now = datetime.utcnow()
        for t in pending:
            t.deleted_at = now
            t.updated_by = "curate_demo_tickets"
        await db.commit()

        remaining = (await db.execute(
            select(SupportTicket)
            .options(noload("*"))
            .where(SupportTicket.deleted_at.is_(None))
        )).scalars().all()

        escalated = [t for t in remaining if t.status == "Escalated"]
        pct = round(len(escalated) / len(remaining) * 100) if remaining else 0
        print(f"\nHid {len(pending)} ticket(s).")
        print(f"Active tickets now : {len(remaining)}")
        print(f"Escalated          : {len(escalated)} ({pct}%)")
        print("\nRemaining:")
        for t in sorted(remaining, key=lambda x: x.created_at):
            print(f"  {t.ticket_number}  {t.status:<12} {t.priority:<9} "
                  f"{t.language:<10} {t.ticket_type}")
        print("\nReversible: python -m app.utils.curate_demo_tickets --restore")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hide non-representative demo tickets.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--restore", action="store_true", help="Un-hide the listed tickets")
    args = parser.parse_args()
    asyncio.run(curate(dry_run=args.dry_run, restore=args.restore))


if __name__ == "__main__":
    main()
