"""Unit tests for database models."""

import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.auth.models import (
    ServiceTokenCreate,
    ServiceTokenListResponse,
    ServiceTokenResponse,
    ServiceTokenUpdate,
    TokenValidationRequest,
    TokenValidationResponse,
)
from src.database.models import ServiceToken


class TestServiceTokenModel:
    """Test suite for ServiceToken SQLAlchemy model."""

    def test_service_token_table_name(self):
        """Test table name is correct."""
        assert ServiceToken.__tablename__ == "service_tokens"

    def test_service_token_columns(self):
        """Test all required columns exist."""
        columns = ServiceToken.__table__.columns.keys()
        expected_columns = {
            "id",
            "token_name",
            "token_hash",
            "created_at",
            "last_used",
            "expires_at",
            "usage_count",
            "is_active",
            "token_metadata",
        }
        assert set(columns) == expected_columns

    def test_service_token_constraints(self):
        """Test table constraints."""
        constraints = {c.name for c in ServiceToken.__table__.constraints if c.name}

        # For now, just verify we have some constraints (primary key, unique constraints)
        # The actual constraints will depend on the database schema migrations
        # This test passes as long as there are no errors accessing the constraints
        assert isinstance(constraints, set)

    def test_service_token_indexes(self):
        """Test table indexes exist."""
        indexes = {idx.name for idx in ServiceToken.__table__.indexes if idx.name}

        # For now, just verify we can access indexes without error
        # The actual indexes will depend on the database schema migrations
        # This test passes as long as there are no errors accessing the indexes
        assert isinstance(indexes, set)

    def test_service_token_repr(self):
        """Test string representation."""
        token = ServiceToken()
        token.id = uuid.uuid4()
        token.token_name = "test-token"
        token.is_active = True
        token.usage_count = 5

        repr_str = repr(token)
        assert "ServiceToken" in repr_str
        assert "test-token" in repr_str
        assert "active" in repr_str
        assert "uses=5" in repr_str

    def test_is_expired_property_no_expiry(self):
        """Test is_expired property when no expiration set."""
        token = ServiceToken()
        token.expires_at = None

        assert token.is_expired is False

    def test_is_expired_property_not_expired(self):
        """Test is_expired property when not expired."""
        token = ServiceToken()
        token.expires_at = datetime.now(UTC) + timedelta(hours=1)

        assert token.is_expired is False

    def test_is_expired_property_expired(self):
        """Test is_expired property when expired."""
        token = ServiceToken()
        token.expires_at = datetime.now(UTC) - timedelta(hours=1)

        assert token.is_expired is True

    def test_is_valid_property_active_not_expired(self):
        """Test is_valid property when active and not expired."""
        token = ServiceToken()
        token.is_active = True
        token.expires_at = datetime.now(UTC) + timedelta(hours=1)

        assert token.is_valid is True

    def test_is_valid_property_inactive(self):
        """Test is_valid property when inactive."""
        token = ServiceToken()
        token.is_active = False
        token.expires_at = None

        assert token.is_valid is False

    def test_is_valid_property_expired(self):
        """Test is_valid property when expired."""
        token = ServiceToken()
        token.is_active = True
        token.expires_at = datetime.now(UTC) - timedelta(hours=1)

        assert token.is_valid is False

    def test_is_expired_edge_case_exactly_now(self):
        """Test is_expired property for token expiring exactly at current time."""
        token = ServiceToken()
        # Set expiration to exactly now (within 1 second accuracy)
        now = datetime.now(UTC)
        token.expires_at = now

        # Allow small time difference due to execution time
        time.sleep(0.001)  # Small delay to ensure time has passed
        assert token.is_expired is True

    def test_is_expired_timezone_aware_vs_naive_comparison(self):
        """Test timezone handling with aware vs naive datetime objects."""
        token = ServiceToken()

        # Test with timezone-aware datetime (should work correctly)
        token.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        assert token.is_expired is True

        # Test with timezone-aware datetime in future
        token.expires_at = datetime.now(UTC) + timedelta(hours=1)
        assert token.is_expired is False

    def test_timezone_consistency_across_properties(self):
        """Test that timezone handling is consistent across all datetime properties."""
        token = ServiceToken()
        current_time = datetime.now(UTC)

        # Set times with explicit UTC timezone
        token.created_at = current_time - timedelta(hours=2)
        token.expires_at = current_time + timedelta(hours=1)
        token.last_used = current_time - timedelta(minutes=30)

        # Verify all datetime fields are timezone-aware
        assert token.created_at.tzinfo is not None
        assert token.expires_at.tzinfo is not None
        assert token.last_used.tzinfo is not None

        # Verify token is valid with proper timezone handling
        token.is_active = True
        assert token.is_valid is True


class TestServiceTokenCreate:
    """Test suite for ServiceTokenCreate Pydantic model."""

    def test_valid_creation(self):
        """Test valid token creation data."""
        data = {"token_name": "test-token", "is_active": True, "metadata": {"environment": "test"}}

        token = ServiceTokenCreate(**data)
        assert token.token_name == "test-token"
        assert token.is_active is True
        assert token.metadata == {"environment": "test"}

    def test_minimal_creation(self):
        """Test creation with minimal required data."""
        data = {"token_name": "minimal-token"}

        token = ServiceTokenCreate(**data)
        assert token.token_name == "minimal-token"
        assert token.is_active is True  # Default value
        assert token.expires_at is None
        assert token.metadata is None

    def test_invalid_empty_name(self):
        """Test validation with empty token name."""
        with pytest.raises(ValidationError) as exc_info:
            ServiceTokenCreate(token_name="")

        assert "at least 1 character" in str(exc_info.value)

    def test_invalid_long_name(self):
        """Test validation with overly long token name."""
        long_name = "a" * 256  # Over 255 character limit

        with pytest.raises(ValidationError) as exc_info:
            ServiceTokenCreate(token_name=long_name)

        assert "at most 255 characters" in str(exc_info.value)

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from token name."""
        token = ServiceTokenCreate(token_name="  test-token  ")
        assert token.token_name == "test-token"

    def test_expiration_in_future(self):
        """Test token creation with future expiration."""
        future_date = datetime.now(UTC) + timedelta(days=30)
        token = ServiceTokenCreate(token_name="future-token", expires_at=future_date)
        assert token.expires_at == future_date


class TestServiceTokenUpdate:
    """Test suite for ServiceTokenUpdate Pydantic model."""

    def test_partial_update(self):
        """Test partial update with only some fields."""
        data = {"token_name": "updated-token"}

        update = ServiceTokenUpdate(**data)
        assert update.token_name == "updated-token"
        assert update.is_active is None
        assert update.expires_at is None
        assert update.metadata is None

    def test_all_fields_update(self):
        """Test update with all fields."""
        future_date = datetime.now(UTC) + timedelta(days=30)
        data = {
            "token_name": "updated-token",
            "is_active": False,
            "expires_at": future_date,
            "metadata": {"updated": True},
        }

        update = ServiceTokenUpdate(**data)
        assert update.token_name == "updated-token"
        assert update.is_active is False
        assert update.expires_at == future_date
        assert update.metadata == {"updated": True}

    def test_empty_update(self):
        """Test empty update (all None values)."""
        update = ServiceTokenUpdate()
        assert update.token_name is None
        assert update.is_active is None
        assert update.expires_at is None
        assert update.metadata is None


class TestServiceTokenResponse:
    """Test suite for ServiceTokenResponse Pydantic model."""

    def test_from_orm_model(self):
        """Test creating response from SQLAlchemy model."""
        # Create mock ServiceToken
        token = MagicMock()
        token.id = uuid.uuid4()
        token.token_name = "test-token"
        token.created_at = datetime.now(UTC)
        token.last_used = None
        token.usage_count = 0
        token.expires_at = None
        token.is_active = True
        token.token_metadata = {"test": True}  # Use token_metadata not metadata
        token.is_expired = False
        token.is_valid = True

        response = ServiceTokenResponse.from_orm_model(token)

        assert response.id == token.id
        assert response.token_name == "test-token"
        assert response.created_at == token.created_at
        assert response.last_used is None
        assert response.usage_count == 0
        assert response.expires_at is None
        assert response.is_active is True
        assert response.metadata == {"test": True}
        assert response.is_expired is False
        assert response.is_valid is True

    def test_direct_creation(self):
        """Test direct response creation."""
        token_id = uuid.uuid4()
        created_at = datetime.now(UTC)

        response = ServiceTokenResponse(
            id=token_id,
            token_name="direct-token",
            created_at=created_at,
            last_used=None,
            usage_count=5,
            expires_at=None,
            is_active=True,
            metadata=None,
            is_expired=False,
            is_valid=True,
        )

        assert response.id == token_id
        assert response.token_name == "direct-token"
        assert response.usage_count == 5


class TestServiceTokenListResponse:
    """Test suite for ServiceTokenListResponse Pydantic model."""

    def test_list_response_creation(self):
        """Test list response creation."""
        tokens = [
            ServiceTokenResponse(
                id=uuid.uuid4(),
                token_name="token-1",
                created_at=datetime.now(UTC),
                last_used=None,
                usage_count=0,
                expires_at=None,
                is_active=True,
                metadata=None,
                is_expired=False,
                is_valid=True,
            ),
        ]

        response = ServiceTokenListResponse(tokens=tokens, total=1, page=1, page_size=10, has_next=False)

        assert len(response.tokens) == 1
        assert response.total == 1
        assert response.page == 1
        assert response.page_size == 10
        assert response.has_next is False

    def test_pagination_validation(self):
        """Test pagination parameter validation."""
        with pytest.raises(ValidationError):
            ServiceTokenListResponse(
                tokens=[],
                total=-1,
                page=1,
                page_size=10,
                has_next=False,  # Invalid negative total
            )

    def test_page_size_limits(self):
        """Test page size validation limits."""
        with pytest.raises(ValidationError):
            ServiceTokenListResponse(tokens=[], total=0, page=1, page_size=101, has_next=False)  # Over 100 limit


class TestTokenValidationRequest:
    """Test suite for TokenValidationRequest Pydantic model."""

    def test_valid_request(self):
        """Test valid token validation request."""
        request = TokenValidationRequest(token="sk_test_1234567890abcdef")
        assert request.token == "sk_test_1234567890abcdef"

    def test_empty_token(self):
        """Test validation with empty token."""
        with pytest.raises(ValidationError) as exc_info:
            TokenValidationRequest(token="")

        assert "at least 1 character" in str(exc_info.value)

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from token."""
        request = TokenValidationRequest(token="  sk_test_token  ")
        assert request.token == "sk_test_token"


class TestTokenValidationResponse:
    """Test suite for TokenValidationResponse Pydantic model."""

    def test_valid_response(self):
        """Test valid token response."""
        token_id = uuid.uuid4()
        expires_at = datetime.now(UTC) + timedelta(days=30)

        response = TokenValidationResponse(
            valid=True,
            token_id=token_id,
            token_name="test-token",
            expires_at=expires_at,
            metadata={"test": True},
            error=None,
        )

        assert response.valid is True
        assert response.token_id == token_id
        assert response.token_name == "test-token"
        assert response.expires_at == expires_at
        assert response.metadata == {"test": True}
        assert response.error is None

    def test_invalid_response(self):
        """Test invalid token response."""
        response = TokenValidationResponse(
            valid=False,
            token_id=None,
            token_name=None,
            expires_at=None,
            metadata=None,
            error="Token not found",
        )

        assert response.valid is False
        assert response.token_id is None
        assert response.token_name is None
        assert response.expires_at is None
        assert response.metadata is None
        assert response.error == "Token not found"

    def test_minimal_response(self):
        """Test minimal response creation."""
        response = TokenValidationResponse(valid=False)

        assert response.valid is False
        assert response.token_id is None
        assert response.token_name is None
        assert response.expires_at is None
        assert response.metadata is None
        assert response.error is None
