"""
Users Router Module

Handles user risk profile and monitoring endpoints.
Decomposed from security_dashboard_endpoints.py for focused responsibility.

Endpoints:
    GET /users/{user_id}/risk-profile - Get user risk profile
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from src.auth.services.security_integration import SecurityIntegrationService
from src.auth.services.suspicious_activity_detector import SuspiciousActivityDetector

logger = logging.getLogger(__name__)


class UserRiskProfileResponse(BaseModel):
    """Response model for user risk profile."""

    user_id: str = Field(..., description="User identifier")
    risk_score: int = Field(..., description="Current risk score")
    risk_level: str = Field(..., description="Risk level classification")
    total_logins: int = Field(..., description="Total login attempts")
    failed_logins_today: int = Field(..., description="Failed login attempts today")
    last_activity: datetime | None = Field(None, description="Last activity timestamp")
    known_locations: int = Field(..., description="Number of known locations")
    suspicious_activities: list[str] = Field(..., description="Recent suspicious activities")
    recommendations: list[str] = Field(..., description="Security recommendations")


# Create router
router = APIRouter(prefix="/users", tags=["users"])


# Dependencies
def get_security_service() -> SecurityIntegrationService:
    """Get security integration service instance."""
    return SecurityIntegrationService()


def get_suspicious_activity_detector() -> SuspiciousActivityDetector:
    """Get suspicious activity detector instance."""
    return SuspiciousActivityDetector()


@router.get("/{user_id}/risk-profile", response_model=UserRiskProfileResponse)
async def get_user_risk_profile(
    user_id: str = Path(..., description="User ID to analyze"),
    service: SecurityIntegrationService = Depends(get_security_service),  # noqa: ARG001
    detector: SuspiciousActivityDetector = Depends(get_suspicious_activity_detector),
) -> UserRiskProfileResponse:
    """Get comprehensive risk profile for a specific user.

    Args:
        user_id: User identifier to analyze
        service: Security integration service
        detector: Suspicious activity detector

    Returns:
        User risk profile with security metrics and recommendations
    """
    try:
        # Get user activity data from detector
        user_activity = await detector.get_user_activity_summary(user_id)

        if user_activity is None:
            raise HTTPException(status_code=404, detail=f"No activity data found for user {user_id}")

        # Calculate risk score based on multiple factors
        base_risk_score = user_activity.get("base_risk_score", 20)

        # Risk factors
        failed_logins_today = user_activity.get("failed_logins_today", 0)
        unusual_locations = user_activity.get("unusual_location_count", 0)
        off_hours_activity = user_activity.get("off_hours_activity_count", 0)

        # Calculate dynamic risk score
        risk_score = base_risk_score
        risk_score += min(30, failed_logins_today * 5)  # Failed logins penalty
        risk_score += min(20, unusual_locations * 3)  # Location penalty
        risk_score += min(15, off_hours_activity * 2)  # Off-hours penalty

        risk_score = min(100, max(0, risk_score))

        # Determine risk level
        if risk_score >= 80:
            risk_level = "CRITICAL"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Get suspicious activities
        suspicious_activities = await detector.get_user_suspicious_activities(user_id)
        activity_descriptions = [activity.get("description", "Unknown activity") for activity in suspicious_activities]

        # Generate recommendations based on risk factors
        recommendations = []
        if failed_logins_today > 5:
            recommendations.append("Consider enforcing stronger password policy")
        if unusual_locations > 2:
            recommendations.append("Review and verify recent login locations")
        if off_hours_activity > 3:
            recommendations.append("Investigate unusual activity timing patterns")
        if risk_score > 70:
            recommendations.append("Mandatory security review required")
        if len(suspicious_activities) > 3:
            recommendations.append("Enhanced monitoring recommended")

        # Default recommendation if no specific issues
        if not recommendations:
            recommendations.append("Continue standard security monitoring")

        return UserRiskProfileResponse(
            user_id=user_id,
            risk_score=risk_score,
            risk_level=risk_level,
            total_logins=user_activity.get("total_logins", 0),
            failed_logins_today=failed_logins_today,
            last_activity=user_activity.get("last_activity"),
            known_locations=user_activity.get("known_location_count", 1),
            suspicious_activities=activity_descriptions,
            recommendations=recommendations,
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"User risk profile retrieval failed: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to get user risk profile") from e
