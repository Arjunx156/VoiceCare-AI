"""Drop test_runs and test_case_results tables

The dashboard's "Test Runs" tab has been removed, along with its API router,
service and ORM models — these two tables now back nothing.

Revision 20260731_0005 (which created them) is deliberately left in place:
deployed databases are already stamped at it, and deleting the file would
leave `alembic upgrade head` — which runs on every container boot per the
Dockerfile CMD — unable to locate the current revision.

Revision ID: 20260804_0006
Revises: 20260731_0005
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260804_0006"
down_revision = "20260731_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Child first — test_case_results.run_id has an FK into test_runs.
    op.drop_index("idx_test_case_results_run_id", table_name="test_case_results")
    op.drop_table("test_case_results")
    op.drop_table("test_runs")


def downgrade() -> None:
    # Mirrors 20260731_0005's upgrade().
    op.create_table(
        "test_runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("total_scenarios", sa.Integer, nullable=False),
        sa.Column("completed_scenarios", sa.Integer, nullable=False, server_default="0"),
        sa.Column("live_call_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("mock_fallback_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(255), nullable=False),
    )

    op.create_table(
        "test_case_results",
        sa.Column("result_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("test_runs.run_id"), nullable=False),
        sa.Column("scenario_id", sa.String(100), nullable=False),
        sa.Column("scenario_label", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("used_live_api", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("intent", sa.String(50), nullable=True),
        sa.Column("sentiment", sa.String(20), nullable=True),
        sa.Column("priority", sa.String(20), nullable=True),
        sa.Column("is_escalated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_test_case_results_run_id", "test_case_results", ["run_id"])
