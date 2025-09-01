"""
Charts Router Module

Handles dashboard visualization and chart data endpoints.
Decomposed from security_dashboard_endpoints.py for focused responsibility.

Endpoints:
    GET /charts/event-timeline - Get event timeline chart data
    GET /charts/risk-distribution - Get risk distribution chart data
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.auth.services.security_integration import SecurityIntegrationService
from src.utils.datetime_compat import UTC, timedelta

logger = logging.getLogger(__name__)


class TimelineDataPoint(BaseModel):
    """Data point for timeline charts."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    value: int = Field(..., description="Data point value")
    label: str | None = Field(None, description="Data point label")


class EventTimelineResponse(BaseModel):
    """Response model for event timeline chart."""

    title: str = Field(..., description="Chart title")
    time_range: str = Field(..., description="Time range description")
    data_points: list[TimelineDataPoint] = Field(..., description="Timeline data points")
    total_events: int = Field(..., description="Total events in period")
    peak_hour: str | None = Field(None, description="Peak activity hour")


class RiskDistributionData(BaseModel):
    """Risk distribution data point."""

    risk_level: str = Field(..., description="Risk level category")
    count: int = Field(..., description="Number of items in category")
    percentage: float = Field(..., description="Percentage of total")
    color: str = Field(..., description="Display color for category")


class RiskDistributionResponse(BaseModel):
    """Response model for risk distribution chart."""

    title: str = Field(..., description="Chart title")
    total_items: int = Field(..., description="Total items analyzed")
    distribution: list[RiskDistributionData] = Field(..., description="Risk distribution data")
    risk_summary: dict[str, float] = Field(..., description="Risk level summary")


# Create router
router = APIRouter(prefix="/charts", tags=["charts"])


# Dependencies
def get_security_service() -> SecurityIntegrationService:
    """Get security integration service instance."""
    return SecurityIntegrationService()


@router.get("/event-timeline", response_model=EventTimelineResponse)
async def get_event_timeline_chart(
    service: SecurityIntegrationService = Depends(get_security_service),  # noqa: ARG001
    hours_back: int = Query(24, ge=1, le=168, description="Hours of data to chart"),
    granularity: str = Query("hour", regex="^(hour|day)$", description="Data granularity"),
) -> EventTimelineResponse:
    """Get event timeline chart data for dashboard visualization.

    Args:
        service: Security integration service
        hours_back: Number of hours to include in timeline
        granularity: Time granularity (hour or day)

    Returns:
        Event timeline chart data with data points and metadata
    """
    try:
        # Calculate time range
        end_time = datetime.now(UTC)

        # Generate mock event timeline data
        data_points = []
        total_events = 0
        peak_count = 0
        peak_hour = None

        # Generate data points based on granularity
        if granularity == "hour":
            interval_delta = timedelta(hours=1)
            num_points = min(hours_back, 48)  # Limit to 48 hours max for hourly
        else:  # day
            interval_delta = timedelta(days=1)
            num_points = min(hours_back // 24, 30)  # Limit to 30 days max for daily

        # Generate mock timeline data with realistic patterns
        for i in range(num_points):
            timestamp = end_time - (interval_delta * i)

            # Generate realistic event counts with patterns
            base_count = 15 + (i % 7) * 3  # Weekly pattern
            time_factor = 1.0

            if granularity == "hour":
                # Simulate daily activity patterns (lower at night)
                hour = timestamp.hour
                if hour >= 22 or hour <= 6:
                    time_factor = 0.3  # Night time low activity
                elif 8 <= hour <= 17:
                    time_factor = 1.5  # Business hours high activity

            event_count = int(base_count * time_factor * (0.8 + (i % 5) * 0.1))  # Add variation

            data_point = TimelineDataPoint(
                timestamp=timestamp,
                value=event_count,
                label=f"{event_count} events",
            )
            data_points.append(data_point)

            total_events += event_count

            # Track peak activity
            if event_count > peak_count:
                peak_count = event_count
                peak_hour = timestamp.strftime("%H:00") if granularity == "hour" else timestamp.strftime("%Y-%m-%d")

        # Sort data points by timestamp (oldest first)
        data_points.sort(key=lambda x: x.timestamp)

        # Generate time range description
        if hours_back <= 24:
            time_range = f"Last {hours_back} hours"
        elif hours_back <= 168:  # 1 week
            days = hours_back // 24
            time_range = f"Last {days} day{'s' if days > 1 else ''}"
        else:
            weeks = hours_back // 168
            time_range = f"Last {weeks} week{'s' if weeks > 1 else ''}"

        return EventTimelineResponse(
            title=f"Security Events Timeline - {time_range}",
            time_range=time_range,
            data_points=data_points,
            total_events=total_events,
            peak_hour=peak_hour,
        )

    except Exception as e:
        logger.error(f"Event timeline chart generation failed: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to get event timeline chart") from e


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
async def get_risk_distribution_chart(
    service: SecurityIntegrationService = Depends(get_security_service),  # noqa: ARG001
    analysis_type: str = Query("users", regex="^(users|events|alerts)$", description="Type of items to analyze"),
) -> RiskDistributionResponse:
    """Get risk distribution chart data for dashboard visualization.

    Args:
        service: Security integration service
        analysis_type: Type of analysis (users, events, or alerts)

    Returns:
        Risk distribution chart data with categories and percentages
    """
    try:
        # Generate mock risk distribution data based on analysis type
        if analysis_type == "users":
            title = "User Risk Distribution"
            # Mock user risk data - simulate realistic distribution
            mock_risk_data = {"low": 156, "medium": 43, "high": 12, "critical": 3}
        elif analysis_type == "events":
            title = "Event Risk Distribution"
            # Mock event risk data - events tend to have more high-risk items
            mock_risk_data = {"low": 89, "medium": 134, "high": 56, "critical": 21}
        else:  # alerts
            title = "Alert Risk Distribution"
            # Mock alert risk data - alerts tend to be higher risk
            mock_risk_data = {"low": 12, "medium": 34, "high": 28, "critical": 16}

        # Define risk categories with colors
        risk_categories = {
            "LOW": {"color": "#28a745", "threshold": (0, 30)},
            "MEDIUM": {"color": "#ffc107", "threshold": (30, 60)},
            "HIGH": {"color": "#fd7e14", "threshold": (60, 80)},
            "CRITICAL": {"color": "#dc3545", "threshold": (80, 100)},
        }

        # Process distribution data
        total_items = sum(mock_risk_data.values())
        distribution = []
        risk_summary = {}

        for risk_level, config in risk_categories.items():
            count = mock_risk_data.get(risk_level.lower(), 0)
            percentage = (count / total_items * 100) if total_items > 0 else 0

            distribution_item = RiskDistributionData(
                risk_level=risk_level,
                count=count,
                percentage=round(percentage, 1),
                color=str(config["color"]),
            )
            distribution.append(distribution_item)

            risk_summary[risk_level.lower()] = percentage

        # Calculate additional risk metrics
        risk_summary["average_risk"] = (
            risk_summary.get("low", 0) * 15  # Low = ~15 points
            + risk_summary.get("medium", 0) * 45  # Medium = ~45 points
            + risk_summary.get("high", 0) * 70  # High = ~70 points
            + risk_summary.get("critical", 0) * 90  # Critical = ~90 points
        ) / 100

        return RiskDistributionResponse(
            title=title,
            total_items=total_items,
            distribution=distribution,
            risk_summary=risk_summary,
        )

    except Exception as e:
        logger.error(f"Risk distribution chart generation failed: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to get risk distribution chart") from e
