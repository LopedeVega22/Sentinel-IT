import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from tools.pending_ai_events import (
    init_pending_ai_events_schema,
    is_resource_exhausted_error,
    mark_pending_ai_event_retry,
    purge_pending_ai_events,
    save_pending_ai_event,
)


class TestPendingAIEvents(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        tmp.close()
        self.db_path = tmp.name
        init_pending_ai_events_schema(self.db_path)

    def tearDown(self):
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_resource_exhausted_error_is_detected_from_google_429_message(self):
        exc = RuntimeError("429 RESOURCE_EXHAUSTED. Your project has exceeded its monthly spending cap.")

        self.assertTrue(is_resource_exhausted_error(exc))

    def test_save_pending_ai_event_marks_event_for_retry(self):
        now = datetime(2026, 5, 28, 12, 0, 0)
        event_id = save_pending_ai_event(
            self.db_path,
            device="Pi4-Felix",
            queue_type="triage",
            raw_log='{"evento":"SQLI_DETECTED"}',
            error_reason="429 RESOURCE_EXHAUSTED",
            now=now,
        )

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT id, device, queue_type, raw_log, status, retry_count, error_reason, next_retry_at "
            "FROM pending_ai_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        conn.close()

        self.assertEqual(row[1], "Pi4-Felix")
        self.assertEqual(row[2], "triage")
        self.assertEqual(row[3], '{"evento":"SQLI_DETECTED"}')
        self.assertEqual(row[4], "PENDING_AI_RETRY")
        self.assertEqual(row[5], 0)
        self.assertIn("429", row[6])
        self.assertGreaterEqual(datetime.fromisoformat(row[7]), now + timedelta(seconds=60))

    def test_retry_backoff_increments_count_and_sets_future_retry_time(self):
        event_id = save_pending_ai_event(
            self.db_path,
            device="Pi4-Felix",
            queue_type="triage",
            raw_log="log",
            error_reason="429 RESOURCE_EXHAUSTED",
        )
        now = datetime(2026, 5, 28, 12, 0, 0)

        mark_pending_ai_event_retry(
            self.db_path,
            event_id=event_id,
            error_reason="429 RESOURCE_EXHAUSTED again",
            now=now,
        )

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT retry_count, next_retry_at, status FROM pending_ai_events WHERE id = ?",
            (event_id,),
        ).fetchone()
        conn.close()

        self.assertEqual(row[0], 1)
        self.assertEqual(row[2], "PENDING_AI_RETRY")
        self.assertGreaterEqual(datetime.fromisoformat(row[1]), now + timedelta(seconds=60))

    def test_purge_pending_ai_events_deletes_retry_records(self):
        save_pending_ai_event(
            self.db_path,
            device="Pi4-Felix",
            queue_type="triage",
            raw_log="log",
            error_reason="429 RESOURCE_EXHAUSTED",
        )

        deleted = purge_pending_ai_events(self.db_path)

        conn = sqlite3.connect(self.db_path)
        remaining = conn.execute("SELECT COUNT(*) FROM pending_ai_events").fetchone()[0]
        conn.close()

        self.assertEqual(deleted, 1)
        self.assertEqual(remaining, 0)


if __name__ == '__main__':
    unittest.main()
