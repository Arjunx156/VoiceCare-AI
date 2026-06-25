"""Initial schema with audit fields

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000 UTC

This migration:
- Creates all VoiceCare AI tables
- Adds audit fields (created_by, updated_by, updated_at) to:
    users, orders, returns, refunds, support_tickets,
    support_messages, support_resolutions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


# ============================================================
# Audit columns helper — reused across tables
# ============================================================
def _audit_columns():
    """Return list of standard audit columns."""
    return [
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    ]


def upgrade() -> None:
    # ---- users ----
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False, unique=True),
        sa.Column("email", sa.String(200), nullable=True, unique=True),
        sa.Column("preferred_language", sa.String(20), nullable=False, server_default="English"),
        sa.Column("customer_segment", sa.String(30), nullable=False, server_default="Regular"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("idx_users_phone", "users", ["phone"], unique=True)

    # ---- products ----
    op.create_table(
        "products",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
    )

    # ---- orders ----
    op.create_table(
        "orders",
        sa.Column("order_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("order_date", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Placed"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("shipping_address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("idx_orders_user_id", "orders", ["user_id"])
    op.create_index("idx_orders_status", "orders", ["status"])

    # ---- order_items ----
    op.create_table(
        "order_items",
        sa.Column("order_item_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.order_id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False, server_default="1"),
        sa.Column("price_at_purchase", sa.Numeric(10, 2), nullable=False),
    )

    # ---- shipments ----
    op.create_table(
        "shipments",
        sa.Column("shipment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.order_id"), nullable=False, unique=True),
        sa.Column("courier_partner", sa.String(100), nullable=False),
        sa.Column("shipment_status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("expected_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("actual_delivery_date", sa.DateTime(), nullable=True),
        sa.Column("tracking_number", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ---- returns ----
    op.create_table(
        "returns",
        sa.Column("return_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.order_id"), nullable=False, unique=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Requested"),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("eligibility_window_days", sa.Integer, nullable=False, server_default="7"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )

    # ---- refunds ----
    op.create_table(
        "refunds",
        sa.Column("refund_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("return_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("returns.return_id"), nullable=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.order_id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("credited_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )

    # ---- payments ----
    op.create_table(
        "payments",
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.order_id"), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="Pending"),
        sa.Column("payment_method", sa.String(50), nullable=False),
        sa.Column("transaction_date", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_payments_order_id", "payments", ["order_id"])
    op.create_index("idx_payments_status", "payments", ["status"])

    # ---- voice_sessions ----
    op.create_table(
        "voice_sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("language_detected", sa.String(20), nullable=True),
        sa.Column("audio_file_path", sa.String(500), nullable=True),
        sa.Column("transcript_original", sa.Text(), nullable=True),
        sa.Column("transcript_english", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
    )

    # ---- support_tickets ----
    op.create_table(
        "support_tickets",
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.order_id"), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("voice_sessions.session_id"), nullable=True),
        sa.Column("ticket_type", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="Medium"),
        sa.Column("status", sa.String(20), nullable=False, server_default="Open"),
        sa.Column("language", sa.String(20), nullable=False, server_default="English"),
        sa.Column("sentiment", sa.String(20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("escalated_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )
    op.create_index("idx_tickets_user_id", "support_tickets", ["user_id"])
    op.create_index("idx_tickets_status", "support_tickets", ["status"])
    op.create_index("idx_tickets_priority", "support_tickets", ["priority"])
    op.create_index("idx_tickets_created_at", "support_tickets", ["created_at"])

    # ---- support_messages ----
    op.create_table(
        "support_messages",
        sa.Column("message_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("support_tickets.ticket_id"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("voice_sessions.session_id"), nullable=True),
        sa.Column("sender_type", sa.String(20), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("language", sa.String(20), nullable=False, server_default="English"),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )

    # ---- support_resolutions ----
    op.create_table(
        "support_resolutions",
        sa.Column("resolution_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("support_tickets.ticket_id"), nullable=False, unique=True),
        sa.Column("recommended_action", sa.String(30), nullable=False),
        sa.Column("policy_reference", sa.Text(), nullable=True),
        sa.Column("final_response_text", sa.Text(), nullable=False),
        sa.Column("final_response_audio", sa.String(500), nullable=True),
        sa.Column("internal_note", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("agent_trace", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("updated_by", sa.String(100), nullable=True),
    )

    # ---- customer_sentiments ----
    op.create_table(
        "customer_sentiments",
        sa.Column("sentiment_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticket_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("support_tickets.ticket_id"), nullable=False),
        sa.Column("sentiment_label", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("raw_text_snippet", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
    )

    # ---- policy_documents ----
    op.create_table(
        "policy_documents",
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chroma_doc_id", sa.String(100), nullable=True),
        sa.Column("version", sa.String(20), nullable=True),
        sa.Column("effective_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("policy_documents")
    op.drop_table("customer_sentiments")
    op.drop_table("support_resolutions")
    op.drop_table("support_messages")
    op.drop_table("support_tickets")
    op.drop_table("voice_sessions")
    op.drop_table("payments")
    op.drop_table("refunds")
    op.drop_table("returns")
    op.drop_table("shipments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("users")
