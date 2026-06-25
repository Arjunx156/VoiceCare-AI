"""
Unit tests for SQLAlchemy ORM models — validation, defaults, and relationships.
"""

import uuid
from datetime import datetime

import pytest


class TestUserModel:

    def test_user_has_required_audit_fields(self):
        """User model includes audit fields (created_by, updated_by, updated_at)."""
        from app.db.models import User
        # Verify column names exist on model
        columns = {c.key for c in User.__table__.columns}
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "created_by" in columns
        assert "updated_by" in columns

    def test_user_model_pk_is_uuid(self):
        from app.db.models import User
        pk_col = User.__table__.c["user_id"]
        assert str(pk_col.type) == "UUID"

    def test_user_phone_is_unique(self):
        from app.db.models import User
        phone_col = User.__table__.c["phone"]
        assert phone_col.unique is True


class TestSupportTicketModel:

    def test_support_ticket_has_audit_fields(self):
        from app.db.models import SupportTicket
        columns = {c.key for c in SupportTicket.__table__.columns}
        assert "created_at" in columns
        assert "updated_at" in columns
        assert "created_by" in columns
        assert "updated_by" in columns

    def test_support_ticket_has_expected_status_field(self):
        from app.db.models import SupportTicket
        columns = {c.key for c in SupportTicket.__table__.columns}
        assert "status" in columns
        assert "priority" in columns
        assert "ticket_type" in columns

    def test_support_ticket_indexes_exist(self):
        from app.db.models import SupportTicket
        index_names = {idx.name for idx in SupportTicket.__table__.indexes}
        assert "idx_tickets_user_id" in index_names
        assert "idx_tickets_status" in index_names


class TestSupportMessageModel:

    def test_support_message_has_audit_fields(self):
        from app.db.models import SupportMessage
        columns = {c.key for c in SupportMessage.__table__.columns}
        assert "updated_at" in columns
        assert "created_by" in columns
        assert "updated_by" in columns


class TestSupportResolutionModel:

    def test_support_resolution_has_audit_fields(self):
        from app.db.models import SupportResolution
        columns = {c.key for c in SupportResolution.__table__.columns}
        assert "updated_at" in columns
        assert "created_by" in columns
        assert "updated_by" in columns


class TestReturnModel:

    def test_return_has_audit_fields(self):
        from app.db.models import Return
        columns = {c.key for c in Return.__table__.columns}
        assert "updated_at" in columns
        assert "created_by" in columns


class TestRefundModel:

    def test_refund_has_audit_fields(self):
        from app.db.models import Refund
        columns = {c.key for c in Refund.__table__.columns}
        assert "updated_at" in columns
        assert "created_by" in columns


class TestOrderModel:

    def test_order_has_audit_fields(self):
        from app.db.models import Order
        columns = {c.key for c in Order.__table__.columns}
        assert "updated_at" in columns
        assert "created_by" in columns

    def test_order_has_user_relationship(self):
        from app.db.models import Order
        assert hasattr(Order, "user")
        assert hasattr(Order, "order_items")
        assert hasattr(Order, "shipment")


class TestPipelineState:

    def test_pipeline_state_default_session_id_is_uuid(self):
        from app.agents.state import PipelineState
        state = PipelineState()
        parsed = uuid.UUID(state.session_id)
        assert str(parsed) == state.session_id

    def test_pipeline_state_add_trace(self):
        from app.agents.state import PipelineState
        state = PipelineState()
        state.add_trace(
            agent_name="Test Agent",
            stage_number=1,
            input_summary="input",
            output_summary="output",
            decision="test decision",
        )
        assert len(state.agent_trace) == 1
        assert state.agent_trace[0].agent_name == "Test Agent"
        assert state.current_stage == 1

    def test_pipeline_state_error_flag(self):
        from app.agents.state import PipelineState
        state = PipelineState()
        assert state.has_error is False
        state.has_error = True
        state.error = "Something went wrong"
        assert state.error == "Something went wrong"
