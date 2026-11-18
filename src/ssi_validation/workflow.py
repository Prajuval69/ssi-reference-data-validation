"""Maker-checker workflow and exception-assignment controls."""

from __future__ import annotations

import sqlite3
from datetime import timedelta

from .audit import record_audit_event
from .config import SystemConfig
from .errors import WorkflowError


class WorkflowManager:
    def __init__(self, connection: sqlite3.Connection, config: SystemConfig):
        self.connection = connection
        self.config = config

    def validate_transition(self, old_status: str, new_status: str) -> None:
        if old_status not in self.config.workflow_transitions:
            raise WorkflowError(f"Unknown current status: {old_status}")
        if new_status not in self.config.workflow_transitions[old_status]:
            raise WorkflowError(f"Invalid transition: {old_status} -> {new_status}")

    @staticmethod
    def validate_maker_checker(maker: str | None, actor: str) -> None:
        if not maker:
            raise WorkflowError("Cannot approve or reject an item without a maker")
        if maker.strip().casefold() == actor.strip().casefold():
            raise WorkflowError("Maker cannot approve or reject their own change")

    def assign_exception(self, exception_id: str, assignee: str, actor: str, reason: str) -> None:
        if not assignee.strip():
            raise WorkflowError("Assignee cannot be blank")
        row = self.connection.execute("SELECT assigned_to FROM exceptions WHERE exception_id = ?", (exception_id,)).fetchone()
        if row is None:
            raise WorkflowError(f"Unknown exception: {exception_id}")
        with self.connection:
            self.connection.execute("UPDATE exceptions SET assigned_to = ? WHERE exception_id = ?", (assignee, exception_id))
            record_audit_event(
                self.connection,
                entity_type="EXCEPTION",
                entity_id=exception_id,
                action="ASSIGNED",
                old_state={"assigned_to": row["assigned_to"]},
                new_state={"assigned_to": assignee},
                performed_by=actor,
                performed_at=self.config.business_datetime,
                reason=reason,
            )

    def transition_exception(
        self,
        exception_id: str,
        new_status: str,
        actor: str,
        reason: str,
        resolution_notes: str | None = None,
        event_offset_hours: int = 0,
    ) -> None:
        row = self.connection.execute(
            """SELECT e.status, e.resolution_notes, s.maker
               FROM exceptions e JOIN ssi_records s ON s.record_id = e.record_id
               WHERE e.exception_id = ?""",
            (exception_id,),
        ).fetchone()
        if row is None:
            raise WorkflowError(f"Unknown exception: {exception_id}")
        self.validate_transition(row["status"], new_status)
        if new_status in self.config.terminal_statuses:
            self.validate_maker_checker(row["maker"], actor)
        performed_at = self.config.business_datetime + timedelta(hours=event_offset_hours)
        resolved_at = performed_at.isoformat() if new_status in self.config.terminal_statuses else None
        notes = resolution_notes if resolution_notes is not None else row["resolution_notes"]
        action = "APPROVED" if new_status == "RESOLVED" else "REJECTED" if new_status == "REJECTED" else "STATUS_TRANSITION"
        with self.connection:
            self.connection.execute(
                "UPDATE exceptions SET status = ?, resolution_notes = ?, resolved_at = ? WHERE exception_id = ?",
                (new_status, notes, resolved_at, exception_id),
            )
            record_audit_event(
                self.connection,
                entity_type="EXCEPTION",
                entity_id=exception_id,
                action=action,
                old_state={"status": row["status"], "resolution_notes": row["resolution_notes"]},
                new_state={"status": new_status, "resolution_notes": notes, "resolved_at": resolved_at},
                performed_by=actor,
                performed_at=performed_at,
                reason=reason,
            )

    def transition_ssi(self, record_id: int, new_status: str, actor: str, reason: str) -> None:
        row = self.connection.execute("SELECT status, maker, checker FROM ssi_records WHERE record_id = ?", (record_id,)).fetchone()
        if row is None:
            raise WorkflowError(f"Unknown SSI record: {record_id}")
        self.validate_transition(row["status"], new_status)
        if new_status in self.config.terminal_statuses:
            self.validate_maker_checker(row["maker"], actor)
        checker = actor if new_status == "UNDER_REVIEW" else row["checker"]
        with self.connection:
            self.connection.execute(
                "UPDATE ssi_records SET status = ?, checker = ?, updated_at = ? WHERE record_id = ?",
                (new_status, checker, self.config.business_datetime.isoformat(), record_id),
            )
            record_audit_event(
                self.connection,
                entity_type="SSI",
                entity_id=str(record_id),
                action="STATUS_TRANSITION",
                old_state={"status": row["status"], "checker": row["checker"]},
                new_state={"status": new_status, "checker": checker},
                performed_by=actor,
                performed_at=self.config.business_datetime,
                reason=reason,
            )
