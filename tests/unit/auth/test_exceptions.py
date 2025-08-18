"""Tests for auth.exceptions module.

This module provides comprehensive test coverage for authentication and authorization
exception handling utilities including the AuthExceptionHandler class and convenience functions.
"""

import logging
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException, status

from src.auth.exceptions import (
    AuthExceptionHandler,
    already_exists,
    authentication_required,
    operation_failed,
    permission_denied,
    permission_not_found,
    role_not_found,
    user_not_found,
    validation_failed,
)
from src.auth.role_manager import (
    PermissionNotFoundError,
    RoleManagerError,
    RoleNotFoundError,
    UserNotFoundError,
)


class TestAuthExceptionHandler:
    """Test cases for AuthExceptionHandler class methods."""

    def test_handle_authentication_error_basic(self):
        """Test basic authentication error handling."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_authentication_error()
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_401_UNAUTHORIZED
            assert exception.detail == "Authentication required"
            assert exception.headers == {"WWW-Authenticate": "Bearer"}
            mock_logger.warning.assert_called_once_with("Authentication failed: Authentication required")

    def test_handle_authentication_error_with_custom_detail(self):
        """Test authentication error with custom detail message."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_authentication_error(
                detail="Invalid token",
                log_message="Token validation failed",
                user_identifier="user123"
            )
            
            assert exception.status_code == status.HTTP_401_UNAUTHORIZED
            assert exception.detail == "Invalid token"
            assert exception.headers == {"WWW-Authenticate": "Bearer"}
            mock_logger.warning.assert_called_once_with(
                "Authentication failed: Token validation failed - user: user123"
            )

    def test_handle_authentication_error_with_user_identifier_only(self):
        """Test authentication error with user identifier but no custom log message."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_authentication_error(
                detail="Token expired",
                user_identifier="user456"
            )
            
            assert exception.detail == "Token expired"
            mock_logger.warning.assert_called_once_with(
                "Authentication failed: Token expired - user: user456"
            )

    def test_handle_permission_error_basic(self):
        """Test basic permission error handling."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_permission_error()
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_403_FORBIDDEN
            assert exception.detail == "Insufficient permissions"
            mock_logger.warning.assert_called_once_with("Permission denied: Insufficient permissions")

    def test_handle_permission_error_with_permission_name(self):
        """Test permission error with permission name."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_permission_error(
                permission_name="admin:delete",
                user_identifier="user789"
            )
            
            assert exception.status_code == status.HTTP_403_FORBIDDEN
            assert exception.detail == "Insufficient permissions: admin:delete required"
            mock_logger.warning.assert_called_once_with(
                "Permission denied: Insufficient permissions: admin:delete required - user: user789"
            )

    def test_handle_permission_error_with_custom_detail(self):
        """Test permission error with custom detail message."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_permission_error(
                detail="Custom permission denied message",
                user_identifier="user101"
            )
            
            assert exception.detail == "Custom permission denied message"
            mock_logger.warning.assert_called_once_with(
                "Permission denied: Custom permission denied message - user: user101"
            )

    def test_handle_not_found_error_basic(self):
        """Test basic not found error handling."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_not_found_error("role")
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert exception.detail == "Role not found"
            mock_logger.info.assert_called_once_with("Entity not found: Role not found")

    def test_handle_not_found_error_with_identifier(self):
        """Test not found error with entity identifier."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_not_found_error(
                "user", 
                "test@example.com"
            )
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert exception.detail == "User 'test@example.com' not found"
            mock_logger.info.assert_called_once_with("Entity not found: User 'test@example.com' not found")

    def test_handle_not_found_error_with_custom_detail(self):
        """Test not found error with custom detail message."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_not_found_error(
                "permission",
                "read:users",
                detail="Custom not found message"
            )
            
            assert exception.detail == "Custom not found message"
            mock_logger.info.assert_called_once_with("Entity not found: Custom not found message")

    def test_handle_validation_error_basic(self):
        """Test basic validation error handling."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_validation_error("Invalid input")
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert exception.detail == "Invalid input"
            mock_logger.info.assert_called_once_with("Validation error: Invalid input")

    def test_handle_validation_error_with_field_name(self):
        """Test validation error with field name."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_validation_error(
                "Email format is invalid",
                field_name="email",
                log_additional="regex validation failed"
            )
            
            assert exception.detail == "Email format is invalid"
            mock_logger.info.assert_called_once_with(
                "Validation error: Email format is invalid - field: email - regex validation failed"
            )

    def test_handle_conflict_error_basic(self):
        """Test basic conflict error handling."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_conflict_error("Resource already exists")
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_409_CONFLICT
            assert exception.detail == "Resource already exists"
            mock_logger.info.assert_called_once_with("Conflict error: Resource already exists")

    def test_handle_conflict_error_with_entity_info(self):
        """Test conflict error with entity information."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_conflict_error(
                "Role name conflict",
                entity_type="role",
                entity_identifier="admin"
            )
            
            assert exception.detail == "Role name conflict"
            mock_logger.info.assert_called_once_with("Conflict error: Role name conflict - role: admin")

    def test_handle_rate_limit_error_basic(self):
        """Test basic rate limit error handling."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_rate_limit_error()
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert exception.detail == "Too many requests"
            assert exception.headers == {"Retry-After": "60"}
            mock_logger.warning.assert_called_once_with("Rate limit exceeded: Too many requests")

    def test_handle_rate_limit_error_with_custom_params(self):
        """Test rate limit error with custom parameters."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_rate_limit_error(
                retry_after=120,
                detail="API quota exceeded",
                client_identifier="client123"
            )
            
            assert exception.detail == "API quota exceeded"
            assert exception.headers == {"Retry-After": "120"}
            mock_logger.warning.assert_called_once_with(
                "Rate limit exceeded: API quota exceeded - client: client123"
            )

    def test_handle_internal_error_basic(self):
        """Test basic internal error handling."""
        test_error = ValueError("Test error")
        
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_internal_error(
                "Database operation",
                test_error
            )
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exception.detail == "Internal server error"
            mock_logger.error.assert_called_once_with(
                "Database operation failed: Test error",
                exc_info=True
            )

    def test_handle_internal_error_with_expose_error(self):
        """Test internal error with error details exposed."""
        test_error = RuntimeError("Database connection failed")
        
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_internal_error(
                "Connection test",
                test_error,
                detail="Service temporarily unavailable",
                expose_error=True
            )
            
            assert exception.detail == "Service temporarily unavailable: Database connection failed"
            mock_logger.error.assert_called_once_with(
                "Connection test failed: Database connection failed",
                exc_info=True
            )

    def test_handle_service_unavailable_basic(self):
        """Test basic service unavailable error handling."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_service_unavailable("database")
            
            assert isinstance(exception, HTTPException)
            assert exception.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert exception.detail == "Service temporarily unavailable: database"
            assert exception.headers == {"Retry-After": "60"}
            mock_logger.error.assert_called_once_with("Service unavailable: database")

    def test_handle_service_unavailable_with_custom_detail(self):
        """Test service unavailable with custom detail and retry after."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_service_unavailable(
                "redis",
                detail="Cache service maintenance in progress",
                retry_after=300
            )
            
            assert exception.detail == "Cache service maintenance in progress"
            assert exception.headers == {"Retry-After": "300"}
            mock_logger.error.assert_called_once_with("Service unavailable: redis")


class TestRoleManagerErrorHandling:
    """Test cases for role manager error handling."""

    def test_handle_role_not_found_error(self):
        """Test handling of RoleNotFoundError."""
        error = RoleNotFoundError("Role 'admin' not found")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert "admin" in exception.detail

    def test_handle_role_not_found_error_without_quotes(self):
        """Test handling of RoleNotFoundError without quoted role name."""
        error = RoleNotFoundError("Role does not exist")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert "role" in exception.detail.lower()

    def test_handle_user_not_found_error(self):
        """Test handling of UserNotFoundError."""
        error = UserNotFoundError("User 'test@example.com' not found")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert "test@example.com" in exception.detail

    def test_handle_permission_not_found_error(self):
        """Test handling of PermissionNotFoundError."""
        error = PermissionNotFoundError("Permission 'read:users' not found")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert "read:users" in exception.detail

    def test_handle_role_manager_error_already_exists(self):
        """Test handling of RoleManagerError for already exists scenario."""
        error = RoleManagerError("Role already exists")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_409_CONFLICT
            assert "already exists" in exception.detail

    def test_handle_role_manager_error_circular_dependency(self):
        """Test handling of RoleManagerError for circular dependency."""
        error = RoleManagerError("Circular dependency detected in role hierarchy")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert "circular" in exception.detail.lower()

    def test_handle_role_manager_error_hierarchy_violation(self):
        """Test handling of RoleManagerError for hierarchy violations."""
        error = RoleManagerError("Role hierarchy violation detected")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert "hierarchy" in exception.detail.lower()

    def test_handle_role_manager_error_dependencies(self):
        """Test handling of RoleManagerError for dependencies issues."""
        error = RoleManagerError("Cannot delete role with dependencies")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert "dependencies" in exception.detail.lower()

    def test_handle_role_manager_error_assigned_to(self):
        """Test handling of RoleManagerError for assigned to issues."""
        error = RoleManagerError("Role is assigned to active users")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert "assigned to" in exception.detail.lower()

    def test_handle_role_manager_error_generic_validation(self):
        """Test handling of generic RoleManagerError validation issues."""
        error = RoleManagerError("Invalid role configuration")
        
        with patch("src.auth.exceptions.logger"):
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid role configuration" in exception.detail

    def test_handle_generic_exception(self):
        """Test handling of generic exceptions."""
        error = RuntimeError("Unexpected error")
        
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = AuthExceptionHandler.handle_role_manager_error(error)
            
            assert exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Internal server error" in exception.detail
            mock_logger.error.assert_called_once()


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    def test_authentication_required_basic(self):
        """Test authentication_required convenience function."""
        with patch("src.auth.exceptions.logger"):
            exception = authentication_required()
            
            assert exception.status_code == status.HTTP_401_UNAUTHORIZED
            assert exception.detail == "Authentication required"
            assert exception.headers == {"WWW-Authenticate": "Bearer"}

    def test_authentication_required_with_user(self):
        """Test authentication_required with user identifier."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = authentication_required("user123")
            
            assert exception.status_code == status.HTTP_401_UNAUTHORIZED
            mock_logger.warning.assert_called_once()
            assert "user123" in mock_logger.warning.call_args[0][0]

    def test_permission_denied_function(self):
        """Test permission_denied convenience function."""
        with patch("src.auth.exceptions.logger"):
            exception = permission_denied("admin:delete", "user456")
            
            assert exception.status_code == status.HTTP_403_FORBIDDEN
            assert "admin:delete required" in exception.detail

    def test_role_not_found_function(self):
        """Test role_not_found convenience function."""
        with patch("src.auth.exceptions.logger"):
            exception = role_not_found("admin")
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert "Role 'admin' not found" in exception.detail

    def test_user_not_found_function(self):
        """Test user_not_found convenience function."""
        with patch("src.auth.exceptions.logger"):
            exception = user_not_found("test@example.com")
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert "User 'test@example.com' not found" in exception.detail

    def test_permission_not_found_function(self):
        """Test permission_not_found convenience function."""
        with patch("src.auth.exceptions.logger"):
            exception = permission_not_found("read:users")
            
            assert exception.status_code == status.HTTP_404_NOT_FOUND
            assert "Permission 'read:users' not found" in exception.detail

    def test_validation_failed_basic(self):
        """Test validation_failed convenience function."""
        with patch("src.auth.exceptions.logger"):
            exception = validation_failed("Invalid email format")
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert exception.detail == "Invalid email format"

    def test_validation_failed_with_field(self):
        """Test validation_failed with field name."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = validation_failed("Too short", "password")
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert exception.detail == "Too short"
            mock_logger.info.assert_called_once()
            assert "password" in mock_logger.info.call_args[0][0]

    def test_already_exists_function(self):
        """Test already_exists convenience function."""
        with patch("src.auth.exceptions.logger"):
            exception = already_exists("role", "admin")
            
            assert exception.status_code == status.HTTP_409_CONFLICT
            assert "Role 'admin' already exists" in exception.detail

    def test_operation_failed_basic(self):
        """Test operation_failed convenience function."""
        test_error = ValueError("Database error")
        
        with patch("src.auth.exceptions.logger") as mock_logger:
            exception = operation_failed("Create user", test_error)
            
            assert exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert exception.detail == "Internal server error"
            mock_logger.error.assert_called_once()

    def test_operation_failed_with_expose_details(self):
        """Test operation_failed with exposed error details."""
        test_error = ConnectionError("Network timeout")
        
        with patch("src.auth.exceptions.logger"):
            exception = operation_failed("Database connection", test_error, expose_details=True)
            
            assert exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Network timeout" in exception.detail


class TestLoggingIntegration:
    """Test cases for logging integration."""

    def test_logging_levels_are_appropriate(self):
        """Test that appropriate logging levels are used for different error types."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            # Authentication and permission errors should be warnings (security events)
            AuthExceptionHandler.handle_authentication_error()
            AuthExceptionHandler.handle_permission_error()
            AuthExceptionHandler.handle_rate_limit_error()
            
            # Not found and validation errors should be info level
            AuthExceptionHandler.handle_not_found_error("user", "test")
            AuthExceptionHandler.handle_validation_error("Invalid input")
            AuthExceptionHandler.handle_conflict_error("Already exists")
            
            # Internal and service errors should be error level
            AuthExceptionHandler.handle_internal_error("Operation", Exception("test"))
            AuthExceptionHandler.handle_service_unavailable("database")
            
            # Check warning calls for security events
            warning_calls = mock_logger.warning.call_args_list
            assert len(warning_calls) == 3
            
            # Check info calls for user errors
            info_calls = mock_logger.info.call_args_list
            assert len(info_calls) == 3
            
            # Check error calls for system errors
            error_calls = mock_logger.error.call_args_list
            assert len(error_calls) == 2

    def test_sensitive_information_not_logged(self):
        """Test that sensitive information is properly handled in logs."""
        with patch("src.auth.exceptions.logger") as mock_logger:
            # Test that internal error details are logged but not exposed
            sensitive_error = ValueError("Database password: secret123")
            
            AuthExceptionHandler.handle_internal_error(
                "Database connection",
                sensitive_error,
                expose_error=False
            )
            
            # Error should be logged with full details
            error_call = mock_logger.error.call_args_list[0]
            assert "secret123" in error_call[0][0]
            
            # But exception detail should not contain sensitive info
            exception = AuthExceptionHandler.handle_internal_error(
                "Database connection",
                sensitive_error,
                expose_error=False
            )
            assert "secret123" not in exception.detail
            assert exception.detail == "Internal server error"


class TestExceptionHeaders:
    """Test cases for HTTP exception headers."""

    def test_authentication_error_has_www_authenticate_header(self):
        """Test that authentication errors include WWW-Authenticate header."""
        exception = AuthExceptionHandler.handle_authentication_error()
        
        assert "WWW-Authenticate" in exception.headers
        assert exception.headers["WWW-Authenticate"] == "Bearer"

    def test_rate_limit_error_has_retry_after_header(self):
        """Test that rate limit errors include Retry-After header."""
        exception = AuthExceptionHandler.handle_rate_limit_error(retry_after=120)
        
        assert "Retry-After" in exception.headers
        assert exception.headers["Retry-After"] == "120"

    def test_service_unavailable_has_retry_after_header(self):
        """Test that service unavailable errors include Retry-After header."""
        exception = AuthExceptionHandler.handle_service_unavailable(
            "database", 
            retry_after=300
        )
        
        assert "Retry-After" in exception.headers
        assert exception.headers["Retry-After"] == "300"

    def test_other_errors_no_headers(self):
        """Test that other error types don't include unexpected headers."""
        exceptions = [
            AuthExceptionHandler.handle_permission_error(),
            AuthExceptionHandler.handle_not_found_error("user", "test"),
            AuthExceptionHandler.handle_validation_error("Invalid"),
            AuthExceptionHandler.handle_conflict_error("Conflict"),
            AuthExceptionHandler.handle_internal_error("Op", Exception("test")),
        ]
        
        for exception in exceptions:
            assert not hasattr(exception, 'headers') or exception.headers is None


class TestEdgeCases:
    """Test cases for edge cases and error conditions."""

    def test_empty_string_parameters(self):
        """Test handling of empty string parameters."""
        with patch("src.auth.exceptions.logger"):
            # Empty strings should be handled gracefully
            exception1 = AuthExceptionHandler.handle_not_found_error("", "")
            exception2 = AuthExceptionHandler.handle_permission_error("", "")
            exception3 = AuthExceptionHandler.handle_validation_error("", "")
            
            assert exception1.status_code == status.HTTP_404_NOT_FOUND
            assert exception2.status_code == status.HTTP_403_FORBIDDEN
            assert exception3.status_code == status.HTTP_400_BAD_REQUEST

    def test_none_parameters_handling(self):
        """Test handling of None parameters where optional."""
        with patch("src.auth.exceptions.logger"):
            # Functions should handle None values gracefully
            exception = AuthExceptionHandler.handle_validation_error(
                "Test error",
                field_name=None,
                log_additional=None
            )
            
            assert exception.status_code == status.HTTP_400_BAD_REQUEST
            assert exception.detail == "Test error"

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters in messages."""
        with patch("src.auth.exceptions.logger"):
            unicode_message = "User 'tëst@éxämplé.cøm' not found 🚫"
            
            exception = AuthExceptionHandler.handle_not_found_error(
                "user",
                detail=unicode_message
            )
            
            assert exception.detail == unicode_message
            assert exception.status_code == status.HTTP_404_NOT_FOUND

    def test_very_long_messages(self):
        """Test handling of very long error messages."""
        with patch("src.auth.exceptions.logger"):
            long_message = "x" * 1000  # Very long message
            
            exception = AuthExceptionHandler.handle_validation_error(long_message)
            
            assert exception.detail == long_message
            assert exception.status_code == status.HTTP_400_BAD_REQUEST