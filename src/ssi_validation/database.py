"""SQLite schema and persistence helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from .errors import PersistenceError


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS reference_currencies (
    currency TEXT PRIMARY KEY, currency_name TEXT NOT NULL, decimal_places INTEGER NOT NULL CHECK(decimal_places >= 0)
);
CREATE TABLE IF NOT EXISTS reference_countries (
    country TEXT PRIMARY KEY, country_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_markets (
    market TEXT PRIMARY KEY, market_name TEXT NOT NULL, country TEXT NOT NULL REFERENCES reference_countries(country)
);
CREATE TABLE IF NOT EXISTS reference_settlement_methods (
    settlement_method TEXT PRIMARY KEY, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_source_channels (
    source_channel TEXT PRIMARY KEY, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_statuses (
    status TEXT PRIMARY KEY, is_terminal INTEGER NOT NULL CHECK(is_terminal IN (0, 1))
);
CREATE TABLE IF NOT EXISTS reference_currency_country (
    country TEXT NOT NULL REFERENCES reference_countries(country),
    currency TEXT NOT NULL REFERENCES reference_currencies(currency),
    PRIMARY KEY(country, currency)
);
CREATE TABLE IF NOT EXISTS reference_workflow_transitions (
    from_status TEXT NOT NULL REFERENCES reference_statuses(status),
    to_status TEXT NOT NULL REFERENCES reference_statuses(status),
    PRIMARY KEY(from_status, to_status)
);

CREATE TABLE IF NOT EXISTS ssi_records (
    record_id INTEGER PRIMARY KEY,
    ssi_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    client_name TEXT,
    market TEXT NOT NULL,
    country TEXT NOT NULL,
    currency TEXT NOT NULL,
    account_number TEXT NOT NULL,
    custodian TEXT NOT NULL,
    beneficiary_name TEXT NOT NULL,
    settlement_method TEXT NOT NULL,
    source_channel TEXT NOT NULL,
    effective_date TEXT,
    expiry_date TEXT,
    status TEXT NOT NULL,
    maker TEXT,
    checker TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS validation_results (
    validation_id TEXT PRIMARY KEY,
    record_id INTEGER NOT NULL REFERENCES ssi_records(record_id),
    ssi_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('PASS', 'FAIL')),
    severity TEXT NOT NULL CHECK(severity IN ('Critical', 'High', 'Medium', 'Low')),
    exception_reason TEXT,
    validated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exceptions (
    exception_id TEXT PRIMARY KEY,
    record_id INTEGER NOT NULL REFERENCES ssi_records(record_id),
    ssi_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('Critical', 'High', 'Medium', 'Low')),
    exception_type TEXT NOT NULL,
    description TEXT NOT NULL,
    detected_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('NEW', 'UNDER_REVIEW', 'REMEDIATION_REQUIRED', 'RESOLVED', 'REJECTED')),
    assigned_to TEXT,
    resolution_notes TEXT,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    audit_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    old_state TEXT,
    new_state TEXT,
    performed_by TEXT NOT NULL,
    performed_at TEXT NOT NULL,
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_ssi_id ON ssi_records(ssi_id);
CREATE INDEX IF NOT EXISTS idx_ssi_status ON ssi_records(status);
CREATE INDEX IF NOT EXISTS idx_ssi_currency ON ssi_records(currency);
CREATE INDEX IF NOT EXISTS idx_ssi_market ON ssi_records(market);
CREATE INDEX IF NOT EXISTS idx_validation_ssi ON validation_results(ssi_id);
CREATE INDEX IF NOT EXISTS idx_validation_rule ON validation_results(rule_id);
CREATE INDEX IF NOT EXISTS idx_exception_ssi ON exceptions(ssi_id);
CREATE INDEX IF NOT EXISTS idx_exception_status ON exceptions(status);
CREATE INDEX IF NOT EXISTS idx_exception_severity ON exceptions(severity);
CREATE INDEX IF NOT EXISTS idx_exception_detected ON exceptions(detected_at);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
"""


REFERENCE_TABLE_MAP = {
    "currencies": "reference_currencies",
    "countries": "reference_countries",
    "markets": "reference_markets",
    "settlement_methods": "reference_settlement_methods",
    "source_channels": "reference_source_channels",
    "statuses": "reference_statuses",
    "currency_country": "reference_currency_country",
    "workflow_transitions": "reference_workflow_transitions",
}


def connect(path: Path | str) -> sqlite3.Connection:
    try:
        connection = sqlite3.connect(path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as exc:
        raise PersistenceError(f"Could not open SQLite database: {exc}") from exc


def initialize_database(connection: sqlite3.Connection) -> None:
    try:
        connection.executescript(SCHEMA_SQL)
        connection.commit()
    except sqlite3.Error as exc:
        connection.rollback()
        raise PersistenceError(f"Could not initialize database: {exc}") from exc


def clear_operational_data(connection: sqlite3.Connection) -> None:
    try:
        for table in ("audit_log", "exceptions", "validation_results", "ssi_records"):
            connection.execute(f"DELETE FROM {table}")
        for table in reversed(tuple(REFERENCE_TABLE_MAP.values())):
            connection.execute(f"DELETE FROM {table}")
        connection.commit()
    except sqlite3.Error as exc:
        connection.rollback()
        raise PersistenceError(f"Could not reset database tables: {exc}") from exc


def persist_dataframe(connection: sqlite3.Connection, frame: pd.DataFrame, table: str) -> None:
    try:
        frame.to_sql(table, connection, if_exists="append", index=False)
        connection.commit()
    except (sqlite3.Error, ValueError) as exc:
        connection.rollback()
        raise PersistenceError(f"Could not persist {table}: {exc}") from exc


def persist_reference_data(connection: sqlite3.Connection, references: dict[str, pd.DataFrame]) -> None:
    for name, table in REFERENCE_TABLE_MAP.items():
        persist_dataframe(connection, references[name], table)

