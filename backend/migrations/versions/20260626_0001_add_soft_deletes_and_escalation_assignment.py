"""add soft deletes and escalation assignment

Revision ID: 20260626_0001
Revises: 001
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "20260626_0001"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Soft-delete columns
    op.add_column("users",           sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("orders",          sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("support_tickets", sa.Column("deleted_at", sa.DateTime(), nullable=True))

    # Escalation assignment — which agent claimed this ticket
    op.add_column("support_tickets", sa.Column("assigned_to", sa.String(255), nullable=True))

    # Indexes on support_messages for fast per-ticket conversation queries
    op.create_index("idx_messages_ticket_id", "support_messages", ["ticket_id"])
    op.create_index("idx_messages_timestamp",  "support_messages", ["timestamp"])


def downgrade() -> None:
    op.drop_index("idx_messages_timestamp",  table_name="support_messages")
    op.drop_index("idx_messages_ticket_id",  table_name="support_messages")
    op.drop_column("support_tickets", "assigned_to")
    op.drop_column("support_tickets", "deleted_at")
    op.drop_column("orders",          "deleted_at")
    op.drop_column("users",           "deleted_at")
