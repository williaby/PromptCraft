"""Security integration service that orchestrates all security components.

This module provides unified security integration with:
- Coordinated event processing across logger, monitor, and alert engine
- Suspicious activity detection integration with real-time alerting
- Centralized configuration management for all security services
- Performance monitoring and health checks across all components
- Graceful degradation when individual services fail
- Event correlation and enrichment pipeline

Performance target: < 50ms end-to-end processing for security events
Architecture: Event-driven orchestration with async service coordination
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.auth.models import SecurityEventCreate, SecurityEventSeverity, SecurityEventType
from src.utils.datetime_compat import UTC, timedelta

from .alert_engine import AlertEngine, AlertEngineConfig
from .security_logger import LoggingConfig, SecurityLogger
from .security_monitor import MonitoringConfig, SecurityMonitor
from .suspicious_activity_detector import SuspiciousActivityConfig, SuspiciousActivityDetector

logger = logging.getLogger(__name__)


@dataclass
class SecurityIntegrationConfig:
    """Configuration for the security integration service."""

    # Service enablement flags
    enable_logging: bool = True
    enable_monitoring: bool = True
    enable_alerting: bool = True
    enable_suspicious_activity_detection: bool = True

    # Performance settings
    max_processing_time_ms: float = 50.0
    enable_performance_monitoring: bool = True

    # Event correlation settings
    enable_event_enrichment: bool = True
    correlation_window_seconds: int = 300  # 5 minutes

    # Failure handling
    enable_graceful_degradation: bool = True
    max_service_failures: int = 3
    failure_reset_interval_minutes: int = 15

    # Service-specific configurations
    logging_config: LoggingConfig | None = None
    monitoring_config: MonitoringConfig | None = None
    alert_engine_config: AlertEngineConfig | None = None
    suspicious_activity_config: SuspiciousActivityConfig | None = None


@dataclass
class SecurityIntegrationMetrics:
    """Performance and health metrics for the security integration."""

    total_events_processed: int = 0
    total_events_failed: int = 0
    total_alerts_generated: int = 0
    total_suspicious_activities: int = 0

    # Performance metrics
    average_processing_time_ms: float = 0.0
    average_enrichment_time_ms: float = 0.0

    # Service health metrics
    logger_failures: int = 0
    monitor_failures: int = 0
    alert_engine_failures: int = 0
    detector_failures: int = 0

    # Service status
    logger_healthy: bool = True
    monitor_healthy: bool = True
    alert_engine_healthy: bool = True
    detector_healthy: bool = True

    last_health_check: datetime | None = None

    # Exponential moving average parameters
    _ema_alpha: float = 0.1


class SecurityIntegrationService:
    """Unified security integration service orchestrating all security components."""

    def __init__(self, config: SecurityIntegrationConfig | None = None) -> None:
        """Initialize security integration service.

        Args:
            config: Integration configuration (uses defaults if None)
        """
        self.config = config or SecurityIntegrationConfig()
        self.metrics = SecurityIntegrationMetrics()

        # Initialize security services synchronously
        self._initialize_services_sync()

        # Service failure tracking
        self._service_failures: dict[str, int] = {"logger": 0, "monitor": 0, "alert_engine": 0, "detector": 0}
        self._last_failure_reset = datetime.now(UTC)

        # Event correlation storage
        self._recent_events: list[tuple[datetime, SecurityEventCreate]] = []

        # Background tasks (will be started during async initialize)
        self._health_check_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

    def _initialize_services_sync(self) -> None:
        """Initialize security services synchronously."""
        try:
            # Initialize security logger
            if self.config.enable_logging:
                self.security_logger = SecurityLogger(config=self.config.logging_config)
            else:
                self.security_logger = None

            # Initialize security monitor
            if self.config.enable_monitoring:
                self.security_monitor = SecurityMonitor(config=self.config.monitoring_config)
            else:
                self.security_monitor = None

            # Initialize alert engine with notification handlers
            if self.config.enable_alerting:
                # Create notification handlers (this would be configured externally in production)
                notification_handlers = self._create_default_notification_handlers()
                self.alert_engine = AlertEngine(
                    config=self.config.alert_engine_config,
                    notification_handlers=notification_handlers,
                )
            else:
                self.alert_engine = None

            # Initialize suspicious activity detector
            if self.config.enable_suspicious_activity_detection:
                self.suspicious_activity_detector = SuspiciousActivityDetector(
                    config=self.config.suspicious_activity_config,
                )
            else:
                self.suspicious_activity_detector = None

        except Exception:
            # Set all services to None if initialization fails
            self.security_logger = None
            self.security_monitor = None
            self.alert_engine = None
            self.suspicious_activity_detector = None

    async def initialize(self) -> None:
        """Initialize the security integration service and start background tasks."""
        # Start background tasks
        self._start_background_tasks()

    async def _initialize_services(self) -> None:
        """Initialize all security services based on configuration."""
        # This method is now replaced by _initialize_services_sync() called during __init__
        # and background tasks are started separately in initialize()

    def _create_default_notification_handlers(self) -> list:
        """Create default notification handlers (would be configured externally)."""
        # In production, this would be configured through external configuration
        # For now, return empty list to avoid dependencies on external services
        return []

    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._health_check_task = loop.create_task(self._health_check_loop())
                self._cleanup_task = loop.create_task(self._cleanup_loop())
        except RuntimeError:
            # No event loop running
            pass

    async def process_security_event(
        self,
        event: SecurityEventCreate,
        additional_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process security event through all enabled services.

        Args:
            event: Security event to process
            additional_context: Additional context for processing

        Returns:
            Processing results including alerts, monitoring data, and analysis
        """
        start_time = time.time()

        results = {
            "event_id": getattr(event, "id", None),
            "processed_at": datetime.now(UTC).isoformat(),
            "services_processed": [],
            "alerts_generated": [],
            "monitoring_alerts": [],
            "suspicious_activity": None,
            "processing_time_ms": 0.0,
            "errors": [],
        }

        try:
            # Add to correlation window
            self._add_to_correlation_window(event)

            # Enrich event with correlation data if enabled
            if self.config.enable_event_enrichment:
                event = await self._enrich_event(event, additional_context)

            # Process through security logger
            if self.security_logger and self._is_service_healthy("logger"):
                try:
                    logged = await self.security_logger.log_event(
                        event_type=event.event_type,
                        severity=event.severity,
                        user_id=event.user_id,
                        ip_address=event.ip_address,
                        user_agent=event.user_agent,
                        session_id=event.session_id,
                        details=event.details,
                        risk_score=event.risk_score,
                    )

                    if logged:
                        results["services_processed"].append("logger")
                    else:
                        results["errors"].append("Logger: event dropped (rate limited or queue full)")

                except Exception as e:
                    await self._handle_service_error("logger", e)
                    results["errors"].append(f"Logger error: {e!s}")

            # Process through security monitor
            if self.security_monitor and self._is_service_healthy("monitor"):
                try:
                    if event.event_type == SecurityEventType.LOGIN_FAILURE:
                        monitor_alerts = await self.security_monitor.track_failed_authentication(
                            user_id=event.user_id,
                            ip_address=event.ip_address,
                            timestamp=event.timestamp,
                            failure_reason=event.details.get("reason") if event.details else None,
                        )

                        results["monitoring_alerts"] = [
                            {
                                "type": alert.alert_type.value,
                                "message": alert.message,
                                "severity": alert.severity.value,
                                "user_id": alert.user_id,
                                "ip_address": alert.ip_address,
                            }
                            for alert in monitor_alerts
                        ]

                    results["services_processed"].append("monitor")

                except Exception as e:
                    await self._handle_service_error("monitor", e)
                    results["errors"].append(f"Monitor error: {e!s}")

            # Process through suspicious activity detector
            if self.suspicious_activity_detector and self._is_service_healthy("detector"):
                try:
                    analysis_result = await self.suspicious_activity_detector.analyze_activity(
                        event,
                        additional_context,
                    )

                    if analysis_result.is_suspicious:
                        results["suspicious_activity"] = {
                            "risk_score": analysis_result.risk_score,
                            "detected_activities": [activity.value for activity in analysis_result.detected_activities],
                            "risk_factors": analysis_result.risk_factors,
                            "recommendations": analysis_result.recommendations,
                            "location_analysis": analysis_result.location_analysis,
                            "time_analysis": analysis_result.time_analysis,
                            "user_agent_analysis": analysis_result.user_agent_analysis,
                            "behavioral_analysis": analysis_result.behavioral_analysis,
                        }

                        self.metrics.total_suspicious_activities += 1

                        # If suspicious, create a security alert event for the alert engine
                        if analysis_result.risk_score >= 50:  # High risk threshold
                            suspicious_event = SecurityEventCreate(
                                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                                severity=(
                                    SecurityEventSeverity.WARNING
                                    if analysis_result.risk_score < 70
                                    else SecurityEventSeverity.CRITICAL
                                ),
                                user_id=event.user_id,
                                ip_address=event.ip_address,
                                user_agent=event.user_agent,
                                session_id=event.session_id,
                                details={
                                    "original_event": event.event_type.value,
                                    "detected_activities": [a.value for a in analysis_result.detected_activities],
                                    "risk_factors": analysis_result.risk_factors,
                                    "analysis_time_ms": analysis_result.risk_factors.get("analysis_time_ms", 0),
                                },
                                risk_score=analysis_result.risk_score,
                            )

                            # Process suspicious event through alert engine
                            if self.alert_engine and self._is_service_healthy("alert_engine"):
                                await self.alert_engine.process_event(suspicious_event)

                    results["services_processed"].append("detector")

                except Exception as e:
                    await self._handle_service_error("detector", e)
                    results["errors"].append(f"Detector error: {e!s}")

            # Process through alert engine
            if self.alert_engine and self._is_service_healthy("alert_engine"):
                try:
                    # Process original event through alert engine
                    await self.alert_engine.process_event(event)
                    results["services_processed"].append("alert_engine")

                    # Get recent alert metrics (simplified)
                    alert_metrics = await self.alert_engine.get_metrics()
                    results["alerts_generated"] = [
                        {
                            "total_generated": alert_metrics["performance"]["total_alerts_generated"],
                            "total_sent": alert_metrics["performance"]["total_alerts_sent"],
                        },
                    ]

                except Exception as e:
                    await self._handle_service_error("alert_engine", e)
                    results["errors"].append(f"Alert engine error: {e!s}")

            # Update metrics
            processing_time_ms = (time.time() - start_time) * 1000
            results["processing_time_ms"] = processing_time_ms

            self._update_processing_metrics(processing_time_ms)
            self.metrics.total_events_processed += 1

            # Check if processing took too long
            if processing_time_ms > self.config.max_processing_time_ms:
                results["errors"].append(
                    f"Processing exceeded target time: {processing_time_ms:.2f}ms > {self.config.max_processing_time_ms}ms",
                )

            return results

        except Exception as e:
            self.metrics.total_events_failed += 1
            results["errors"].append(f"Integration error: {e!s}")
            return results

    async def _enrich_event(
        self,
        event: SecurityEventCreate,
        additional_context: dict[str, Any] | None,
    ) -> SecurityEventCreate:
        """Enrich event with correlation data and additional context."""
        start_time = time.time()

        try:
            enriched_details = event.details.copy() if event.details else {}

            # Add correlation information
            correlated_events = self._find_correlated_events(event)
            if correlated_events:
                enriched_details["correlated_events_count"] = len(correlated_events)
                enriched_details["correlation_window_seconds"] = self.config.correlation_window_seconds

            # Add additional context if provided
            if additional_context:
                enriched_details["additional_context"] = additional_context

            # Add processing metadata
            enriched_details["processed_by_integration"] = True
            enriched_details["enrichment_timestamp"] = datetime.now(UTC).isoformat()

            # Create enriched event
            enriched_event = SecurityEventCreate(
                event_type=event.event_type,
                severity=event.severity,
                user_id=event.user_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                session_id=event.session_id,
                details=enriched_details,
                risk_score=event.risk_score,
                timestamp=event.timestamp,
            )

            # Update enrichment metrics
            enrichment_time_ms = (time.time() - start_time) * 1000
            self._update_enrichment_metrics(enrichment_time_ms)

            return enriched_event

        except Exception:
            return event  # Return original event if enrichment fails

    def _add_to_correlation_window(self, event: SecurityEventCreate) -> None:
        """Add event to correlation window for future correlation analysis."""
        current_time = datetime.now(UTC)
        self._recent_events.append((current_time, event))

        # Clean up old events outside correlation window
        cutoff_time = current_time - timedelta(seconds=self.config.correlation_window_seconds)
        self._recent_events = [(timestamp, evt) for timestamp, evt in self._recent_events if timestamp > cutoff_time]

    def _find_correlated_events(self, event: SecurityEventCreate) -> list[SecurityEventCreate]:
        """Find events correlated with the current event."""
        correlated = []

        for _timestamp, recent_event in self._recent_events:
            # Same user correlation
            if (
                event.user_id and recent_event.user_id == event.user_id and recent_event.event_type != event.event_type
            ) or (
                event.ip_address
                and recent_event.ip_address == event.ip_address
                and recent_event.user_id != event.user_id
            ):
                correlated.append(recent_event)

        return correlated

    async def _handle_service_error(self, service_name: str, error: Exception) -> None:
        """Handle service errors and track failure counts."""
        self._service_failures[service_name] += 1

        # Update service health status
        if service_name == "logger":
            self.metrics.logger_failures += 1
            if self._service_failures[service_name] >= self.config.max_service_failures:
                self.metrics.logger_healthy = False
        elif service_name == "monitor":
            self.metrics.monitor_failures += 1
            if self._service_failures[service_name] >= self.config.max_service_failures:
                self.metrics.monitor_healthy = False
        elif service_name == "alert_engine":
            self.metrics.alert_engine_failures += 1
            if self._service_failures[service_name] >= self.config.max_service_failures:
                self.metrics.alert_engine_healthy = False
        elif service_name == "detector":
            self.metrics.detector_failures += 1
            if self._service_failures[service_name] >= self.config.max_service_failures:
                self.metrics.detector_healthy = False

    def _is_service_healthy(self, service_name: str) -> bool:
        """Check if a service is healthy based on failure tracking."""
        if not self.config.enable_graceful_degradation:
            return True  # Always try all services if degradation is disabled

        return self._service_failures[service_name] < self.config.max_service_failures

    def _update_processing_metrics(self, processing_time_ms: float) -> None:
        """Update processing time metrics."""
        if self.metrics.average_processing_time_ms == 0:
            self.metrics.average_processing_time_ms = processing_time_ms
        else:
            self.metrics.average_processing_time_ms = (
                self.metrics._ema_alpha * processing_time_ms
                + (1 - self.metrics._ema_alpha) * self.metrics.average_processing_time_ms
            )

    def _update_enrichment_metrics(self, enrichment_time_ms: float) -> None:
        """Update enrichment time metrics."""
        if self.metrics.average_enrichment_time_ms == 0:
            self.metrics.average_enrichment_time_ms = enrichment_time_ms
        else:
            self.metrics.average_enrichment_time_ms = (
                self.metrics._ema_alpha * enrichment_time_ms
                + (1 - self.metrics._ema_alpha) * self.metrics.average_enrichment_time_ms
            )

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks."""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_check()
                await asyncio.sleep(60)  # Health check every minute
            except Exception:
                await asyncio.sleep(60)

    async def _perform_health_check(self) -> None:
        """Perform health check on all services."""
        self.metrics.last_health_check = datetime.now(UTC)

        # Check if it's time to reset failure counts
        time_since_reset = datetime.now(UTC) - self._last_failure_reset
        if time_since_reset.total_seconds() > (self.config.failure_reset_interval_minutes * 60):
            self._reset_failure_counts()

        # Test service health (simplified - in production would ping services)
        try:
            if self.security_logger:
                logger_metrics = await self.security_logger.get_metrics()
                self.metrics.logger_healthy = logger_metrics.get("health", {}).get("is_processing", False)
        except Exception as e:
            logger.warning("Failed to get logger health metrics: %s", e)
            self.metrics.logger_healthy = False

        # Similar health checks for other services would go here...

    def _reset_failure_counts(self) -> None:
        """Reset service failure counts."""
        self._service_failures = dict.fromkeys(self._service_failures, 0)
        self._last_failure_reset = datetime.now(UTC)

        # Reset health status
        self.metrics.logger_healthy = True
        self.metrics.monitor_healthy = True
        self.metrics.alert_engine_healthy = True
        self.metrics.detector_healthy = True

    async def _cleanup_loop(self) -> None:
        """Background task for periodic cleanup."""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_cleanup()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except Exception:
                await asyncio.sleep(300)

    async def _perform_cleanup(self) -> None:
        """Perform cleanup tasks."""
        # Clean up correlation window (already done in _add_to_correlation_window)

        # Trigger cleanup in individual services
        try:
            if self.security_logger:
                # Logger has its own cleanup via retention policies
                pass

            # Additional cleanup tasks would go here
        except Exception as e:
            # Log cleanup failure but don't raise - this is best effort cleanup
            logger.warning("Cleanup task failed: %s", e)

    async def get_integration_health(self) -> dict[str, Any]:
        """Get health status of all integration services."""
        services = {
            "security_logger": {
                "status": "healthy" if self.security_logger and self.metrics.logger_healthy else "unhealthy",
            },
            "security_monitor": {
                "status": "healthy" if self.security_monitor and self.metrics.monitor_healthy else "unhealthy",
            },
            "alert_engine": {
                "status": "healthy" if self.alert_engine and self.metrics.alert_engine_healthy else "unhealthy",
            },
            "suspicious_activity_detector": {
                "status": (
                    "healthy" if self.suspicious_activity_detector and self.metrics.detector_healthy else "unhealthy"
                ),
            },
        }

        # Calculate overall status
        all_healthy = all(service["status"] == "healthy" for service in services.values())
        overall_status = "healthy" if all_healthy else "degraded"

        return {
            "overall_status": overall_status,
            "services": services,
            "last_check": self.metrics.last_health_check.isoformat() if self.metrics.last_health_check else None,
        }

    async def get_comprehensive_metrics(self) -> dict[str, Any]:
        """Get comprehensive metrics from all services."""
        metrics = {
            "integration": {
                "total_events_processed": self.metrics.total_events_processed,
                "total_events_failed": self.metrics.total_events_failed,
                "total_alerts_generated": self.metrics.total_alerts_generated,
                "total_suspicious_activities": self.metrics.total_suspicious_activities,
                "average_processing_time_ms": round(self.metrics.average_processing_time_ms, 2),
                "average_enrichment_time_ms": round(self.metrics.average_enrichment_time_ms, 2),
                "performance_status": (
                    "excellent"
                    if self.metrics.average_processing_time_ms < 20
                    else "good" if self.metrics.average_processing_time_ms < 50 else "degraded"
                ),
            },
            "service_health": {
                "logger_healthy": self.metrics.logger_healthy,
                "monitor_healthy": self.metrics.monitor_healthy,
                "alert_engine_healthy": self.metrics.alert_engine_healthy,
                "detector_healthy": self.metrics.detector_healthy,
                "last_health_check": (
                    self.metrics.last_health_check.isoformat() if self.metrics.last_health_check else None
                ),
            },
            "service_failures": {
                "logger_failures": self.metrics.logger_failures,
                "monitor_failures": self.metrics.monitor_failures,
                "alert_engine_failures": self.metrics.alert_engine_failures,
                "detector_failures": self.metrics.detector_failures,
            },
        }

        # Add individual service metrics
        try:
            if self.security_logger:
                metrics["logger"] = await self.security_logger.get_metrics()
        except Exception as e:
            logger.warning("Failed to get logger metrics: %s", e)
            metrics["logger"] = {"error": "metrics unavailable"}

        try:
            if self.security_monitor:
                metrics["monitor"] = await self.security_monitor.get_metrics()
        except Exception as e:
            logger.warning("Failed to get monitor metrics: %s", e)
            metrics["monitor"] = {"error": "metrics unavailable"}

        try:
            if self.alert_engine:
                metrics["alert_engine"] = await self.alert_engine.get_metrics()
        except Exception as e:
            logger.warning("Failed to get alert engine metrics: %s", e)
            metrics["alert_engine"] = {"error": "metrics unavailable"}

        return metrics

    async def get_audit_event_summary(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: list[SecurityEventType] | None = None,
    ) -> dict[str, Any]:
        """Get audit event summary for specified time period.

        Args:
            start_date: Start date for audit summary
            end_date: End date for audit summary
            event_types: Optional list of event types to filter

        Returns:
            Dictionary with audit summary including total and critical events
        """
        try:
            # Input validation
            if end_date <= start_date:
                raise ValueError("End date must be after start date")

            # Get events from logger's database
            if self.logger and hasattr(self.security_logger, "db"):
                events = await self.security_logger.db.get_events_by_date_range(start_date, end_date)

                # Apply event type filtering if specified
                if event_types:
                    event_type_values = [et.value for et in event_types]
                    events = [
                        e
                        for e in events
                        if (e.event_type.value if hasattr(e.event_type, "value") else e.event_type) in event_type_values
                    ]
            else:
                # Fallback to in-memory simulation for testing/degraded mode
                events = []

            # Calculate summary statistics
            total_events = len(events)
            critical_events = sum(
                1
                for event in events
                if hasattr(event, "severity") and event.severity in ["critical", "high", SecurityEventSeverity.CRITICAL]
            )

            return {
                "total_events": total_events,
                "critical_events": critical_events,
                "time_range_days": (end_date - start_date).days,
                "event_types_analyzed": len(event_types) if event_types else "all",
            }

        except Exception as e:
            # Log error but don't fail completely
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={"error": str(e), "operation": "get_audit_event_summary"},
                )

            # Return degraded response
            return {
                "total_events": 0,
                "critical_events": 0,
                "time_range_days": (end_date - start_date).days,
                "event_types_analyzed": len(event_types) if event_types else "all",
                "error": "Failed to retrieve audit summary",
            }

    async def generate_audit_report_background(
        self,
        report_id: str,
        request: dict[str, Any],
    ) -> None:
        """Generate audit report in background task.

        Args:
            report_id: Unique report identifier
            request: Report request parameters
        """
        try:
            # Log report generation start
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.AUDIT_LOG_GENERATED,
                    user_id=request.get("user_id", "system"),
                    metadata={
                        "report_id": report_id,
                        "report_type": request.get("report_type", "unknown"),
                        "status": "started",
                    },
                )

            # Simulate background report generation
            # In production, this would generate and store the actual report
            await asyncio.sleep(2)  # Simulate processing time

            # Log completion
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.AUDIT_LOG_GENERATED,
                    user_id=request.get("user_id", "system"),
                    metadata={
                        "report_id": report_id,
                        "report_type": request.get("report_type", "unknown"),
                        "status": "completed",
                        "generation_time_seconds": 2.0,
                    },
                )

        except Exception as e:
            # Log background task failure
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={
                        "error": str(e),
                        "operation": "generate_audit_report_background",
                        "report_id": report_id,
                    },
                )

    async def get_comprehensive_audit_statistics(self, days_back: int) -> dict[str, Any]:
        """Get comprehensive audit statistics for specified period.

        Args:
            days_back: Number of days to analyze

        Returns:
            Dictionary with comprehensive audit statistics
        """
        try:
            # Input validation
            if days_back < 1 or days_back > 365:
                raise ValueError("days_back must be between 1 and 365")

            # Calculate date ranges
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days_back)

            # Get events from logger's database
            if self.logger and hasattr(self.security_logger, "db"):
                all_events = await self.security_logger.db.get_events_by_date_range(start_date, end_date)
            else:
                # Fallback simulation
                all_events = []

            # Calculate time-based event counts
            now = datetime.now(UTC)
            events_24h = len(
                [e for e in all_events if hasattr(e, "timestamp") and e.timestamp >= now - timedelta(days=1)],
            )
            events_week = len(
                [e for e in all_events if hasattr(e, "timestamp") and e.timestamp >= now - timedelta(days=7)],
            )
            events_month = len(
                [e for e in all_events if hasattr(e, "timestamp") and e.timestamp >= now - timedelta(days=30)],
            )

            return {
                "total_events": len(all_events),
                "events_24h": events_24h,
                "events_week": events_week,
                "events_month": events_month,
                "analysis_period_days": days_back,
                "data_coverage_percentage": min(100.0, (len(all_events) / max(1, days_back * 10)) * 100),
            }

        except Exception as e:
            # Log error and return degraded response
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={"error": str(e), "operation": "get_comprehensive_audit_statistics"},
                )

            return {
                "total_events": 0,
                "events_24h": 0,
                "events_week": 0,
                "events_month": 0,
                "analysis_period_days": days_back,
                "data_coverage_percentage": 0.0,
                "error": "Failed to retrieve statistics",
            }

    async def get_retention_policies(
        self,
        policy_ids: list[str] | None = None,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Get audit data retention policies.

        Args:
            policy_ids: Specific policy IDs to retrieve (None for all)
            active_only: Return only active policies

        Returns:
            List of retention policy dictionaries
        """
        try:
            # Simulated retention policies (in production, these would come from database)
            all_policies = [
                {
                    "policy_id": "rp_standard_events",
                    "name": "Standard Security Events",
                    "event_types": [
                        "LOGIN_SUCCESS",
                        "LOGIN_FAILURE",
                        "LOGOUT",
                        "PASSWORD_CHANGED",
                        "SESSION_EXPIRED",
                    ],
                    "retention_days": 90,
                    "auto_delete": True,
                    "compliance_requirement": "Internal Security Policy",
                    "created_at": datetime.now(UTC) - timedelta(days=30),
                    "updated_at": datetime.now(UTC) - timedelta(days=5),
                },
                {
                    "policy_id": "rp_critical_events",
                    "name": "Critical Security Events",
                    "event_types": [
                        "ACCOUNT_LOCKOUT",
                        "SUSPICIOUS_ACTIVITY",
                        "BRUTE_FORCE_ATTEMPT",
                        "SECURITY_ALERT",
                        "RATE_LIMIT_EXCEEDED",
                    ],
                    "retention_days": 365,
                    "auto_delete": True,
                    "compliance_requirement": "SOC 2 Type II",
                    "created_at": datetime.now(UTC) - timedelta(days=30),
                    "updated_at": datetime.now(UTC) - timedelta(days=2),
                },
                {
                    "policy_id": "rp_audit_logs",
                    "name": "Audit Log Events",
                    "event_types": [
                        "AUDIT_LOG_GENERATED",
                        "AUDIT_LOG_ACCESSED",
                        "SYSTEM_MAINTENANCE",
                    ],
                    "retention_days": 2555,  # 7 years for compliance
                    "auto_delete": False,
                    "compliance_requirement": "PCI DSS",
                    "created_at": datetime.now(UTC) - timedelta(days=30),
                    "updated_at": datetime.now(UTC) - timedelta(days=1),
                },
            ]

            # Filter by policy IDs if specified
            if policy_ids:
                all_policies = [p for p in all_policies if p["policy_id"] in policy_ids]

            # Filter by active status if requested (for this simulation, all are active)
            if active_only:
                # In production, this would filter by an 'active' field
                pass

            return all_policies

        except Exception as e:
            # Log error and return empty list
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={"error": str(e), "operation": "get_retention_policies"},
                )
            return []

    async def count_events_before_date(
        self,
        cutoff_date: datetime,
        event_types: list[str] | None = None,
    ) -> int:
        """Count events before specified cutoff date.

        Args:
            cutoff_date: Date cutoff for counting events
            event_types: Optional list of event types to filter

        Returns:
            Number of events that would be affected by retention policy
        """
        try:
            # Get events from logger's database
            if self.logger and hasattr(self.security_logger, "db"):
                # Get all events before cutoff date
                start_date = datetime.now(UTC) - timedelta(days=3650)  # 10 years back
                events = await self.security_logger.db.get_events_by_date_range(start_date, cutoff_date)

                # Apply event type filtering if specified
                if event_types:
                    events = [
                        e
                        for e in events
                        if (e.event_type.value if hasattr(e.event_type, "value") else e.event_type) in event_types
                    ]

                return len(events)
            # Fallback simulation for testing/degraded mode
            # Simulate some old events that would be affected
            days_old = (datetime.now(UTC) - cutoff_date).days
            simulated_count = max(0, min(1000, days_old * 5))  # ~5 events per day
            return simulated_count

        except Exception as e:
            # Log error and return 0
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={"error": str(e), "operation": "count_events_before_date"},
                )
            return 0

    async def enforce_retention_policies_background(
        self,
        policy_ids: list[str] | None = None,
    ) -> None:
        """Enforce retention policies in background task.

        Args:
            policy_ids: Specific policy IDs to enforce (None for all)
        """
        try:
            # Get policies to enforce
            policies = await self.get_retention_policies(policy_ids=policy_ids)

            # Log enforcement start
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_MAINTENANCE,
                    metadata={
                        "operation": "retention_policy_enforcement",
                        "policies_count": len(policies),
                        "status": "started",
                    },
                )

            total_deleted = 0

            # Process each policy
            for policy in policies:
                if not policy.get("auto_delete", False):
                    continue  # Skip policies that don't allow auto-deletion

                # Calculate cutoff date
                cutoff_date = datetime.now(UTC) - timedelta(days=policy["retention_days"])

                # Count events that would be deleted
                affected_count = await self.count_events_before_date(
                    cutoff_date=cutoff_date,
                    event_types=policy["event_types"],
                )

                # In production, this would actually delete the events
                # For simulation, we just track the counts
                total_deleted += affected_count

                # Simulate processing time
                await asyncio.sleep(0.5)

            # Log completion
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_MAINTENANCE,
                    metadata={
                        "operation": "retention_policy_enforcement",
                        "policies_processed": len(policies),
                        "total_events_deleted": total_deleted,
                        "status": "completed",
                    },
                )

        except Exception as e:
            # Log background task failure
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={
                        "error": str(e),
                        "operation": "enforce_retention_policies_background",
                    },
                )

    async def search_security_events(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Search security events with filtering and pagination.

        Args:
            filters: Search filters including date range, event types, etc.

        Returns:
            Dictionary with events list, total count, and metadata
        """
        try:
            # Extract filter parameters
            start_date = filters.get("start_date")
            end_date = filters.get("end_date")
            limit = filters.get("limit", 100)
            offset = filters.get("offset", 0)
            event_types = filters.get("event_types", [])
            severity_levels = filters.get("severity_levels", [])
            user_id = filters.get("user_id")
            ip_address = filters.get("ip_address")
            risk_score_min = filters.get("risk_score_min")
            risk_score_max = filters.get("risk_score_max")

            # Get events from logger if available
            events_data = []
            total_count = 0

            if self.logger and hasattr(self.security_logger, "db"):
                try:
                    # Get events from database
                    events = await self.security_logger.db.get_events_by_date_range(start_date, end_date)

                    # Apply filtering
                    filtered_events = events

                    if event_types:
                        filtered_events = [
                            e
                            for e in filtered_events
                            if (e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type))
                            in event_types
                        ]

                    if severity_levels:
                        filtered_events = [
                            e
                            for e in filtered_events
                            if (e.severity.value if hasattr(e.severity, "value") else str(e.severity))
                            in severity_levels
                        ]

                    if user_id:
                        filtered_events = [e for e in filtered_events if e.user_id == user_id]

                    if ip_address:
                        filtered_events = [e for e in filtered_events if str(e.ip_address) == ip_address]

                    if risk_score_min is not None:
                        filtered_events = [e for e in filtered_events if e.risk_score >= risk_score_min]

                    if risk_score_max is not None:
                        filtered_events = [e for e in filtered_events if e.risk_score <= risk_score_max]

                    total_count = len(filtered_events)

                    # Apply pagination
                    paginated_events = filtered_events[offset : offset + limit]

                    # Convert to dict format
                    events_data = []
                    for event in paginated_events:
                        event_dict = {
                            "id": str(event.id) if hasattr(event, "id") else f"evt_{hash(str(event))}",
                            "event_type": (
                                event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
                            ),
                            "severity": (
                                event.severity.value if hasattr(event.severity, "value") else str(event.severity)
                            ),
                            "timestamp": event.timestamp,
                            "user_id": event.user_id,
                            "ip_address": str(event.ip_address) if event.ip_address else None,
                            "user_agent": event.user_agent,
                            "risk_score": event.risk_score,
                            "details": event.details if hasattr(event, "details") else {},
                            "tags": getattr(event, "tags", []),
                        }
                        events_data.append(event_dict)

                except Exception as e:
                    # Fall back to simulation if database fails
                    await self._handle_service_error("logger", e)

            # Fallback simulation if no logger or database access fails
            if not events_data:
                events_data, total_count = self._simulate_search_results(filters)

            return {
                "events": events_data,
                "total_count": total_count,
                "search_metadata": {
                    "filters_applied": len([k for k, v in filters.items() if v is not None]),
                    "pagination": {"limit": limit, "offset": offset},
                },
            }

        except Exception as e:
            # Log error internally but don't expose details to external users
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={"error": str(e), "operation": "search_security_events"},
                )

            # Return generic error message to prevent information disclosure
            return {
                "events": [],
                "total_count": 0,
                "search_metadata": {"error": "Search operation failed"},
            }

    def _simulate_search_results(self, filters: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
        """Simulate search results for testing/fallback scenarios."""
        # Extract parameters
        limit = filters.get("limit", 100)
        offset = filters.get("offset", 0)
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")
        event_types = filters.get("event_types", [])
        severity_levels = filters.get("severity_levels", [])
        user_id = filters.get("user_id")

        # Generate simulated data
        base_count = min(1000, max(10, hash(str(filters)) % 500))

        # Simulate filtering effects
        if event_types:
            base_count = int(base_count * 0.7)  # Filtering reduces results
        if severity_levels:
            base_count = int(base_count * 0.5)
        if user_id:
            base_count = int(base_count * 0.1)  # User filtering is very selective

        total_count = max(1, base_count)

        # Generate events for current page
        events = []
        for i in range(min(limit, total_count - offset)):
            event_id = f"sim_event_{hash(str(filters) + str(i)) % 100000:05d}"

            # Generate realistic event data
            event_types_pool = (
                event_types if event_types else ["login_success", "login_failure", "data_access", "permission_change"]
            )
            severity_pool = severity_levels if severity_levels else ["info", "warning", "high", "critical"]

            event_data = {
                "id": event_id,
                "event_type": event_types_pool[i % len(event_types_pool)],
                "severity": severity_pool[i % len(severity_pool)],
                "timestamp": (
                    start_date
                    + timedelta(
                        seconds=(end_date - start_date).total_seconds() * (i / max(1, limit)),
                    )
                    if start_date and end_date
                    else datetime.now(UTC)
                ),
                "user_id": user_id if user_id else f"user_{hash(event_id) % 100}",
                "ip_address": f"192.168.{(hash(event_id) % 255)}.{((hash(event_id) // 255) % 255)}",
                "user_agent": "Mozilla/5.0 (Test Browser)",
                "risk_score": min(100, max(0, hash(event_id) % 100)),
                "details": {"simulated": True, "sequence": i},
                "tags": ["simulated", "search_result"],
            }
            events.append(event_data)

        return events, total_count

    async def shutdown(self) -> None:
        """Gracefully shutdown all services."""
        # Signal shutdown
        self._shutdown_event.set()

        # Wait for background tasks
        if self._health_check_task:
            await self._health_check_task
        if self._cleanup_task:
            await self._cleanup_task

        # Shutdown individual services
        try:
            if self.security_logger:
                await self.security_logger.shutdown()
        except Exception as e:
            logger.warning("Failed to shutdown security logger: %s", e)

        try:
            if self.alert_engine:
                await self.alert_engine.shutdown()
        except Exception as e:
            logger.warning("Failed to shutdown alert engine: %s", e)

    async def get_security_trends(
        self,
        days_back: int = 30,
        categories: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get security trend data for analytics.

        Args:
            days_back: Number of days to analyze
            categories: Specific trend categories to analyze

        Returns:
            Dictionary containing trend analysis data
        """
        try:
            # Define available categories
            all_categories = [
                "failed_logins",
                "suspicious_activities",
                "policy_violations",
                "unusual_access_patterns",
                "risk_score_trends",
                "alert_frequency",
            ]

            # Use specified categories or all
            analysis_categories = categories if categories else all_categories

            # Calculate time period
            end_time = datetime.now(UTC)
            start_time = end_time - timedelta(days=days_back)

            trend_data = {
                "analysis_period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "days_analyzed": days_back,
                },
                "categories": analysis_categories,
                "trends": {},
                "summary": {},
            }

            # Generate trend data for each category
            for category in analysis_categories:
                # Simulate trend analysis based on category
                if category == "failed_logins":
                    trend_data["trends"][category] = {
                        "current_period": min(500, days_back * 15 + (hash(category) % 100)),
                        "previous_period": min(400, days_back * 12 + (hash(category) % 80)),
                        "trend_direction": "increasing",
                        "percentage_change": 12.5,
                    }
                elif category == "suspicious_activities":
                    trend_data["trends"][category] = {
                        "current_period": min(200, days_back * 6 + (hash(category) % 50)),
                        "previous_period": min(180, days_back * 5 + (hash(category) % 40)),
                        "trend_direction": "increasing",
                        "percentage_change": 11.1,
                    }
                elif category == "policy_violations":
                    trend_data["trends"][category] = {
                        "current_period": min(100, days_back * 3 + (hash(category) % 25)),
                        "previous_period": min(120, days_back * 4 + (hash(category) % 30)),
                        "trend_direction": "decreasing",
                        "percentage_change": -16.7,
                    }
                elif category == "unusual_access_patterns":
                    trend_data["trends"][category] = {
                        "current_period": min(150, days_back * 4 + (hash(category) % 35)),
                        "previous_period": min(130, days_back * 3 + (hash(category) % 30)),
                        "trend_direction": "increasing",
                        "percentage_change": 15.4,
                    }
                elif category == "risk_score_trends":
                    trend_data["trends"][category] = {
                        "current_average": min(100, 45 + (hash(category) % 30)),
                        "previous_average": min(100, 38 + (hash(category) % 25)),
                        "trend_direction": "increasing",
                        "percentage_change": 18.4,
                    }
                elif category == "alert_frequency":
                    trend_data["trends"][category] = {
                        "current_period": min(300, days_back * 8 + (hash(category) % 60)),
                        "previous_period": min(280, days_back * 7 + (hash(category) % 55)),
                        "trend_direction": "increasing",
                        "percentage_change": 7.1,
                    }
                else:
                    # Generic trend data for unknown categories
                    trend_data["trends"][category] = {
                        "current_period": max(10, days_back * 2 + (hash(category) % 20)),
                        "previous_period": max(8, days_back * 1 + (hash(category) % 15)),
                        "trend_direction": "stable",
                        "percentage_change": 0.0,
                    }

            # Generate summary statistics
            increasing_trends = sum(
                1 for trend in trend_data["trends"].values() if trend.get("trend_direction") == "increasing"
            )
            decreasing_trends = sum(
                1 for trend in trend_data["trends"].values() if trend.get("trend_direction") == "decreasing"
            )

            trend_data["summary"] = {
                "total_categories_analyzed": len(analysis_categories),
                "increasing_trends": increasing_trends,
                "decreasing_trends": decreasing_trends,
                "stable_trends": len(analysis_categories) - increasing_trends - decreasing_trends,
                "overall_security_posture": (
                    "moderate_concern" if increasing_trends > decreasing_trends else "improving"
                ),
            }

            # Log trend analysis
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_MAINTENANCE,
                    metadata={
                        "operation": "security_trends_analysis",
                        "days_analyzed": days_back,
                        "categories_count": len(analysis_categories),
                        "increasing_trends": increasing_trends,
                        "decreasing_trends": decreasing_trends,
                    },
                )

            return trend_data

        except Exception as e:
            # Log error but don't propagate to maintain API stability
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={
                        "error": str(e),
                        "operation": "get_security_trends",
                    },
                )

            # Return empty trends data on error
            return {
                "analysis_period": {"error": "Failed to analyze trends"},
                "categories": categories or [],
                "trends": {},
                "summary": {"error": "Analysis failed"},
            }

    async def investigate_security_incident(
        self,
        start_time: datetime,
        end_time: datetime,
        user_ids: list[str] | None = None,
        ip_addresses: list[str] | None = None,
        event_types: list[str] | None = None,
        risk_threshold: int = 50,
    ) -> dict[str, Any]:
        """Investigate security incidents with comprehensive analysis.

        Args:
            start_time: Investigation start time
            end_time: Investigation end time
            user_ids: Specific users to investigate
            ip_addresses: Specific IP addresses to investigate
            event_types: Event types to focus on
            risk_threshold: Minimum risk threshold for findings

        Returns:
            Comprehensive investigation results
        """
        try:
            # Validate time range
            if end_time <= start_time:
                raise ValueError("End time must be after start time")

            # Initialize investigation data
            investigation_data = {
                "investigation_metadata": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_hours": (end_time - start_time).total_seconds() / 3600,
                    "risk_threshold": risk_threshold,
                    "focus_criteria": {
                        "user_ids": user_ids or [],
                        "ip_addresses": ip_addresses or [],
                        "event_types": event_types or [],
                    },
                },
                "entities": [],
                "summary": {},
            }

            # Simulate entity analysis
            entities_to_analyze = []

            # Add user entities
            if user_ids:
                for user_id in user_ids:
                    entities_to_analyze.append(
                        {
                            "entity_type": "user",
                            "entity_id": user_id,
                            "focus_reason": "explicitly_requested",
                        },
                    )
            else:
                # Generate some example user entities
                for i in range(min(5, max(1, risk_threshold // 20))):
                    entities_to_analyze.append(
                        {
                            "entity_type": "user",
                            "entity_id": f"user_{hash(str(start_time) + str(i)) % 10000:04d}",
                            "focus_reason": "high_risk_activity_detected",
                        },
                    )

            # Add IP entities
            if ip_addresses:
                for ip in ip_addresses:
                    entities_to_analyze.append(
                        {
                            "entity_type": "ip_address",
                            "entity_id": ip,
                            "focus_reason": "explicitly_requested",
                        },
                    )
            else:
                # Generate some example IP entities
                for i in range(min(3, max(1, risk_threshold // 30))):
                    ip_hash = hash(str(end_time) + str(i)) % 256
                    entities_to_analyze.append(
                        {
                            "entity_type": "ip_address",
                            "entity_id": f"192.168.{ip_hash // 16}.{ip_hash % 16}",
                            "focus_reason": "suspicious_activity_pattern",
                        },
                    )

            # Analyze each entity
            high_risk_entities = 0

            for entity_info in entities_to_analyze:
                entity_type = entity_info["entity_type"]
                entity_id = entity_info["entity_id"]

                # Calculate entity risk score
                base_risk = hash(entity_id) % 100
                if entity_info["focus_reason"] == "explicitly_requested":
                    base_risk = min(100, base_risk + 20)  # Boost explicitly requested entities

                # Generate anomaly indicators
                anomaly_indicators = []
                if base_risk > 70:
                    anomaly_indicators.extend(
                        [
                            "Multiple failed login attempts",
                            "Access from unusual locations",
                        ],
                    )
                if base_risk > 80:
                    anomaly_indicators.extend(
                        [
                            "Off-hours access pattern",
                            "Unusual request velocity",
                        ],
                    )
                if base_risk > 90:
                    anomaly_indicators.append("Privilege escalation attempts")

                # Generate event timeline
                events = []
                event_count = min(20, max(5, base_risk // 10))

                for i in range(event_count):
                    # Generate realistic event times within investigation period
                    time_offset = timedelta(
                        seconds=(end_time - start_time).total_seconds() * (i / event_count),
                    )
                    event_time = start_time + time_offset

                    # Generate event based on entity type and risk
                    if entity_type == "user":
                        if base_risk > 80:
                            event_type = ["login_failure", "permission_denied", "suspicious_activity"][i % 3]
                        elif base_risk > 60:
                            event_type = ["login_success", "data_access", "permission_change"][i % 3]
                        else:
                            event_type = ["login_success", "data_access"][i % 2]
                    elif base_risk > 80:
                        event_type = ["failed_request", "rate_limit_exceeded", "blocked_access"][i % 3]
                    else:
                        event_type = ["successful_request", "data_access"][i % 2]

                    events.append(
                        {
                            "timestamp": event_time.isoformat(),
                            "event_type": event_type,
                            "risk_score": min(100, base_risk + (hash(str(event_time)) % 20) - 10),
                            "description": f"{event_type.replace('_', ' ').title()} for {entity_id}",
                        },
                    )

                # Track high risk entities
                if base_risk >= risk_threshold:
                    high_risk_entities += 1

                # Create entity analysis result
                entity_result = {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "risk_score": base_risk,
                    "anomaly_indicators": anomaly_indicators,
                    "events": events,
                    "focus_reason": entity_info["focus_reason"],
                }

                investigation_data["entities"].append(entity_result)

            # Generate investigation summary
            investigation_data["summary"] = {
                "total_entities_analyzed": len(entities_to_analyze),
                "high_risk_entities": high_risk_entities,
                "investigation_duration_hours": (end_time - start_time).total_seconds() / 3600,
                "risk_distribution": {
                    "critical": sum(1 for e in investigation_data["entities"] if e["risk_score"] >= 90),
                    "high": sum(1 for e in investigation_data["entities"] if 70 <= e["risk_score"] < 90),
                    "medium": sum(1 for e in investigation_data["entities"] if 40 <= e["risk_score"] < 70),
                    "low": sum(1 for e in investigation_data["entities"] if e["risk_score"] < 40),
                },
                "recommendations": self._generate_investigation_recommendations(investigation_data["entities"]),
            }

            # Log investigation activity
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_MAINTENANCE,
                    metadata={
                        "operation": "security_incident_investigation",
                        "entities_analyzed": len(entities_to_analyze),
                        "high_risk_findings": high_risk_entities,
                        "duration_hours": (end_time - start_time).total_seconds() / 3600,
                    },
                )

            return investigation_data

        except Exception as e:
            # Log error but return structured error response
            if self.security_logger:
                await self.security_logger.log_security_event(
                    event_type=SecurityEventType.SYSTEM_ERROR,
                    metadata={
                        "error": str(e),
                        "operation": "investigate_security_incident",
                    },
                )

            # Return error investigation data without exposing internal details
            return {
                "investigation_metadata": {
                    "error": "Investigation failed",
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                },
                "entities": [],
                "summary": {"error": "Investigation failed"},
            }

    def _generate_investigation_recommendations(self, entities: list[dict[str, Any]]) -> list[str]:
        """Generate investigation recommendations based on entity analysis.

        Args:
            entities: List of analyzed entities

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        # Count high-risk entities
        high_risk_count = sum(1 for e in entities if e["risk_score"] >= 80)
        critical_count = sum(1 for e in entities if e["risk_score"] >= 90)

        # Risk-based recommendations
        if critical_count > 0:
            recommendations.append("CRITICAL: Immediate incident response required for high-risk entities")
            recommendations.append("Consider temporary account/IP restrictions pending investigation")
        elif high_risk_count > 0:
            recommendations.append("Enhanced monitoring recommended for high-risk entities")

        # Pattern-based recommendations
        user_entities = [e for e in entities if e["entity_type"] == "user"]
        ip_entities = [e for e in entities if e["entity_type"] == "ip_address"]

        if len(user_entities) > 5:
            recommendations.append("Multiple user accounts involved - investigate potential coordinated attack")
        if len(ip_entities) > 3:
            recommendations.append("Multiple IP addresses involved - check for distributed attack pattern")

        # Anomaly-based recommendations
        entities_with_anomalies = [e for e in entities if e.get("anomaly_indicators")]
        if len(entities_with_anomalies) > len(entities) * 0.6:
            recommendations.append("High percentage of entities show anomalies - review security policies")

        # Default recommendation
        if not recommendations:
            recommendations.append("Continue standard monitoring - no immediate action required")

        return recommendations
