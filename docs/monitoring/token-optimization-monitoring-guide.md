# Token Optimization Performance Monitoring Guide

## Overview

The Token Optimization Performance Monitoring System provides comprehensive monitoring, metrics collection, and validation for the dynamic function loading system's **70% token reduction goal**. This system ensures that optimization claims are statistically validated and that user experience remains optimal.

## Key Features

### 📊 Core Monitoring Capabilities
- **Token Usage Tracking**: Measure actual vs. baseline token consumption
- **Function Loading Performance**: Monitor loading latency by tier (Tier 1: <50ms, Tier 2: <100ms, Tier 3: <200ms)
- **User Experience Metrics**: Track success rates, error rates, and user satisfaction
- **Statistical Validation**: Rigorous statistical testing of optimization claims

### 🎯 Validation Goals
- **Primary Goal**: Validate 70% token reduction with 95% confidence
- **Performance Goal**: Maintain function loading latency under 200ms (P95)
- **Experience Goal**: Maintain 95%+ success rate and 80%+ task detection accuracy
- **Reliability Goal**: Keep fallback activation rate under 10%

### 🔄 Real-time Capabilities
- Live dashboard with WebSocket updates
- Automated alerting and notifications
- Trend analysis and anomaly detection
- External system integrations (Prometheus, Grafana, DataDog, etc.)

## Quick Start

### 1. Basic Setup

```python
from src.monitoring import initialize_monitoring_system

# Initialize with default configuration
monitor, collector, dashboard = await initialize_monitoring_system()

# Monitor a user session
await monitor.start_session_monitoring(
    session_id="session_123",
    user_id="user_456",
    task_type="debugging",
    optimization_level=OptimizationStatus.BALANCED
)

# Record function loading
await monitor.record_function_loading(
    session_id="session_123",
    tier=FunctionTier.TIER_1,
    functions_loaded=["debug_analyzer", "error_handler"],
    loading_time_ms=45.2,
    tokens_consumed=1200,
    cache_hit=True
)

# Record function usage
await monitor.record_function_usage(
    session_id="session_123",
    function_name="debug_analyzer",
    success=True,
    tier=FunctionTier.TIER_1
)

# End session monitoring
session_metrics = await monitor.end_session_monitoring("session_123")
```

### 2. Configuration

Create `config/monitoring_config.yaml`:

```yaml
enabled: true
validation_target: 0.70  # 70% token reduction
dashboard_enabled: true
dashboard_port: 8080
integrations_enabled: true
```

### 3. Dashboard Access

Access the real-time dashboard at: `http://localhost:8080`

## Detailed Usage

### Session Monitoring Workflow

```python
import asyncio
from src.monitoring import get_monitoring_system
from src.core.token_optimization_monitor import OptimizationStatus, FunctionTier

async def monitor_user_session():
    # Get monitoring system
    system = get_monitoring_system()
    monitor = system.monitor

    # 1. Start session monitoring
    await monitor.start_session_monitoring(
        session_id="debug_session_001",
        user_id="developer_123",
        task_type="debugging",
        optimization_level=OptimizationStatus.AGGRESSIVE
    )

    # 2. Record task detection
    await monitor.record_task_detection(
        session_id="debug_session_001",
        detected_task="debugging",
        confidence=0.92,
        actual_task="debugging"  # For accuracy measurement
    )

    # 3. Record function loading by tier
    # Tier 1 functions (most frequently used)
    await monitor.record_function_loading(
        session_id="debug_session_001",
        tier=FunctionTier.TIER_1,
        functions_loaded=["debug_analyzer", "error_handler", "log_parser"],
        loading_time_ms=42.1,
        tokens_consumed=800,
        cache_hit=True
    )

    # Tier 2 functions (moderately used)
    await monitor.record_function_loading(
        session_id="debug_session_001",
        tier=FunctionTier.TIER_2,
        functions_loaded=["performance_profiler", "memory_analyzer"],
        loading_time_ms=89.5,
        tokens_consumed=600,
        cache_hit=False
    )

    # 4. Record actual function usage
    functions_used = [
        ("debug_analyzer", True, FunctionTier.TIER_1),
        ("error_handler", True, FunctionTier.TIER_1),
        ("log_parser", False, FunctionTier.TIER_1),  # Failed
        ("performance_profiler", True, FunctionTier.TIER_2)
    ]

    for func_name, success, tier in functions_used:
        await monitor.record_function_usage(
            session_id="debug_session_001",
            function_name=func_name,
            success=success,
            tier=tier
        )

    # 5. Record any fallback activations
    if "some_missing_function" not in ["debug_analyzer", "error_handler"]:
        await monitor.record_fallback_activation(
            session_id="debug_session_001",
            reason="function_not_loaded",
            missing_functions=["some_missing_function"]
        )

    # 6. End session and get metrics
    final_metrics = await monitor.end_session_monitoring("debug_session_001")

    print(f"Session completed:")
    print(f"- Token reduction: {final_metrics.baseline_tokens_loaded - final_metrics.optimized_tokens_loaded} tokens")
    print(f"- Functions loaded: {final_metrics.optimized_functions_loaded}")
    print(f"- Functions used: {len(final_metrics.functions_actually_used)}")
    print(f"- Success rate: {final_metrics.commands_successful / (final_metrics.commands_successful + final_metrics.commands_failed)}")

# Run the monitoring
asyncio.run(monitor_user_session())
```

### Metrics Collection and Analysis

```python
from src.monitoring.metrics_collector import get_metrics_collector
from datetime import timedelta

async def analyze_performance():
    collector = get_metrics_collector()

    # Generate comprehensive report
    report = await collector.generate_comprehensive_report(
        time_period=timedelta(days=7)
    )

    # Check validation results
    validation = report["validation_results"]["token_reduction_claim"]
    if validation["validated"]:
        print(f"✅ Token reduction validated with {validation['confidence_level']*100:.1f}% confidence")
        print(f"📊 Average reduction: {validation['details']['sample_mean']:.1f}%")
    else:
        print(f"❌ Token reduction validation failed")
        print(f"📊 Current average: {validation['details']['sample_mean']:.1f}%")
        print(f"🎯 Target: {validation['details']['target_reduction']:.1f}%")

    # Check trend analysis
    trends = report["trend_analysis"]
    token_trend = trends["token_reduction_percentage"]

    print(f"\n📈 Token Reduction Trend:")
    print(f"- Direction: {token_trend['trend_direction']}")
    print(f"- Strength: {token_trend['trend_strength']:.2f}")
    print(f"- Statistical significance: {token_trend['statistical_significance']}")

    # Performance analysis
    latency_trend = trends["loading_latency_ms"]
    print(f"\n⚡ Loading Latency Trend:")
    print(f"- Direction: {latency_trend['trend_direction']}")
    print(f"- Average latency: {latency_trend['predicted_values'][0]:.1f}ms")

    return report

# Analyze current performance
report = asyncio.run(analyze_performance())
```

### Dashboard Integration

```python
from src.monitoring.performance_dashboard import get_dashboard_app
import uvicorn

# Get the FastAPI dashboard app
app = get_dashboard_app()

# Run the dashboard server
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
```

### External Integration Setup

```python
from src.monitoring.integration_utils import get_integration_manager

async def setup_integrations():
    # Load integration manager
    integration_manager = get_integration_manager("config/integrations_config.json")

    # Validate all configurations
    validation_results = await integration_manager.validate_all_configurations()

    for integration_name, is_valid in validation_results.items():
        if is_valid:
            print(f"✅ {integration_name} integration configured correctly")
        else:
            print(f"❌ {integration_name} integration has configuration issues")

    # Send test metrics
    test_metrics = {
        "system_health": {
            "average_token_reduction": 72.5,
            "overall_success_rate": 96.2,
            "concurrent_sessions": 15
        }
    }

    # Send to all configured integrations
    results = await integration_manager.send_metrics_to_all(test_metrics)

    for integration_name, success in results.items():
        status = "✅ sent" if success else "❌ failed"
        print(f"{integration_name}: {status}")

# Setup integrations
asyncio.run(setup_integrations())
```

## Dashboard Features

### Real-time Metrics Display

The dashboard provides live updates every 5 seconds showing:

1. **Key Performance Indicators**
   - Average token reduction percentage
   - Overall success rate
   - Average loading latency
   - Active sessions count

2. **Interactive Charts**
   - Token reduction over time
   - Loading latency performance (average, P95, P99)
   - Function tier performance breakdown

3. **Validation Status**
   - Overall optimization validation status
   - Confidence percentage
   - Individual criteria status (color-coded)

4. **Active Sessions Table**
   - Real-time session monitoring
   - Per-session metrics
   - Duration and progress tracking

5. **Alert Panel**
   - Current system alerts
   - Alert severity levels
   - Recent alert history

### Dashboard API Endpoints

```bash
# Prometheus metrics
GET /metrics

# JSON metrics
GET /api/metrics

# System health
GET /api/health

# Optimization report
GET /api/optimization-report?user_id=optional

# Current alerts
GET /api/alerts

# Alert summary
GET /api/alerts/summary?hours=24

# WebSocket for real-time updates
WS /ws/dashboard
```

## Configuration Reference

### Core Monitoring Settings

```yaml
# monitoring_config.yaml
enabled: true                        # Enable/disable monitoring
validation_target: 0.70             # 70% token reduction target
min_acceptable_reduction: 0.50      # 50% minimum acceptable
max_loading_latency_ms: 200.0       # Max latency threshold

# Collection intervals (seconds)
metrics_collection_interval: 30.0   # How often to collect metrics
aggregation_interval: 300.0         # How often to aggregate
dashboard_update_interval: 5.0      # Dashboard refresh rate

# Alert thresholds
alert_thresholds:
  token_reduction_min: 50.0         # Alert if below 50%
  latency_max_ms: 200.0            # Alert if above 200ms
  success_rate_min: 0.95           # Alert if below 95%
  task_accuracy_min: 0.80          # Alert if below 80%
  fallback_rate_max: 0.10          # Alert if above 10%
```

### External Integration Settings

```json
{
  "prometheus": {
    "enabled": true,
    "pushgateway_url": "http://localhost:9091",
    "job_name": "token_optimization"
  },
  "grafana": {
    "enabled": true,
    "api_url": "http://localhost:3000/api",
    "api_key": "your_grafana_api_key"
  },
  "slack": {
    "enabled": true,
    "webhook_url": "https://hooks.slack.com/...",
    "channel": "#alerts"
  }
}
```

## Statistical Validation

### Validation Criteria

The system validates the 70% token reduction claim using rigorous statistical methods:

1. **Sample Size**: Minimum 10 sessions for basic validation, 50+ for high confidence
2. **Statistical Test**: One-sample t-test against 70% target
3. **Significance Level**: p < 0.05 required for validation
4. **Effect Size**: Cohen's d > 0.5 for meaningful difference
5. **Statistical Power**: > 80% power required for reliable results

### Validation Report

```python
# Get validation report
report = await collector.generate_comprehensive_report()
validation = report["validation_results"]["token_reduction_claim"]

print(f"Validation Status: {validation['validated']}")
print(f"Confidence Level: {validation['confidence_level']*100:.1f}%")
print(f"P-value: {validation['p_value']:.4f}")
print(f"Effect Size: {validation['effect_size']:.2f}")
print(f"Sample Size: {validation['sample_size']}")
print(f"Statistical Power: {validation['statistical_power']*100:.1f}%")
print(f"Evidence Strength: {validation['evidence_strength']}")
```

## Performance Benchmarks

### Target Performance Metrics

| Metric | Target | Threshold | Alert Level |
|--------|--------|-----------|-------------|
| Token Reduction | 70% | 50% minimum | Critical if <50% |
| Loading Latency (P95) | <200ms | <300ms | Warning if >200ms |
| Success Rate | >95% | >90% | Warning if <95% |
| Task Detection Accuracy | >80% | >70% | Warning if <80% |
| Fallback Rate | <10% | <15% | Warning if >10% |
| Concurrent Sessions | 1000+ | 500+ | Info if approaching |

### Function Tier Performance

| Tier | Target Latency | Functions | Usage Pattern |
|------|----------------|-----------|---------------|
| Tier 1 | <50ms | Most frequent | 80%+ of sessions |
| Tier 2 | <100ms | Moderate use | 40-60% of sessions |
| Tier 3 | <200ms | Occasional | <20% of sessions |
| Fallback | Variable | On-demand | Emergency only |

## Troubleshooting

### Common Issues

1. **Low Token Reduction**
   ```python
   # Check task detection accuracy
   report = await monitor.get_optimization_report()
   accuracy = report["user_experience"]["average_task_detection_accuracy"]

   if accuracy < 80:
       print("Issue: Poor task detection accuracy")
       print("Solution: Review task detection algorithm")
   ```

2. **High Loading Latency**
   ```python
   # Check cache performance
   tier_metrics = monitor.function_metrics[FunctionTier.TIER_1]
   cache_hit_rate = tier_metrics.cache_hits / (tier_metrics.cache_hits + tier_metrics.cache_misses)

   if cache_hit_rate < 0.8:
       print("Issue: Low cache hit rate")
       print("Solution: Optimize caching strategy")
   ```

3. **Validation Failures**
   ```python
   # Check sample size and statistical power
   validation = report["validation_results"]["token_reduction_claim"]

   if validation["sample_size"] < 20:
       print("Issue: Insufficient sample size")
       print("Solution: Collect more data before validation")

   if validation["statistical_power"] < 0.8:
       print("Issue: Low statistical power")
       print("Solution: Increase sample size or effect size")
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger("src.monitoring").setLevel(logging.DEBUG)

# Or in configuration
development:
  debug_logging: true
```

## API Reference

### Core Monitoring API

```python
# TokenOptimizationMonitor
await monitor.start_session_monitoring(session_id, user_id, task_type, optimization_level)
await monitor.record_function_loading(session_id, tier, functions, latency, tokens, cache_hit)
await monitor.record_function_usage(session_id, function_name, success, tier)
await monitor.record_task_detection(session_id, detected_task, confidence, actual_task)
await monitor.record_fallback_activation(session_id, reason, missing_functions)
await monitor.record_user_override(session_id, override_type, from_opt, to_opt)
await monitor.end_session_monitoring(session_id)
await monitor.generate_system_health_report()
await monitor.export_metrics(format, include_raw_data)
```

### Metrics Collection API

```python
# MetricsCollector
await collector.start_collection()
await collector.stop_collection()
await collector.generate_comprehensive_report(time_period)
await collector.export_for_external_analysis(format)
```

### Dashboard API

```python
# Dashboard endpoints
GET /                              # Main dashboard
GET /metrics                       # Prometheus metrics
GET /api/metrics                   # JSON metrics
GET /api/health                    # Health status
GET /api/optimization-report       # Optimization report
GET /api/alerts                    # Current alerts
WS /ws/dashboard                   # Real-time updates
```

## Privacy and Security

### Data Protection
- User identifiers are anonymized by default
- No raw session data collected unless explicitly enabled
- Configurable data retention periods
- GDPR-compliant data handling

### Security Measures
- No sensitive information in metrics
- Secure external integration credentials
- Rate limiting on API endpoints
- Input validation and sanitization

## Best Practices

### 1. Session Monitoring
- Always call `start_session_monitoring()` before other tracking
- Ensure `end_session_monitoring()` is called even on errors
- Use meaningful session and user IDs (but anonymized)
- Specify accurate task types for better analysis

### 2. Function Loading Tracking
- Record loading metrics immediately after function loading
- Accurately specify function tiers based on usage patterns
- Track cache hits/misses for performance optimization
- Include actual token consumption measurements

### 3. Performance Optimization
- Monitor tier assignment accuracy regularly
- Optimize based on actual usage patterns, not assumptions
- Use statistical validation before claiming performance improvements
- Set up automated alerts for performance regressions

### 4. Statistical Validation
- Collect sufficient sample sizes (50+ for robust validation)
- Use appropriate confidence levels (95% recommended)
- Consider effect sizes, not just statistical significance
- Validate claims periodically, not just once

## Support and Maintenance

### Regular Maintenance Tasks

1. **Daily**: Check dashboard for alerts and anomalies
2. **Weekly**: Review validation status and trend analysis
3. **Monthly**: Analyze comprehensive reports and optimize
4. **Quarterly**: Update thresholds based on performance data

### Monitoring Health

```python
# Check monitoring system health
system = get_monitoring_system()
status = await system.get_system_status()

print(f"System running: {status['running']}")
print(f"Validation status: {status['health_report']['optimization_validated']}")
print(f"Integration health: {status['integrations']['overall_healthy']}")
```

This comprehensive monitoring system ensures that the dynamic function loading optimization delivers on its promises while maintaining excellent user experience and system reliability.
