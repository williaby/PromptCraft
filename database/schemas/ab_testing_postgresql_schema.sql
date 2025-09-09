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
