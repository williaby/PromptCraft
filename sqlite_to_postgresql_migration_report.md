# SQLite to PostgreSQL Migration Analysis Report
Generated on 2025-08-24 06:50:00

## Executive Summary

- **Databases**: 4
- **Total Size**: 4.3 MB
- **Total Tables**: 9
- **Total Rows**: 12,900
- **Average Complexity**: 4.0/10

### Migration Priority
- **MEDIUM**: analytics, security_events
- **LOW**: ab_testing, metrics

## Detailed Database Analysis

### ab_testing Database

- **File Size**: 0.20 MB
- **Tables**: 3
- **Total Rows**: 92
- **Complexity**: 3/10
- **Priority**: LOW

#### Tables
- **ab_experiments**: 90 rows, 21 columns, complexity 1/10
  - Complex columns: config, start_time, end_time, created_at, updated_at
- **ab_metric_events**: 0 rows, 15 columns, complexity 3/10
- **ab_user_assignments**: 2 rows, 11 columns, complexity 2/10
  - Complex columns: assignment_time, last_interaction

#### Migration Strategy
- Validate JSON data in tables: ab_experiments, ab_user_assignments
- Consider JSONB type for better performance

### analytics Database

- **File Size**: 3.97 MB
- **Tables**: 2
- **Total Rows**: 12,808
- **Complexity**: 3/10
- **Priority**: MEDIUM

#### Tables
- **session_metrics**: 0 rows, 12 columns, complexity 1/10
- **usage_events**: 12,808 rows, 7 columns, complexity 3/10
  - Complex columns: event_data

#### Migration Strategy
- Validate JSON data in tables: usage_events
- Consider JSONB type for better performance

### metrics Database

- **File Size**: 0.04 MB
- **Tables**: 3
- **Total Rows**: 0
- **Complexity**: 4/10
- **Priority**: LOW

#### Tables
- **aggregated_metrics**: 0 rows, 10 columns, complexity 2/10
- **metric_points**: 0 rows, 7 columns, complexity 3/10
- **validation_results**: 0 rows, 11 columns, complexity 5/10

#### Migration Strategy
- Direct migration suitable - low complexity

### security_events Database

- **File Size**: 0.05 MB
- **Tables**: 1
- **Total Rows**: 0
- **Complexity**: 6/10
- **Priority**: MEDIUM

#### Tables
- **security_events**: 0 rows, 11 columns, complexity 6/10

#### Migration Strategy
- Direct migration suitable - low complexity

## PostgreSQL Schema Generation

### ab_testing Schema

```sql
-- PostgreSQL schema for ab_testing
-- Generated on 2025-08-24 06:50:00

-- Table: ab_experiments
CREATE TABLE ab_experiments (
    id VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    description VARCHAR,
    experiment_type VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    config JSONB NOT NULL,
    variants JSONB NOT NULL,
    success_criteria JSONB NOT NULL,
    failure_thresholds JSONB NOT NULL,
    target_percentage REAL NOT NULL,
    current_percentage REAL NOT NULL,
    segment_filters JSONB,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    planned_duration_hours INTEGER,
    total_users INTEGER,
    conversion_events INTEGER,
    statistical_significance REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by VARCHAR,
    PRIMARY KEY (id)
);

-- Table: ab_metric_events
CREATE TABLE ab_metric_events (
    id VARCHAR NOT NULL,
    experiment_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    variant VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    event_name VARCHAR NOT NULL,
    event_value REAL,
    event_data JSONB,
    session_id VARCHAR,
    request_id VARCHAR,
    timestamp TIMESTAMP,
    response_time_ms REAL,
    token_reduction_percentage REAL,
    success BOOLEAN,
    error_message VARCHAR,
    PRIMARY KEY (id)
);

-- Table: ab_user_assignments
CREATE TABLE ab_user_assignments (
    id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    experiment_id VARCHAR NOT NULL,
    variant VARCHAR NOT NULL,
    segment VARCHAR,
    user_characteristics JSONB,
    assignment_time TIMESTAMP,
    assignment_method VARCHAR,
    opt_out BOOLEAN,
    last_interaction TIMESTAMP,
    total_interactions INTEGER,
    PRIMARY KEY (id)
);

-- Indexes for ab_experiments
CREATE UNIQUE INDEX idx_ab_experiments_id ON ab_experiments (id);

-- Indexes for ab_metric_events
CREATE INDEX idx_ab_metric_events_user_id ON ab_metric_events (user_id);
CREATE INDEX idx_ab_metric_events_experiment_id ON ab_metric_events (experiment_id);
CREATE INDEX idx_ab_metric_events_timestamp ON ab_metric_events (timestamp);
CREATE UNIQUE INDEX idx_ab_metric_events_id ON ab_metric_events (id);

-- Indexes for ab_user_assignments
CREATE INDEX idx_ab_user_assignments_user_id ON ab_user_assignments (user_id);
CREATE INDEX idx_ab_user_assignments_experiment_id ON ab_user_assignments (experiment_id);
CREATE UNIQUE INDEX idx_ab_user_assignments_id ON ab_user_assignments (id);

```

### analytics Schema

```sql
-- PostgreSQL schema for analytics
-- Generated on 2025-08-24 06:50:00

-- Table: session_metrics
CREATE TABLE session_metrics (
    session_id TEXT,
    user_id TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    commands_executed INTEGER DEFAULT 0,
    functions_used TEXT,
    categories_loaded TEXT,
    performance_mode TEXT DEFAULT ''conservative'',
    total_tokens_used INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    help_requests INTEGER DEFAULT 0,
    optimization_applied BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (session_id)
);

-- Table: usage_events
CREATE TABLE usage_events (
    id SERIAL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT NOT NULL,
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    context TEXT,
    PRIMARY KEY (id)
);

-- Indexes for session_metrics
CREATE UNIQUE INDEX idx_session_metrics_session_id ON session_metrics (session_id);

-- Indexes for usage_events
CREATE INDEX idx_usage_events_user_id ON usage_events (user_id);
CREATE INDEX idx_usage_events_timestamp ON usage_events (timestamp);

```

### metrics Schema

```sql
-- PostgreSQL schema for metrics
-- Generated on 2025-08-24 06:50:00

-- Table: aggregated_metrics
CREATE TABLE aggregated_metrics (
    id SERIAL,
    metric_name TEXT NOT NULL,
    time_window TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    aggregation_type TEXT NOT NULL,
    value REAL NOT NULL,
    sample_count INTEGER NOT NULL,
    labels TEXT,
    created_at TEXT DEFAULT 'CURRENT_TIMESTAMP',
    PRIMARY KEY (id)
);

-- Table: metric_points
CREATE TABLE metric_points (
    id SERIAL,
    timestamp TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL,
    labels TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT 'CURRENT_TIMESTAMP',
    PRIMARY KEY (id)
);

-- Table: validation_results
CREATE TABLE validation_results (
    id SERIAL,
    claim TEXT NOT NULL,
    validated BOOLEAN NOT NULL,
    confidence_level REAL NOT NULL,
    p_value REAL,
    effect_size REAL,
    sample_size INTEGER,
    statistical_power REAL,
    evidence_strength TEXT,
    details TEXT,
    created_at TEXT DEFAULT 'CURRENT_TIMESTAMP',
    PRIMARY KEY (id)
);

-- Indexes for aggregated_metrics
CREATE INDEX idx_aggregated_metrics_window_start_window_end ON aggregated_metrics (window_start, window_end);

-- Indexes for metric_points
CREATE INDEX idx_metric_points_metric_name ON metric_points (metric_name);
CREATE INDEX idx_metric_points_timestamp ON metric_points (timestamp);

-- Indexes for validation_results
CREATE INDEX idx_validation_results_created_at ON validation_results (created_at);

```

### security_events Schema

```sql
-- PostgreSQL schema for security_events
-- Generated on 2025-08-24 06:50:00

-- Table: security_events
CREATE TABLE security_events (
    id TEXT,
    timestamp TIMESTAMP NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    user_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    session_id TEXT,
    details TEXT,
    risk_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- Indexes for security_events
CREATE INDEX idx_security_events_user_id_timestamp ON security_events (user_id, timestamp);
CREATE INDEX idx_security_events_event_type_severity ON security_events (event_type, severity);
CREATE INDEX idx_security_events_created_at ON security_events (created_at);
CREATE INDEX idx_security_events_risk_score ON security_events (risk_score);
CREATE INDEX idx_security_events_session_id ON security_events (session_id);
CREATE INDEX idx_security_events_ip_address ON security_events (ip_address);
CREATE INDEX idx_security_events_user_id ON security_events (user_id);
CREATE INDEX idx_security_events_severity ON security_events (severity);
CREATE INDEX idx_security_events_event_type ON security_events (event_type);
CREATE INDEX idx_security_events_timestamp ON security_events (timestamp);
CREATE UNIQUE INDEX idx_security_events_id ON security_events (id);

```

## Migration Complexity Assessment

### Type Conversion Issues
#### metrics
- aggregated_metrics.value: REAL type may have precision differences
- metric_points.value: REAL type may have precision differences
- validation_results.confidence_level: REAL type may have precision differences
- validation_results.p_value: REAL type may have precision differences
- validation_results.effect_size: REAL type may have precision differences
- validation_results.statistical_power: REAL type may have precision differences

## Recommendations

- **JSON Data**: Validate JSON format and consider JSONB for better performance
- **Testing**: Validate data integrity after migration using row counts and sample data verification
- **Backup**: Create full SQLite backups before starting migration
