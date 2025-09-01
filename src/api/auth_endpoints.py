"""Authentication API endpoints for AUTH-2 service token management.

This module provides FastAPI endpoints for service token management including:
- Token creation and management (admin-only)
- Current user/service token information
- Authentication status and health checks
- Usage analytics and audit logging
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.auth import require_role
from src.auth.middleware import ServiceTokenUser, require_authentication
from src.auth.models import AuthenticatedUser
from src.auth.service_token_manager import ServiceTokenManager
from src.utils.datetime_compat import UTC, timedelta


def require_admin_role(request: Request) -> AuthenticatedUser:
    """Dependency to require admin role for endpoints."""
    return require_role(request, "admin")


def get_service_token_manager() -> ServiceTokenManager:
    """Dependency to get ServiceTokenManager instance."""
    return ServiceTokenManager()


class TokenCreationRequest(BaseModel):
    """Request model for creating service tokens."""

    token_name: str = Field(..., description="Unique name for the service token")
    permissions: list[str] = Field(default=[], description="List of permissions for the token")
    expires_days: int | None = Field(None, description="Token expires in N days (optional)")
    purpose: str | None = Field(None, description="Purpose of this token")
    environment: str | None = Field(None, description="Environment (production, staging, dev)")


class TokenCreationResponse(BaseModel):
    """Response model for token creation."""

    token_id: str = Field(..., description="Unique token identifier")
    token_name: str = Field(..., description="Token name")
    token_value: str = Field(..., description="Service token value (save securely)")
    expires_at: datetime | None = Field(None, description="Token expiration date")
    metadata: dict = Field(..., description="Token metadata including permissions")


class TokenInfo(BaseModel):
    """Basic token information (without sensitive data)."""

    token_id: str = Field(..., description="Token identifier")
    token_name: str = Field(..., description="Token name")
    usage_count: int = Field(..., description="Number of times token has been used")
    last_used: datetime | None = Field(None, description="Last usage timestamp")
    is_active: bool = Field(..., description="Whether token is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    permissions: list[str] = Field(..., description="Token permissions")


class CurrentUserResponse(BaseModel):
    """Response model for current user information."""

    user_type: str = Field(..., description="Type of authentication (jwt_user or service_token)")
    email: str | None = Field(None, description="User email (JWT auth only)")
    role: str | None = Field(None, description="User role (JWT auth only)")
    token_name: str | None = Field(None, description="Token name (service token auth only)")
    token_id: str | None = Field(None, description="Token ID (service token auth only)")
    permissions: list[str] = Field(default=[], description="User/token permissions")
    usage_count: int | None = Field(None, description="Token usage count (service token only)")


class AuthHealthResponse(BaseModel):
    """Authentication system health response."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    database_status: str = Field(..., description="Database connectivity status")
    active_tokens: int = Field(..., description="Number of active service tokens")
    recent_authentications: int = Field(..., description="Recent authentication count")


# Create router
auth_router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@auth_router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    request: Request,  # noqa: ARG001
    current_user: AuthenticatedUser | ServiceTokenUser = Depends(require_authentication),
) -> CurrentUserResponse:
    """Get current authenticated user or service token information.

    This endpoint returns information about the currently authenticated user
    or service token. It works with both JWT authentication and service tokens.
    """
    if isinstance(current_user, ServiceTokenUser):
        # Service token authentication
        return CurrentUserResponse(
            user_type="service_token",
            token_name=current_user.token_name,
            token_id=current_user.token_id,
            permissions=current_user.metadata.get("permissions", []),
            usage_count=current_user.usage_count,
        )
    
    # JWT user authentication
    if current_user is None or not isinstance(current_user, AuthenticatedUser):
        raise HTTPException(status_code=401, detail="User authentication failed")
    
    return CurrentUserResponse(
        user_type="jwt_user",
        email=current_user.email,
        role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        permissions=[],  # JWT users get permissions through roles
    )


@auth_router.get("/health", response_model=AuthHealthResponse)
async def auth_health_check(
    manager: ServiceTokenManager = Depends(get_service_token_manager),
) -> AuthHealthResponse:
    """Authentication system health check.

    This endpoint provides health information about the authentication system
    including database connectivity and service token statistics.
    """

    try:
        # Get token analytics for health metrics
        analytics = await manager.get_token_usage_analytics(days=1)

        database_status = "healthy"
        if analytics and "summary" in analytics:
            active_tokens = analytics["summary"]["active_tokens"]
            recent_authentications = analytics["summary"]["total_usage"]
        else:
            active_tokens = -1
            recent_authentications = -1

    except Exception as e:
        database_status = f"error: {e!s}"
        active_tokens = -1
        recent_authentications = -1

    # Determine overall status
    status = "healthy" if database_status == "healthy" else "degraded"

    return AuthHealthResponse(
        status=status,
        timestamp=datetime.now(UTC),
        database_status=database_status,
        active_tokens=active_tokens,
        recent_authentications=recent_authentications,
    )


@auth_router.post("/tokens", response_model=TokenCreationResponse)
async def create_service_token(
    request: Request,  # noqa: ARG001
    token_request: TokenCreationRequest,
    current_user: AuthenticatedUser = Depends(require_admin_role),
    manager: ServiceTokenManager = Depends(get_service_token_manager),
) -> TokenCreationResponse:
    """Create a new service token (admin only).

    This endpoint allows administrators to create new service tokens for
    non-interactive API access. The token value is only returned once.
    """

    # Build token metadata
    metadata = {
        "permissions": token_request.permissions,
        "created_by": current_user.email,
        "purpose": token_request.purpose or "Created via API",
        "environment": token_request.environment or "production",
        "created_via": "admin_api",
    }

    # Calculate expiration
    expires_at = None
    if token_request.expires_days:
        expires_at = datetime.now(UTC) + timedelta(days=token_request.expires_days)

    try:
        result = await manager.create_service_token(
            token_name=token_request.token_name,
            metadata=metadata,
            expires_at=expires_at,
            is_active=True,
        )

        if result is None:
            raise HTTPException(status_code=500, detail="Failed to create service token")

        token_value, token_id = result

        return TokenCreationResponse(
            token_id=token_id,
            token_name=token_request.token_name,
            token_value=token_value,
            expires_at=expires_at,
            metadata=metadata,
        )

    except ValueError as e:
        # Token name already exists
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        # Other errors
        raise HTTPException(status_code=500, detail=f"Failed to create token: {e!s}") from e


@auth_router.delete("/tokens/{token_identifier}")
async def revoke_service_token(
    request: Request,  # noqa: ARG001
    token_identifier: str,
    reason: str = Query(..., description="Reason for revocation"),
    current_user: AuthenticatedUser = Depends(require_admin_role),
    manager: ServiceTokenManager = Depends(get_service_token_manager),
) -> dict[str, str]:
    """Revoke a service token (admin only).

    This endpoint allows administrators to revoke service tokens.
    The token will be immediately deactivated and cannot be used for authentication.
    """
    try:
        success = await manager.revoke_service_token(
            token_identifier=token_identifier,
            revocation_reason=f"{reason} (revoked by {current_user.email} via API)",
        )

        if success:
            return {
                "status": "success",
                "message": f"Token '{token_identifier}' has been revoked",
                "revoked_by": current_user.email,
                "reason": reason,
            }
        raise HTTPException(status_code=404, detail=f"Token '{token_identifier}' not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke token: {e!s}") from e


@auth_router.post("/tokens/{token_identifier}/rotate")
async def rotate_service_token(
    request: Request,  # noqa: ARG001
    token_identifier: str,
    reason: str = Query("manual_rotation", description="Reason for rotation"),
    current_user: AuthenticatedUser = Depends(require_admin_role),
    manager: ServiceTokenManager = Depends(get_service_token_manager),
) -> TokenCreationResponse:
    """Rotate a service token (admin only).

    This endpoint creates a new token with the same permissions and deactivates the old one.
    The new token value is only returned once.
    """
    try:
        result = await manager.rotate_service_token(
            token_identifier=token_identifier,
            rotation_reason=f"{reason} (rotated by {current_user.email} via API)",
        )

        if result:
            new_token_value, new_token_id = result

            # Get the new token info for response
            analytics = await manager.get_token_usage_analytics(token_identifier=new_token_id)

            if analytics and "error" not in analytics:
                return TokenCreationResponse(
                    token_id=new_token_id,
                    token_name=analytics.get("token_name", "rotated_token"),
                    token_value=new_token_value,
                    expires_at=None,  # Will be same as original
                    metadata={"rotated_by": current_user.email, "rotation_reason": reason},
                )
            return TokenCreationResponse(
                token_id=new_token_id,
                token_name="rotated_token",  # nosec B106  # noqa: S106
                token_value=new_token_value,
                expires_at=None,
                metadata={"rotated_by": current_user.email, "rotation_reason": reason},
            )
        raise HTTPException(status_code=404, detail=f"Token '{token_identifier}' not found or inactive")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rotate token: {e!s}") from e


@auth_router.get("/tokens", response_model=list[TokenInfo])
async def list_service_tokens(
    request: Request,  # noqa: ARG001
    current_user: AuthenticatedUser = Depends(require_admin_role),  # noqa: ARG001
    manager: ServiceTokenManager = Depends(get_service_token_manager),
) -> list[TokenInfo]:
    """List all service tokens (admin only).

    This endpoint returns information about all service tokens without
    sensitive data like token values or hashes.
    """
    try:
        # Get comprehensive analytics to list all tokens
        analytics = await manager.get_token_usage_analytics(days=365)

        tokens = []

        # Process top tokens (active tokens)
        if analytics and "top_tokens" in analytics:
            for token_data in analytics.get("top_tokens", []):
                # Get detailed info for each token
                token_analytics = await manager.get_token_usage_analytics(token_identifier=token_data["token_name"])

                if token_analytics and "error" not in token_analytics:
                    permissions: list[str] = []  # Would need to fetch from database

                    tokens.append(
                        TokenInfo(
                            token_id="",  # We don't expose token IDs in listings  # nosec B106
                            token_name=token_analytics["token_name"],
                            usage_count=token_analytics["usage_count"],
                            last_used=(
                                datetime.fromisoformat(token_analytics["last_used"])
                                if token_analytics["last_used"]
                                else None
                            ),
                            is_active=token_analytics["is_active"],
                            created_at=datetime.fromisoformat(token_analytics["created_at"]),
                            permissions=permissions,
                        ),
                    )

        return tokens

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tokens: {e!s}") from e


@auth_router.get("/tokens/{token_identifier}/analytics")
async def get_token_analytics(
    request: Request,  # noqa: ARG001
    token_identifier: str,
    days: int = Query(30, description="Number of days to analyze"),
    current_user: AuthenticatedUser = Depends(require_admin_role),  # noqa: ARG001
    manager: ServiceTokenManager = Depends(get_service_token_manager),
) -> dict:
    """Get detailed analytics for a specific service token (admin only).

    This endpoint provides usage analytics and recent events for a service token.
    """
    try:
        analytics = await manager.get_token_usage_analytics(token_identifier=token_identifier, days=days)

        if analytics and "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])

        return analytics or {}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {e!s}") from e


@auth_router.post("/emergency-revoke")
async def emergency_revoke_all_tokens(
    request: Request,  # noqa: ARG001
    reason: str = Query(..., description="Emergency revocation reason"),
    confirm: bool = Query(False, description="Confirmation required"),
    current_user: AuthenticatedUser = Depends(require_admin_role),
    manager: ServiceTokenManager = Depends(get_service_token_manager),
) -> dict[str, str | int]:
    """Emergency revocation of ALL service tokens (admin only).

    This is a nuclear option that deactivates ALL service tokens immediately.
    Use only in case of security incidents or system compromise.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Emergency revocation requires explicit confirmation (confirm=true)",
        )

    try:
        revoked_count = await manager.emergency_revoke_all_tokens(
            emergency_reason=f"{reason} (emergency revoked by {current_user.email} via API)",
        )

        return {
            "status": "emergency_revocation_completed",
            "tokens_revoked": revoked_count or 0,
            "revoked_by": current_user.email,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat() + "Z",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emergency revocation failed: {e!s}") from e


# System status endpoints (protected by service tokens)
system_router = APIRouter(prefix="/api/v1/system", tags=["system"])


@system_router.get("/status")
async def system_status(
    request: Request,  # noqa: ARG001
    current_user: AuthenticatedUser | ServiceTokenUser = Depends(require_authentication),
) -> dict[str, str]:
    """Get system status information.

    This endpoint requires authentication but works with both JWT and service tokens.
    Service tokens need 'system_status' permission.
    """
    # Check permissions for service tokens
    if isinstance(current_user, ServiceTokenUser):
        if not current_user.has_permission("system_status"):
            raise HTTPException(status_code=403, detail="Service token lacks 'system_status' permission")

    return {
        "status": "operational",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "version": "1.0.0",
        "authenticated_as": getattr(current_user, "email", getattr(current_user, "token_name", "unknown")),
    }


@system_router.get("/health")
async def system_health() -> dict[str, str]:
    """Public system health check (no authentication required).

    This endpoint is excluded from authentication middleware and can be used
    for basic health monitoring without credentials.
    """
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat() + "Z"}


# Audit endpoints for CI/CD logging
audit_router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@audit_router.post("/cicd-event")
async def log_cicd_event(
    request: Request,  # noqa: ARG001
    event_data: dict,
    current_user: AuthenticatedUser | ServiceTokenUser = Depends(require_authentication),
) -> dict[str, str]:
    """Log CI/CD workflow events for audit trail.

    This endpoint allows CI/CD systems to log workflow events for audit purposes.
    Service tokens need 'audit_log' permission.
    """
    # Check permissions for service tokens
    if isinstance(current_user, ServiceTokenUser):
        if not current_user.has_permission("audit_log"):
            raise HTTPException(status_code=403, detail="Service token lacks 'audit_log' permission")

    # Here you would typically log to your audit system
    # For now, we'll just acknowledge the event

    return {
        "status": "logged",
        "timestamp": datetime.now(UTC).isoformat() + "Z",
        "event_type": event_data.get("event_type", "unknown"),
        "logged_by": getattr(current_user, "email", getattr(current_user, "token_name", "unknown")),
    }
