"""add short customer code

Adds a human-readable, customer-facing code (CUST-xxxx) to users alongside the
internal UUID primary key, and backfills every existing row.

Revision ID: 20260630_0003
Revises: 20260630_0002
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

from app.utils.short_ids import generate_customer_code

revision = "20260630_0003"
down_revision = "20260630_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("customer_code", sa.String(16), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(sa.text("SELECT user_id FROM users WHERE customer_code IS NULL")).fetchall()
    used: set[str] = set()
    for (pk,) in rows:
        code = generate_customer_code(lambda c: c in used)
        used.add(code)
        bind.execute(
            sa.text("UPDATE users SET customer_code = :code WHERE user_id = :pk"),
            {"code": code, "pk": pk},
        )

    op.create_unique_constraint("uq_users_customer_code", "users", ["customer_code"])


def downgrade() -> None:
    op.drop_constraint("uq_users_customer_code", "users", type_="unique")
    op.drop_column("users", "customer_code")
