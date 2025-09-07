# Stateless Security Monitor Implementation

## Overview

The `SecurityMonitor` has been converted from a stateful to stateless design to support multi-worker FastAPI deployment. All monitoring state is now persisted in PostgreSQL database instead of in-memory data structures.

## Key Changes

### Removed Stateful Components

The following in-memory state has been removed:

- `_event_history`: Dict of event tracking by entity key
- `_blocked_ips`: Set of blocked IP addresses
- `_blocked_users`: Set of blocked user IDs
- `_threat_scores`: Dict of threat scores by entity
- `_monitoring_task`: Background monitoring task
- `_alert_callbacks`: List of alert callback functions

### Added Database Models

Four new PostgreSQL tables support the stateless design:

#### SecurityEvent (security_events_monitor)

- Stores security events for monitoring and correlation
- Indexed by entity_key, timestamp, event_type, severity
- Replaces in-memory `_event_history`

#### BlockedEntity (blocked_entities)

- Stores blocked IP addresses and users
- Supports expiration dates and blocking reasons
- Replaces in-memory `_blocked_ips` and `_blocked_users`

#### ThreatScore (threat_scores)

- Stores dynamic threat scores with automatic decay
- Supports upsert operations for efficient updates
- Replaces in-memory `_threat_scores`

#### MonitoringThreshold (monitoring_thresholds)

- Stores configurable monitoring thresholds
- Allows runtime configuration updates
- Supports multiple threshold types

## Public API Compatibility

The public API remains identical for backward compatibility:

```python
# Existing API still works
monitor = SecurityMonitor(alert_threshold=5, time_window=60)
await monitor.initialize()
await monitor.track_event(security_event)
score = await monitor.get_threat_score("192.168.1.1", "ip")
await monitor.block_ip("192.168.1.1", "Suspicious activity")
blocked = monitor.is_blocked("192.168.1.1", "ip")
stats = await monitor.get_monitoring_stats()
```

### New Async Methods

Additional async methods provide better performance:

```python
# New async version for better performance
blocked = await monitor.is_blocked_async("192.168.1.1", "ip")

# New cleanup method for data retention
cleanup_stats = await monitor.cleanup_old_data(retention_hours=24)
```

## Database Schema

### Migration Script

The migration script creates all necessary tables with proper indexes:

```sql
-- Security events for monitoring
CREATE TABLE security_events_monitor (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_key VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    ip_address INET,
    risk_score INTEGER DEFAULT 0,
    event_details JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Blocked entities (IPs and users)
CREATE TABLE blocked_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_key VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(20) NOT NULL,
    entity_value VARCHAR(255) NOT NULL,
    reason TEXT,
    blocked_by VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    blocked_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dynamic threat scores
CREATE TABLE threat_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_key VARCHAR(255) UNIQUE NOT NULL,
    entity_type VARCHAR(20) NOT NULL,
    entity_value VARCHAR(255) NOT NULL,
    score INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    score_details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Monitoring configuration
CREATE TABLE monitoring_thresholds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    threshold_name VARCHAR(100) UNIQUE NOT NULL,
    threshold_value INTEGER NOT NULL,
    description TEXT,
    threshold_metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);
```

### Performance Indexes

Optimized indexes support common query patterns:

```sql
-- Security events indexes
CREATE INDEX ix_security_events_monitor_entity_key ON security_events_monitor(entity_key);
CREATE INDEX ix_security_events_monitor_timestamp ON security_events_monitor(timestamp);
CREATE INDEX ix_security_events_monitor_entity_timestamp ON security_events_monitor(entity_key, timestamp);

-- Blocked entities indexes
CREATE INDEX ix_blocked_entities_active_lookup ON blocked_entities(entity_key, is_active);

-- Threat scores indexes
CREATE INDEX ix_threat_scores_entity_key ON threat_scores(entity_key);
CREATE INDEX ix_threat_scores_last_updated ON threat_scores(last_updated);
```

## Implementation Details

### Event Tracking

Events are now stored directly in the database:

```python
async def track_event(self, event: SecurityEventResponse) -> None:
    async with self._db_manager.get_session() as session:
        # Store event in database
        await self._store_security_event(session, event)

        # Check thresholds using database queries
        if event.ip_address:
            ip_key = f"ip:{event.ip_address}"
            if await self._check_threshold(session, ip_key, event.timestamp):
                await self._trigger_alert("ip_threshold", event.ip_address)

        await session.commit()
```

### Threshold Checking

Thresholds are checked using database queries:

```python
async def _check_threshold(self, session, entity_key: str, event_timestamp: datetime) -> bool:
    # Get threshold from database
    stmt = select(MonitoringThreshold.threshold_value).where(
        and_(
            MonitoringThreshold.threshold_name == "alert_threshold",
            MonitoringThreshold.is_active == True
        )
    )
    result = await session.execute(stmt)
    threshold = result.scalar() or self.alert_threshold

    # Count recent events
    cutoff = event_timestamp - timedelta(seconds=self.time_window)
    stmt = select(func.count(SecurityEvent.id)).where(
        and_(
            SecurityEvent.entity_key == entity_key,
            SecurityEvent.timestamp > cutoff
        )
    )
    result = await session.execute(stmt)
    count = result.scalar() or 0

    return count >= threshold
```

### Threat Score Updates

Threat scores use PostgreSQL upsert for efficiency:

```python
async def _upsert_threat_score(self, session, entity_key: str,
                             entity_type: str, entity_value: str,
                             score_increment: int) -> None:
    stmt = insert(ThreatScore).values(
        entity_key=entity_key,
        entity_type=entity_type,
        entity_value=entity_value,
        score=score_increment
    )

    stmt = stmt.on_conflict_do_update(
        index_elements=['entity_key'],
        set_=dict(
            score=ThreatScore.score + stmt.excluded.score,
            last_updated=func.now()
        )
    )

    await session.execute(stmt)
```

## Multi-Worker Benefits

### Scalability

- No shared in-memory state between workers
- Each worker can process events independently
- Database handles concurrency and consistency

### Reliability

- State persists across worker restarts
- No data loss from worker failures
- Consistent behavior across all workers

### Monitoring

- Centralized monitoring data in database
- Easy to query and analyze across all workers
- Built-in data retention and cleanup

## Performance Considerations

### Database Optimization

- All tables have appropriate indexes
- Composite indexes for common query patterns
- JSONB columns for flexible metadata storage

### Query Efficiency

- Minimal database queries per operation
- Efficient upsert operations for updates
- Bulk operations for cleanup tasks

### Memory Usage

- No memory growth from accumulated state
- Fixed memory footprint per worker
- Automatic cleanup of old data

## Data Retention

### Automatic Cleanup

The stateless design includes automatic data cleanup:

```python
async def cleanup_old_data(self, retention_hours: int = 24) -> Dict[str, int]:
    # Clean old security events
    # Remove expired blocks
    # Decay threat scores
    # Remove low scores

    return {
        "deleted_events": deleted_events,
        "expired_blocks": expired_blocks,
        "decayed_scores": decayed_scores,
        "cleaned_scores": cleaned_scores
    }
```

### Configurable Retention

- Retention policies configurable per data type
- Automatic score decay to prevent inflation
- Expired blocks automatically removed

## Migration Guide

### Database Setup

1. Run the migration script:

   ```bash
   alembic upgrade head
   ```

2. Verify tables were created:

   ```sql
   \dt *security* *blocked* *threat* *monitoring*
   ```

### Application Updates

1. Update imports (no changes needed)
2. Initialize with database connection
3. Test with existing code (API unchanged)

### Monitoring Updates

Update monitoring dashboards to query database tables:

```sql
-- Active threats
SELECT entity_type, COUNT(*)
FROM threat_scores
WHERE score > 50
GROUP BY entity_type;

-- Recent security events
SELECT event_type, severity, COUNT(*)
FROM security_events_monitor
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY event_type, severity;

-- Currently blocked entities
SELECT entity_type, COUNT(*)
FROM blocked_entities
WHERE is_active = true
GROUP BY entity_type;
```

## Testing

### Unit Tests

Comprehensive test coverage for stateless behavior:

- Database integration tests
- Performance tests (no memory leaks)
- API compatibility tests
- Multi-worker simulation tests

### Integration Tests

- Full database workflow tests
- Concurrent access tests
- Data consistency tests
- Migration tests

## Deployment Notes

### Environment Variables

No new environment variables required. Uses existing database connection.

### Monitoring

- Monitor database performance and connection pool usage
- Set up alerts for threat score thresholds
- Monitor cleanup job execution

### Backup

- Include new tables in database backups
- Consider separate retention policies for security data
- Test recovery procedures with monitoring data

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database connectivity
   - Verify connection pool settings
   - Review database permissions

2. **Performance Issues**
   - Check index usage with EXPLAIN
   - Monitor query performance
   - Consider partition strategies for large datasets

3. **Data Consistency**
   - Verify transaction boundaries
   - Check for race conditions
   - Monitor concurrent access patterns

### Debugging

Enable debug logging for database queries:

```python
# In settings
DB_ECHO = True  # Development only
```

Monitor database performance:

```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE query LIKE '%security_events_monitor%'
ORDER BY mean_time DESC;
```
