"""Comprehensive unit tests for AuditService.

Tests compliance reporting, data retention, export functionality,
and regulatory compliance features for security audit trails.
"""

import asyncio
import csv
import json
import time
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.models import SecurityEvent, SecurityEventType
from src.auth.services.audit_service import (
    AuditReportRequest,
    AuditService,
    AuditStatistics,
    ComplianceReport,
    ExportFormat,
    RetentionPolicy,
)


class TestAuditServiceInitialization:
    """Test audit service initialization and configuration."""

    def test_init_default_configuration(self):
        """Test audit service initialization with default settings."""
        service = AuditService()

        # Check dependencies are initialized
        assert service.db is not None
        assert service.security_logger is not None

        # Check default retention policies
        assert len(service.retention_policies) == 2

        # Check standard events policy (90 days)
        standard_policy = next(p for p in service.retention_policies if p.retention_days == 90)
        assert SecurityEventType.LOGIN_FAILURE in standard_policy.event_types
        assert SecurityEventType.LOGIN_SUCCESS in standard_policy.event_types
        assert SecurityEventType.LOGOUT in standard_policy.event_types
        assert SecurityEventType.PASSWORD_CHANGED in standard_policy.event_types
        assert SecurityEventType.SESSION_EXPIRED in standard_policy.event_types

        # Check critical events policy (365 days)
        critical_policy = next(p for p in service.retention_policies if p.retention_days == 365)
        assert SecurityEventType.ACCOUNT_LOCKOUT in critical_policy.event_types
        assert SecurityEventType.SUSPICIOUS_ACTIVITY in critical_policy.event_types
        assert SecurityEventType.BRUTE_FORCE_ATTEMPT in critical_policy.event_types
        assert SecurityEventType.SECURITY_ALERT in critical_policy.event_types
        assert SecurityEventType.RATE_LIMIT_EXCEEDED in critical_policy.event_types

        # Check performance tracking
        assert isinstance(service._report_generation_times, list)
        assert len(service._report_generation_times) == 0

    def test_init_with_dependencies(self):
        """Test initialization with custom dependencies."""
        mock_db = MagicMock()
        mock_logger = MagicMock()

        service = AuditService(db=mock_db, security_logger=mock_logger)

        assert service.db == mock_db
        assert service.security_logger == mock_logger

    def test_custom_retention_policies(self):
        """Test audit service with custom retention policies."""
        custom_policies = [
            RetentionPolicy(
                event_types=[SecurityEventType.LOGIN_SUCCESS],
                retention_days=30,
                description="Short-term login retention",
            ),
        ]

        service = AuditService()
        service.retention_policies = custom_policies

        assert len(service.retention_policies) == 1
        assert service.retention_policies[0].retention_days == 30


class TestAuditServiceReportGeneration:
    """Test compliance report generation."""

    @pytest.fixture
    def service(self):
        """Create audit service with mocked dependencies."""
        with patch("src.auth.services.audit_service.SecurityEventsPostgreSQL") as mock_db_class:
            with patch("src.auth.services.audit_service.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                service = AuditService(db=mock_db, security_logger=mock_logger)

                yield service

    @pytest.fixture
    def sample_events(self):
        """Create sample security events for testing."""
        events = []
        base_time = datetime.now() - timedelta(days=7)

        for i in range(50):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS if i % 2 == 0 else SecurityEventType.LOGIN_FAILURE,
                user_id=f"user{i % 10}",
                ip_address=f"192.168.1.{100 + (i % 50)}",
                user_agent=f"Browser{i % 3}",
                severity="warning" if i % 3 == 0 else "info",
                source="auth",
                timestamp=base_time + timedelta(hours=i),
                details={"session_id": f"sess_{i}", "login_method": "password"},
            )
            events.append(event)

        return events

    async def test_generate_compliance_report_success(self, service, sample_events):
        """Test successful compliance report generation."""
        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            format=ExportFormat.CSV,
            include_metadata=True,
        )

        # Mock database response
        service.db.get_events_by_date_range.return_value = sample_events

        report = await service.generate_compliance_report(request)

        assert isinstance(report, ComplianceReport)
        assert len(report.report_id) > 0
        assert report.report_id.startswith("audit_")
        assert report.generated_at is not None
        assert report.report_request == request
        assert len(report.events) == len(sample_events)

        # Check statistics
        assert report.statistics.total_events == len(sample_events)
        assert report.statistics.unique_users == 10  # user0 to user9
        assert len(report.statistics.events_by_type) > 0
        assert len(report.statistics.events_by_severity) > 0

        # Verify logging
        service.security_logger.log_security_event.assert_called()
        call_args = service.security_logger.log_security_event.call_args
        assert call_args[1]["event_type"] == SecurityEventType.AUDIT_LOG_GENERATED

    async def test_generate_compliance_report_invalid_date_range(self, service):
        """Test report generation with invalid date range."""
        request = AuditReportRequest(
            start_date=datetime.now(),
            end_date=datetime.now() - timedelta(days=1),  # End before start
            format=ExportFormat.JSON,
        )

        with pytest.raises(ValueError, match="End date must be after start date"):
            await service.generate_compliance_report(request)

    async def test_generate_compliance_report_large_date_range_warning(self, service, sample_events):
        """Test warning for large date range reports."""
        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=400),  # > 1 year
            end_date=datetime.now(),
            format=ExportFormat.CSV,
        )

        service.db.get_events_by_date_range.return_value = sample_events

        with patch("src.auth.services.audit_service.logger") as mock_logger:
            await service.generate_compliance_report(request)

            # Should generate warning for large date range
            mock_logger.warning.assert_called()
            warning_call = mock_logger.warning.call_args
            assert "exceeds 1 year" in warning_call[0][0]

    async def test_generate_compliance_report_with_filters(self, service, sample_events):
        """Test report generation with various filters."""
        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            user_id="user1",  # Filter by specific user
            event_types=[SecurityEventType.LOGIN_SUCCESS],  # Filter by event type
            severity_levels=["medium"],  # Filter by severity
            format=ExportFormat.JSON,
            include_metadata=False,
        )

        # Mock database response
        service.db.get_events_by_date_range.return_value = sample_events

        report = await service.generate_compliance_report(request)

        # Verify filters were applied in _fetch_filtered_events
        assert isinstance(report, ComplianceReport)
        assert report.report_request.user_id == "user1"
        assert SecurityEventType.LOGIN_SUCCESS in report.report_request.event_types
        assert "medium" in report.report_request.severity_levels

    async def test_generate_compliance_report_performance_tracking(self, service, sample_events):
        """Test that report generation tracks performance metrics."""
        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            format=ExportFormat.CSV,
        )

        service.db.get_events_by_date_range.return_value = sample_events

        initial_count = len(service._report_generation_times)

        await service.generate_compliance_report(request)

        # Should track generation time
        assert len(service._report_generation_times) == initial_count + 1
        assert service._report_generation_times[-1] > 0  # Should be positive time

    async def test_generate_compliance_report_error_handling(self, service):
        """Test error handling during report generation."""
        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            format=ExportFormat.JSON,
        )

        # Mock database error
        service.db.get_events_by_date_range.side_effect = Exception("Database connection failed")

        with pytest.raises(Exception, match="Database connection failed"):
            await service.generate_compliance_report(request)

        # Should log the error
        service.security_logger.log_security_event.assert_called()
        error_call = service.security_logger.log_security_event.call_args
        assert error_call[1]["event_type"] == SecurityEventType.SYSTEM_ERROR


class TestAuditServiceExportFunctionality:
    """Test export functionality for different formats."""

    @pytest.fixture
    def service(self):
        """Create audit service with mocked dependencies."""
        with patch("src.auth.services.audit_service.SecurityEventsPostgreSQL") as mock_db_class:
            with patch("src.auth.services.audit_service.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                service = AuditService(db=mock_db, security_logger=mock_logger)

                yield service

    @pytest.fixture
    def sample_report(self):
        """Create sample compliance report for export testing."""
        events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="test_user",
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0",
                severity="info",
                session_id="test_session",
                timestamp=datetime.now(),
                details={"login_method": "password"},
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_FAILURE,
                user_id="test_user2",
                ip_address="192.168.1.101",
                user_agent="Chrome/91.0",
                severity="warning",
                session_id="test_session_2",
                timestamp=datetime.now() - timedelta(hours=1),
                details={"reason": "invalid_password"},
            ),
        ]

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            format=ExportFormat.CSV,
            include_metadata=True,
        )

        statistics = AuditStatistics(
            total_events=2,
            events_by_type={"login_success": 1, "login_failure": 1},
            events_by_severity={"low": 1, "medium": 1},
            unique_users=2,
            unique_ip_addresses=2,
            report_period="2024-01-01 to 2024-01-02 (1 days)",
        )

        return ComplianceReport(
            report_id="test_report_123",
            generated_at=datetime.now(),
            report_request=request,
            statistics=statistics,
            events=events,
        )

    async def test_export_report_csv_with_metadata(self, service, sample_report):
        """Test CSV export with metadata included."""
        csv_output = await service.export_report_csv(sample_report)

        assert isinstance(csv_output, str)
        assert len(csv_output) > 0

        # Parse CSV to verify structure
        csv_reader = csv.DictReader(StringIO(csv_output))
        rows = list(csv_reader)

        assert len(rows) == 2  # Two events

        # Check required columns
        expected_columns = [
            "timestamp",
            "event_type",
            "user_id",
            "ip_address",
            "user_agent",
            "severity",
            "session_id",
            "risk_score",
            "details",
        ]
        assert all(col in rows[0] for col in expected_columns)

        # Check data integrity
        assert rows[0]["event_type"] == "login_success"
        assert rows[0]["user_id"] == "test_user"
        assert rows[0]["ip_address"] == "192.168.1.100"
        assert "test_session" in rows[0]["session_id"]

        assert rows[1]["event_type"] == "login_failure"
        assert rows[1]["user_id"] == "test_user2"

    async def test_export_report_csv_without_metadata(self, service, sample_report):
        """Test CSV export without metadata."""
        # Modify request to exclude metadata
        sample_report.report_request.include_metadata = False

        csv_output = await service.export_report_csv(sample_report)

        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_output))
        rows = list(csv_reader)

        # Should not include details column
        assert "details" not in rows[0]

        # Should still have other columns
        expected_columns = [
            "timestamp",
            "event_type",
            "user_id",
            "ip_address",
            "user_agent",
            "severity",
            "session_id",
            "risk_score",
        ]
        assert all(col in rows[0] for col in expected_columns)

    async def test_export_report_json_format(self, service, sample_report):
        """Test JSON export format."""
        json_output = await service.export_report_json(sample_report)

        assert isinstance(json_output, str)

        # Parse JSON to verify structure
        data = json.loads(json_output)

        # Check report metadata
        assert "report_metadata" in data
        assert data["report_metadata"]["report_id"] == sample_report.report_id
        assert "generated_at" in data["report_metadata"]
        assert "statistics" in data["report_metadata"]
        assert "request_parameters" in data["report_metadata"]

        # Check events data
        assert "events" in data
        assert len(data["events"]) == 2

        # Verify event structure
        event1 = data["events"][0]
        assert event1["event_type"] == "login_success"
        assert event1["user_id"] == "test_user"
        assert event1["ip_address"] == "192.168.1.100"
        assert "timestamp" in event1

        # Check details inclusion
        if sample_report.report_request.include_metadata:
            assert "details" in event1

        # Check statistics
        stats = data["report_metadata"]["statistics"]
        assert stats["total_events"] == 2
        assert stats["unique_users"] == 2

    async def test_export_report_json_without_metadata(self, service, sample_report):
        """Test JSON export without metadata."""
        sample_report.report_request.include_metadata = False

        json_output = await service.export_report_json(sample_report)
        data = json.loads(json_output)

        # Events should not include metadata
        for event in data["events"]:
            assert "metadata" not in event

    async def test_export_handles_special_characters(self, service):
        """Test export handles special characters and encoding."""
        # Create event with special characters
        special_event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_SUCCESS,
            user_id="用户测试",  # Chinese characters
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 «Special» Chars",
            severity="info",
            source="auth",
            timestamp=datetime.now(),
            details={"note": "Special chars: àáâãäå øæå ñ"},
        )

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            format=ExportFormat.JSON,
            include_metadata=True,
        )

        statistics = AuditStatistics(
            total_events=1,
            events_by_type={"login_success": 1},
            events_by_severity={"low": 1},
            unique_users=1,
            unique_ip_addresses=1,
            report_period="test period",
        )

        report = ComplianceReport(
            report_id="special_chars_test",
            generated_at=datetime.now(),
            report_request=request,
            statistics=statistics,
            events=[special_event],
        )

        # Should handle special characters without error
        csv_output = await service.export_report_csv(report)
        json_output = await service.export_report_json(report)

        assert len(csv_output) > 0
        assert len(json_output) > 0

        # JSON should properly encode special characters
        data = json.loads(json_output)
        assert data["events"][0]["user_id"] == "用户测试"


class TestAuditServiceRetentionPolicies:
    """Test data retention policy enforcement."""

    @pytest.fixture
    def service(self):
        """Create audit service with mocked dependencies."""
        with patch("src.auth.services.audit_service.SecurityEventsPostgreSQL") as mock_db_class:
            with patch("src.auth.services.audit_service.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                service = AuditService(db=mock_db, security_logger=mock_logger)

                yield service

    async def test_enforce_retention_policies_success(self, service):
        """Test successful retention policy enforcement."""
        # Mock database cleanup responses
        service.db.cleanup_expired_events.side_effect = [10, 5]  # Two policies delete 10 and 5 events
        service.db.vacuum_database.return_value = None

        cleanup_stats = await service.enforce_retention_policies()

        # Should call cleanup for each policy
        assert service.db.cleanup_expired_events.call_count == 2

        # Should call vacuum since events were deleted
        service.db.vacuum_database.assert_called_once()

        # Should return cleanup statistics
        assert isinstance(cleanup_stats, dict)
        assert len(cleanup_stats) == 2  # Two retention policies

        # Check specific policy results
        standard_policy_key = "Standard security events - 90 days retention"
        critical_policy_key = "Critical security events - 1 year retention"

        assert cleanup_stats[standard_policy_key] == 10
        assert cleanup_stats[critical_policy_key] == 5

        # Should log maintenance event
        service.security_logger.log_security_event.assert_called()
        maintenance_call = service.security_logger.log_security_event.call_args
        assert maintenance_call[1]["event_type"] == SecurityEventType.SYSTEM_MAINTENANCE
        assert maintenance_call[1]["metadata"]["total_events_deleted"] == 15

    async def test_enforce_retention_policies_no_cleanup_needed(self, service):
        """Test retention policy enforcement when no cleanup is needed."""
        # Mock no events to clean up
        service.db.cleanup_expired_events.side_effect = [0, 0]

        cleanup_stats = await service.enforce_retention_policies()

        # Should not call vacuum if no events deleted
        service.db.vacuum_database.assert_not_called()

        assert all(count == 0 for count in cleanup_stats.values())

    async def test_enforce_retention_policies_with_cutoff_dates(self, service):
        """Test that retention policies use correct cutoff dates."""
        service.db.cleanup_expired_events.return_value = 0

        with patch("src.auth.services.audit_service.datetime") as mock_datetime:
            current_time = datetime(2024, 1, 15, 10, 0, 0)
            mock_datetime.now.return_value = current_time

            await service.enforce_retention_policies()

            # Check cutoff dates for each policy
            call_args_list = service.db.cleanup_expired_events.call_args_list

            # First call should be for 90-day policy
            first_call = call_args_list[0]
            expected_90_day_cutoff = current_time - timedelta(days=90)
            assert first_call[1]["cutoff_date"] == expected_90_day_cutoff

            # Second call should be for 365-day policy
            second_call = call_args_list[1]
            expected_365_day_cutoff = current_time - timedelta(days=365)
            assert second_call[1]["cutoff_date"] == expected_365_day_cutoff

    async def test_enforce_retention_policies_event_type_filtering(self, service):
        """Test that retention policies filter by event types correctly."""
        service.db.cleanup_expired_events.return_value = 0

        await service.enforce_retention_policies()

        call_args_list = service.db.cleanup_expired_events.call_args_list

        # First call (90-day policy) should include standard event types
        first_call_event_types = call_args_list[0][1]["event_types"]
        assert SecurityEventType.LOGIN_FAILURE in first_call_event_types
        assert SecurityEventType.LOGIN_SUCCESS in first_call_event_types
        assert SecurityEventType.LOGOUT in first_call_event_types

        # Second call (365-day policy) should include critical event types
        second_call_event_types = call_args_list[1][1]["event_types"]
        assert SecurityEventType.BRUTE_FORCE_ATTEMPT in second_call_event_types
        assert SecurityEventType.SECURITY_ALERT in second_call_event_types
        assert SecurityEventType.ACCOUNT_LOCKOUT in second_call_event_types

    async def test_enforce_retention_policies_error_handling(self, service):
        """Test error handling during retention policy enforcement."""
        # Mock database error
        service.db.cleanup_expired_events.side_effect = Exception("Database error during cleanup")

        with pytest.raises(Exception, match="Database error during cleanup"):
            await service.enforce_retention_policies()

        # Should log the error
        service.security_logger.log_security_event.assert_called()
        error_call = service.security_logger.log_security_event.call_args
        assert error_call[1]["event_type"] == SecurityEventType.SYSTEM_ERROR

    async def test_schedule_retention_cleanup_success(self, service):
        """Test scheduled retention cleanup."""
        service.db.cleanup_expired_events.side_effect = [5, 3]
        service.db.vacuum_database.return_value = None

        # Should complete without error
        await service.schedule_retention_cleanup()

        # Should call the main retention enforcement
        assert service.db.cleanup_expired_events.call_count == 2

    async def test_schedule_retention_cleanup_error(self, service):
        """Test scheduled retention cleanup error handling."""
        service.db.cleanup_expired_events.side_effect = Exception("Scheduled cleanup failed")

        with pytest.raises(Exception, match="Scheduled cleanup failed"):
            await service.schedule_retention_cleanup()


class TestAuditServiceStatistics:
    """Test audit statistics and analytics."""

    @pytest.fixture
    def service(self):
        """Create audit service with mocked dependencies."""
        with patch("src.auth.services.audit_service.SecurityEventsPostgreSQL") as mock_db_class:
            with patch("src.auth.services.audit_service.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                service = AuditService(db=mock_db, security_logger=mock_logger)

                yield service

    @pytest.fixture
    def sample_events_for_stats(self):
        """Create sample events for statistics testing."""
        events = []
        base_time = datetime.now() - timedelta(days=5)

        # Create diverse set of events for comprehensive statistics
        event_configs = [
            (SecurityEventType.LOGIN_SUCCESS, "user1", "192.168.1.100", "info"),
            (SecurityEventType.LOGIN_SUCCESS, "user1", "192.168.1.100", "info"),
            (SecurityEventType.LOGIN_FAILURE, "user1", "192.168.1.100", "warning"),
            (SecurityEventType.LOGIN_SUCCESS, "user2", "192.168.1.101", "info"),
            (SecurityEventType.BRUTE_FORCE_ATTEMPT, "user2", "192.168.1.101", "critical"),
            (SecurityEventType.SECURITY_ALERT, "user3", "192.168.1.102", "critical"),
            (SecurityEventType.LOGOUT, "user1", "192.168.1.100", "info"),
            (SecurityEventType.ACCOUNT_LOCKOUT, "user2", "192.168.1.101", "critical"),
        ]

        for i, (event_type, user_id, ip_address, severity) in enumerate(event_configs):
            event = SecurityEvent(
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                severity=severity,
                session_id=f"session_{i}",
                timestamp=base_time + timedelta(hours=i),
                details={"test_event": i},
                risk_score=10 + i * 5,
            )
            events.append(event)

        return events

    async def test_get_audit_statistics_comprehensive(self, service, sample_events_for_stats):
        """Test comprehensive audit statistics generation."""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        service.db.get_events_by_date_range.return_value = sample_events_for_stats

        statistics = await service.get_audit_statistics(start_date, end_date)

        assert isinstance(statistics, AuditStatistics)
        assert statistics.total_events == 8

        # Check events by type
        assert statistics.events_by_type["login_success"] == 3
        assert statistics.events_by_type["login_failure"] == 1
        assert statistics.events_by_type["brute_force_attempt"] == 1
        assert statistics.events_by_type["security_alert"] == 1
        assert statistics.events_by_type["logout"] == 1
        assert statistics.events_by_type["account_lockout"] == 1

        # Check events by severity
        assert statistics.events_by_severity["info"] == 4
        assert statistics.events_by_severity["warning"] == 1
        assert statistics.events_by_severity["critical"] == 3

        # Check unique counts
        assert statistics.unique_users == 3  # user1, user2, user3
        assert statistics.unique_ip_addresses == 3  # 192.168.1.100, 101, 102

        # Check report period formatting
        assert "days)" in statistics.report_period
        assert start_date.strftime("%Y-%m-%d") in statistics.report_period
        assert end_date.strftime("%Y-%m-%d") in statistics.report_period

    async def test_generate_statistics_empty_events(self, service):
        """Test statistics generation with no events."""
        request = AuditReportRequest(start_date=datetime.now() - timedelta(days=1), end_date=datetime.now())

        statistics = service._generate_statistics([], request)

        assert statistics.total_events == 0
        assert len(statistics.events_by_type) == 0
        assert len(statistics.events_by_severity) == 0
        assert statistics.unique_users == 0
        assert statistics.unique_ip_addresses == 0

    async def test_generate_statistics_none_values_handling(self, service):
        """Test statistics generation handles None values properly."""
        events_with_nones = [
            SecurityEvent(
                event_type=SecurityEventType.SYSTEM_ERROR,
                user_id=None,  # None user_id
                ip_address=None,  # None IP
                severity="critical",
                source="system",
                timestamp=datetime.now(),
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="real_user",
                ip_address="192.168.1.100",
                severity="info",
                source="auth",
                timestamp=datetime.now(),
            ),
        ]

        request = AuditReportRequest(start_date=datetime.now() - timedelta(days=1), end_date=datetime.now())

        statistics = service._generate_statistics(events_with_nones, request)

        assert statistics.total_events == 2
        assert statistics.unique_users == 1  # Only counts non-None user_ids
        assert statistics.unique_ip_addresses == 1  # Only counts non-None IPs

    async def test_get_audit_statistics_error_handling(self, service):
        """Test error handling in audit statistics generation."""
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        service.db.get_events_by_date_range.side_effect = Exception("Database query failed")

        with pytest.raises(Exception, match="Database query failed"):
            await service.get_audit_statistics(start_date, end_date)


class TestAuditServicePerformanceMetrics:
    """Test audit service performance monitoring."""

    @pytest.fixture
    def service(self):
        """Create audit service with mocked dependencies."""
        with patch("src.auth.services.audit_service.SecurityEventsPostgreSQL") as mock_db_class:
            with patch("src.auth.services.audit_service.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                service = AuditService(db=mock_db, security_logger=mock_logger)

                yield service

    def test_get_performance_metrics_no_reports(self, service):
        """Test performance metrics when no reports have been generated."""
        metrics = service.get_performance_metrics()

        assert metrics["reports_generated"] == 0
        assert metrics["average_generation_time"] == 0.0
        assert metrics["max_generation_time"] == 0.0
        assert metrics["min_generation_time"] == 0.0
        assert metrics["total_retention_policies"] == 2  # Default policies

    def test_get_performance_metrics_with_data(self, service):
        """Test performance metrics with report generation history."""
        # Simulate report generation times
        service._report_generation_times = [1.5, 2.3, 0.8, 3.1, 1.9]

        metrics = service.get_performance_metrics()

        assert metrics["reports_generated"] == 5
        assert metrics["average_generation_time"] == sum(service._report_generation_times) / 5
        assert metrics["max_generation_time"] == 3.1
        assert metrics["min_generation_time"] == 0.8
        assert metrics["total_retention_policies"] == 2

    async def test_performance_tracking_during_report_generation(self, service):
        """Test that performance is tracked during report generation."""
        request = AuditReportRequest(start_date=datetime.now() - timedelta(days=1), end_date=datetime.now())

        # Mock minimal database response
        service.db.get_events_by_date_range.return_value = []

        initial_count = len(service._report_generation_times)

        await service.generate_compliance_report(request)

        # Should have recorded performance
        assert len(service._report_generation_times) == initial_count + 1
        assert service._report_generation_times[-1] >= 0


class TestAuditServicePerformanceRequirements:
    """Test audit service performance requirements."""

    @pytest.fixture
    def service(self):
        """Create audit service with mocked dependencies."""
        with patch("src.auth.services.audit_service.SecurityEventsPostgreSQL") as mock_db_class:
            with patch("src.auth.services.audit_service.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                service = AuditService(db=mock_db, security_logger=mock_logger)

                yield service

    @pytest.mark.performance
    async def test_report_generation_performance_small_dataset(self, service):
        """Test report generation performance with small dataset."""
        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now(),
            format=ExportFormat.CSV,
        )

        # Mock small dataset (100 events)
        small_events = []
        for i in range(100):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id=f"user{i}",
                timestamp=datetime.now() - timedelta(hours=i),
                severity="info",
                source="auth",
            )
            small_events.append(event)

        service.db.get_events_by_date_range.return_value = small_events

        start_time = time.time()
        await service.generate_compliance_report(request)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 1000, f"Small report generation took {execution_time:.2f}ms (>1000ms limit)"

    @pytest.mark.performance
    async def test_csv_export_performance(self, service):
        """Test CSV export performance."""
        # Create moderate-sized dataset for export
        events = []
        for i in range(500):
            event = SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS if i % 2 == 0 else SecurityEventType.LOGIN_FAILURE,
                user_id=f"user{i % 50}",
                ip_address=f"192.168.1.{i % 255}",
                timestamp=datetime.now() - timedelta(minutes=i),
                severity="warning",
                source="auth",
                details={"session_id": f"session_{i}"},
            )
            events.append(event)

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            format=ExportFormat.CSV,
            include_metadata=True,
        )

        statistics = AuditStatistics(
            total_events=500,
            events_by_type={"login_success": 250, "login_failure": 250},
            events_by_severity={"medium": 500},
            unique_users=50,
            unique_ip_addresses=255,
            report_period="test period",
        )

        report = ComplianceReport(
            report_id="performance_test",
            generated_at=datetime.now(),
            report_request=request,
            statistics=statistics,
            events=events,
        )

        start_time = time.time()
        csv_output = await service.export_report_csv(report)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 500, f"CSV export took {execution_time:.2f}ms (>500ms limit)"
        assert len(csv_output) > 1000  # Should have substantial content

    @pytest.mark.performance
    async def test_json_export_performance(self, service):
        """Test JSON export performance."""
        # Create moderate-sized dataset for export
        events = []
        for i in range(300):
            event = SecurityEvent(
                event_type=SecurityEventType.SECURITY_ALERT if i % 10 == 0 else SecurityEventType.LOGIN_SUCCESS,
                user_id=f"user{i % 30}",
                ip_address=f"10.0.{i//100}.{i % 100}",
                timestamp=datetime.now() - timedelta(seconds=i * 10),
                severity="critical" if i % 10 == 0 else "info",
                source="security" if i % 10 == 0 else "auth",
                details={"complex_data": {"level1": {"level2": [f"item_{j}" for j in range(5)]}}},
            )
            events.append(event)

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now(),
            format=ExportFormat.JSON,
            include_metadata=True,
        )

        statistics = AuditStatistics(
            total_events=300,
            events_by_type={"login_success": 270, "security_alert": 30},
            events_by_severity={"low": 270, "high": 30},
            unique_users=30,
            unique_ip_addresses=100,
            report_period="test period",
        )

        report = ComplianceReport(
            report_id="json_performance_test",
            generated_at=datetime.now(),
            report_request=request,
            statistics=statistics,
            events=events,
        )

        start_time = time.time()
        json_output = await service.export_report_json(report)
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 800, f"JSON export took {execution_time:.2f}ms (>800ms limit)"

        # Verify JSON is valid and complete
        data = json.loads(json_output)
        assert len(data["events"]) == 300

    @pytest.mark.performance
    async def test_retention_cleanup_performance(self, service):
        """Test retention policy cleanup performance."""
        # Mock database cleanup to simulate different performance scenarios
        cleanup_times = [50, 75]  # Simulate cleanup times for different policies

        def mock_cleanup(*args, **kwargs):
            time.sleep(0.05)  # Simulate 50ms database operation
            return cleanup_times.pop(0) if cleanup_times else 0

        service.db.cleanup_expired_events.side_effect = mock_cleanup
        service.db.vacuum_database.return_value = None

        start_time = time.time()
        await service.enforce_retention_policies()
        end_time = time.time()

        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert execution_time < 1000, f"Retention cleanup took {execution_time:.2f}ms (>1000ms limit)"

    @pytest.mark.performance
    async def test_concurrent_report_generation_performance(self, service):
        """Test concurrent report generation performance."""

        async def generate_test_report(report_id: str):
            """Generate a test report."""
            request = AuditReportRequest(
                start_date=datetime.now() - timedelta(hours=1),
                end_date=datetime.now(),
                format=ExportFormat.CSV,
            )

            # Mock small dataset for each report
            test_events = [
                SecurityEvent(
                    event_type=SecurityEventType.LOGIN_SUCCESS,
                    user_id=f"user_{report_id}",
                    timestamp=datetime.now(),
                    severity="info",
                    source="auth",
                ),
            ]

            service.db.get_events_by_date_range.return_value = test_events

            return await service.generate_compliance_report(request)

        # Generate multiple reports concurrently
        start_time = time.time()
        reports = await asyncio.gather(
            generate_test_report("report1"),
            generate_test_report("report2"),
            generate_test_report("report3"),
            generate_test_report("report4"),
            generate_test_report("report5"),
        )
        end_time = time.time()

        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time_per_report = total_time / 5

        assert len(reports) == 5
        assert all(isinstance(report, ComplianceReport) for report in reports)
        assert avg_time_per_report < 500, f"Concurrent reports avg {avg_time_per_report:.2f}ms per report"


class TestAuditServiceErrorHandling:
    """Test audit service error handling and edge cases."""

    @pytest.fixture
    def service(self):
        """Create audit service with mocked dependencies."""
        with patch("src.auth.services.audit_service.SecurityEventsPostgreSQL") as mock_db_class:
            with patch("src.auth.services.audit_service.SecurityLogger") as mock_logger_class:
                mock_db = AsyncMock()
                mock_logger = AsyncMock()

                mock_db_class.return_value = mock_db
                mock_logger_class.return_value = mock_logger

                service = AuditService(db=mock_db, security_logger=mock_logger)

                yield service

    async def test_fetch_filtered_events_user_filter(self, service):
        """Test _fetch_filtered_events applies user filter correctly."""
        events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="user1",
                severity="info",
                source="auth",
                timestamp=datetime.now(),
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="user2",
                severity="info",
                source="auth",
                timestamp=datetime.now(),
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="user1",
                severity="info",
                source="auth",
                timestamp=datetime.now(),
            ),
        ]

        service.db.get_events_by_date_range.return_value = events

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            user_id="user1",  # Filter by user1
        )

        filtered_events = await service._fetch_filtered_events(request)

        assert len(filtered_events) == 2
        assert all(event.user_id == "user1" for event in filtered_events)

    async def test_fetch_filtered_events_event_type_filter(self, service):
        """Test _fetch_filtered_events applies event type filter correctly."""
        events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="user1",
                severity="info",
                source="auth",
                timestamp=datetime.now(),
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_FAILURE,
                user_id="user1",
                severity="warning",
                source="auth",
                timestamp=datetime.now(),
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGOUT,
                user_id="user1",
                severity="info",
                source="auth",
                timestamp=datetime.now(),
            ),
        ]

        service.db.get_events_by_date_range.return_value = events

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            event_types=[SecurityEventType.LOGIN_SUCCESS, SecurityEventType.LOGIN_FAILURE],
        )

        filtered_events = await service._fetch_filtered_events(request)

        assert len(filtered_events) == 2
        assert all(
            event.event_type in [SecurityEventType.LOGIN_SUCCESS, SecurityEventType.LOGIN_FAILURE]
            for event in filtered_events
        )

    async def test_fetch_filtered_events_severity_filter(self, service):
        """Test _fetch_filtered_events applies severity filter correctly."""
        events = [
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_SUCCESS,
                user_id="user1",
                severity="info",
                source="auth",
                timestamp=datetime.now(),
            ),
            SecurityEvent(
                event_type=SecurityEventType.LOGIN_FAILURE,
                user_id="user1",
                severity="warning",
                source="auth",
                timestamp=datetime.now(),
            ),
            SecurityEvent(
                event_type=SecurityEventType.SECURITY_ALERT,
                user_id="user1",
                severity="critical",
                source="auth",
                timestamp=datetime.now(),
            ),
        ]

        service.db.get_events_by_date_range.return_value = events

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            severity_levels=["warning", "critical"],
        )

        filtered_events = await service._fetch_filtered_events(request)

        assert len(filtered_events) == 2
        assert all(event.severity in ["warning", "critical"] for event in filtered_events)

    async def test_export_handles_empty_events(self, service):
        """Test export functions handle empty event lists."""
        request = AuditReportRequest(start_date=datetime.now() - timedelta(days=1), end_date=datetime.now())

        statistics = AuditStatistics(
            total_events=0,
            events_by_type={},
            events_by_severity={},
            unique_users=0,
            unique_ip_addresses=0,
            report_period="test period",
        )

        empty_report = ComplianceReport(
            report_id="empty_test",
            generated_at=datetime.now(),
            report_request=request,
            statistics=statistics,
            events=[],
        )

        # Should handle empty events gracefully
        csv_output = await service.export_report_csv(empty_report)
        json_output = await service.export_report_json(empty_report)

        # CSV should have headers but no data rows
        csv_lines = csv_output.strip().split("\n")
        assert len(csv_lines) == 1  # Only header line

        # JSON should have empty events array
        json_data = json.loads(json_output)
        assert json_data["events"] == []

    async def test_report_id_generation_uniqueness(self, service):
        """Test that report IDs are generated uniquely."""
        request = AuditReportRequest(start_date=datetime.now() - timedelta(days=1), end_date=datetime.now())

        service.db.get_events_by_date_range.return_value = []

        # Generate multiple reports rapidly
        reports = []
        for _ in range(5):
            report = await service.generate_compliance_report(request)
            reports.append(report)
            await asyncio.sleep(0.001)  # Small delay to ensure timestamp differences

        # All report IDs should be unique
        report_ids = [report.report_id for report in reports]
        assert len(set(report_ids)) == len(report_ids)  # All unique

        # All should start with "audit_"
        assert all(rid.startswith("audit_") for rid in report_ids)

    async def test_large_metadata_export_handling(self, service):
        """Test handling of events with large metadata during export."""
        # Create event with very large metadata
        large_metadata = {
            "large_field": "x" * 10000,  # 10KB of data
            "nested_data": {f"key_{i}": f"value_{i}" * 100 for i in range(100)},
        }

        large_event = SecurityEvent(
            event_type=SecurityEventType.SECURITY_ALERT,
            user_id="large_metadata_user",
            timestamp=datetime.now(),
            severity="critical",
            session_id="large_session",
            details=large_metadata,
            risk_score=85,
        )

        request = AuditReportRequest(
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            include_metadata=True,
        )

        statistics = AuditStatistics(
            total_events=1,
            events_by_type={"security_alert": 1},
            events_by_severity={"critical": 1},
            unique_users=1,
            unique_ip_addresses=0,
            report_period="test period",
        )

        report = ComplianceReport(
            report_id="large_metadata_test",
            generated_at=datetime.now(),
            report_request=request,
            statistics=statistics,
            events=[large_event],
        )

        # Should handle large metadata without error
        csv_output = await service.export_report_csv(report)
        json_output = await service.export_report_json(report)

        assert len(csv_output) > 10000  # Should contain the large metadata
        assert len(json_output) > 10000  # Should contain the large metadata

        # JSON should be valid despite large size
        json_data = json.loads(json_output)
        assert len(json_data["events"]) == 1
        assert "large_field" in json_data["events"][0]["details"]
