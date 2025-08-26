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
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from ..models import SecurityEventCreate, SecurityEventSeverity, SecurityEventType
from .alert_engine import AlertEngine, AlertEngineConfig
from .security_logger import LoggingConfig, SecurityLogger
from .security_monitor import MonitoringConfig, SecurityMonitor
from .suspicious_activity_detector import SuspiciousActivityConfig, SuspiciousActivityDetector


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

        # Initialize security services
        self.logger: SecurityLogger | None = None
        self.monitor: SecurityMonitor | None = None
        self.alert_engine: AlertEngine | None = None
        self.suspicious_detector: SuspiciousActivityDetector | None = None

        # Service failure tracking
        self._service_failures: dict[str, int] = {"logger": 0, "monitor": 0, "alert_engine": 0, "detector": 0}
        self._last_failure_reset = datetime.now(UTC)

        # Event correlation storage
        self._recent_events: list[tuple[datetime, SecurityEventCreate]] = []

        # Background tasks
        self._health_check_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

        # Initialize services
        asyncio.create_task(self._initialize_services())

    async def _initialize_services(self) -> None:
        """Initialize all security services based on configuration."""
        try:
            # Initialize security logger
            if self.config.enable_logging:
                self.logger = SecurityLogger(config=self.config.logging_config)

            # Initialize security monitor
            if self.config.enable_monitoring:
                self.monitor = SecurityMonitor(config=self.config.monitoring_config)

            # Initialize alert engine with notification handlers
            if self.config.enable_alerting:
                # Create notification handlers (this would be configured externally in production)
                notification_handlers = self._create_default_notification_handlers()
                self.alert_engine = AlertEngine(
                    config=self.config.alert_engine_config,
                    notification_handlers=notification_handlers,
                )

            # Initialize suspicious activity detector
            if self.config.enable_suspicious_activity_detection:
                self.suspicious_detector = SuspiciousActivityDetector(config=self.config.suspicious_activity_config)

            # Start background tasks
            self._start_background_tasks()

        except Exception as e:
            print(f"Error initializing security services: {e}")

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
            if self.logger and self._is_service_healthy("logger"):
                try:
                    logged = await self.logger.log_event(
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
            if self.monitor and self._is_service_healthy("monitor"):
                try:
                    if event.event_type == SecurityEventType.LOGIN_FAILURE:
                        monitor_alerts = await self.monitor.track_failed_authentication(
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
            if self.suspicious_detector and self._is_service_healthy("detector"):
                try:
                    analysis_result = await self.suspicious_detector.analyze_activity(event, additional_context)

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

        except Exception as e:
            print(f"Event enrichment failed: {e}")
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

        for timestamp, recent_event in self._recent_events:
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

        print(f"Service error in {service_name}: {error}")

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
            except Exception as e:
                print(f"Health check error: {e}")
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
            if self.logger:
                logger_metrics = await self.logger.get_metrics()
                self.metrics.logger_healthy = logger_metrics.get("health", {}).get("is_processing", False)
        except:
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
            except Exception as e:
                print(f"Cleanup error: {e}")
                await asyncio.sleep(300)

    async def _perform_cleanup(self) -> None:
        """Perform cleanup tasks."""
        # Clean up correlation window (already done in _add_to_correlation_window)

        # Trigger cleanup in individual services
        try:
            if self.logger:
                # Logger has its own cleanup via retention policies
                pass

            # Additional cleanup tasks would go here
        except Exception as e:
            print(f"Service cleanup error: {e}")

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
            if self.logger:
                metrics["logger"] = await self.logger.get_metrics()
        except:
            pass

        try:
            if self.monitor:
                metrics["monitor"] = await self.monitor.get_metrics()
        except:
            pass

        try:
            if self.alert_engine:
                metrics["alert_engine"] = await self.alert_engine.get_metrics()
        except:
            pass

        return metrics

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
            if self.logger:
                await self.logger.shutdown()
        except:
            pass

        try:
            if self.alert_engine:
                await self.alert_engine.shutdown()
        except:
            pass
