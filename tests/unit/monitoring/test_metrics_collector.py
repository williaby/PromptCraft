import asyncio
from datetime import datetime, timedelta

import pytest

from src.core.token_optimization_monitor import FunctionTier
from src.monitoring.metrics_collector import (
    AggregatedMetric,
    MetricAggregationType,
    MetricPoint,
    MetricsAggregator,
    MetricsCollector,
    MetricsDatabase,
    StatisticalValidator,
    TimeWindow,
    TrendAnalyzer,
    ValidationResult,
)
from src.utils.datetime_compat import UTC


@pytest.mark.asyncio
async def test_metrics_database_store_and_query(tmp_path):
    db = MetricsDatabase(tmp_path / "metrics.db")

    ts = datetime.now(UTC)
    point = MetricPoint(
        timestamp=ts,
        metric_name="token_reduction_percentage",
        value=75.0,
        labels={"source": "system_health"},
        metadata={"example": 1},
    )
    await db.store_metric_point(point)

    agg = AggregatedMetric(
        metric_name="token_reduction_percentage",
        time_window=TimeWindow.FIVE_MINUTES,
        window_start=ts - timedelta(minutes=5),
        window_end=ts,
        aggregation_type=MetricAggregationType.AVERAGE,
        value=75.0,
        sample_count=1,
        labels={"source": "system_health"},
    )
    await db.store_aggregated_metric(agg)

    vr = ValidationResult(
        claim="Token reduction >= 70%",
        validated=True,
        confidence_level=0.95,
        p_value=0.01,
        effect_size=0.8,
        sample_size=30,
        statistical_power=0.9,
        evidence_strength="strong",
        details={"note": "ok"},
    )
    await db.store_validation_result(vr)

    points = await db.get_metric_points(
        "token_reduction_percentage",
        ts - timedelta(hours=1),
        ts + timedelta(hours=1),
        labels={"source": "system_health"},
    )
    assert len(points) == 1
    assert points[0].metric_name == "token_reduction_percentage"


@pytest.mark.asyncio
async def test_metrics_aggregator_aggregate(tmp_path):
    db = MetricsDatabase(tmp_path / "agg.db")
    aggr = MetricsAggregator(db)

    # Insert points over 1 hour, every 10 minutes
    end = datetime.now(UTC)
    start = end - timedelta(hours=1)
    cur = start
    values = []
    i = 0
    while cur <= end:
        val = float(50 + i)
        values.append(val)
        await db.store_metric_point(MetricPoint(timestamp=cur, metric_name="m1", value=val, labels={"k": "v"}))
        cur += timedelta(minutes=10)
        i += 1

    # Aggregate with multiple types to cover branches
    agg_types = [
        MetricAggregationType.SUM,
        MetricAggregationType.AVERAGE,
        MetricAggregationType.MEDIAN,
        MetricAggregationType.COUNT,
        MetricAggregationType.MIN,
        MetricAggregationType.MAX,
        MetricAggregationType.PERCENTILE_95,
        MetricAggregationType.PERCENTILE_99,
        MetricAggregationType.STANDARD_DEVIATION,
    ]
    out = await aggr.aggregate_metrics(
        metric_name="m1",
        time_window=TimeWindow.FIFTEEN_MINUTES,
        start_time=start,
        end_time=end,
        aggregation_types=agg_types,
    )
    assert out, "should produce aggregated metrics"
    # Ensure grouping produced some windows and stored
    assert any(m.aggregation_type == MetricAggregationType.AVERAGE for m in out)

    # No points path
    out2 = await aggr.aggregate_metrics(
        metric_name="no_such_metric",
        time_window=TimeWindow.MINUTE,
        start_time=start,
        end_time=end,
        aggregation_types=[MetricAggregationType.SUM],
    )
    assert out2 == []


@pytest.mark.asyncio
async def test_trend_analyzer_analysis_and_anomalies(tmp_path):
    db = MetricsDatabase(tmp_path / "trend.db")
    ta = TrendAnalyzer(db)

    end = datetime.now(UTC)
    # Insufficient data
    for i in range(3):
        await db.store_metric_point(
            MetricPoint(timestamp=end - timedelta(minutes=10 * i), metric_name="t1", value=10 + i),
        )
    res = await ta.analyze_trend("t1", timedelta(hours=1), end_time=end)
    assert res.trend_direction == "insufficient_data"

    # Enough data, increasing trend
    db2 = MetricsDatabase(tmp_path / "trend2.db")
    ta2 = TrendAnalyzer(db2)
    for i in range(12):
        await db2.store_metric_point(
            MetricPoint(timestamp=end - timedelta(minutes=5 * (11 - i)), metric_name="t2", value=float(i)),
        )
    res2 = await ta2.analyze_trend("t2", timedelta(hours=1), end_time=end)
    assert res2.trend_direction in {"increasing", "stable"}
    assert len(res2.predicted_values) == 24

    # Anomaly detection
    for i in range(15):
        await db2.store_metric_point(
            MetricPoint(timestamp=end - timedelta(minutes=2 * (14 - i)), metric_name="t3", value=100.0),
        )
    # Inject an outlier
    await db2.store_metric_point(MetricPoint(timestamp=end - timedelta(minutes=1), metric_name="t3", value=1000.0))
    anomalies = await ta2.detect_anomalies("t3", timedelta(hours=1), sensitivity=2.0)
    assert isinstance(anomalies, list)
    assert any(abs(p.value - 1000.0) < 1e-6 for p in anomalies)


@pytest.mark.asyncio
async def test_statistical_validator_paths(tmp_path):
    db = MetricsDatabase(tmp_path / "val.db")
    sv = StatisticalValidator(db)

    # Insufficient data for token reduction claim
    res_insuf = await sv.validate_token_reduction_claim(target_reduction=0.7, time_period=timedelta(days=7))
    assert res_insuf.validated is False
    assert res_insuf.sample_size < 10

    # Enough high reductions -> validated True
    now = datetime.now(UTC)
    for i in range(30):
        # Add slight variance to avoid SciPy precision-loss warnings in t-test
        val = 85.0 + (i % 3) * 0.2
        await db.store_metric_point(
            MetricPoint(
                timestamp=now - timedelta(hours=i),
                metric_name="token_reduction_percentage",
                value=val,
            ),
        )
    res_ok = await sv.validate_token_reduction_claim()
    assert res_ok.validated is True

    # Validate multiple claims; prepare metrics
    for i in range(12):
        await db.store_metric_point(
            MetricPoint(timestamp=now - timedelta(hours=i), metric_name="function_loading_latency_ms", value=150.0),
        )
        await db.store_metric_point(
            MetricPoint(timestamp=now - timedelta(hours=i), metric_name="success_rate_percentage", value=97.0),
        )
        await db.store_metric_point(
            MetricPoint(timestamp=now - timedelta(hours=i), metric_name="task_detection_accuracy", value=85.0),
        )
    results = await sv.validate_performance_claims()
    assert len(results) == 4
    # Expect at least one True
    assert any(r.validated for r in results)

    # Directly exercise evidence strength branches
    assert sv._determine_evidence_strength(effect_size=0.1, p_value=0.2, power=0.1) == "weak"
    assert sv._determine_evidence_strength(effect_size=0.6, p_value=0.02, power=0.9) in {"moderate", "weak"}
    assert sv._determine_evidence_strength(effect_size=0.4, p_value=0.005, power=0.85) in {"strong", "moderate"}
    assert sv._determine_evidence_strength(effect_size=0.6, p_value=0.0005, power=0.9) in {"very_strong", "strong"}


class FakeHealth:
    def __init__(self):
        self.average_token_reduction_percentage = 72.0
        self.average_loading_latency_ms = 120.0
        self.p95_loading_latency_ms = 180.0
        self.p99_loading_latency_ms = 220.0
        self.overall_success_rate = 0.98
        self.task_detection_accuracy_rate = 0.9
        self.fallback_activation_rate = 0.05
        self.concurrent_sessions_handled = 3
        self.total_sessions = 10


class FakeTierMetrics:
    def __init__(self):
        self.functions_loaded = 5
        self.loading_time_ms = 50.0
        self.cache_hits = 2
        self.cache_misses = 1
        self.tokens_consumed = 123
        self.usage_frequency = 0.5


class FakeMonitor:
    def __init__(self):
        self.validation_confidence = 0.8
        self.optimization_validated = True
        self.function_metrics = {
            FunctionTier.TIER_1: FakeTierMetrics(),
            FunctionTier.TIER_2: FakeTierMetrics(),
        }

    async def generate_system_health_report(self):
        return FakeHealth()

    async def export_metrics(self, include_raw_data: bool = False):
        return {"exported": True, "raw": include_raw_data}


@pytest.mark.asyncio
async def test_metrics_collector_collect_and_report(tmp_path, monkeypatch):
    db_path = tmp_path / "collector.db"
    mc = MetricsCollector(FakeMonitor(), db_path=db_path)

    # Collect once
    await mc._collect_current_metrics()

    # Confirm some metrics stored
    pts = await mc.database.get_metric_points(
        "token_reduction_percentage",
        datetime.now(UTC) - timedelta(hours=1),
        datetime.now(UTC) + timedelta(hours=1),
    )
    assert len(pts) >= 1

    # Patch validator and trend analyzer to speed report
    class VF:
        async def validate_performance_claims(self):
            return [
                ValidationResult(
                    claim="c1",
                    validated=True,
                    confidence_level=0.9,
                    p_value=0.01,
                    effect_size=0.5,
                    sample_size=10,
                    statistical_power=0.85,
                    evidence_strength="strong",
                    details={},
                ),
            ]

        async def validate_token_reduction_claim(self):
            return ValidationResult(
                claim="token",
                validated=True,
                confidence_level=0.95,
                p_value=0.001,
                effect_size=0.6,
                sample_size=30,
                statistical_power=0.9,
                evidence_strength="very_strong",
                details={},
            )

    class TA:
        async def analyze_trend(self, metric, period):
            from src.monitoring.metrics_collector import TrendAnalysis

            return TrendAnalysis(
                metric_name=metric,
                time_period=period,
                trend_direction="increasing",
                trend_strength=0.9,
                slope=1.0,
                r_squared=0.8,
                statistical_significance=True,
                confidence_interval=(0.5, 1.5),
                predicted_values=[1, 2, 3],
            )

        async def detect_anomalies(self, metric, period):
            return []

    mc.validator = VF()
    mc.trend_analyzer = TA()
    report = await mc.generate_comprehensive_report(time_period=timedelta(days=1))
    assert report["validation_results"]["overall_validation_status"] is True
    assert "trend_analysis" in report
    assert "anomaly_detection" in report

    # Export wrapper
    export = await mc.export_for_external_analysis(format_type="json")
    assert export["export_format"] == "json"
    assert "data" in export

    # Exercise other export format branches
    exp_p = await mc.export_for_external_analysis(format_type="prometheus")
    assert exp_p["export_format"] == "prometheus"
    exp_g = await mc.export_for_external_analysis(format_type="grafana")
    assert exp_g["export_format"] == "grafana"


@pytest.mark.asyncio
async def test_metrics_collector_aggregation_loop_and_start_stop(monkeypatch, tmp_path):
    # Speed up sleeps
    async def fast_sleep(_):
        await asyncio.sleep(0)

    mc = MetricsCollector(FakeMonitor(), db_path=tmp_path / "loop.db")
    mc.collection_interval = 0.01
    mc.aggregation_interval = 0.01

    # Replace aggregator to induce an error once
    calls = {"n": 0}

    class FA:
        async def aggregate_metrics(self, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("boom")
            return []

    mc.aggregator = FA()

    # Monkeypatch sleep inside this test scope using original to avoid recursion
    _orig_sleep = asyncio.sleep

    async def _fast(t):
        await _orig_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", _fast)

    # Start and run briefly, then stop
    await mc.start_collection()
    # Let the event loop process a bit
    await asyncio.sleep(0.05)
    await mc.stop_collection()
    assert mc._collection_task is None or mc._collection_task.done()
    assert mc._aggregation_task is None or mc._aggregation_task.done()


@pytest.mark.asyncio
async def test_global_collector_initialization(monkeypatch):
    # Ensure singleton is reset
    from src.monitoring import metrics_collector as mc_mod

    mc_mod._global_collector = None

    # Provide fake monitor
    monkeypatch.setattr(
        "src.core.token_optimization_monitor.get_token_optimization_monitor",
        lambda: FakeMonitor(),
    )

    # Prevent background tasks
    async def _noop_start(self):
        return None

    monkeypatch.setattr(mc_mod.MetricsCollector, "start_collection", _noop_start)

    # initialize and get collector
    coll = await mc_mod.initialize_metrics_collection()
    assert isinstance(coll, mc_mod.MetricsCollector)
    # get_metrics_collector returns same instance
    assert mc_mod.get_metrics_collector() is coll
