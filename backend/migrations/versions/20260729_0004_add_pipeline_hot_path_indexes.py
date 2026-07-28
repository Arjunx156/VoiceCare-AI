"""Add indexes for the two unindexed pipeline hot-path lookups.

`support_tickets.session_id` is queried on EVERY conversation turn by pipeline
agent 9 (get-or-create the ticket for this conversation) and had no index, so it
degraded to a sequential scan that grows with ticket volume.

`refunds.return_id` is a nullable FK queried by agent 3 on refund-intent turns
and likewise had no index.

Revision ID: 20260729_0004
Revises: 20260630_0003
"""
from alembic import op

revision = "20260729_0004"
down_revision = "20260630_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Raw CREATE INDEX IF NOT EXISTS rather than op.create_index: these indexes
    # are also declared in models.py __table_args__, so any database built via
    # Base.metadata.create_all (dev boxes, tests) already has them. The Dockerfile
    # soft-fails `alembic upgrade head` on boot, so a hard failure here would be
    # silently swallowed and leave the chain unstamped.
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tickets_session_id "
        "ON support_tickets (session_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_refunds_return_id "
        "ON refunds (return_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_refunds_return_id")
    op.execute("DROP INDEX IF EXISTS idx_tickets_session_id")
