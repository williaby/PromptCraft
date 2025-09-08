"""
Metrics storage backend for production monitoring.

This module provides persistent storage for metric events using SQLite
for development and PostgreSQL for production. It handles database schema
creation, event storage, and query operations for analytics.
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

from .events import MetricEvent, MetricEventType


class MetricsStorage:
    """Storage backend for metric events with SQLite support."""

    def __init__(self, database_path: str = "metrics.db") -> None:
        """Initialize metrics storage with database connection."""
        self.database_path = database_path
        self.logger = logging.getLogger(__name__)

        # Ensure database directory exists
        db_path = Path(database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS metric_events (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            user_id TEXT,

            -- HyDE Specific Metrics
            hyde_score INTEGER,
            action_taken TEXT,
            conceptual_issues TEXT,
            query_specificity_level TEXT,

            -- User Feedback Metrics
            feedback_type TEXT,
            feedback_target TEXT,
            feedback_score INTEGER,

            -- Performance Metrics
            response_time_ms INTEGER,
            error_details TEXT,
            error_type TEXT,
            latency_category TEXT,

            -- Query Analysis (Privacy-Safe)
            query_text_hash TEXT,
            query_length INTEGER,
            query_category TEXT,
            query_language TEXT,

            -- Vector Store Performance
            vector_search_results INTEGER,
            vector_search_score_threshold REAL,
            vector_store_type TEXT,

            -- Domain-Specific Metrics
            domain_detected TEXT,
            mismatch_type TEXT,
            suggested_alternative TEXT,

            -- Business Intelligence
            differentiation_value TEXT,
            competitive_comparison TEXT,
            user_retention_indicator BOOLEAN,

            -- System Context
            system_version TEXT,
            feature_flags TEXT,
            environment TEXT,

            -- Additional Data
            additional_data TEXT
        );

        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_event_type ON metric_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_timestamp ON metric_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_session_id ON metric_events(session_id);
        CREATE INDEX IF NOT EXISTS idx_hyde_score ON metric_events(hyde_score);
        CREATE INDEX IF NOT EXISTS idx_feedback_type ON metric_events(feedback_type);
        CREATE INDEX IF NOT EXISTS idx_latency_category ON metric_events(latency_category);
        CREATE INDEX IF NOT EXISTS idx_domain_detected ON metric_events(domain_detected);
        """

        with sqlite3.connect(self.database_path) as conn:
            conn.executescript(schema_sql)
            conn.commit()

        self.logger.info("Metrics database schema initialized: %s", self.database_path)

    async def store_event(self, event: MetricEvent) -> bool:
        """Store a metric event in the database."""
        try:
            storage_dict = event.to_storage_dict()

            # Prepare INSERT statement
            columns = list(storage_dict.keys())
            placeholders = ", ".join(["?" for _ in columns])
            values = [storage_dict[col] for col in columns]

            insert_sql = f"""  # noqa: S608
            INSERT OR REPLACE INTO metric_events
            ({', '.join(columns)})
            VALUES ({placeholders})
            """

            with sqlite3.connect(self.database_path) as conn:
                conn.execute(insert_sql, values)
                conn.commit()

            self.logger.debug("Stored metric event: %s (%s)", event.event_id, event.event_type)
            return True

        except Exception as e:
            self.logger.error("Failed to store metric event %s: %s", event.event_id, str(e))
            return False

    async def store_events_batch(self, events: list[MetricEvent]) -> int:
        """Store multiple events in a single transaction."""
        if not events:
            return 0

        try:
            storage_dicts = [event.to_storage_dict() for event in events]

            # Use the first event to determine columns
            columns = list(storage_dicts[0].keys())
            placeholders = ", ".join(["?" for _ in columns])

            insert_sql = f"""  # noqa: S608
            INSERT OR REPLACE INTO metric_events
            ({', '.join(columns)})
            VALUES ({placeholders})
            """

            # Prepare values for batch insert
            batch_values = []
            for storage_dict in storage_dicts:
                values = [storage_dict.get(col) for col in columns]
                batch_values.append(values)

            with sqlite3.connect(self.database_path) as conn:
                conn.executemany(insert_sql, batch_values)
                conn.commit()

            self.logger.info("Stored %d metric events in batch", len(events))
            return len(events)

        except Exception as e:
            self.logger.error("Failed to store batch of %d events: %s", len(events), str(e))
            return 0

    async def get_events(
        self,
        event_types: list[MetricEventType] | None = None,
        session_id: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        limit: int = 1000,
    ) -> list[MetricEvent]:
        """Retrieve events with optional filtering."""
        try:
            query = "SELECT * FROM metric_events WHERE 1=1"
            params = []

            if event_types:
                type_placeholders = ", ".join(["?" for _ in event_types])
                query += f" AND event_type IN ({type_placeholders})"
                params.extend([et.value for et in event_types])

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)

            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(str(limit))

            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row  # Enable column access by name
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

            # Convert rows back to MetricEvent objects
            events = []
            for row in rows:
                row_dict = dict(row)
                # Remove None values to avoid Pydantic validation issues
                row_dict = {k: v for k, v in row_dict.items() if v is not None}
                events.append(MetricEvent.from_storage_dict(row_dict))

            self.logger.debug("Retrieved %d metric events", len(events))
            return events

        except Exception as e:
            self.logger.error("Failed to retrieve events: %s", str(e))
            return []

    async def get_metrics_summary(self, hours: int = 24) -> dict[str, Any]:
        """Get summary metrics for the specified time period."""
        try:
            # Calculate time window
            current_time = time.time()
            start_timestamp = current_time - (hours * 3600)
            start_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(start_timestamp))

            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row

                # Basic event counts
                event_counts = conn.execute(
                    """
                    SELECT event_type, COUNT(*) as count
                    FROM metric_events
                    WHERE timestamp >= ?
                    GROUP BY event_type
                """,
                    (start_time,),
                ).fetchall()

                # HyDE performance metrics
                hyde_metrics = conn.execute(
                    """
                    SELECT
                        COUNT(*) as total_queries,
                        AVG(hyde_score) as avg_hyde_score,
                        AVG(response_time_ms) as avg_response_time,
                        SUM(CASE WHEN conceptual_issues IS NOT NULL AND conceptual_issues != '' THEN 1 ELSE 0 END) as conceptual_detections
                    FROM metric_events
                    WHERE event_type = 'query_processed' AND timestamp >= ?
                """,
                    (start_time,),
                ).fetchone()

                # User feedback metrics
                feedback_metrics = conn.execute(
                    """
                    SELECT
                        feedback_type,
                        COUNT(*) as count
                    FROM metric_events
                    WHERE event_type = 'user_feedback' AND timestamp >= ?
                    GROUP BY feedback_type
                """,
                    (start_time,),
                ).fetchall()

                # Performance distribution
                latency_distribution = conn.execute(
                    """
                    SELECT
                        latency_category,
                        COUNT(*) as count
                    FROM metric_events
                    WHERE latency_category IS NOT NULL AND timestamp >= ?
                    GROUP BY latency_category
                """,
                    (start_time,),
                ).fetchall()

                # Error summary
                error_summary = conn.execute(
                    """
                    SELECT COUNT(*) as error_count
                    FROM metric_events
                    WHERE event_type = 'error_occurred' AND timestamp >= ?
                """,
                    (start_time,),
                ).fetchone()

            # Format results
            summary = {
                "time_window_hours": hours,
                "event_counts": {row["event_type"]: row["count"] for row in event_counts},
                "hyde_performance": dict(hyde_metrics) if hyde_metrics else {},
                "user_feedback": {row["feedback_type"]: row["count"] for row in feedback_metrics},
                "latency_distribution": {row["latency_category"]: row["count"] for row in latency_distribution},
                "error_count": error_summary["error_count"] if error_summary else 0,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
            }

            # Calculate derived metrics
            if hyde_metrics and hyde_metrics["total_queries"]:
                summary["mismatch_detection_rate"] = (
                    hyde_metrics["conceptual_detections"] / hyde_metrics["total_queries"]
                ) * 100

            # Calculate user agreement rate
            feedback_counts = summary["user_feedback"]
            if isinstance(feedback_counts, dict):
                total_feedback = sum(feedback_counts.values())
                if total_feedback > 0:
                    positive_feedback = feedback_counts.get("thumbs_up", 0)
                summary["user_agreement_rate"] = (positive_feedback / total_feedback) * 100

            return summary

        except Exception as e:
            self.logger.error("Failed to generate metrics summary: %s", str(e))
            return {"error": str(e)}

    async def cleanup_old_events(self, days_to_keep: int = 30) -> int:
        """Remove old events to manage storage size."""
        try:
            # Calculate cutoff time
            cutoff_timestamp = time.time() - (days_to_keep * 24 * 3600)
            cutoff_time = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(cutoff_timestamp))

            with sqlite3.connect(self.database_path) as conn:
                cursor = conn.execute("DELETE FROM metric_events WHERE timestamp < ?", (cutoff_time,))
                deleted_count = cursor.rowcount
                conn.commit()

            self.logger.info("Cleaned up %d old metric events (older than %d days)", deleted_count, days_to_keep)
            return deleted_count

        except Exception as e:
            self.logger.error("Failed to cleanup old events: %s", str(e))
            return 0

    async def get_database_stats(self) -> dict[str, Any]:
        """Get database statistics and health information."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Total event count
                total_events = conn.execute("SELECT COUNT(*) FROM metric_events").fetchone()[0]

                # Database size
                db_size = Path(self.database_path).stat().st_size

                # Oldest and newest events
                oldest_event = conn.execute(
                    "SELECT timestamp FROM metric_events ORDER BY timestamp ASC LIMIT 1",
                ).fetchone()
                newest_event = conn.execute(
                    "SELECT timestamp FROM metric_events ORDER BY timestamp DESC LIMIT 1",
                ).fetchone()

                return {
                    "database_path": str(self.database_path),
                    "total_events": total_events,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / (1024 * 1024), 2),
                    "oldest_event": oldest_event[0] if oldest_event else None,
                    "newest_event": newest_event[0] if newest_event else None,
                }

        except Exception as e:
            self.logger.error("Failed to get database stats: %s", str(e))
            return {"error": str(e)}
