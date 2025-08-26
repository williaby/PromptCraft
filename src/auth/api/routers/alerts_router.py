"""
Alerts Router Module

Handles security alert management endpoints.
Decomposed from security_dashboard_endpoints.py for focused responsibility.

Endpoints:
    GET /alerts - Get security alerts list
    POST /alerts/{alert_id}/acknowledge - Acknowledge alert
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.alert_engine import AlertEngine
from ...services.security_integration import SecurityIntegrationService


class AlertSummaryResponse(BaseModel):
    """Response model for alert summary."""

    id: UUID = Field(..., description="Alert ID")
    alert_type: str = Field(..., description="Alert type")
    severity: str = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    timestamp: datetime = Field(..., description="Alert timestamp")
    affected_user: str | None = Field(None, description="Affected user")
    affected_ip: str | None = Field(None, description="Affected IP address")
    acknowledged: bool = Field(..., description="Alert acknowledgment status")
    risk_score: int = Field(..., description="Risk score")


# Create router
router = APIRouter(prefix="/alerts", tags=["alerts"])

# Dependency to get security integration service
_security_integration_service: SecurityIntegrationService | None = None
_alert_engine: AlertEngine | None = None


async def get_security_service() -> SecurityIntegrationService:
    """Get security integration service instance."""
    global _security_integration_service
    if not _security_integration_service:
        _security_integration_service = SecurityIntegrationService()
    return _security_integration_service


async def get_alert_engine() -> AlertEngine:
    """Get alert engine instance."""
    global _alert_engine
    if not _alert_engine:
        _alert_engine = AlertEngine()
    return _alert_engine


@router.get("/", response_model=list[AlertSummaryResponse])
async def get_security_alerts(
    service: SecurityIntegrationService = Depends(get_security_service),
    alert_engine: AlertEngine = Depends(get_alert_engine),
    severity: str | None = Query(None, regex="^(low|medium|high|critical)$", description="Filter by severity"),
    acknowledged: bool | None = Query(None, description="Filter by acknowledgment status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum alerts to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> list[AlertSummaryResponse]:
    """Get list of security alerts with filtering and pagination.

    Args:
        service: Security integration service
        alert_engine: Alert engine instance
        severity: Filter alerts by severity level
        acknowledged: Filter by acknowledgment status
        limit: Maximum number of alerts to return
        offset: Number of alerts to skip (pagination)

    Returns:
        List of alert summaries
    """
    try:
        # Get alerts from alert engine
        alerts = await alert_engine.get_recent_alerts(limit=limit + offset)

        # Apply filters
        filtered_alerts = []
        for alert in alerts:
            # Skip alerts before offset
            if len(filtered_alerts) < offset:
                continue

            # Apply severity filter
            if severity and alert.severity.value.lower() != severity:
                continue

            # Apply acknowledged filter
            if acknowledged is not None and alert.acknowledged != acknowledged:
                continue

            # Convert to response model
            alert_response = AlertSummaryResponse(
                id=alert.id,
                alert_type=alert.alert_type,
                severity=alert.severity.value,
                title=alert.title,
                timestamp=alert.timestamp,
                affected_user=alert.affected_user,
                affected_ip=alert.affected_ip,
                acknowledged=alert.acknowledged,
                risk_score=alert.risk_score,
            )

            filtered_alerts.append(alert_response)

            # Stop when we have enough results
            if len(filtered_alerts) >= limit:
                break

        return filtered_alerts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve security alerts: {e!s}")


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: UUID,
    background_tasks: BackgroundTasks,
    alert_engine: AlertEngine = Depends(get_alert_engine),
    service: SecurityIntegrationService = Depends(get_security_service),
    user_id: str = Query(..., description="User acknowledging the alert"),
    notes: str | None = Query(None, description="Acknowledgment notes"),
):
    """Acknowledge a security alert.

    Args:
        alert_id: Alert ID to acknowledge
        background_tasks: FastAPI background tasks
        alert_engine: Alert engine instance
        service: Security integration service
        user_id: ID of user acknowledging alert
        notes: Optional notes about acknowledgment

    Returns:
        Success message with acknowledgment details
    """
    try:
        # Get the alert to verify it exists
        alert = await alert_engine.get_alert_by_id(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert with ID {alert_id} not found")

        if alert.acknowledged:
            raise HTTPException(status_code=409, detail=f"Alert {alert_id} is already acknowledged")

        # Acknowledge the alert
        await alert_engine.acknowledge_alert(alert_id, user_id, notes)

        # Log the acknowledgment
        background_tasks.add_task(
            service.log_security_event,
            event_type="alert_acknowledged",
            user_id=user_id,
            details={
                "alert_id": str(alert_id),
                "alert_type": alert.alert_type,
                "severity": alert.severity.value,
                "notes": notes,
            },
        )

        return {
            "message": "Alert acknowledged successfully",
            "alert_id": str(alert_id),
            "acknowledged_by": user_id,
            "acknowledged_at": datetime.now().isoformat(),
            "notes": notes,
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {e!s}")
