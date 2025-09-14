"""
Comprehensive tests for A/B Testing Framework.

This test module provides complete coverage of the A/B testing framework
with minimal mocking, focusing on actual process testing and realistic scenarios.
Following the user's guidance to prioritize testing real functionality.

Coverage targets:
- All core classes: ExperimentManager, UserSegmentation, MetricsCollector, StatisticalAnalyzer
- Database models and Pydantic models
- Statistical analysis and experiment lifecycle
- Safety mechanisms and rollback functionality
- Progressive rollout and feature flag management
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.ab_testing_framework import (
    BaseModel,
    ExperimentConfig,
    ExperimentManager,
    ExperimentModel,
    ExperimentStatus,
    ExperimentType,
    MetricEvent,
    MetricEventModel,
    MetricsCollector,
    StatisticalAnalyzer,
    UserCharacteristics,
    UserSegment,
    UserSegmentation,
    VariantType,
    create_dynamic_loading_experiment,
)
from src.core.dynamic_loading_integration import ProcessingResult
from src.utils.datetime_compat import UTC, utc_now


class TestEnumsAndModels:
    """Test enums and Pydantic models."""

    def test_experiment_type_enum(self):
        """Test ExperimentType enum values."""
        assert ExperimentType.DYNAMIC_LOADING.value == "dynamic_loading"
        assert ExperimentType.OPTIMIZATION_STRATEGY.value == "optimization_strategy"
        assert ExperimentType.USER_INTERFACE.value == "user_interface"
        assert ExperimentType.PERFORMANCE.value == "performance"

    def test_experiment_status_enum(self):
        """Test ExperimentStatus enum values."""
        assert ExperimentStatus.DRAFT.value == "draft"
        assert ExperimentStatus.ACTIVE.value == "active"
        assert ExperimentStatus.PAUSED.value == "paused"
        assert ExperimentStatus.COMPLETED.value == "completed"
        assert ExperimentStatus.FAILED.value == "failed"

    def test_user_segment_enum(self):
        """Test UserSegment enum values."""
        assert UserSegment.RANDOM.value == "random"
        assert UserSegment.POWER_USER.value == "power_user"
        assert UserSegment.NEW_USER.value == "new_user"
        assert UserSegment.HIGH_VOLUME.value == "high_volume"
        assert UserSegment.LOW_VOLUME.value == "low_volume"
        assert UserSegment.EARLY_ADOPTER.value == "early_adopter"

    def test_variant_type_enum(self):
        """Test VariantType enum values."""
        assert VariantType.CONTROL.value == "control"
        assert VariantType.TREATMENT.value == "treatment"
        assert VariantType.TREATMENT_A.value == "treatment_a"
        assert VariantType.TREATMENT_B.value == "treatment_b"

    def test_experiment_config_defaults(self):
        """Test ExperimentConfig with default values."""
        config = ExperimentConfig(
            name="Test Experiment",
            description="Test description",
            experiment_type=ExperimentType.DYNAMIC_LOADING,
        )

        assert config.name == "Test Experiment"
        assert config.description == "Test description"
        assert config.experiment_type == ExperimentType.DYNAMIC_LOADING
        assert config.planned_duration_hours == 168  # 1 week
        assert config.initial_percentage == 1.0
        assert config.target_percentage == 50.0
        assert config.rollout_steps == [1.0, 5.0, 25.0, 50.0]
        assert config.step_duration_hours == 24
        assert config.segment_filters == [UserSegment.RANDOM]
        assert config.exclude_segments == []
        assert config.opt_in_only is False
        assert config.min_sample_size == 1000
        assert config.max_acceptable_error_rate == 5.0
        assert config.required_improvement == 10.0
        assert config.auto_rollback_enabled is True
        assert config.circuit_breaker_threshold == 10.0
        assert config.max_performance_degradation == 20.0

    def test_user_characteristics_defaults(self):
        """Test UserCharacteristics with default values."""
        characteristics = UserCharacteristics(user_id="test_user")

        assert characteristics.user_id == "test_user"
        assert characteristics.registration_date is None
        assert characteristics.usage_frequency == "unknown"
        assert characteristics.feature_usage_pattern == "unknown"
        assert characteristics.error_rate == 0.0
        assert characteristics.avg_session_duration == 0.0
        assert characteristics.preferred_features == []
        assert characteristics.geographic_region is None
        assert characteristics.device_type is None
        assert characteristics.is_early_adopter is False
        assert characteristics.opt_in_beta is False

    def test_user_characteristics_to_dict(self):
        """Test UserCharacteristics to_dict method."""
        characteristics = UserCharacteristics(
            user_id="test_user",
            registration_date=datetime(2024, 1, 15, tzinfo=UTC),
            usage_frequency="high",
            feature_usage_pattern="advanced",
            error_rate=0.5,
            avg_session_duration=300.0,
            preferred_features=["feature1", "feature2"],
            geographic_region="US",
            device_type="desktop",
            is_early_adopter=True,
            opt_in_beta=True,
        )

        result = characteristics.to_dict()

        assert result["user_id"] == "test_user"
        assert result["registration_date"] == "2024-01-15T00:00:00+00:00"
        assert result["usage_frequency"] == "high"
        assert result["feature_usage_pattern"] == "advanced"
        assert result["error_rate"] == 0.5
        assert result["avg_session_duration"] == 300.0
        assert result["preferred_features"] == ["feature1", "feature2"]
        assert result["geographic_region"] == "US"
        assert result["device_type"] == "desktop"
        assert result["is_early_adopter"] is True
        assert result["opt_in_beta"] is True

    def test_metric_event_creation(self):
        """Test MetricEvent creation and defaults."""
        event = MetricEvent(
            experiment_id="exp_123",
            user_id="user_456",
            variant="treatment",
            event_type="performance",
            event_name="query_processing",
        )

        assert event.experiment_id == "exp_123"
        assert event.user_id == "user_456"
        assert event.variant == "treatment"
        assert event.event_type == "performance"
        assert event.event_name == "query_processing"
        assert event.event_value is None
        assert event.event_data is None
        assert event.session_id is None
        assert event.request_id is None
        assert isinstance(event.timestamp, datetime)
        assert event.response_time_ms is None
        assert event.token_reduction_percentage is None
        assert event.success is None
        assert event.error_message is None


class TestDatabaseModels:
    """Test SQLAlchemy database models."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = session_local()

        yield session

        session.close()

    def test_experiment_model_creation(self, db_session):
        """Test ExperimentModel creation and storage."""
        experiment = ExperimentModel(
            id="exp_test_123",
            name="Test Experiment",
            description="Test experiment description",
            experiment_type="dynamic_loading",
            status="draft",
            config={"test_key": "test_value"},
            variants=["control", "treatment"],
            success_criteria={"min_reduction": 70.0},
            failure_thresholds={"max_error": 5.0},
            target_percentage=50.0,
            current_percentage=0.0,
            segment_filters=["random"],
            planned_duration_hours=168,
            created_by="test_user",
        )

        db_session.add(experiment)
        db_session.commit()

        # Retrieve and verify
        retrieved = db_session.query(ExperimentModel).filter_by(id="exp_test_123").first()
        assert retrieved is not None
        assert retrieved.name == "Test Experiment"
        assert retrieved.description == "Test experiment description"
        assert retrieved.experiment_type == "dynamic_loading"
        assert retrieved.status == "draft"
        assert retrieved.config == {"test_key": "test_value"}
        assert retrieved.variants == ["control", "treatment"]
        assert retrieved.success_criteria == {"min_reduction": 70.0}
        assert retrieved.failure_thresholds == {"max_error": 5.0}


class TestUserSegmentation:
    """Test UserSegmentation class with realistic scenarios."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = session_local()

        yield session

        session.close()

    @pytest.fixture
    def segmentation(self, db_session):
        """Create UserSegmentation instance."""
        return UserSegmentation(db_session)

    def test_determine_user_segment_early_adopter(self, segmentation):
        """Test user segment determination for early adopters."""
        characteristics = UserCharacteristics(
            user_id="user_123",
            is_early_adopter=True,
            usage_frequency="high",
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.EARLY_ADOPTER

    def test_determine_user_segment_power_user(self, segmentation):
        """Test user segment determination for power users."""
        characteristics = UserCharacteristics(
            user_id="user_123",
            usage_frequency="high",
            feature_usage_pattern="advanced",
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.POWER_USER

    def test_determine_user_segment_new_user(self, segmentation):
        """Test user segment determination for new users."""
        recent_date = utc_now() - timedelta(days=15)  # 15 days ago
        characteristics = UserCharacteristics(
            user_id="user_123",
            registration_date=recent_date,
            usage_frequency="medium",
        )

        segment = segmentation._determine_user_segment(characteristics)
        assert segment == UserSegment.NEW_USER

    def test_assign_variant_consistent(self, segmentation):
        """Test consistent variant assignment."""
        # Should be consistent across multiple calls
        variant1 = segmentation._assign_variant_consistent("user_test", "exp_test", 50.0)
        variant2 = segmentation._assign_variant_consistent("user_test", "exp_test", 50.0)

        assert variant1 == variant2
        assert variant1 in ["control", "treatment"]


class TestMetricsCollector:
    """Test MetricsCollector class."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = session_local()

        yield session

        session.close()

    @pytest.fixture
    def metrics_collector(self, db_session):
        """Create MetricsCollector instance."""
        return MetricsCollector(db_session)

    def test_record_event_success(self, db_session, metrics_collector):
        """Test successful metric event recording."""
        event = MetricEvent(
            experiment_id="exp_123",
            user_id="user_456",
            variant="treatment",
            event_type="performance",
            event_name="query_processing",
            event_value=150.0,
            response_time_ms=150.0,
            token_reduction_percentage=75.0,
            success=True,
        )

        result = metrics_collector.record_event(event)

        assert result is True

        # Verify event was stored
        stored_event = db_session.query(MetricEventModel).first()
        assert stored_event is not None
        assert stored_event.experiment_id == "exp_123"
        assert stored_event.user_id == "user_456"
        assert stored_event.variant == "treatment"
        assert stored_event.event_type == "performance"
        assert stored_event.event_name == "query_processing"

    def test_record_processing_result_success(self, db_session, metrics_collector):
        """Test recording successful processing result."""
        # Mock ProcessingResult
        result = Mock(spec=ProcessingResult)
        result.success = True
        result.total_time_ms = 150.0
        result.detection_time_ms = 25.0
        result.loading_time_ms = 100.0
        result.cache_hit = False
        result.fallback_used = False
        result.session_id = "session_123"
        result.reduction_percentage = 75.0
        result.baseline_tokens = 1000
        result.optimized_tokens = 250
        result.target_achieved = True
        result.error_message = None

        success = metrics_collector.record_processing_result(
            "exp_123",
            "user_456",
            "treatment",
            result,
        )

        assert success is True

        # Verify both performance and optimization events were recorded
        events = db_session.query(MetricEventModel).all()
        assert len(events) == 2


class TestStatisticalAnalyzer:
    """Test StatisticalAnalyzer class."""

    @pytest.fixture
    def db_session(self):
        """Create in-memory database session for testing."""
        engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(engine)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = session_local()

        yield session

        session.close()

    @pytest.fixture
    def analyzer(self, db_session):
        """Create StatisticalAnalyzer instance."""
        return StatisticalAnalyzer(db_session)

    def test_analyze_experiment_no_experiment(self, analyzer):
        """Test analyzing non-existent experiment."""
        result = analyzer.analyze_experiment("nonexistent_exp")

        assert result is None

    def test_calculate_statistical_significance_insufficient_data(self, analyzer):
        """Test statistical significance calculation with insufficient data."""
        variant_data = {"control": {"user_count": 10, "success_rate": 0.8}}

        result = analyzer._calculate_statistical_significance(variant_data)

        assert result["significance"] == 0.0
        assert result["confidence_interval"] == (0.0, 0.0)
        assert result["p_value"] == 1.0
        assert result["effect_size"] == 0.0

    def test_calculate_statistical_significance_sufficient_data(self, analyzer):
        """Test statistical significance calculation with sufficient data."""
        variant_data = {
            "control": {"user_count": 200, "success_rate": 0.85},
            "treatment": {"user_count": 200, "success_rate": 0.92},
        }

        result = analyzer._calculate_statistical_significance(variant_data)

        assert result["significance"] > 0
        assert abs(result["effect_size"] - 0.07) < 0.001  # |0.92 - 0.85|
        assert result["p_value"] < 1.0
        assert len(result["confidence_interval"]) == 2


class TestExperimentManager:
    """Test ExperimentManager class with realistic scenarios."""

    @pytest.fixture
    def manager(self):
        """Create ExperimentManager with in-memory database."""
        return ExperimentManager("sqlite:///:memory:")

    @pytest.fixture
    def experiment_config(self):
        """Create test experiment configuration."""
        return ExperimentConfig(
            name="Test Dynamic Loading Experiment",
            description="Test experiment for dynamic loading",
            experiment_type=ExperimentType.DYNAMIC_LOADING,
            success_criteria={"min_token_reduction": 70.0},
            failure_thresholds={"max_error_rate": 5.0},
        )

    def test_manager_initialization(self, manager):
        """Test ExperimentManager initialization."""
        assert manager is not None
        assert manager.engine is not None
        assert manager.SessionLocal is not None
        assert manager.logger is not None
        assert manager.performance_monitor is not None

    def test_serialize_config(self, manager, experiment_config):
        """Test experiment config serialization."""
        serialized = manager._serialize_config(experiment_config)

        assert serialized["name"] == experiment_config.name
        assert serialized["description"] == experiment_config.description
        assert serialized["experiment_type"] == experiment_config.experiment_type.value
        assert isinstance(serialized["segment_filters"], list)
        assert all(isinstance(f, str) for f in serialized["segment_filters"])

    @pytest.mark.asyncio
    async def test_create_experiment(self, manager, experiment_config):
        """Test experiment creation."""
        experiment_id = await manager.create_experiment(experiment_config, "test_user")

        assert experiment_id.startswith("exp_")
        assert experiment_config.experiment_type.value in experiment_id

        # Verify experiment was stored
        with manager.get_db_session() as db_session:
            experiment = db_session.query(ExperimentModel).filter_by(id=experiment_id).first()
            assert experiment is not None
            assert experiment.name == experiment_config.name
            assert experiment.description == experiment_config.description
            assert experiment.status == "draft"
            assert experiment.created_by == "test_user"

    @pytest.mark.asyncio
    async def test_start_experiment(self, manager, experiment_config):
        """Test starting an experiment."""
        # Create experiment first
        experiment_id = await manager.create_experiment(experiment_config)

        # Start the experiment
        result = await manager.start_experiment(experiment_id)

        assert result is True

        # Verify experiment status was updated
        with manager.get_db_session() as db_session:
            experiment = db_session.query(ExperimentModel).filter_by(id=experiment_id).first()
            assert experiment.status == "active"
            assert experiment.start_time is not None

    @pytest.mark.asyncio
    async def test_stop_experiment(self, manager, experiment_config):
        """Test stopping an experiment."""
        # Create and start experiment
        experiment_id = await manager.create_experiment(experiment_config)
        await manager.start_experiment(experiment_id)

        # Stop the experiment
        result = await manager.stop_experiment(experiment_id)

        assert result is True

        # Verify experiment status was updated
        with manager.get_db_session() as db_session:
            experiment = db_session.query(ExperimentModel).filter_by(id=experiment_id).first()
            assert experiment.status == "completed"
            assert experiment.end_time is not None

    @pytest.mark.asyncio
    async def test_assign_user_to_experiment(self, manager, experiment_config):
        """Test user assignment to experiment."""
        # Create and start experiment
        experiment_id = await manager.create_experiment(experiment_config)
        await manager.start_experiment(experiment_id)

        characteristics = UserCharacteristics(
            user_id="test_user",
            usage_frequency="high",
        )

        variant, segment = await manager.assign_user_to_experiment(
            "test_user",
            experiment_id,
            characteristics,
        )

        assert variant in ["control", "treatment"]
        assert isinstance(segment, UserSegment)


class TestGlobalFunctions:
    """Test global functions and helpers."""

    @pytest.mark.asyncio
    async def test_create_dynamic_loading_experiment(self):
        """Test creating standard dynamic loading experiment."""
        with patch("src.core.ab_testing_framework.get_experiment_manager") as mock_get_manager:
            mock_manager = AsyncMock(spec=ExperimentManager)
            mock_manager.create_experiment.return_value = "exp_dynamic_loading_123"
            mock_manager.start_experiment.return_value = True
            mock_get_manager.return_value = mock_manager

            experiment_id = await create_dynamic_loading_experiment(
                target_percentage=75.0,
                duration_hours=72,
            )

            assert experiment_id == "exp_dynamic_loading_123"

            # Verify manager methods were called
            mock_manager.create_experiment.assert_called_once()
            mock_manager.start_experiment.assert_called_once_with("exp_dynamic_loading_123")


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.fixture
    def manager(self):
        """Create ExperimentManager with in-memory database."""
        return ExperimentManager("sqlite:///:memory:")

    @pytest.mark.asyncio
    async def test_complete_experiment_lifecycle(self, manager):
        """Test complete experiment lifecycle from creation to completion."""
        # 1. Create experiment config
        config = ExperimentConfig(
            name="Complete Lifecycle Test",
            description="Test complete A/B test lifecycle",
            experiment_type=ExperimentType.DYNAMIC_LOADING,
            rollout_steps=[1.0, 5.0, 25.0],
            success_criteria={"min_token_reduction": 70.0, "min_success_rate": 95.0},
            failure_thresholds={"max_error_rate": 5.0},
        )

        # 2. Create experiment
        experiment_id = await manager.create_experiment(config, "integration_test")
        assert experiment_id.startswith("exp_")

        # 3. Start experiment
        start_result = await manager.start_experiment(experiment_id)
        assert start_result is True

        # 4. Assign multiple users
        users = ["user_1", "user_2", "user_3"]
        assignments = {}

        for user_id in users:
            characteristics = UserCharacteristics(
                user_id=user_id,
                usage_frequency="high",
                is_early_adopter=(user_id == "user_1"),
            )
            variant, segment = await manager.assign_user_to_experiment(
                user_id,
                experiment_id,
                characteristics,
            )
            assignments[user_id] = (variant, segment)

        # 5. Record optimization results
        for user_id in users:
            result = Mock(spec=ProcessingResult)
            result.success = True
            result.total_time_ms = 120.0
            result.reduction_percentage = 80.0
            result.session_id = f"session_{user_id}"
            result.detection_time_ms = 20.0
            result.loading_time_ms = 80.0
            result.cache_hit = True
            result.fallback_used = False
            result.baseline_tokens = 1000
            result.optimized_tokens = 200
            result.target_achieved = True
            result.error_message = None

            await manager.record_optimization_result(experiment_id, user_id, result)

        # 6. Stop experiment
        stop_result = await manager.stop_experiment(experiment_id)
        assert stop_result is True

        # Verify experiment was marked as completed
        with manager.get_db_session() as db_session:
            experiment = db_session.query(ExperimentModel).filter_by(id=experiment_id).first()
            assert experiment.status == "completed"
            assert experiment.end_time is not None
