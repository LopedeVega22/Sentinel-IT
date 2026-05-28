import sqlite3
from datetime import datetime, timedelta


STATUS_PENDING = "PENDING_AI_RETRY"
STATUS_PROCESSED = "PROCESSED"


def is_resource_exhausted_error(exc: Exception) -> bool:
    """Detecta errores de cuota/gasto de Gemini sin acoplarse a clases SDK."""
    text = f"{type(exc).__name__}: {exc}"
    return "429" in text and "RESOURCE_EXHAUSTED" in text


def init_pending_ai_events_schema(db_path: str) -> None:
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_ai_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device TEXT NOT NULL,
                queue_type TEXT NOT NULL,
                raw_log TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING_AI_RETRY',
                error_reason TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                next_retry_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_pending_ai_event(
    db_path: str,
    device: str,
    queue_type: str,
    raw_log: str,
    error_reason: str,
    now: datetime | None = None,
) -> int:
    init_pending_ai_events_schema(db_path)
    now = now or datetime.now()
    next_retry_at = now + timedelta(seconds=_backoff_seconds(0))
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    try:
        cursor = conn.execute(
            """
            INSERT INTO pending_ai_events (
                device, queue_type, raw_log, status, error_reason,
                retry_count, next_retry_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                device,
                queue_type,
                raw_log,
                STATUS_PENDING,
                error_reason,
                next_retry_at.isoformat(timespec="seconds"),
                now.isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def _backoff_seconds(retry_count: int) -> int:
    if retry_count <= 0:
        return 60
    if retry_count == 1:
        return 300
    if retry_count == 2:
        return 900
    return 3600


def mark_pending_ai_event_retry(
    db_path: str,
    event_id: int,
    error_reason: str,
    now: datetime | None = None,
) -> None:
    init_pending_ai_events_schema(db_path)
    now = now or datetime.now()
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    try:
        row = conn.execute(
            "SELECT retry_count FROM pending_ai_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        retry_count = int(row[0]) if row else 0
        next_count = retry_count + 1
        next_retry_at = now + timedelta(seconds=_backoff_seconds(retry_count))
        conn.execute(
            """
            UPDATE pending_ai_events
            SET retry_count = ?,
                next_retry_at = ?,
                status = ?,
                error_reason = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                next_count,
                next_retry_at.isoformat(timespec="seconds"),
                STATUS_PENDING,
                error_reason,
                now.isoformat(timespec="seconds"),
                event_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def fetch_due_pending_ai_events(
    db_path: str,
    now: datetime | None = None,
    limit: int = 10,
) -> list[dict]:
    init_pending_ai_events_schema(db_path)
    now = now or datetime.now()
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, device, queue_type, raw_log, retry_count, error_reason
            FROM pending_ai_events
            WHERE status = ?
              AND (next_retry_at IS NULL OR next_retry_at <= ?)
            ORDER BY created_at ASC, id ASC
            LIMIT ?
            """,
            (STATUS_PENDING, now.isoformat(timespec="seconds"), limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def mark_pending_ai_event_processed(db_path: str, event_id: int) -> None:
    init_pending_ai_events_schema(db_path)
    now = datetime.now().isoformat(timespec="seconds")
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    try:
        conn.execute(
            """
            UPDATE pending_ai_events
            SET status = ?, updated_at = ?
            WHERE id = ?
            """,
            (STATUS_PROCESSED, now, event_id),
        )
        conn.commit()
    finally:
        conn.close()


def purge_pending_ai_events(db_path: str) -> int:
    init_pending_ai_events_schema(db_path)
    conn = sqlite3.connect(db_path, timeout=15.0, check_same_thread=False)
    try:
        deleted = conn.execute("DELETE FROM pending_ai_events").rowcount
        conn.commit()
        return int(deleted)
    finally:
        conn.close()
