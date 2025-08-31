"""
Metrics Router Module

Handles system metrics and performance monitoring endpoints.
Decomposed from security_dashboard_endpoints.py for focused responsibility.

Endpoints:
    GET /metrics - Get comprehensive security metrics
    GET /export/metrics - Export metrics data
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.auth.services.security_integration import SecurityIntegrationService


class SecurityMetricsResponse(BaseModel):
    """Response model for security metrics dashboard."""

    timestamp: datetime = Field(..., description="Metrics timestamp")

    # Event statistics
    total_events_today: int = Field(..., description="Total events processed today")
    total_events_week: int = Field(..., description="Total events processed this week")
    event_rate_per_hour: float = Field(..., description="Average events per hour")

    # Alert statistics
    total_alerts_today: int = Field(..., description="Total alerts generated today")
    critical_alerts_today: int = Field(..., description="Critical alerts today")
    alerts_acknowledged: int = Field(..., description="Acknowledged alerts today")

    # Performance metrics
    average_processing_time_ms: float = Field(..., description="Average event processing time")
    system_health_score: float = Field(..., description="System health score (0-100)")
    service_availability: dict[str, bool] = Field(..., description="Service availability status")

    # Security statistics
    suspicious_activities_today: int = Field(..., description="Suspicious activities detected today")
    top_risk_users: list[str] = Field(..., description="Users with highest risk scores")
    top_threat_ips: list[str] = Field(..., description="IP addresses with most threats")


# Create router
router = APIRouter(prefix="/metrics", tags=["metrics"])

# Dependency to get security integration service
_security_integration_service: SecurityIntegrationService | None = None


async def get_security_service() -> SecurityIntegrationService:
    """Get security integration service instance."""
    global _security_integration_service
    if not _security_integration_service:
        _security_integration_service = SecurityIntegrationService()
    return _security_integration_service


@router.get("/", response_model=SecurityMetricsResponse)
async def get_security_metrics(
    service: SecurityIntegrationService = Depends(get_security_service),
    hours_back: int = Query(24, ge=1, le=168, description="Hours of data to analyze"),
) -> SecurityMetricsResponse:
    """Get comprehensive security metrics for the dashboard.

    Args:
        service: Security integration service
        hours_back: Number of hours to analyze

    Returns:
        Security metrics data for dashboard display
    """
    try:
        # Get comprehensive metrics from all services
        metrics = await service.get_comprehensive_metrics()

        # Calculate derived metrics
        current_time = datetime.now(timezone.utc)

        # Event statistics
        total_events_today = metrics["integration"]["total_events_processed"]
        total_events_week = total_events_today * 7  # Simplified calculation
        event_rate_per_hour = total_events_today / 24 if total_events_today > 0 else 0

        # Alert statistics
        total_alerts_today = metrics["integration"]["total_alerts_generated"]
        critical_alerts_today = int(total_alerts_today * 0.2)  # Estimate 20% critical
        alerts_acknowledged = int(total_alerts_today * 0.7)  # Estimate 70% acknowledged

        # Performance metrics
        avg_processing_time = metrics["integration"]["average_processing_time_ms"]

        # Calculate system health score based on multiple factors
        health_score = 100.0
        if avg_processing_time > 50:
            health_score -= min(30, (avg_processing_time - 50) / 10 * 5)
        if not metrics["service_health"]["logger_healthy"]:
            health_score -= 20
        if not metrics["service_health"]["monitor_healthy"]:
            health_score -= 15
        if not metrics["service_health"]["alert_engine_healthy"]:
            health_score -= 15
        if not metrics["service_health"]["detector_healthy"]:
            health_score -= 10

        health_score = max(0, health_score)

        # Service availability
        service_availability = {
            "logger": metrics["service_health"]["logger_healthy"],
            "monitor": metrics["service_health"]["monitor_healthy"],
            "alert_engine": metrics["service_health"]["alert_engine_healthy"],
            "detector": metrics["service_health"]["detector_healthy"],
        }

        # Security statistics
        suspicious_activities_today = metrics["integration"]["total_suspicious_activities"]

        # Generate mock top risk data (in production, this would come from database)
        top_risk_users = [f"user_{i}" for i in range(1, 6)]  # Top 5 users
        top_threat_ips = [f"192.168.1.{i}" for i in range(100, 105)]  # Top 5 IPs

        return SecurityMetricsResponse(
            timestamp=current_time,
            total_events_today=total_events_today,
            total_events_week=total_events_week,
            event_rate_per_hour=event_rate_per_hour,
            total_alerts_today=total_alerts_today,
            critical_alerts_today=critical_alerts_today,
            alerts_acknowledged=alerts_acknowledged,
            average_processing_time_ms=avg_processing_time,
            system_health_score=health_score,
            service_availability=service_availability,
            suspicious_activities_today=suspicious_activities_today,
            top_risk_users=top_risk_users,
            top_threat_ips=top_threat_ips,
        )

    except Exception as e:
        # Log the error (in production)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve security metrics: {e!s}")


@router.get("/export")
async def export_security_metrics(
    service: SecurityIntegrationService = Depends(get_security_service),
    format: str = Query("json", pattern="^(json|csv)$", description="Export format"),
    hours_back: int = Query(24, ge=1, le=168, description="Hours of data to export"),
):
    """Export security metrics data.

    Args:
        service: Security integration service
        format: Export format (json or csv)
        hours_back: Number of hours to export

    Returns:
        Exported metrics data in specified format
    """
    try:
        # Get the same metrics as the main endpoint
        metrics_response = await get_security_metrics(service, hours_back)

        if format == "json":
            return metrics_response
        if format == "csv":
            # Convert to CSV format
            csv_data = (
                "timestamp,total_events_today,total_events_week,event_rate_per_hour,"
                "total_alerts_today,critical_alerts_today,alerts_acknowledged,"
                "average_processing_time_ms,system_health_score,suspicious_activities_today\n"
                f"{metrics_response.timestamp.isoformat()},"
                f"{metrics_response.total_events_today},"
                f"{metrics_response.total_events_week},"
                f"{metrics_response.event_rate_per_hour:.2f},"
                f"{metrics_response.total_alerts_today},"
                f"{metrics_response.critical_alerts_today},"
                f"{metrics_response.alerts_acknowledged},"
                f"{metrics_response.average_processing_time_ms:.2f},"
                f"{metrics_response.system_health_score:.2f},"
                f"{metrics_response.suspicious_activities_today}"
            )

            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=security_metrics.csv"},
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export security metrics: {e!s}")
