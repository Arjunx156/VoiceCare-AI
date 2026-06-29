"""add short order and ticket numbers

Adds human-readable, customer-facing codes (ORD-xxxx / TKT-xxxxx) alongside the
internal UUID primary keys, and backfills every existing row.

Revision ID: 20260630_0002
Revises: 20260626_0001
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

from app.utils.short_ids import generate_order_number, generate_ticket_number

revision = "20260630_0002"
down_revision = "20260626_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("order_number", sa.String(16), nullable=True))
    op.add_column("support_tickets", sa.Column("ticket_number", sa.String(16), nullable=True))

    bind = op.get_bind()
    _backfill(bind, "orders", "order_id", "order_number", generate_order_number)
    _backfill(bind, "support_tickets", "ticket_id", "ticket_number", generate_ticket_number)

    op.create_unique_constraint("uq_orders_order_number", "orders", ["order_number"])
    op.create_unique_constraint("uq_support_tickets_ticket_number", "support_tickets", ["ticket_number"])


def _backfill(bind, table, pk_col, code_col, gen):
    """Assign a unique short code to every existing row."""
    rows = bind.execute(sa.text(f"SELECT {pk_col} FROM {table} WHERE {code_col} IS NULL")).fetchall()
    used: set[str] = set()
    for (pk,) in rows:
        code = gen(lambda c: c in used)
        used.add(code)
        bind.execute(
            sa.text(f"UPDATE {table} SET {code_col} = :code WHERE {pk_col} = :pk"),
            {"code": code, "pk": pk},
        )


def downgrade() -> None:
    op.drop_constraint("uq_support_tickets_ticket_number", "support_tickets", type_="unique")
    op.drop_constraint("uq_orders_order_number", "orders", type_="unique")
    op.drop_column("support_tickets", "ticket_number")
    op.drop_column("orders", "order_number")
