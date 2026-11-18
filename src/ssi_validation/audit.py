"""Structured audit-event creation and persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any


def _json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, sort_keys=True, default=str)


def record_audit_event(
    connection: sqlite3.Connection,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    performed_by: str,
    performed_at: datetime,
    old_state: Any = None,
    new_state: Any = None,
    reason: str | None = None,
) -> str:
    next_number = connection.execute("SELECT COUNT(*) + 1 FROM audit_log").fetchone()[0]
    audit_id = f"AUD-{next_number:07d}"
    connection.execute(
        """INSERT INTO audit_log
           (audit_id, entity_type, entity_id, action, old_state, new_state, performed_by, performed_at, reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            audit_id,
            entity_type,
            entity_id,
            action,
            _json(old_state),
            _json(new_state),
            performed_by,
            performed_at.isoformat(),
            reason,
        ),
    )
    return audit_id
