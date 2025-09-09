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
