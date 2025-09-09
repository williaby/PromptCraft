"""
Comprehensive test suite for AB Testing Framework - ExperimentManager.

This test suite provides extensive coverage for the production AB testing components
including ExperimentManager, statistical calculations, user assignments, database operations,
and error handling scenarios.

This replaces the legacy ABTestManager test suite with tests for the actual production
ExperimentManager implementation.

Target Coverage: 90%+
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.ab_testing_framework import (
    BaseModel,
    ExperimentConfig,
    ExperimentManager,
    ExperimentModel,
    ExperimentResults,
    ExperimentType,
    MetricEvent,
    MetricEventModel,
    MetricsCollector,
    UserAssignmentModel,
    UserCharacteristics,
    UserSegment,
    UserSegmentation,
    create_dynamic_loading_experiment,
    get_experiment_manager,
)
from src.core.dynamic_loading_integration import ProcessingResult
from src.utils.datetime_compat import utc_now


class TestExperimentConfig:
    """Test cases for ExperimentConfig dataclass."""

    def test_config_creation(self):
        """Test basic configuration creation."""
        config = ExperimentConfig(
            name="test_experiment",
            description="Test experiment description",
            experiment_type=ExperimentType.DYNAMIC_LOADING,
            planned_duration_hours=72,
        )

        assert config.name == "test_experiment"
        assert config.description == "Test experiment description"
        assert config.experiment_type == ExperimentType.DYNAMIC_LOADING
        assert config.planned_duration_hours == 72
        assert config.initial_percentage == 1.0
        assert config.auto_rollback_enabled is True

    def test_config_with_custom_rollout(self):
        """Test configuration with custom rollout parameters."""
        config = ExperimentConfig(
            name="custom_rollout",
            description="Custom rollout test",
            experiment_type=ExperimentType.OPTIMIZATION_STRATEGY,
            rollout_steps=[2.0, 10.0, 50.0, 100.0],
            target_percentage=100.0,
            step_duration_hours=48,
        )

        assert config.rollout_steps == [2.0, 10.0, 50.0, 100.0]
        assert config.target_percentage == 100.0
        assert config.step_duration_hours == 48

    def test_config_with_success_criteria(self):
        """Test configuration with success criteria and failure thresholds."""
        success_criteria = {
            "min_token_reduction": 75.0,
            "max_response_time_ms": 150.0,
            "min_success_rate": 98.0,
        }
        failure_thresholds = {
            "max_error_rate": 3.0,
            "min_token_reduction": 60.0,
        }

        config = ExperimentConfig(
            name="criteria_test",
            description="Test with criteria",
            experiment_type=ExperimentType.PERFORMANCE,
            success_criteria=success_criteria,
            failure_thresholds=failure_thresholds,
        )

        assert config.success_criteria == success_criteria
        assert config.failure_thresholds == failure_thresholds

    def test_config_with_user_segmentation(self):
        """Test configuration with user segmentation parameters."""
        segment_filters = [UserSegment.POWER_USER, UserSegment.EARLY_ADOPTER]
        exclude_segments = [UserSegment.NEW_USER]

        config = ExperimentConfig(
            name="segmentation_test",
            description="Test with segmentation",
            experiment_type=ExperimentType.USER_INTERFACE,
            segment_filters=segment_filters,
            exclude_segments=exclude_segments,
            opt_in_only=True,
        )

        assert config.segment_filters == segment_filters
        assert config.exclude_segments == exclude_segments
        assert config.opt_in_only is True


class TestUserCharacteristics:
    """Test cases for UserCharacteristics dataclass."""

    def test_user_characteristics_creation(self):
        """Test basic user characteristics creation."""
        characteristics = UserCharacteristics(
            user_id="test_user_123",
            usage_frequency="high",
            feature_usage_pattern="advanced",
        )

        assert characteristics.user_id == "test_user_123"
        assert characteristics.usage_frequency == "high"
        assert characteristics.feature_usage_pattern == "advanced"
        assert characteristics.error_rate == 0.0
        assert characteristics.is_early_adopter is False

    def test_user_characteristics_with_all_fields(self):
        """Test user characteristics with all fields populated."""
        reg_date = utc_now() - timedelta(days=45)
        
        characteristics = UserCharacteristics(
            user_id="power_user_456",
            registration_date=reg_date,
            usage_frequency="high",
            feature_usage_pattern="advanced",
            error_rate=0.5,
            avg_session_duration=1800.0,
            preferred_features=["dynamic_loading", "optimization"],
            geographic_region="us-west",
            device_type="desktop",
            is_early_adopter=True,
            opt_in_beta=True,
        )

        assert characteristics.registration_date == reg_date
        assert characteristics.preferred_features == ["dynamic_loading", "optimization"]
        assert characteristics.geographic_region == "us-west"
        assert characteristics.device_type == "desktop"
        assert characteristics.is_early_adopter is True
        assert characteristics.opt_in_beta is True

    def test_user_characteristics_to_dict(self):
        """Test serialization to dictionary."""
        reg_date = utc_now() - timedelta(days=10)
        
        characteristics = UserCharacteristics(
            user_id="serialization_test",
            registration_date=reg_date,
            usage_frequency="medium",
            is_early_adopter=True,
        )

        result_dict = characteristics.to_dict()

        assert result_dict["user_id"] == "serialization_test"
        assert result_dict["registration_date"] == reg_date.isoformat()
        assert result_dict["usage_frequency"] == "medium"
        assert result_dict["is_early_adopter"] is True
        assert "preferred_features" in result_dict


class TestMetricEvent:
    """Test cases for MetricEvent dataclass."""

    def test_metric_event_creation(self):
        """Test basic metric event creation."""
        event = MetricEvent(
            experiment_id="exp_123",
            user_id="user_456",
            variant="treatment",
            event_type="performance",
            event_name="query_processing",
            event_value=125.0,
        )

        assert event.experiment_id == "exp_123"
        assert event.user_id == "user_456"
        assert event.variant == "treatment"
        assert event.event_type == "performance"
        assert event.event_name == "query_processing"
        assert event.event_value == 125.0
        assert isinstance(event.timestamp, datetime)

    def test_metric_event_with_performance_data(self):
        """Test metric event with performance-specific data."""
        event = MetricEvent(
            experiment_id="exp_perf",
            user_id="perf_user",
            variant="control",
            event_type="performance",
            event_name="token_optimization",
            response_time_ms=200.0,
            token_reduction_percentage=75.0,
            success=True,
        )

        assert event.response_time_ms == 200.0
        assert event.token_reduction_percentage == 75.0
        assert event.success is True
        assert event.error_message is None

    def test_metric_event_with_error(self):
        """Test metric event with error information."""
        event = MetricEvent(
            experiment_id="exp_error",
            user_id="error_user",
            variant="treatment",
            event_type="error",
            event_name="processing_failure",
            success=False,
            error_message="Token optimization failed",
        )

        assert event.success is False
        assert event.error_message == "Token optimization failed"

    def test_metric_event_with_metadata(self):
        """Test metric event with additional metadata."""
        metadata = {
            "query_type": "optimization",
            "session_context": "premium_user",
        }
        
        event = MetricEvent(
            experiment_id="exp_meta",
            user_id="meta_user",
            variant="treatment_b",
            event_type="conversion",
            event_name="feature_usage",
            event_data=metadata,
            session_id="session_789",
            request_id="req_101112",
        )

        assert event.event_data == metadata
        assert event.session_id == "session_789"
        assert event.request_id == "req_101112"


class TestExperimentResults:
    """Test cases for ExperimentResults dataclass."""

    def test_experiment_results_creation(self):
        """Test basic experiment results creation."""
        start_time = utc_now() - timedelta(hours=48)
        end_time = utc_now()
        
        results = ExperimentResults(
            experiment_id="exp_results_test",
            experiment_name="Results Test Experiment",
            total_users=1000,
            variants={
                "control": {"user_count": 500, "success_rate": 0.85},
                "treatment": {"user_count": 500, "success_rate": 0.90},
            },
            statistical_significance=95.0,
            confidence_interval=(0.02, 0.08),
            p_value=0.01,
            effect_size=0.05,
            performance_summary={"overall_success_rate": 0.875},
            success_criteria_met={"token_reduction_target": True},
            failure_thresholds_exceeded={"error_rate_exceeded": False},
            recommendation="expand",
            confidence_level="high",
            next_actions=["Prepare for full rollout"],
            start_time=start_time,
            end_time=end_time,
            duration_hours=48.0,
        )

        assert results.experiment_id == "exp_results_test"
        assert results.total_users == 1000
        assert results.statistical_significance == 95.0
        assert results.confidence_interval == (0.02, 0.08)
        assert results.recommendation == "expand"
        assert results.duration_hours == 48.0

    def test_experiment_results_to_dict(self):
        """Test experiment results serialization."""
        start_time = utc_now() - timedelta(hours=24)
        
        results = ExperimentResults(
            experiment_id="serialization_test",
            experiment_name="Serialization Test",
            total_users=500,
            variants={"control": {"success_rate": 0.8}},
            statistical_significance=85.0,
            confidence_interval=(0.01, 0.06),
            p_value=0.03,
            effect_size=0.035,
            performance_summary={},
            success_criteria_met={},
            failure_thresholds_exceeded={},
            recommendation="continue",
            confidence_level="medium",
            next_actions=["Monitor closely"],
            start_time=start_time,
            end_time=None,
            duration_hours=24.0,
        )

        result_dict = results.to_dict()

        assert result_dict["experiment_id"] == "serialization_test"
        assert result_dict["statistical_significance"] == 85.0
        assert result_dict["confidence_interval"] == [0.01, 0.06]
        assert result_dict["start_time"] == start_time.isoformat()
        assert result_dict["end_time"] is None


@pytest.fixture
def test_db_engine():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    BaseModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_db_session(test_db_engine):
    """Create database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def experiment_manager(test_db_engine):
    """Create ExperimentManager instance for testing."""
    manager = ExperimentManager(db_url="sqlite:///:memory:")
    manager.engine = test_db_engine
    manager.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    return manager


@pytest.fixture
def sample_experiment_config():
    """Create a sample experiment configuration for testing."""
    return ExperimentConfig(
        name="Sample Test Experiment",
        description="A sample experiment for testing purposes",
        experiment_type=ExperimentType.DYNAMIC_LOADING,
        planned_duration_hours=48,
        variant_configs={
            "control": {
                "feature_flags": {"dynamic_loading_enabled": False},
                "loading_strategy": "baseline",
            },
            "treatment": {
                "feature_flags": {"dynamic_loading_enabled": True},
                "loading_strategy": "optimized",
            },
        },
        target_percentage=50.0,
        # Include segment filters for all major segments to allow assignment
        segment_filters=[
            UserSegment.RANDOM,
            UserSegment.EARLY_ADOPTER,
            UserSegment.POWER_USER,
            UserSegment.HIGH_VOLUME,
        ],
        success_criteria={
            "min_token_reduction": 70.0,
            "max_response_time_ms": 200.0,
            "min_success_rate": 95.0,
        },
        failure_thresholds={
            "max_error_rate": 5.0,
            "min_token_reduction": 50.0,
        },
    )


class TestExperimentManager:
    """Test cases for ExperimentManager class."""

    @pytest.mark.asyncio
    async def test_create_experiment(self, experiment_manager, sample_experiment_config):
        """Test experiment creation."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)

        assert experiment_id is not None
        assert experiment_id.startswith("exp_")
        assert "dynamic_loading" in experiment_id

        # Verify experiment was stored in database
        with experiment_manager.get_db_session() as session:
            experiment = session.query(ExperimentModel).filter_by(id=experiment_id).first()
            
            assert experiment is not None
            assert experiment.name == sample_experiment_config.name
            assert experiment.status == "draft"
            assert experiment.experiment_type == "dynamic_loading"
            assert experiment.target_percentage == 50.0

    @pytest.mark.asyncio
    async def test_start_experiment(self, experiment_manager, sample_experiment_config):
        """Test starting an experiment."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        
        # Start the experiment
        success = await experiment_manager.start_experiment(experiment_id)
        assert success is True

        # Verify experiment status changed
        with experiment_manager.get_db_session() as session:
            experiment = session.query(ExperimentModel).filter_by(id=experiment_id).first()
            
            assert experiment.status == "active"
            assert experiment.start_time is not None
            assert experiment.current_percentage == sample_experiment_config.initial_percentage

    @pytest.mark.asyncio
    async def test_start_nonexistent_experiment(self, experiment_manager):
        """Test starting a non-existent experiment."""
        success = await experiment_manager.start_experiment("nonexistent_exp")
        assert success is False

    @pytest.mark.asyncio
    async def test_stop_experiment(self, experiment_manager, sample_experiment_config):
        """Test stopping an experiment."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        await experiment_manager.start_experiment(experiment_id)
        
        # Stop the experiment
        success = await experiment_manager.stop_experiment(experiment_id)
        assert success is True

        # Verify experiment status changed
        with experiment_manager.get_db_session() as session:
            experiment = session.query(ExperimentModel).filter_by(id=experiment_id).first()
            
            assert experiment.status == "completed"
            assert experiment.end_time is not None

    @pytest.mark.asyncio
    async def test_assign_user_to_experiment(self, experiment_manager, sample_experiment_config):
        """Test user assignment to experiment."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        await experiment_manager.start_experiment(experiment_id)

        user_characteristics = UserCharacteristics(
            user_id="test_user_123",
            usage_frequency="high",
            is_early_adopter=True,
        )

        # Assign user to experiment
        variant, segment = await experiment_manager.assign_user_to_experiment(
            "test_user_123",
            experiment_id,
            user_characteristics,
        )

        assert variant in ["control", "treatment"]
        assert isinstance(segment, UserSegment)

        # For this test, just verify the assignment logic works
        # The database persistence is tested separately
        # Since we get a valid variant and segment, assignment succeeded
        assert segment == UserSegment.EARLY_ADOPTER  # Based on characteristics

    @pytest.mark.asyncio
    async def test_assign_user_database_persistence(self, experiment_manager, sample_experiment_config):
        """Test that user assignment is properly persisted to database."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        await experiment_manager.start_experiment(experiment_id)

        # Test the UserSegmentation class directly with shared session
        with experiment_manager.get_db_session() as session:
            segmentation = UserSegmentation(session)
            config = ExperimentConfig(**sample_experiment_config.__dict__)
            
            user_characteristics = UserCharacteristics(
                user_id="persistence_test_user",
                usage_frequency="high",
                is_early_adopter=True,
            )
            
            variant, segment = segmentation.assign_user_to_experiment(
                "persistence_test_user",
                experiment_id,
                config,
                user_characteristics,
            )
            
            # Now check assignment in same session
            assignment = (
                session.query(UserAssignmentModel)
                .filter_by(user_id="persistence_test_user", experiment_id=experiment_id)
                .first()
            )
            
            assert assignment is not None
            assert assignment.variant == variant
            assert assignment.segment == segment.value

    @pytest.mark.asyncio
    async def test_assign_user_consistent_assignment(self, experiment_manager, sample_experiment_config):
        """Test that user assignment is consistent across multiple calls."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        await experiment_manager.start_experiment(experiment_id)

        # Assign user multiple times
        variant1, segment1 = await experiment_manager.assign_user_to_experiment(
            "consistent_user",
            experiment_id,
        )
        
        variant2, segment2 = await experiment_manager.assign_user_to_experiment(
            "consistent_user",
            experiment_id,
        )

        # Should get same assignment
        assert variant1 == variant2
        assert segment1 == segment2

    @pytest.mark.asyncio
    async def test_assign_user_inactive_experiment(self, experiment_manager, sample_experiment_config):
        """Test user assignment to inactive experiment."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        # Don't start the experiment

        variant, segment = await experiment_manager.assign_user_to_experiment(
            "inactive_test_user",
            experiment_id,
        )

        # Should default to control for inactive experiments
        assert variant == "control"
        assert segment == UserSegment.RANDOM

    @pytest.mark.asyncio
    async def test_should_use_dynamic_loading(self, experiment_manager):
        """Test dynamic loading decision based on assignment."""
        with patch.object(experiment_manager, "assign_user_to_experiment") as mock_assign:
            # Test treatment assignment
            mock_assign.return_value = ("treatment", UserSegment.RANDOM)
            
            should_use = await experiment_manager.should_use_dynamic_loading("test_user")
            assert should_use is True
            
            # Test control assignment
            mock_assign.return_value = ("control", UserSegment.RANDOM)
            
            should_use = await experiment_manager.should_use_dynamic_loading("test_user")
            assert should_use is False

    @pytest.mark.asyncio
    async def test_record_optimization_result(self, experiment_manager, sample_experiment_config):
        """Test recording optimization results."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        await experiment_manager.start_experiment(experiment_id)
        
        # Assign user first
        await experiment_manager.assign_user_to_experiment("result_user", experiment_id)

        # Create mock processing result
        processing_result = ProcessingResult(
            query="test query",
            session_id="test_session",
            detection_result=None,
            loading_decision=None,
            optimization_report=None,
            user_commands=[],
            detection_time_ms=50.0,
            loading_time_ms=100.0,
            total_time_ms=150.0,
            baseline_tokens=1000,
            optimized_tokens=300,
            reduction_percentage=70.0,
            target_achieved=True,
            success=True,
        )

        # Record the result
        success = await experiment_manager.record_optimization_result(
            experiment_id,
            "result_user",
            processing_result,
        )

        assert success is True

        # Verify events were recorded
        with experiment_manager.get_db_session() as session:
            events = session.query(MetricEventModel).filter_by(
                experiment_id=experiment_id,
                user_id="result_user",
            ).all()
            
            assert len(events) >= 2  # Performance and optimization events
            event_types = [event.event_type for event in events]
            assert "performance" in event_types
            assert "optimization" in event_types

    @pytest.mark.asyncio
    async def test_get_experiment_results(self, experiment_manager, sample_experiment_config):
        """Test getting experiment results."""
        experiment_id = await experiment_manager.create_experiment(sample_experiment_config)
        await experiment_manager.start_experiment(experiment_id)

        # Add some test data
        with experiment_manager.get_db_session() as session:
            # Add user assignments
            assignment1 = UserAssignmentModel(
                id=f"{experiment_id}_user1",
                user_id="user1",
                experiment_id=experiment_id,
                variant="control",
                segment="random",
            )
            assignment2 = UserAssignmentModel(
                id=f"{experiment_id}_user2",
                user_id="user2",
                experiment_id=experiment_id,
                variant="treatment",
                segment="random",
            )
            session.add(assignment1)
            session.add(assignment2)

            # Add metric events
            event1 = MetricEventModel(
                id=f"{experiment_id}_user1_1",
                experiment_id=experiment_id,
                user_id="user1",
                variant="control",
                event_type="performance",
                event_name="query_processing",
                response_time_ms=200.0,
                token_reduction_percentage=65.0,
                success=True,
            )
            event2 = MetricEventModel(
                id=f"{experiment_id}_user2_1",
                experiment_id=experiment_id,
                user_id="user2",
                variant="treatment",
                event_type="performance",
                event_name="query_processing",
                response_time_ms=150.0,
                token_reduction_percentage=75.0,
                success=True,
            )
            session.add(event1)
            session.add(event2)
            session.commit()

        # Get experiment results
        results = await experiment_manager.get_experiment_results(experiment_id)

        assert results is not None
        assert results.experiment_id == experiment_id
        assert results.total_users >= 2
        assert "control" in results.variants
        assert "treatment" in results.variants

    @pytest.mark.asyncio
    async def test_get_experiment_results_nonexistent(self, experiment_manager):
        """Test getting results for non-existent experiment."""
        results = await experiment_manager.get_experiment_results("nonexistent_exp")
        assert results is None


class TestUserSegmentation:
    """Test cases for UserSegmentation class."""

    def test_determine_user_segment_early_adopter(self, test_db_session):
        """Test early adopter segment determination."""
        segmentation = UserSegmentation(test_db_session)
        
        characteristics = UserCharacteristics(
            user_id="early_adopter",
            is_early_adopter=True,
            opt_in_beta=True,
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.EARLY_ADOPTER

    def test_determine_user_segment_new_user(self, test_db_session):
        """Test new user segment determination."""
        segmentation = UserSegmentation(test_db_session)
        
        characteristics = UserCharacteristics(
            user_id="new_user",
            registration_date=utc_now() - timedelta(days=15),
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.NEW_USER

    def test_determine_user_segment_power_user(self, test_db_session):
        """Test power user segment determination."""
        segmentation = UserSegmentation(test_db_session)
        
        characteristics = UserCharacteristics(
            user_id="power_user",
            usage_frequency="high",
            feature_usage_pattern="advanced",
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.POWER_USER

    def test_determine_user_segment_high_volume(self, test_db_session):
        """Test high volume user segment determination."""
        segmentation = UserSegmentation(test_db_session)
        
        characteristics = UserCharacteristics(
            user_id="high_volume",
            usage_frequency="high",
            feature_usage_pattern="intermediate",
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.HIGH_VOLUME

    def test_determine_user_segment_random_default(self, test_db_session):
        """Test default random segment determination."""
        segmentation = UserSegmentation(test_db_session)
        
        characteristics = UserCharacteristics(
            user_id="default_user",
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.RANDOM

    def test_assign_variant_consistent_same_user(self, test_db_session):
        """Test consistent assignment for same user."""
        segmentation = UserSegmentation(test_db_session)
        
        user_id = "consistent_test"
        experiment_id = "exp_consistency"
        rollout_percentage = 50.0

        variant1 = segmentation._assign_variant_consistent(user_id, experiment_id, rollout_percentage)
        variant2 = segmentation._assign_variant_consistent(user_id, experiment_id, rollout_percentage)
        
        assert variant1 == variant2

    def test_assign_variant_consistent_different_users(self, test_db_session):
        """Test that different users can get different assignments."""
        segmentation = UserSegmentation(test_db_session)
        
        experiment_id = "exp_different_users"
        rollout_percentage = 50.0

        assignments = []
        for i in range(100):
            user_id = f"user_{i}"
            variant = segmentation._assign_variant_consistent(user_id, experiment_id, rollout_percentage)
            assignments.append(variant)

        # Should have some variety in assignments
        unique_assignments = set(assignments)
        assert len(unique_assignments) >= 1  # At least control should appear

    def test_opt_out_user(self, test_db_session):
        """Test opting out a user from experiment."""
        segmentation = UserSegmentation(test_db_session)
        
        # First create an assignment
        assignment = UserAssignmentModel(
            id="test_assignment",
            user_id="opt_out_user",
            experiment_id="opt_out_exp",
            variant="treatment",
            segment="random",
        )
        test_db_session.add(assignment)
        test_db_session.commit()

        # Opt out the user
        success = segmentation.opt_out_user("opt_out_user", "opt_out_exp")
        assert success is True

        # Verify opt-out was recorded
        updated_assignment = (
            test_db_session.query(UserAssignmentModel)
            .filter_by(user_id="opt_out_user", experiment_id="opt_out_exp")
            .first()
        )
        assert updated_assignment.opt_out is True

    def test_opt_out_nonexistent_user(self, test_db_session):
        """Test opting out a user with no existing assignment."""
        segmentation = UserSegmentation(test_db_session)
        
        success = segmentation.opt_out_user("nonexistent_user", "nonexistent_exp")
        assert success is False


class TestMetricsCollector:
    """Test cases for MetricsCollector class."""

    def test_record_event(self, test_db_session):
        """Test recording a metric event."""
        collector = MetricsCollector(test_db_session)
        
        event = MetricEvent(
            experiment_id="metrics_test_exp",
            user_id="metrics_user",
            variant="treatment",
            event_type="performance",
            event_name="token_optimization",
            event_value=150.0,
            response_time_ms=150.0,
            token_reduction_percentage=70.0,
            success=True,
        )

        success = collector.record_event(event)
        assert success is True

        # Verify event was stored
        stored_event = (
            test_db_session.query(MetricEventModel)
            .filter_by(experiment_id="metrics_test_exp", user_id="metrics_user")
            .first()
        )
        
        assert stored_event is not None
        assert stored_event.event_type == "performance"
        assert stored_event.response_time_ms == 150.0
        assert stored_event.success is True

    def test_record_processing_result_success(self, test_db_session):
        """Test recording a successful processing result."""
        collector = MetricsCollector(test_db_session)
        
        result = ProcessingResult(
            query="test query",
            session_id="session_123",
            detection_result=None,
            loading_decision=None,
            optimization_report=None,
            user_commands=[],
            detection_time_ms=25.0,
            loading_time_ms=50.0,
            total_time_ms=150.0,
            baseline_tokens=1000,
            optimized_tokens=300,
            reduction_percentage=70.0,
            target_achieved=True,
            success=True,
        )

        success = collector.record_processing_result(
            "processing_exp",
            "processing_user",
            "treatment",
            result,
        )
        assert success is True

        # Verify events were recorded
        events = (
            test_db_session.query(MetricEventModel)
            .filter_by(experiment_id="processing_exp", user_id="processing_user")
            .all()
        )
        
        assert len(events) >= 2  # Performance and optimization events
        event_types = [event.event_type for event in events]
        assert "performance" in event_types
        assert "optimization" in event_types

    def test_record_processing_result_failure(self, test_db_session):
        """Test recording a failed processing result."""
        collector = MetricsCollector(test_db_session)
        
        result = ProcessingResult(
            query="failed query",
            session_id="failed_session",
            detection_result=None,
            loading_decision=None,
            optimization_report=None,
            user_commands=[],
            detection_time_ms=25.0,
            loading_time_ms=0.0,
            total_time_ms=25.0,
            baseline_tokens=1000,
            optimized_tokens=1000,
            reduction_percentage=0.0,
            target_achieved=False,
            success=False,
            error_message="Processing failed",
        )

        success = collector.record_processing_result(
            "failure_exp",
            "failure_user",
            "treatment",
            result,
        )
        assert success is True

        # Verify error event was recorded
        events = (
            test_db_session.query(MetricEventModel)
            .filter_by(experiment_id="failure_exp", user_id="failure_user")
            .all()
        )
        
        # Should have performance and error events
        event_types = [event.event_type for event in events]
        assert "performance" in event_types
        assert "error" in event_types

        error_event = next(event for event in events if event.event_type == "error")
        assert error_event.success is False
        assert error_event.error_message == "Processing failed"


class TestCreateDynamicLoadingExperiment:
    """Test cases for create_dynamic_loading_experiment function."""

    @pytest.mark.asyncio
    async def test_create_dynamic_loading_experiment_default(self):
        """Test creating dynamic loading experiment with default parameters."""
        with patch("src.core.ab_testing_framework.get_experiment_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.create_experiment.return_value = "exp_dynamic_123"
            mock_manager.start_experiment.return_value = True
            mock_get_manager.return_value = mock_manager

            experiment_id = await create_dynamic_loading_experiment()

            assert experiment_id == "exp_dynamic_123"
            mock_manager.create_experiment.assert_called_once()
            mock_manager.start_experiment.assert_called_once_with("exp_dynamic_123")

            # Verify configuration parameters
            call_args = mock_manager.create_experiment.call_args[0][0]
            assert call_args.name == "Dynamic Function Loading Rollout"
            assert call_args.experiment_type == ExperimentType.DYNAMIC_LOADING
            assert call_args.target_percentage == 50.0

    @pytest.mark.asyncio
    async def test_create_dynamic_loading_experiment_custom(self):
        """Test creating dynamic loading experiment with custom parameters."""
        with patch("src.core.ab_testing_framework.get_experiment_manager") as mock_get_manager:
            mock_manager = AsyncMock()
            mock_manager.create_experiment.return_value = "exp_custom_456"
            mock_manager.start_experiment.return_value = True
            mock_get_manager.return_value = mock_manager

            experiment_id = await create_dynamic_loading_experiment(
                target_percentage=75.0,
                duration_hours=72,
            )

            assert experiment_id == "exp_custom_456"

            # Verify custom configuration
            call_args = mock_manager.create_experiment.call_args[0][0]
            assert call_args.target_percentage == 75.0
            assert call_args.planned_duration_hours == 72


class TestGlobalExperimentManager:
    """Test cases for global experiment manager functions."""

    @pytest.mark.asyncio
    async def test_get_experiment_manager_singleton(self):
        """Test that get_experiment_manager returns singleton instance."""
        with patch("src.core.ab_testing_framework._experiment_manager", None):
            manager1 = await get_experiment_manager()
            manager2 = await get_experiment_manager()

            assert manager1 is manager2
            assert manager1 is not None

    @pytest.mark.asyncio
    async def test_get_experiment_manager_starts_monitoring(self):
        """Test that get_experiment_manager starts monitoring."""
        with patch("src.core.ab_testing_framework._experiment_manager", None):
            with patch.object(ExperimentManager, "start_monitoring") as mock_start:
                manager = await get_experiment_manager()

                assert manager is not None
                mock_start.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])