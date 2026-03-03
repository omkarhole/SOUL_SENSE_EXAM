-- Migration: Add Auth Anomaly Event table for #1263
-- Description: Creates auth_anomaly_events table to track authentication anomalies

CREATE TABLE IF NOT EXISTS auth_anomaly_events (
    id INTEGER NOT NULL,
    user_id INTEGER,
    anomaly_type VARCHAR NOT NULL,
    risk_level VARCHAR NOT NULL,
    risk_score FLOAT NOT NULL,
    ip_address VARCHAR NOT NULL,
    user_agent VARCHAR,
    triggered_rules TEXT,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Add user_id to login_attempts table if it doesn't exist
PRAGMA table_info(login_attempts);
-- This will be checked at runtime, but for migration we assume it needs to be added
ALTER TABLE login_attempts ADD COLUMN user_id INTEGER REFERENCES users(id);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_auth_anomaly_events_user_id ON auth_anomaly_events (user_id);
CREATE INDEX IF NOT EXISTS ix_auth_anomaly_events_anomaly_type ON auth_anomaly_events (anomaly_type);
CREATE INDEX IF NOT EXISTS ix_auth_anomaly_events_created_at ON auth_anomaly_events (created_at);
CREATE INDEX IF NOT EXISTS ix_auth_anomaly_events_risk_level ON auth_anomaly_events (risk_level);

-- Insert migration record
INSERT OR IGNORE INTO alembic_version (version_num) VALUES ('auth_anomaly_1263');