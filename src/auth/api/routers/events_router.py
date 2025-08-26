"""
Events Router Module

Handles security event search and management endpoints.
Decomposed from security_dashboard_endpoints.py for focused responsibility.

Endpoints:
    POST /events/search - Search security events
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ...models import SecurityEventSeverity, SecurityEventType
from ...services.security_integration import SecurityIntegrationService


class SecurityEventSearchRequest(BaseModel):
    """Request model for security event search."""

    start_date: datetime = Field(..., description="Search start date")
    end_date: datetime = Field(..., description="Search end date")
    event_types: list[SecurityEventType] | None = Field(None, description="Event types to filter")
    severity_levels: list[SecurityEventSeverity] | None = Field(None, description="Severity levels to filter")
    user_id: str | None = Field(None, description="User ID to filter")
    ip_address: str | None = Field(None, description="IP address to filter")
    risk_score_min: int | None = Field(None, ge=0, le=100, description="Minimum risk score")
    risk_score_max: int | None = Field(None, ge=0, le=100, description="Maximum risk score")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")


class SecurityEventResponse(BaseModel):
    """Response model for security event."""

    id: str = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    severity: str = Field(..., description="Event severity")
    timestamp: datetime = Field(..., description="Event timestamp")
    user_id: str | None = Field(None, description="Associated user ID")
    ip_address: str | None = Field(None, description="Source IP address")
    user_agent: str | None = Field(None, description="User agent string")
    risk_score: int = Field(..., description="Event risk score")
    details: dict = Field(..., description="Event details")
    tags: list[str] = Field(..., description="Event tags")


class SecurityEventSearchResponse(BaseModel):
    """Response model for security event search results."""

    events: list[SecurityEventResponse] = Field(..., description="Found events")
    total_count: int = Field(..., description="Total events matching criteria")
    search_time_ms: float = Field(..., description="Search execution time")
    has_more: bool = Field(..., description="Whether more results are available")


# Create router
router = APIRouter(prefix="/events", tags=["events"])

# Dependencies
_security_integration_service: SecurityIntegrationService | None = None


async def get_security_service() -> SecurityIntegrationService:
    """Get security integration service instance."""
    global _security_integration_service
    if not _security_integration_service:
        _security_integration_service = SecurityIntegrationService()
    return _security_integration_service


@router.post("/search", response_model=SecurityEventSearchResponse)
async def search_security_events(
    search_request: SecurityEventSearchRequest,
    service: SecurityIntegrationService = Depends(get_security_service),
) -> SecurityEventSearchResponse:
    """Search security events with advanced filtering and pagination.

    Args:
        search_request: Search criteria and filters
        service: Security integration service

    Returns:
        Search results with matching events and metadata
    """
    try:
        start_time = datetime.now()

        # Validate date range
        if search_request.end_date <= search_request.start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        # Validate risk score range if both are provided
        if (
            search_request.risk_score_min is not None
            and search_request.risk_score_max is not None
            and search_request.risk_score_min > search_request.risk_score_max
        ):
            raise HTTPException(
                status_code=400,
                detail="Minimum risk score must be less than or equal to maximum risk score",
            )

        # Build search filters
        filters = {
            "start_date": search_request.start_date,
            "end_date": search_request.end_date,
            "limit": search_request.limit,
            "offset": search_request.offset,
        }

        # Add optional filters
        if search_request.event_types:
            filters["event_types"] = [et.value for et in search_request.event_types]

        if search_request.severity_levels:
            filters["severity_levels"] = [sl.value for sl in search_request.severity_levels]

        if search_request.user_id:
            filters["user_id"] = search_request.user_id

        if search_request.ip_address:
            filters["ip_address"] = search_request.ip_address

        if search_request.risk_score_min is not None:
            filters["risk_score_min"] = search_request.risk_score_min

        if search_request.risk_score_max is not None:
            filters["risk_score_max"] = search_request.risk_score_max

        # Perform the search (in production, this would query a database or search index)
        search_results = await service.search_security_events(filters)

        # Convert results to response format
        events = []
        for event_data in search_results.get("events", []):
            event_response = SecurityEventResponse(
                id=event_data["id"],
                event_type=event_data["event_type"],
                severity=event_data["severity"],
                timestamp=event_data["timestamp"],
                user_id=event_data.get("user_id"),
                ip_address=event_data.get("ip_address"),
                user_agent=event_data.get("user_agent"),
                risk_score=event_data.get("risk_score", 0),
                details=event_data.get("details", {}),
                tags=event_data.get("tags", []),
            )
            events.append(event_response)

        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000

        # Determine if there are more results
        total_count = search_results.get("total_count", len(events))
        has_more = (search_request.offset + len(events)) < total_count

        return SecurityEventSearchResponse(
            events=events,
            total_count=total_count,
            search_time_ms=search_time,
            has_more=has_more,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search security events: {e!s}")
