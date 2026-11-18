from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from ssi_validation.database import connect, initialize_database, persist_dataframe, persist_reference_data
from ssi_validation.errors import WorkflowError
from ssi_validation.exceptions import ExceptionQueue, QueueFilters
from ssi_validation.references import build_reference_data
from ssi_validation.workflow import WorkflowManager


def seed_database(tmp_path, config, valid_record):
    connection = connect(tmp_path / "test.db")
    initialize_database(connection)
    persist_reference_data(connection, build_reference_data(config))
    persist_dataframe(connection, pd.DataFrame([valid_record]), "ssi_records")
    exception = pd.DataFrame(
        [
            {
                "exception_id": "EXC-TEST-1",
                "record_id": 1,
                "ssi_id": valid_record["ssi_id"],
                "rule_id": "SSI-005",
                "severity": "High",
                "exception_type": "Account format",
                "description": "Synthetic test exception",
                "detected_at": config.business_datetime.isoformat(),
                "status": "NEW",
                "assigned_to": None,
                "resolution_notes": None,
                "resolved_at": None,
            }
        ]
    )
    persist_dataframe(connection, exception, "exceptions")
    return connection


def test_valid_exception_workflow_and_audit(tmp_path, config, valid_record):
    connection = seed_database(tmp_path, config, valid_record)
    workflow = WorkflowManager(connection, config)
    workflow.assign_exception("EXC-TEST-1", "analyst", "router", "test assignment")
    workflow.transition_exception("EXC-TEST-1", "UNDER_REVIEW", "checker_test", "review")
    workflow.transition_exception("EXC-TEST-1", "RESOLVED", "checker_test", "approved", "fixed")
    row = connection.execute("SELECT status, resolved_at FROM exceptions").fetchone()
    assert row["status"] == "RESOLVED"
    assert row["resolved_at"] is not None
    actions = [row[0] for row in connection.execute("SELECT action FROM audit_log ORDER BY audit_id")]
    assert actions == ["ASSIGNED", "STATUS_TRANSITION", "APPROVED"]
    connection.close()


def test_invalid_transition_rejected(tmp_path, config, valid_record):
    connection = seed_database(tmp_path, config, valid_record)
    with pytest.raises(WorkflowError, match="Invalid transition"):
        WorkflowManager(connection, config).transition_exception("EXC-TEST-1", "RESOLVED", "checker_test", "skip review")
    connection.close()


def test_maker_cannot_self_approve(tmp_path, config, valid_record):
    connection = seed_database(tmp_path, config, valid_record)
    workflow = WorkflowManager(connection, config)
    workflow.transition_exception("EXC-TEST-1", "UNDER_REVIEW", "checker_test", "review")
    with pytest.raises(WorkflowError, match="Maker cannot"):
        workflow.transition_exception("EXC-TEST-1", "RESOLVED", valid_record["maker"], "self approval")
    connection.close()


def test_exception_queue_filtering(tmp_path, config, valid_record):
    connection = seed_database(tmp_path, config, valid_record)
    queue = ExceptionQueue(connection, config)
    assert len(queue.query(QueueFilters(severity="High", currency="SUSD", client="CL-TEST-001"))) == 1
    assert queue.query(QueueFilters(severity="Critical")).empty
    connection.close()


def test_database_foreign_keys_are_enabled(tmp_path):
    connection = connect(tmp_path / "fk.db")
    initialize_database(connection)
    assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    connection.close()

