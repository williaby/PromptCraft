"""
Analytics Router Module

Handles security analytics and insights endpoints.
Decomposed from security_dashboard_endpoints.py for focused responsibility.

Endpoints:
    GET /analytics/trends - Get security trend analysis
    GET /analytics/patterns - Get behavioral pattern analysis
    POST /analytics/investigate - Investigate security incidents
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.auth.services.security_integration import SecurityIntegrationService
from src.auth.services.suspicious_activity_detector import SuspiciousActivityDetector


class TrendDataPoint(BaseModel):
    """Data point for trend analysis."""

    timestamp: datetime = Field(..., description="Data point timestamp")
    value: float = Field(..., description="Trend value")
    category: str = Field(..., description="Trend category")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SecurityTrendsResponse(BaseModel):
    """Response model for security trend analysis."""

    analysis_period: str = Field(..., description="Analysis time period")
    trend_categories: list[str] = Field(..., description="Available trend categories")
    trends: dict[str, list[TrendDataPoint]] = Field(..., description="Trend data by category")
    insights: list[str] = Field(..., description="Key insights from trend analysis")
    risk_indicators: list[str] = Field(..., description="Risk indicators identified")


class BehaviorPattern(BaseModel):
    """Behavioral pattern model."""

    pattern_id: str = Field(..., description="Pattern identifier")
    pattern_type: str = Field(..., description="Type of behavior pattern")
    description: str = Field(..., description="Pattern description")
    confidence_score: float = Field(..., description="Pattern confidence (0-100)")
    affected_users: int = Field(..., description="Number of users showing this pattern")
    risk_level: str = Field(..., description="Associated risk level")
    first_observed: datetime = Field(..., description="First observation timestamp")
    last_observed: datetime = Field(..., description="Last observation timestamp")
    frequency: str = Field(..., description="Pattern frequency")


class PatternAnalysisResponse(BaseModel):
    """Response model for behavioral pattern analysis."""

    analysis_timestamp: datetime = Field(..., description="Analysis execution timestamp")
    total_patterns: int = Field(..., description="Total patterns identified")
    high_risk_patterns: int = Field(..., description="High risk patterns count")
    patterns: list[BehaviorPattern] = Field(..., description="Identified behavior patterns")
    recommendations: list[str] = Field(..., description="Security recommendations")


class IncidentInvestigationRequest(BaseModel):
    """Request model for incident investigation."""

    incident_id: str | None = Field(None, description="Specific incident ID")
    start_time: datetime = Field(..., description="Investigation start time")
    end_time: datetime = Field(..., description="Investigation end time")
    user_ids: list[str] | None = Field(None, description="Specific users to investigate")
    ip_addresses: list[str] | None = Field(None, description="Specific IP addresses")
    event_types: list[str] | None = Field(None, description="Event types to focus on")
    risk_threshold: int = Field(50, ge=0, le=100, description="Minimum risk threshold")


class InvestigationResult(BaseModel):
    """Single investigation result."""

    entity_type: str = Field(..., description="Type of entity (user, ip, event)")
    entity_id: str = Field(..., description="Entity identifier")
    risk_score: int = Field(..., description="Calculated risk score")
    anomaly_indicators: list[str] = Field(..., description="Detected anomalies")
    related_events: int = Field(..., description="Number of related events")
    timeline: list[dict[str, Any]] = Field(..., description="Event timeline")
    recommendations: list[str] = Field(..., description="Investigation recommendations")


class IncidentInvestigationResponse(BaseModel):
    """Response model for incident investigation."""

    investigation_id: str = Field(..., description="Investigation identifier")
    request_summary: str = Field(..., description="Investigation request summary")
    investigation_time_ms: float = Field(..., description="Investigation execution time")
    total_entities_analyzed: int = Field(..., description="Total entities analyzed")
    high_risk_entities: int = Field(..., description="High risk entities found")
    results: list[InvestigationResult] = Field(..., description="Investigation results")
    overall_risk_assessment: str = Field(..., description="Overall risk assessment")
    next_steps: list[str] = Field(..., description="Recommended next steps")


# Create router
router = APIRouter(prefix="/analytics", tags=["analytics"])

# Dependencies
_security_integration_service: SecurityIntegrationService | None = None
_suspicious_activity_detector: SuspiciousActivityDetector | None = None


async def get_security_service() -> SecurityIntegrationService:
    """Get security integration service instance."""
    global _security_integration_service
    if not _security_integration_service:
        _security_integration_service = SecurityIntegrationService()
    return _security_integration_service


async def get_suspicious_activity_detector() -> SuspiciousActivityDetector:
    """Get suspicious activity detector instance."""
    global _suspicious_activity_detector
    if not _suspicious_activity_detector:
        _suspicious_activity_detector = SuspiciousActivityDetector()
    return _suspicious_activity_detector


@router.get("/trends", response_model=SecurityTrendsResponse)
async def get_security_trends(
    service: SecurityIntegrationService = Depends(get_security_service),
    days_back: int = Query(30, ge=1, le=365, description="Days of trend data to analyze"),
    categories: str | None = Query(None, description="Comma-separated trend categories"),
) -> SecurityTrendsResponse:
    """Get security trend analysis for specified time period.

    Args:
        service: Security integration service
        days_back: Number of days to analyze
        categories: Specific categories to analyze

    Returns:
        Security trend analysis with insights and risk indicators
    """
    try:
        # Parse categories if provided
        category_list = None
        if categories:
            category_list = [cat.strip() for cat in categories.split(",")]

        # Get trend data from service
        await service.get_security_trends(days_back=days_back, categories=category_list)

        # Available trend categories
        available_categories = [
            "failed_logins",
            "suspicious_activities",
            "policy_violations",
            "unusual_access_patterns",
            "risk_score_trends",
            "alert_frequency",
        ]

        # Build trend analysis
        trends = {}
        insights = []
        risk_indicators = []

        for category in available_categories:
            if category_list and category not in category_list:
                continue

            # Generate trend data points (in production, this would come from actual data)
            trend_points = []
            base_time = datetime.now(UTC) - timedelta(days=days_back)

            for i in range(days_back):
                timestamp = base_time + timedelta(days=i)

                # Mock trend values based on category
                if category == "failed_logins":
                    value = max(0, 50 + (i % 7) * 10 - (i // 7) * 2)
                elif category == "suspicious_activities":
                    value = max(0, 25 + (i % 5) * 5 + (i // 10) * 3)
                elif category == "risk_score_trends":
                    value = min(100, 30 + (i % 14) * 2)
                else:
                    value = max(0, 20 + (i % 10) * 3)

                trend_point = TrendDataPoint(
                    timestamp=timestamp,
                    value=value,
                    category=category,
                    metadata={"day_of_week": timestamp.strftime("%A")},
                )
                trend_points.append(trend_point)

            trends[category] = trend_points

            # Generate insights based on trends
            recent_avg = sum(p.value for p in trend_points[-7:]) / 7
            older_avg = sum(p.value for p in trend_points[-14:-7]) / 7

            if recent_avg > older_avg * 1.2:
                insights.append(f"Significant increase in {category.replace('_', ' ')} over past week")
                if category in ["failed_logins", "suspicious_activities"]:
                    risk_indicators.append(f"Elevated {category.replace('_', ' ')} trend")

        # Generate analysis period description
        if days_back <= 7:
            analysis_period = f"Last {days_back} days"
        elif days_back <= 30:
            analysis_period = f"Last {days_back // 7} weeks"
        else:
            analysis_period = f"Last {days_back // 30} months"

        return SecurityTrendsResponse(
            analysis_period=analysis_period,
            trend_categories=available_categories,
            trends=trends,
            insights=insights,
            risk_indicators=risk_indicators,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security trends: {e!s}")


@router.get("/patterns", response_model=PatternAnalysisResponse)
async def get_behavioral_patterns(
    detector: SuspiciousActivityDetector = Depends(get_suspicious_activity_detector),
    service: SecurityIntegrationService = Depends(get_security_service),
    min_confidence: float = Query(70.0, ge=0, le=100, description="Minimum pattern confidence"),
    pattern_types: str | None = Query(None, description="Comma-separated pattern types"),
) -> PatternAnalysisResponse:
    """Get behavioral pattern analysis for security monitoring.

    Args:
        detector: Suspicious activity detector
        service: Security integration service
        min_confidence: Minimum confidence threshold for patterns
        pattern_types: Specific pattern types to analyze

    Returns:
        Behavioral pattern analysis with recommendations
    """
    try:
        current_time = datetime.now(UTC)

        # Parse pattern types if provided
        type_filter = None
        if pattern_types:
            type_filter = [t.strip() for t in pattern_types.split(",")]

        # Get behavioral patterns
        pattern_data = await detector.analyze_behavioral_patterns(
            min_confidence=min_confidence,
            pattern_types=type_filter,
        )

        # Convert to response models
        patterns = []
        high_risk_count = 0

        for pattern_info in pattern_data:
            risk_level = _calculate_risk_level(pattern_info["risk_score"])
            if risk_level in ["HIGH", "CRITICAL"]:
                high_risk_count += 1

            pattern = BehaviorPattern(
                pattern_id=pattern_info["pattern_id"],
                pattern_type=pattern_info["pattern_type"],
                description=pattern_info["description"],
                confidence_score=pattern_info["confidence_score"],
                affected_users=pattern_info["affected_users"],
                risk_level=risk_level,
                first_observed=pattern_info["first_observed"],
                last_observed=pattern_info["last_observed"],
                frequency=pattern_info["frequency"],
            )
            patterns.append(pattern)

        # Generate recommendations based on patterns
        recommendations = []
        if high_risk_count > 0:
            recommendations.append("Immediate investigation required for high-risk patterns")
        if len(patterns) > 10:
            recommendations.append("Consider implementing automated pattern detection rules")
        if any(p.pattern_type == "unusual_access" for p in patterns):
            recommendations.append("Review access control policies and user permissions")
        if any(p.confidence_score > 90 for p in patterns):
            recommendations.append("High-confidence patterns should trigger automatic alerts")

        if not recommendations:
            recommendations.append("Continue monitoring for emerging behavioral patterns")

        return PatternAnalysisResponse(
            analysis_timestamp=current_time,
            total_patterns=len(patterns),
            high_risk_patterns=high_risk_count,
            patterns=patterns,
            recommendations=recommendations,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get behavioral patterns: {e!s}")


@router.post("/investigate", response_model=IncidentInvestigationResponse)
async def investigate_security_incident(
    investigation_request: IncidentInvestigationRequest,
    service: SecurityIntegrationService = Depends(get_security_service),
    detector: SuspiciousActivityDetector = Depends(get_suspicious_activity_detector),
) -> IncidentInvestigationResponse:
    """Investigate security incidents with comprehensive analysis.

    Args:
        investigation_request: Investigation parameters
        service: Security integration service
        detector: Suspicious activity detector

    Returns:
        Comprehensive investigation results with recommendations
    """
    try:
        start_time = datetime.now(UTC)

        # Validate time range
        if investigation_request.end_time <= investigation_request.start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")

        # Generate investigation ID
        investigation_id = f"inv_{int(start_time.timestamp())}"

        # Perform investigation
        investigation_data = await service.investigate_security_incident(
            start_time=investigation_request.start_time,
            end_time=investigation_request.end_time,
            user_ids=investigation_request.user_ids,
            ip_addresses=investigation_request.ip_addresses,
            event_types=investigation_request.event_types,
            risk_threshold=investigation_request.risk_threshold,
        )

        # Process investigation results
        results = []
        high_risk_count = 0

        for entity_data in investigation_data.get("entities", []):
            # Create timeline from events
            timeline = []
            for event in entity_data.get("events", [])[:10]:  # Limit to 10 most recent
                timeline.append(
                    {
                        "timestamp": event["timestamp"],
                        "event_type": event["event_type"],
                        "risk_score": event.get("risk_score", 0),
                        "description": event.get("description", ""),
                    },
                )

            # Generate recommendations for this entity
            entity_recommendations = []
            risk_score = entity_data["risk_score"]

            if risk_score >= 80:
                entity_recommendations.append("Immediate security review required")
                high_risk_count += 1
            elif risk_score >= 60:
                entity_recommendations.append("Enhanced monitoring recommended")

            if len(entity_data.get("anomaly_indicators", [])) > 3:
                entity_recommendations.append("Multiple anomalies detected - investigate patterns")

            result = InvestigationResult(
                entity_type=entity_data["entity_type"],
                entity_id=entity_data["entity_id"],
                risk_score=risk_score,
                anomaly_indicators=entity_data.get("anomaly_indicators", []),
                related_events=len(entity_data.get("events", [])),
                timeline=timeline,
                recommendations=entity_recommendations,
            )
            results.append(result)

        # Calculate investigation time
        investigation_time = (datetime.now(UTC) - start_time).total_seconds() * 1000

        # Generate overall risk assessment
        if high_risk_count > 0:
            overall_risk = "HIGH - Immediate action required"
        elif len(results) > 5:
            overall_risk = "MEDIUM - Enhanced monitoring recommended"
        else:
            overall_risk = "LOW - Continue standard monitoring"

        # Generate next steps
        next_steps = []
        if high_risk_count > 0:
            next_steps.append("Initiate incident response procedures")
        if any(r.risk_score > 70 for r in results):
            next_steps.append("Contact affected users for verification")
        next_steps.append("Update monitoring rules based on findings")
        next_steps.append("Schedule follow-up investigation in 24 hours")

        # Generate request summary
        summary_parts = [f"Investigated {len(results)} entities"]
        if investigation_request.user_ids:
            summary_parts.append(f"focusing on {len(investigation_request.user_ids)} specific users")
        if investigation_request.ip_addresses:
            summary_parts.append(f"and {len(investigation_request.ip_addresses)} IP addresses")

        request_summary = ", ".join(summary_parts)

        return IncidentInvestigationResponse(
            investigation_id=investigation_id,
            request_summary=request_summary,
            investigation_time_ms=investigation_time,
            total_entities_analyzed=len(results),
            high_risk_entities=high_risk_count,
            results=results,
            overall_risk_assessment=overall_risk,
            next_steps=next_steps,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to investigate security incident: {e!s}")


def _calculate_risk_level(risk_score: float) -> str:
    """Calculate risk level from risk score.

    Args:
        risk_score: Numeric risk score

    Returns:
        Risk level string
    """
    if risk_score >= 80:
        return "CRITICAL"
    if risk_score >= 60:
        return "HIGH"
    if risk_score >= 40:
        return "MEDIUM"
    return "LOW"
