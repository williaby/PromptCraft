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
