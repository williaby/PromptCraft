"""Unit tests for database models."""

import uuid

import pytest
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

from src.database.models import AuthenticationEvent, Base, UserSession


@pytest.mark.unit
@pytest.mark.fast
class TestUserSession:
    """Test UserSession model."""

    def test_user_session_table_name(self):
        """Test UserSession table name."""
        assert UserSession.__tablename__ == "user_sessions"

    def test_user_session_inheritance(self):
        """Test UserSession inherits from Base."""
        assert issubclass(UserSession, Base)

    def test_user_session_columns(self):
        """Test UserSession has required columns."""
        # Get table columns
        table = UserSession.__table__
        column_names = [col.name for col in table.columns]

        expected_columns = [
            "id",
            "email",
            "cloudflare_sub",
            "first_seen",
            "last_seen",
            "session_count",
            "preferences",
            "user_metadata",
        ]

        for column in expected_columns:
            assert column in column_names

    def test_user_session_id_column(self):
        """Test UserSession id column properties."""
        table = UserSession.__table__
        id_column = table.columns["id"]

        assert id_column.primary_key is True
        assert isinstance(id_column.type, UUID)
        assert id_column.nullable is False

    def test_user_session_email_column(self):
        """Test UserSession email column properties."""
        table = UserSession.__table__
        email_column = table.columns["email"]

        assert email_column.nullable is False
        assert email_column.type.length == 255
        assert hasattr(email_column, "index")

    def test_user_session_cloudflare_sub_column(self):
        """Test UserSession cloudflare_sub column properties."""
        table = UserSession.__table__
        sub_column = table.columns["cloudflare_sub"]

        assert sub_column.nullable is False
        assert sub_column.type.length == 255
        assert hasattr(sub_column, "index")

    def test_user_session_timestamp_columns(self):
        """Test UserSession timestamp columns."""
        table = UserSession.__table__

        first_seen = table.columns["first_seen"]
        last_seen = table.columns["last_seen"]

        assert first_seen.nullable is False
        assert last_seen.nullable is False
        # Both should have default values
        assert first_seen.default is not None
        assert last_seen.default is not None

    def test_user_session_session_count_column(self):
        """Test UserSession session_count column properties."""
        table = UserSession.__table__
        count_column = table.columns["session_count"]

        assert count_column.nullable is False
        assert count_column.default.arg == 1

    def test_user_session_jsonb_columns(self):
        """Test UserSession JSONB columns."""
        table = UserSession.__table__

        preferences_column = table.columns["preferences"]
        metadata_column = table.columns["user_metadata"]

        assert isinstance(preferences_column.type, JSONB)
        assert isinstance(metadata_column.type, JSONB)
        assert preferences_column.nullable is False
        assert metadata_column.nullable is False

    def test_user_session_creation(self):
        """Test UserSession instance creation."""
        session = UserSession(
            email="test@example.com",
            cloudflare_sub="cf-sub-123",
            session_count=1,
            preferences={"theme": "dark"},
            user_metadata={"last_login": "2025-01-01T00:00:00Z"},
        )

        assert session.email == "test@example.com"
        assert session.cloudflare_sub == "cf-sub-123"
        assert session.session_count == 1
        assert session.preferences == {"theme": "dark"}
        assert session.user_metadata == {"last_login": "2025-01-01T00:00:00Z"}

    def test_user_session_creation_with_defaults(self):
        """Test UserSession creation uses default values."""
        session = UserSession(
            email="test@example.com",
            cloudflare_sub="cf-sub-123",
        )

        assert session.email == "test@example.com"
        assert session.cloudflare_sub == "cf-sub-123"
        # Should use defaults
        assert session.preferences == {}
        assert session.user_metadata == {}

    def test_user_session_repr(self):
        """Test UserSession string representation."""
        session_id = uuid.uuid4()
        session = UserSession(
            id=session_id,
            email="test@example.com",
            cloudflare_sub="cf-sub-123",
            session_count=5,
        )

        repr_str = repr(session)
        assert "UserSession" in repr_str
        assert str(session_id) in repr_str
        assert "test@example.com" in repr_str
        assert "sessions=5" in repr_str

    def test_user_session_complex_jsonb_data(self):
        """Test UserSession with complex JSONB data."""
        complex_preferences = {
            "theme": "dark",
            "notifications": {
                "email": True,
                "push": False,
                "settings": {"frequency": "daily", "types": ["security", "updates"]},
            },
            "layout": {"sidebar": "collapsed", "panels": ["activity", "metrics"]},
        }

        complex_metadata = {
            "user_agent": "Mozilla/5.0...",
            "login_history": [
                {"timestamp": "2025-01-01T10:00:00Z", "ip": "192.168.1.1"},
                {"timestamp": "2025-01-01T11:00:00Z", "ip": "192.168.1.2"},
            ],
            "feature_flags": {"beta_features": True, "experimental": False},
        }

        session = UserSession(
            email="test@example.com",
            cloudflare_sub="cf-sub-123",
            preferences=complex_preferences,
            user_metadata=complex_metadata,
        )

        assert session.preferences == complex_preferences
        assert session.user_metadata == complex_metadata


@pytest.mark.unit
@pytest.mark.fast
class TestAuthenticationEvent:
    """Test AuthenticationEvent model."""

    def test_authentication_event_table_name(self):
        """Test AuthenticationEvent table name."""
        assert AuthenticationEvent.__tablename__ == "authentication_events"

    def test_authentication_event_inheritance(self):
        """Test AuthenticationEvent inherits from Base."""
        assert issubclass(AuthenticationEvent, Base)

    def test_authentication_event_columns(self):
        """Test AuthenticationEvent has required columns."""
        table = AuthenticationEvent.__table__
        column_names = [col.name for col in table.columns]

        expected_columns = [
            "id",
            "user_email",
            "event_type",
            "ip_address",
            "user_agent",
            "cloudflare_ray_id",
            "success",
            "error_details",
            "performance_metrics",
            "created_at",
        ]

        for column in expected_columns:
            assert column in column_names

    def test_authentication_event_id_column(self):
        """Test AuthenticationEvent id column properties."""
        table = AuthenticationEvent.__table__
        id_column = table.columns["id"]

        assert id_column.primary_key is True
        assert isinstance(id_column.type, UUID)
        assert id_column.nullable is False

    def test_authentication_event_user_email_column(self):
        """Test AuthenticationEvent user_email column properties."""
        table = AuthenticationEvent.__table__
        email_column = table.columns["user_email"]

        assert email_column.nullable is False
        assert email_column.type.length == 255
        assert hasattr(email_column, "index")

    def test_authentication_event_event_type_column(self):
        """Test AuthenticationEvent event_type column properties."""
        table = AuthenticationEvent.__table__
        type_column = table.columns["event_type"]

        assert type_column.nullable is False
        assert type_column.type.length == 50
        assert hasattr(type_column, "index")

    def test_authentication_event_ip_address_column(self):
        """Test AuthenticationEvent ip_address column properties."""
        table = AuthenticationEvent.__table__
        ip_column = table.columns["ip_address"]

        assert ip_column.nullable is True
        assert isinstance(ip_column.type, INET)

    def test_authentication_event_success_column(self):
        """Test AuthenticationEvent success column properties."""
        table = AuthenticationEvent.__table__
        success_column = table.columns["success"]

        assert success_column.nullable is False
        assert success_column.default.arg is True
        assert hasattr(success_column, "index")

    def test_authentication_event_jsonb_columns(self):
        """Test AuthenticationEvent JSONB columns."""
        table = AuthenticationEvent.__table__

        error_column = table.columns["error_details"]
        metrics_column = table.columns["performance_metrics"]

        assert isinstance(error_column.type, JSONB)
        assert isinstance(metrics_column.type, JSONB)
        assert error_column.nullable is True
        assert metrics_column.nullable is True

    def test_authentication_event_created_at_column(self):
        """Test AuthenticationEvent created_at column properties."""
        table = AuthenticationEvent.__table__
        created_column = table.columns["created_at"]

        assert created_column.nullable is False
        assert created_column.default is not None
        assert hasattr(created_column, "index")

    def test_authentication_event_creation(self):
        """Test AuthenticationEvent instance creation."""
        event = AuthenticationEvent(
            user_email="test@example.com",
            event_type="login",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 Test Browser",
            cloudflare_ray_id="ray-12345",
            success=True,
            error_details=None,
            performance_metrics={"jwt_time_ms": 5.2, "total_time_ms": 45.1},
        )

        assert event.user_email == "test@example.com"
        assert event.event_type == "login"
        assert event.ip_address == "192.168.1.1"
        assert event.user_agent == "Mozilla/5.0 Test Browser"
        assert event.cloudflare_ray_id == "ray-12345"
        assert event.success is True
        assert event.error_details is None
        assert event.performance_metrics == {"jwt_time_ms": 5.2, "total_time_ms": 45.1}

    def test_authentication_event_creation_with_defaults(self):
        """Test AuthenticationEvent creation uses default values."""
        event = AuthenticationEvent(
            user_email="test@example.com",
            event_type="login",
        )

        assert event.user_email == "test@example.com"
        assert event.event_type == "login"
        # Should use defaults
        assert event.success is True

    def test_authentication_event_failure_case(self):
        """Test AuthenticationEvent for failure case."""
        error_details = {
            "error_type": "JWT_INVALID",
            "error_message": "Token expired",
            "request_path": "/api/protected",
            "request_method": "GET",
        }

        event = AuthenticationEvent(
            user_email="unknown",
            event_type="failed_login",
            ip_address="192.168.1.100",
            success=False,
            error_details=error_details,
        )

        assert event.user_email == "unknown"
        assert event.event_type == "failed_login"
        assert event.success is False
        assert event.error_details == error_details

    def test_authentication_event_performance_metrics(self):
        """Test AuthenticationEvent with performance metrics."""
        performance_metrics = {
            "jwt_validation_ms": 12.5,
            "database_operation_ms": 8.3,
            "total_processing_ms": 65.7,
            "timestamp": 1704067200.0,
            "memory_usage_mb": 45.2,
            "cpu_usage_percent": 2.1,
        }

        event = AuthenticationEvent(
            user_email="test@example.com",
            event_type="login",
            performance_metrics=performance_metrics,
        )

        assert event.performance_metrics == performance_metrics

    def test_authentication_event_repr(self):
        """Test AuthenticationEvent string representation."""
        event_id = uuid.uuid4()
        event = AuthenticationEvent(
            id=event_id,
            user_email="test@example.com",
            event_type="login",
            success=True,
        )

        repr_str = repr(event)
        assert "AuthenticationEvent" in repr_str
        assert str(event_id) in repr_str
        assert "test@example.com" in repr_str
        assert "login" in repr_str
        assert "SUCCESS" in repr_str

    def test_authentication_event_repr_failure(self):
        """Test AuthenticationEvent string representation for failures."""
        event_id = uuid.uuid4()
        event = AuthenticationEvent(
            id=event_id,
            user_email="test@example.com",
            event_type="failed_login",
            success=False,
        )

        repr_str = repr(event)
        assert "AuthenticationEvent" in repr_str
        assert "test@example.com" in repr_str
        assert "failed_login" in repr_str
        assert "FAILED" in repr_str

    def test_authentication_event_complex_data(self):
        """Test AuthenticationEvent with complex nested data."""
        error_details = {
            "error_code": "AUTH_001",
            "error_message": "Invalid JWT signature",
            "stack_trace": [
                "auth/middleware.py:245",
                "auth/jwt_validator.py:123",
            ],
            "context": {
                "request_id": "req-12345",
                "user_agent": "Chrome/91.0",
                "headers": {"cf-ray": "ray-67890", "cf-connecting-ip": "203.0.113.1"},
            },
        }

        performance_metrics = {
            "stages": {
                "token_extraction": {"duration_ms": 0.5, "success": True},
                "jwt_validation": {"duration_ms": 15.2, "success": False},
                "database_lookup": {"duration_ms": 0.0, "success": False},
            },
            "memory": {"peak_usage_mb": 128.5, "allocations": 456},
            "network": {"dns_lookup_ms": 2.1, "tcp_connect_ms": 12.3},
        }

        event = AuthenticationEvent(
            user_email="user@company.com",
            event_type="validation_error",
            ip_address="203.0.113.1",
            success=False,
            error_details=error_details,
            performance_metrics=performance_metrics,
        )

        assert event.error_details == error_details
        assert event.performance_metrics == performance_metrics


@pytest.mark.unit
@pytest.mark.fast
class TestBaseModel:
    """Test Base declarative base."""

    def test_base_declarative_base(self):
        """Test Base is a declarative base."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_models_use_base(self):
        """Test both models inherit from Base."""
        assert issubclass(UserSession, Base)
        assert issubclass(AuthenticationEvent, Base)

    def test_base_exports(self):
        """Test Base is exported in __all__."""
        from src.database.models import __all__

        assert "Base" in __all__
        assert "UserSession" in __all__
        assert "AuthenticationEvent" in __all__


@pytest.mark.unit
@pytest.mark.fast
class TestModelConstraints:
    """Test model constraints and validation."""

    def test_user_session_required_fields(self):
        """Test UserSession validates required fields."""
        # This would typically be tested with actual database operations
        # For unit tests, we verify the column definitions are correct
        table = UserSession.__table__

        # Check non-nullable columns
        non_nullable_columns = [
            col.name for col in table.columns if not col.nullable and col.name != "id"  # id has default
        ]

        expected_required = [
            "email",
            "cloudflare_sub",
            "first_seen",
            "last_seen",
            "session_count",
            "preferences",
            "user_metadata",
        ]
        for column in expected_required:
            assert column in non_nullable_columns

    def test_authentication_event_required_fields(self):
        """Test AuthenticationEvent validates required fields."""
        table = AuthenticationEvent.__table__

        # Check non-nullable columns
        non_nullable_columns = [
            col.name for col in table.columns if not col.nullable and col.name != "id"  # id has default
        ]

        expected_required = ["user_email", "event_type", "success", "created_at"]
        for column in expected_required:
            assert column in non_nullable_columns

    def test_user_session_defaults(self):
        """Test UserSession default values."""
        table = UserSession.__table__

        # Check columns with defaults
        session_count_col = table.columns["session_count"]
        preferences_col = table.columns["preferences"]
        metadata_col = table.columns["user_metadata"]

        assert session_count_col.default.arg == 1
        assert preferences_col.server_default is not None
        assert metadata_col.server_default is not None

    def test_authentication_event_defaults(self):
        """Test AuthenticationEvent default values."""
        table = AuthenticationEvent.__table__

        # Check success column default
        success_col = table.columns["success"]
        assert success_col.default.arg is True
        assert success_col.server_default is not None
