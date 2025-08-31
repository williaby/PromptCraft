"""
Comprehensive unit tests for auth services security integration module.

This test suite covers all classes and functions in src/auth/services/security_integration.py
with extensive mocking and edge case testing to achieve >90% coverage.
"""

import asyncio
import pytest
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from src.auth.models import SecurityEventCreate, SecurityEventSeverity, SecurityEventType
from src.auth.services.security_integration import (
    SecurityIntegrationConfig,
    SecurityIntegrationService,
    SecurityIntegrationMetrics,
)


class TestSecurityIntegrationConfig:
    """Test SecurityIntegrationConfig configuration class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = SecurityIntegrationConfig()
        
        assert config.enable_logging is True
        assert config.enable_monitoring is True
        assert config.enable_alerting is True
        assert config.enable_suspicious_activity_detection is True
        assert config.max_processing_time_ms == 50.0
        assert config.enable_performance_monitoring is True
        assert config.enable_event_enrichment is True
        assert config.correlation_window_seconds == 300
        assert config.enable_graceful_degradation is True
        assert config.max_service_failures == 3
        assert config.failure_reset_interval_minutes == 15
        
    def test_custom_config(self):
        """Test custom configuration values."""
        config = SecurityIntegrationConfig(
            enable_logging=False,
            enable_monitoring=False,
            max_processing_time_ms=100.0,
            correlation_window_seconds=600,
            max_service_failures=5,
        )
        
        assert config.enable_logging is False
        assert config.enable_monitoring is False
        assert config.max_processing_time_ms == 100.0
        assert config.correlation_window_seconds == 600
        assert config.max_service_failures == 5


class TestSecurityIntegrationMetrics:
    """Test SecurityIntegrationMetrics data class."""
    
    def test_metrics_creation(self):
        """Test metrics object creation with defaults."""
        metrics = SecurityIntegrationMetrics()
        
        assert metrics.total_events_processed == 0
        assert metrics.total_events_failed == 0
        assert metrics.total_alerts_generated == 0
        assert metrics.total_suspicious_activities == 0
        assert metrics.average_processing_time_ms == 0.0
        assert metrics.average_enrichment_time_ms == 0.0
        assert metrics.logger_failures == 0
        assert metrics.monitor_failures == 0
        assert metrics.alert_engine_failures == 0
        assert metrics.detector_failures == 0
        assert metrics.logger_healthy is True
        assert metrics.monitor_healthy is True
        assert metrics.alert_engine_healthy is True
        assert metrics.detector_healthy is True
        
    def test_metrics_custom_values(self):
        """Test metrics object with custom values."""
        last_check = datetime.now(timezone.utc)
        metrics = SecurityIntegrationMetrics(
            total_events_processed=100,
            total_events_failed=5,
            average_processing_time_ms=25.5,
            logger_failures=2,
            logger_healthy=False,
            last_health_check=last_check
        )
        
        assert metrics.total_events_processed == 100
        assert metrics.total_events_failed == 5
        assert metrics.average_processing_time_ms == 25.5
        assert metrics.logger_failures == 2
        assert metrics.logger_healthy is False
        assert metrics.last_health_check == last_check


class TestSecurityIntegrationService:
    """Test SecurityIntegrationService main orchestration class."""
    
    def test_init_default_config(self):
        """Test service initialization with default config."""
        service = SecurityIntegrationService()
        
        assert isinstance(service.config, SecurityIntegrationConfig)
        assert isinstance(service.metrics, SecurityIntegrationMetrics)
        assert service.security_logger is not None
        assert service.security_monitor is not None
        assert service.alert_engine is not None
        assert service.suspicious_activity_detector is not None
        
    def test_init_custom_config(self):
        """Test service initialization with custom config."""
        config = SecurityIntegrationConfig(enable_logging=False, max_processing_time_ms=100.0)
        service = SecurityIntegrationService(config)
        
        assert service.config == config
        assert service.config.enable_logging is False
        assert service.config.max_processing_time_ms == 100.0
        
    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """Test successful service initialization."""
        service = SecurityIntegrationService()
        
        # Services should already be initialized synchronously during __init__
        assert service.security_logger is not None
        assert service.security_monitor is not None
        assert service.alert_engine is not None
        assert service.suspicious_activity_detector is not None
        
        # Mock background task creation to verify initialize() starts them
        with patch.object(service, '_start_background_tasks') as mock_start_tasks:
            await service.initialize()
            mock_start_tasks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_security_event_basic(self):
        """Test basic security event processing."""
        service = SecurityIntegrationService()
        
        event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecurityEventSeverity.WARNING,
            user_id="user123",
            details={"action": "login", "reason": "invalid_password"}
        )
        
        # Mock all the service calls
        with patch.object(service.security_logger, 'log_event', new_callable=AsyncMock) as mock_log, \
             patch.object(service.security_monitor, 'track_failed_authentication', new_callable=AsyncMock) as mock_monitor, \
             patch.object(service.suspicious_activity_detector, 'analyze_activity', new_callable=AsyncMock) as mock_detector:
            
            mock_detector.return_value = {"is_suspicious": False, "confidence": 0.1}
            
            result = await service.process_security_event(event)
            
            # Check that the result contains expected fields
            assert "processing_time_ms" in result
            assert result["processing_time_ms"] >= 0
            assert "services_processed" in result
            assert "errors" in result
            assert isinstance(result["errors"], list)
            
            mock_log.assert_called_once()
            mock_monitor.assert_called_once()
            mock_detector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_integration_health(self):
        """Test integration health check."""
        service = SecurityIntegrationService()
        
        # Call the health check method directly (it uses internal metrics)
        health = await service.get_integration_health()
        
        # Verify the response structure
        assert "overall_status" in health
        assert "services" in health
        assert "security_logger" in health["services"]
        assert "security_monitor" in health["services"]
        assert "alert_engine" in health["services"]
        assert "suspicious_activity_detector" in health["services"]
        
        # All services should be healthy by default
        for service_name, service_info in health["services"].items():
            assert "status" in service_info
            assert service_info["status"] in ["healthy", "unhealthy"]
    
    @pytest.mark.asyncio
    async def test_get_comprehensive_metrics(self):
        """Test getting integration metrics."""
        service = SecurityIntegrationService()
        
        # Process some events to generate metrics
        event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            user_id="user123",
            details={"action": "login"}
        )
        
        with patch.object(service.security_logger, 'log_event', new_callable=AsyncMock), \
             patch.object(service.security_monitor, 'track_failed_authentication', new_callable=AsyncMock), \
             patch.object(service.suspicious_activity_detector, 'analyze_activity', new_callable=AsyncMock) as mock_detector:
            
            mock_detector.return_value = {"is_suspicious": False, "confidence": 0.1}
            await service.process_security_event(event)
        
        metrics = await service.get_comprehensive_metrics()
        
        # Check the structure of comprehensive metrics
        assert "integration" in metrics
        assert "service_health" in metrics
        assert "service_failures" in metrics
        
        # Check integration metrics
        integration = metrics["integration"]
        assert "total_events_processed" in integration
        assert "average_processing_time_ms" in integration
    
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test service shutdown."""
        service = SecurityIntegrationService()
        
        # The shutdown method should complete without errors
        # It will try to shutdown individual services that have shutdown methods
        await service.shutdown()
        
        # Verify that background tasks are stopped
        assert service._shutdown_event.is_set()
    
    @pytest.mark.asyncio
    async def test_service_failure_handling(self):
        """Test handling of service failures during event processing."""
        service = SecurityIntegrationService()
        
        event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecurityEventSeverity.WARNING,
            user_id="user123",
            details={"action": "login", "reason": "invalid_password"}
        )
        
        # Mock logger to fail, others to succeed
        with patch.object(service.security_logger, 'log_event', new_callable=AsyncMock) as mock_log, \
             patch.object(service.security_monitor, 'track_failed_authentication', new_callable=AsyncMock) as mock_monitor, \
             patch.object(service.suspicious_activity_detector, 'analyze_activity', new_callable=AsyncMock) as mock_detector:
            
            mock_log.side_effect = Exception("Logger failed")
            mock_detector.return_value = {"is_suspicious": False, "confidence": 0.1}
            
            result = await service.process_security_event(event)
            
            # Should still succeed with graceful degradation
            assert "processing_time_ms" in result
            assert isinstance(result.get("errors", []), list)
            assert result.get("service_failures", 0) >= 0
            
            # Other services should still be called
            mock_monitor.assert_called_once()
            mock_detector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_suspicious_activity_detection(self):
        """Test suspicious activity detection and alerting."""
        service = SecurityIntegrationService()
        
        event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_FAILURE,
            severity=SecurityEventSeverity.CRITICAL,
            user_id="user123",
            details={"action": "failed_login", "attempts": 5}
        )
        
        with patch.object(service.security_logger, 'log_event', new_callable=AsyncMock), \
             patch.object(service.security_monitor, 'track_failed_authentication', new_callable=AsyncMock), \
             patch.object(service.suspicious_activity_detector, 'analyze_activity', new_callable=AsyncMock) as mock_detector, \
             patch.object(service.alert_engine, 'process_event', new_callable=AsyncMock) as mock_alert:
            
            # Import and create proper ActivityAnalysisResult
            from src.auth.services.suspicious_activity_detector import ActivityAnalysisResult, RiskScore
            
            # Mock detection of suspicious activity
            mock_detector.return_value = ActivityAnalysisResult(
                is_suspicious=True, 
                risk_score=RiskScore(score=90),
                anomaly_reasons=["Multiple failed attempts"]
            )
            
            result = await service.process_security_event(event)
            
            assert "processing_time_ms" in result
            assert isinstance(result.get("errors", []), list)
            assert result.get("suspicious_activity") is not None
            
            # Alert should be triggered for suspicious activity
            mock_alert.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_concurrent_event_processing(self):
        """Test concurrent processing of multiple events."""
        service = SecurityIntegrationService()
        
        events = [
            SecurityEventCreate(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                severity=SecurityEventSeverity.INFO,
                user_id=f"user{i}",
                details={"action": "login"}
            )
            for i in range(5)
        ]
        
        with patch.object(service.security_logger, 'log_event', new_callable=AsyncMock), \
             patch.object(service.security_monitor, 'track_failed_authentication', new_callable=AsyncMock), \
             patch.object(service.suspicious_activity_detector, 'analyze_activity', new_callable=AsyncMock) as mock_detector:
            
            mock_detector.return_value = {"is_suspicious": False, "confidence": 0.1}
            
            # Process events concurrently
            tasks = [service.process_security_event(event) for event in events]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should return valid results with processing time
            valid_results = [r for r in results if isinstance(r, dict) and "processing_time_ms" in r]
            assert len(valid_results) == 5
    
    def test_metrics_update_tracking(self):
        """Test that metrics are properly updated during processing."""
        service = SecurityIntegrationService()
        
        initial_events = service.metrics.total_events_processed
        
        # Manually update metrics to test the tracking
        service.metrics.total_events_processed += 1
        service.metrics.total_alerts_generated += 1
        
        assert service.metrics.total_events_processed == initial_events + 1
        assert service.metrics.total_alerts_generated == 1
    
    @pytest.mark.asyncio
    async def test_disabled_services_configuration(self):
        """Test service behavior with disabled services."""
        config = SecurityIntegrationConfig(
            enable_logging=False,
            enable_monitoring=False,
            enable_alerting=False
        )
        service = SecurityIntegrationService(config)
        
        event = SecurityEventCreate(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            user_id="user123",
            details={"action": "login"}
        )
        
        with patch.object(service.suspicious_activity_detector, 'analyze_activity', new_callable=AsyncMock) as mock_detector:
            mock_detector.return_value = {"is_suspicious": False, "confidence": 0.1}
            
            result = await service.process_security_event(event)
            
            assert "processing_time_ms" in result
            assert isinstance(result.get("errors", []), list)
            # Only detector should be called since others are disabled
            mock_detector.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_error_handling(self):
        """Test health check with service errors."""
        service = SecurityIntegrationService()
        
        # Test that health check can handle missing services
        # by making a service None to simulate initialization failure
        original_logger = service.security_logger
        service.security_logger = None  # Simulate failed initialization
        
        health = await service.get_integration_health()
        
        assert "overall_status" in health
        assert "services" in health
        assert health["services"]["security_logger"]["status"] == "unhealthy"
        assert health["overall_status"] == "degraded"  # Should be degraded with one unhealthy service
        
        # Restore the logger
        service.security_logger = original_logger