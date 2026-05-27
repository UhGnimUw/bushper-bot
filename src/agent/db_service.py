"""Backend database service for metrics and conversations storage."""
import sqlite3
import time
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Optional


DB_PATH = Path(__file__).parent.parent.parent / "metrics.db"


def get_db_path():
    """Get the metrics database path."""
    return DB_PATH


@contextmanager
def get_conn():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the metrics database."""
    if DB_PATH.exists():
        return

    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS metrics_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cpu_percent REAL,
            memory_percent REAL,
            request_count INTEGER DEFAULT 0,
            response_time_ms REAL
        );

        CREATE TABLE IF NOT EXISTS feishu_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            chat_id TEXT,
            user_name TEXT,
            message TEXT NOT NULL,
            response TEXT,
            intent TEXT,
            timestamp TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_feishu_session ON feishu_conversations(session_id);
        CREATE INDEX IF NOT EXISTS idx_feishu_timestamp ON feishu_conversations(timestamp);
    """)
    conn.commit()
    conn.close()
    print(f"Metrics database initialized: {DB_PATH}")


def log_metrics(cpu_percent: float = None, memory_percent: float = None,
                request_count: int = 0, response_time_ms: float = None):
    """Log a metrics entry."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO metrics_log (timestamp, cpu_percent, memory_percent, request_count, response_time_ms)
               VALUES (?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), cpu_percent, memory_percent, request_count, response_time_ms)
        )
        conn.commit()


def get_recent_metrics(hours: int = 24, limit: int = 100) -> list:
    """Get recent metrics entries."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT * FROM metrics_log
               WHERE timestamp >= datetime('now', ?)
               ORDER BY timestamp DESC
               LIMIT ?""",
            (f"-{hours} hours", limit)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_metrics_summary(hours: int = 24) -> dict:
    """Get metrics summary for the last N hours."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT
                   COUNT(*) as total_requests,
                   AVG(response_time_ms) as avg_response_time,
                   MAX(response_time_ms) as max_response_time,
                   MIN(response_time_ms) as min_response_time,
                   AVG(cpu_percent) as avg_cpu,
                   AVG(memory_percent) as avg_memory
               FROM metrics_log
               WHERE timestamp >= datetime('now', ?)""",
            (f"-{hours} hours",)
        )
        row = cursor.fetchone()
        return dict(row) if row else {}


def save_feishu_conversation(session_id: str, message: str, response: str = None,
                            user_name: str = None, chat_id: str = None, intent: str = None):
    """Save a Feishu conversation."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO feishu_conversations
               (session_id, chat_id, user_name, message, response, intent, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, chat_id, user_name, message, response, intent, datetime.now().isoformat())
        )
        conn.commit()


def get_feishu_conversations(session_id: str = None, limit: int = 50) -> list:
    """Get Feishu conversations."""
    with get_conn() as conn:
        if session_id:
            cursor = conn.execute(
                """SELECT * FROM feishu_conversations
                   WHERE session_id = ?
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (session_id, limit)
            )
        else:
            cursor = conn.execute(
                """SELECT * FROM feishu_conversations
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]


def get_feishu_sessions(limit: int = 20) -> list:
    """Get distinct Feishu sessions."""
    with get_conn() as conn:
        cursor = conn.execute(
            """SELECT session_id, user_name, chat_id, COUNT(*) as message_count,
                      MIN(timestamp) as first_message, MAX(timestamp) as last_message
               FROM feishu_conversations
               GROUP BY session_id
               ORDER BY last_message DESC
               LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully")
    print(f"DB path: {DB_PATH}")