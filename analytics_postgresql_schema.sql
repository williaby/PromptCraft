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
