"""
Unit tests for the Analytics Engine.

Focuses on testing individual components like UsageTracker, PatternDetector,
and InsightGenerator in isolation.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from src.utils.datetime_compat import UTC
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.analytics_engine import (
    AnalyticsEngine,
    InsightGenerator,
    OptimizationInsight,
    PatternDetector,
    UsageEvent,
    UsageTracker,
    UserBehaviorPattern,
)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Create a temporary database path for testing."""
    return tmp_path / "test_analytics.db"


@pytest.fixture
def usage_tracker(db_path: Path) -> UsageTracker:
    """Fixture for UsageTracker with a temporary database."""
    return UsageTracker(db_path)


@pytest.fixture
def pattern_detector(usage_tracker: UsageTracker) -> PatternDetector:
    """Fixture for PatternDetector."""
    return PatternDetector(usage_tracker)


@pytest.fixture
def insight_generator(usage_tracker: UsageTracker, pattern_detector: PatternDetector) -> InsightGenerator:
    """Fixture for InsightGenerator."""
    return InsightGenerator(usage_tracker, pattern_detector)


@pytest.fixture
def analytics_engine(db_path: Path) -> AnalyticsEngine:
    """Fixture for the main AnalyticsEngine."""
    return AnalyticsEngine(db_path)


# ===================================
# UsageTracker Tests
# ===================================


class TestUsageTracker:
    """Tests for the UsageTracker class."""

    def test_initialization(self, usage_tracker: UsageTracker, db_path: Path) -> None:
        """Test that the database is initialized correctly."""
        assert usage_tracker.db_path == db_path
        assert db_path.exists()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_events'")
            assert cursor.fetchone() is not None
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='session_metrics'")
            assert cursor.fetchone() is not None

    def test_track_event(self, usage_tracker: UsageTracker) -> None:
        """Test tracking a single event."""
        user_id = "user1"
        session_id = "session1"
        event_type = "command_executed"
        event_data = {"command": "test", "success": True}

        usage_tracker.track_event(event_type, event_data, user_id, session_id)

        assert len(usage_tracker.session_events) == 1
        event = usage_tracker.session_events[0]
        assert event.user_id == user_id
        assert event.session_id == session_id
        assert event.event_type == event_type
        assert event.event_data == event_data

        # Check that session metrics are updated
        assert session_id in usage_tracker.active_sessions
        session = usage_tracker.active_sessions[session_id]
        assert session.commands_executed == 1

    def test_track_multiple_event_types(self, usage_tracker: UsageTracker) -> None:
        """Test tracking various event types and their impact on session metrics."""
        user_id = "user2"
        session_id = "session2"

        # Command execution
        usage_tracker.track_event("command_executed", {"command": "test1", "success": True}, user_id, session_id)
        # Function call
        usage_tracker.track_event("function_called", {"function_name": "func1"}, user_id, session_id)
        # Category loaded
        usage_tracker.track_event("category_loaded", {"category": "cat1", "token_cost": 100}, user_id, session_id)
        # Help request
        usage_tracker.track_event("help_requested", {}, user_id, session_id)
        # Optimization applied
        usage_tracker.track_event("optimization_applied", {}, user_id, session_id)
        # Performance mode change
        usage_tracker.track_event("performance_mode_changed", {"mode": "aggressive"}, user_id, session_id)
        # Command failure
        usage_tracker.track_event("command_executed", {"command": "test2", "success": False}, user_id, session_id)

        session = usage_tracker.active_sessions[session_id]
        assert session.commands_executed == 2
        assert "func1" in session.functions_used
        assert "cat1" in session.categories_loaded
        assert session.total_tokens_used == 100
        assert session.help_requests == 1
        assert session.optimization_applied is True
        assert session.performance_mode == "aggressive"
        assert session.errors_encountered == 1

    def test_persist_event(self, usage_tracker: UsageTracker, db_path: Path) -> None:
        """Test that events are persisted to the database."""
        user_id = "user3"
        session_id = "session3"
        event_type = "command_executed"
        event_data = {"command": "persist_test"}

        usage_tracker.track_event(event_type, event_data, user_id, session_id)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usage_events WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row[2] == event_type
            assert json.loads(row[3]) == event_data

    def test_end_session_not_found(self, usage_tracker: UsageTracker) -> None:
        """Test ending a session that doesn't exist."""
        result = usage_tracker.end_session("non_existent_session")
        assert result is None

    def test_end_session_success(self, usage_tracker: UsageTracker, db_path: Path) -> None:
        """Test ending a session successfully."""
        user_id = "user4"
        session_id = "session4"
        usage_tracker.track_event("command_executed", {"command": "test"}, user_id, session_id)

        session = usage_tracker.end_session(session_id)
        assert session is not None
        assert session.end_time is not None
        assert session_id not in usage_tracker.active_sessions

        # Verify persistence
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM session_metrics WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == session_id

    def test_get_recent_events(self, usage_tracker: UsageTracker) -> None:
        """Test retrieving recent events with filtering."""
        now = datetime.now(UTC)
        with patch("src.core.analytics_engine.datetime") as mock_dt:
            mock_dt.now.return_value = now
            usage_tracker.track_event("command_executed", {}, "user1", "session1")
            mock_dt.now.return_value = now - timedelta(hours=1)
            usage_tracker.track_event("command_executed", {}, "user2", "session2")
            mock_dt.now.return_value = now - timedelta(hours=3)
            usage_tracker.track_event("command_executed", {}, "user1", "session3")

        # Test filtering by time
        recent = usage_tracker.get_recent_events(hours=2)
        assert len(recent) == 2

        # Test filtering by user
        user1_events = usage_tracker.get_recent_events(user_id="user1")
        assert len(user1_events) == 2

        # Test filtering by event type
        usage_tracker.track_event("help_requested", {}, "user1", "session1")
        help_events = usage_tracker.get_recent_events(event_type="help_requested")
        assert len(help_events) == 1

    def test_get_session_summary_active(self, usage_tracker: UsageTracker) -> None:
        """Test getting a summary for an active session."""
        usage_tracker.track_event("command_executed", {}, "user1", "session1")
        summary = usage_tracker.get_session_summary("session1")
        assert summary is not None
        assert summary["session_id"] == "session1"
        assert summary["commands_executed"] == 1

    def test_get_session_summary_from_db(self, usage_tracker: UsageTracker) -> None:
        """Test getting a summary for a session loaded from the database."""
        usage_tracker.track_event("command_executed", {}, "user1", "session1")
        usage_tracker.end_session("session1")  # Persists the session

        summary = usage_tracker.get_session_summary("session1")
        assert summary is not None
        assert summary["session_id"] == "session1"
        assert summary["duration_seconds"] is not None

    def test_load_session_from_db_not_found(self, usage_tracker: UsageTracker) -> None:
        """Test loading a non-existent session from the database."""
        session = usage_tracker._load_session_from_db("non_existent")
        assert session is None


# ===================================
# PatternDetector Tests
# ===================================


class TestPatternDetector:
    """Tests for the PatternDetector class."""

    def test_detect_patterns_insufficient_data(self, pattern_detector: PatternDetector) -> None:
        """Test that pattern detection returns empty with insufficient data."""
        patterns = pattern_detector.detect_patterns("user1")
        assert not patterns

    def test_detect_sequential_patterns(self, pattern_detector: PatternDetector) -> None:
        """Test detection of sequential command patterns."""
        # Simulate events
        for i in range(5):
            pattern_detector.usage_tracker.track_event("command_executed", {"command": "cmd1"}, "user1", f"session{i}")
            pattern_detector.usage_tracker.track_event("command_executed", {"command": "cmd2"}, "user1", f"session{i}")

        patterns = pattern_detector._detect_sequential_patterns(pattern_detector.usage_tracker.session_events)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "sequential"
        assert pattern.typical_sequence == ["cmd1", "cmd2"]
        assert pattern.frequency == 1.0

    def test_detect_temporal_patterns(self, pattern_detector: PatternDetector) -> None:
        """Test detection of time-based usage patterns."""
        # Simulate high usage at a specific hour
        with patch("src.core.analytics_engine.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2023, 1, 1, 14, 30, tzinfo=UTC)  # 2 PM
            for _ in range(10):
                pattern_detector.usage_tracker.track_event(
                    "category_loaded",
                    {"category": "devops"},
                    "user1",
                    "session1",
                )

        patterns = pattern_detector._detect_temporal_patterns(pattern_detector.usage_tracker.session_events)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "temporal"
        assert "14:00" in pattern.description
        assert "devops" in pattern.associated_categories

    def test_detect_preference_patterns(self, pattern_detector: PatternDetector) -> None:
        """Test detection of user preference patterns."""
        # Simulate preference for a performance mode
        for _ in range(5):
            pattern_detector.usage_tracker.track_event(
                "performance_mode_changed",
                {"mode": "aggressive"},
                "user1",
                "session1",
            )
        # Simulate preference for a category
        for _ in range(10):
            pattern_detector.usage_tracker.track_event("category_loaded", {"category": "security"}, "user1", "session1")

        patterns = pattern_detector._detect_preference_patterns(pattern_detector.usage_tracker.session_events)

        assert len(patterns) == 2
        mode_pattern = next(p for p in patterns if "mode" in p.pattern_id)
        category_pattern = next(p for p in patterns if "category" in p.pattern_id)

        assert mode_pattern.description == "Strong preference for aggressive performance mode"
        assert category_pattern.description == "Frequently uses security category"

    def test_detect_workflow_patterns(self, pattern_detector: PatternDetector) -> None:
        """Test detection of workflow-specific patterns."""
        # Simulate optimization workflow
        for i in range(5):
            pattern_detector.usage_tracker.track_event(
                "optimization_applied",
                {"task_type": "testing"},
                "user1",
                f"session{i}",
            )

        patterns = pattern_detector._detect_workflow_patterns(pattern_detector.usage_tracker.session_events)

        assert len(patterns) == 1
        pattern = patterns[0]
        assert pattern.pattern_type == "workflow"
        assert "testing" in pattern.description
        assert "test" in pattern.associated_categories

    def test_infer_categories_from_commands(self, pattern_detector: PatternDetector) -> None:
        """Test inference of categories from command sequences."""
        commands = ("load-category", "optimize-for", "unknown-command")
        categories = pattern_detector._infer_categories_from_commands(commands)
        assert "management" in categories
        assert "optimization" in categories
        assert len(categories) == 2

    def test_get_optimization_categories(self, pattern_detector: PatternDetector) -> None:
        """Test getting categories associated with task optimization."""
        categories = pattern_detector._get_optimization_categories("testing")
        assert "test" in categories
        assert "quality" in categories

        # Test fallback for unknown task type
        categories = pattern_detector._get_optimization_categories("unknown")
        assert not categories


# ===================================
# InsightGenerator Tests
# ===================================


class TestInsightGenerator:
    """Tests for the InsightGenerator class."""

    def test_generate_insights_no_patterns(self, insight_generator: InsightGenerator) -> None:
        """Test that no insights are generated when there are no patterns."""
        insights = insight_generator.generate_insights("user1")
        assert not insights

    def test_generate_performance_insights(self, insight_generator: InsightGenerator) -> None:
        """Test generation of performance optimization insights."""
        # Create a mock pattern
        pattern = UserBehaviorPattern(
            pattern_id="seq_123",
            pattern_type="sequential",
            description="",
            frequency=0.8,
            confidence=0.9,
            associated_categories=[],
            typical_sequence=["cmd1", "cmd2"],
            performance_impact={"token_savings": 300},
            suggested_optimizations=[],
        )

        insights = insight_generator._generate_performance_insights([pattern], "user1")

        assert len(insights) == 1
        insight = insights[0]
        assert insight.insight_type == "performance"
        assert "Command Sequence Optimization" in insight.title

    def test_generate_workflow_insights(self, insight_generator: InsightGenerator) -> None:
        """Test generation of workflow optimization insights."""
        pattern = UserBehaviorPattern(
            pattern_id="workflow_456",
            pattern_type="workflow",
            description="Frequently optimizes for testing tasks",
            frequency=0.9,
            confidence=0.9,
            associated_categories=["test"],
            typical_sequence=[],
            performance_impact={"workflow_efficiency": 400},
            suggested_optimizations=[],
        )

        insights = insight_generator._generate_workflow_insights([pattern], "user1")

        assert len(insights) == 1
        insight = insights[0]
        assert insight.insight_type == "workflow"
        assert "Automate testing Workflow" in insight.title

    def test_generate_learning_insights(self, insight_generator: InsightGenerator) -> None:
        """Test generation of learning and education insights."""
        # Simulate many help requests
        for _ in range(10):
            insight_generator.usage_tracker.track_event("help_requested", {}, "user1", "session1")

        insights = insight_generator._generate_learning_insights("user1")

        assert len(insights) == 1
        insight = insights[0]
        assert insight.insight_type == "learning"
        assert "Learning Opportunity Detected" in insight.title

    def test_generate_system_insights(self, insight_generator: InsightGenerator) -> None:
        """Test generation of system-wide optimization insights."""
        # Create mock patterns
        patterns = [
            UserBehaviorPattern(
                pattern_id=f"seq_{i}",
                pattern_type="sequential",
                description="",
                frequency=0.8,
                confidence=0.9,
                associated_categories=[],
                typical_sequence=[f"cmd{i}", f"cmd{i+1}"],
                performance_impact={"token_savings": 300},
                suggested_optimizations=[],
            )
            for i in range(4)
        ]

        insights = insight_generator._generate_system_insights(patterns)

        assert len(insights) == 1
        insight = insights[0]
        assert insight.insight_type == "performance"
        assert "System-Wide Sequential Pattern Optimization" in insight.title
        assert "system-wide" in insight.applicable_users

    def test_calculate_insight_priority(self, insight_generator: InsightGenerator) -> None:
        """Test the insight priority calculation."""
        high_impact_easy = OptimizationInsight(
            insight_id="1",
            insight_type="",
            title="",
            description="",
            impact_estimate="high",
            effort_estimate="easy",
            suggested_actions=[],
            evidence={},
            applicable_users=[],
        )
        low_impact_complex = OptimizationInsight(
            insight_id="2",
            insight_type="",
            title="",
            description="",
            impact_estimate="low",
            effort_estimate="complex",
            suggested_actions=[],
            evidence={},
            applicable_users=[],
        )

        priority1 = insight_generator._calculate_insight_priority(high_impact_easy)
        priority2 = insight_generator._calculate_insight_priority(low_impact_complex)

        assert priority1 > priority2

    def test_generate_insights(self, insight_generator: InsightGenerator) -> None:
        """Test the main insight generation orchestrator."""
        with patch.object(insight_generator.pattern_detector, "detect_patterns") as mock_detect:
            mock_detect.return_value = [
                UserBehaviorPattern(
                    pattern_id="1",
                    pattern_type="sequential",
                    description="",
                    frequency=0.8,
                    confidence=0.9,
                    associated_categories=[],
                    typical_sequence=["a", "b"],
                    performance_impact={"token_savings": 300},
                    suggested_optimizations=[],
                ),
            ]
            insights = insight_generator.generate_insights("user1")
            assert len(insights) > 0
            assert insights[0].insight_type == "performance"


# ===================================
# AnalyticsEngine Tests
# ===================================


class TestAnalyticsEngine:
    """Tests for the main AnalyticsEngine class."""

    def test_track_user_action(self, analytics_engine: AnalyticsEngine) -> None:
        """Test that user actions are tracked correctly."""
        with patch.object(analytics_engine.usage_tracker, "track_event") as mock_track:
            analytics_engine.track_user_action("test_action", {}, "user1", "session1")
            mock_track.assert_called_once()

    def test_get_user_analytics(self, analytics_engine: AnalyticsEngine) -> None:
        """Test getting user analytics."""
        user_id = "user1"
        with patch.object(analytics_engine.usage_tracker, "get_recent_events") as mock_events:
            mock_events.return_value = [
                UsageEvent(datetime.now(UTC), "command_executed", {"command": "c1"}, user_id, "s1"),
            ]
            analytics = analytics_engine.get_user_analytics(user_id)
            assert analytics["user_id"] == user_id
            assert analytics["total_events"] == 1

    @pytest.mark.parametrize(
        ("cache_ttl", "first_call_count", "second_call_count"),
        [
            (timedelta(seconds=10), 2, 2),  # 2 calls: one in get_user_analytics, one in generate_insights
            (timedelta(seconds=-1), 2, 4),  # 4 calls: 2 for first call, 2 more for second call (no cache)
        ],
    )
    def test_get_user_analytics_caching(
        self,
        db_path: Path,
        cache_ttl: timedelta,
        first_call_count: int,
        second_call_count: int,
    ) -> None:
        """Test that user analytics results are cached."""
        analytics_engine = AnalyticsEngine(db_path)
        analytics_engine.cache_ttl = cache_ttl
        user_id = "user_cache"

        with patch.object(analytics_engine.pattern_detector, "detect_patterns", return_value=[]) as mock_detect:
            # First call, should compute
            analytics_engine.get_user_analytics(user_id)
            assert mock_detect.call_count == first_call_count

            # Second call, should be cached or recomputed based on TTL
            analytics_engine.get_user_analytics(user_id)
            assert mock_detect.call_count == second_call_count

    def test_get_system_analytics(self, analytics_engine: AnalyticsEngine) -> None:
        """Test getting system-wide analytics."""
        with patch.object(analytics_engine.usage_tracker, "get_recent_events") as mock_events:
            mock_events.return_value = [
                UsageEvent(datetime.now(UTC), "command_executed", {"command": "c1"}, "u1", "s1"),
                UsageEvent(datetime.now(UTC), "category_loaded", {"category": "cat1"}, "u2", "s2"),
            ]
            analytics = analytics_engine.get_system_analytics()
            assert analytics["total_events"] == 2
            assert analytics["active_users"] == 2
            assert "c1" in analytics["most_popular_commands"]

    def test_export_analytics(self, analytics_engine: AnalyticsEngine) -> None:
        """Test exporting analytics data."""
        with patch.object(analytics_engine, "get_user_analytics") as mock_get_analytics:
            mock_get_analytics.return_value = {"test": "data"}
            export_data = analytics_engine.export_analytics("user1")
            assert export_data["export_type"] == "user"
            assert export_data["data"]["test"] == "data"

        with patch.object(analytics_engine, "get_system_analytics") as mock_get_system_analytics:
            mock_get_system_analytics.return_value = {"system_test": "data"}
            export_data = analytics_engine.export_analytics()
            assert export_data["export_type"] == "system"
            assert export_data["data"]["system_test"] == "data"
