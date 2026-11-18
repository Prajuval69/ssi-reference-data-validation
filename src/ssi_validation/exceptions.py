"""Exception creation, aging and operational queue queries."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .config import SystemConfig


SEVERITY_RANK = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}


def aging_bucket(days: float) -> str:
    if days <= 1:
        return "0-1 day"
    if days <= 3:
        return "2-3 days"
    if days <= 7:
        return "4-7 days"
    if days <= 30:
        return "8-30 days"
    return "30+ days"


def create_exceptions(validation_results: pd.DataFrame, records: pd.DataFrame, config: SystemConfig) -> pd.DataFrame:
    failures = validation_results[validation_results["result"] == "FAIL"].copy().reset_index(drop=True)
    client_columns = records[["record_id", "client_id", "client_name", "market", "currency", "maker"]]
    failures = failures.merge(client_columns, on="record_id", how="left", suffixes=("", "_record"))
    detected_at = pd.Timestamp(config.business_datetime)
    rows: list[dict[str, Any]] = []
    for i, row in failures.iterrows():
        rows.append(
            {
                "exception_id": f"EXC-{i + 1:07d}",
                "record_id": int(row["record_id"]),
                "ssi_id": row["ssi_id"],
                "rule_id": row["rule_id"],
                "severity": row["severity"],
                "exception_type": row["rule_name"],
                "description": row["exception_reason"],
                "detected_at": detected_at.isoformat(),
                "status": "NEW",
                "assigned_to": None,
                "resolution_notes": None,
                "resolved_at": None,
                "client_id": row["client_id"],
                "client_name": row["client_name"],
                "market": row["market"],
                "currency": row["currency"],
                "maker": row["maker"],
            }
        )
    return pd.DataFrame(rows)


@dataclass
class QueueFilters:
    severity: str | None = None
    status: str | None = None
    client: str | None = None
    market: str | None = None
    currency: str | None = None
    rule: str | None = None
    minimum_age_days: int | None = None
    assignee: str | None = None


class ExceptionQueue:
    def __init__(self, connection: sqlite3.Connection, config: SystemConfig):
        self.connection = connection
        self.config = config

    def query(self, filters: QueueFilters | None = None) -> pd.DataFrame:
        filters = filters or QueueFilters()
        sql = """
            SELECT e.exception_id, e.record_id, e.ssi_id, e.rule_id, e.severity,
                   e.exception_type, e.description, e.detected_at, e.status,
                   e.assigned_to, e.resolution_notes, e.resolved_at,
                   s.client_id, s.client_name, s.market, s.currency
            FROM exceptions e
            JOIN ssi_records s ON s.record_id = e.record_id
            WHERE 1=1
        """
        parameters: list[Any] = []
        mappings = {
            "severity": filters.severity,
            "status": filters.status,
            "market": filters.market,
            "currency": filters.currency,
            "rule_id": filters.rule,
            "assigned_to": filters.assignee,
        }
        for column, value in mappings.items():
            if value is not None:
                sql += f" AND e.{column} = ?" if column not in {"market", "currency"} else f" AND s.{column} = ?"
                parameters.append(value)
        if filters.client is not None:
            sql += " AND (s.client_id = ? OR s.client_name = ?)"
            parameters.extend([filters.client, filters.client])
        frame = pd.read_sql_query(sql, self.connection, params=parameters)
        if frame.empty:
            return frame.assign(age_days=pd.Series(dtype=float), aging_bucket=pd.Series(dtype=str))
        detected = pd.to_datetime(frame["detected_at"], utc=True)
        age_days = (pd.Timestamp(self.config.business_datetime) - detected).dt.total_seconds() / 86400
        frame["age_days"] = age_days.clip(lower=0)
        frame["aging_bucket"] = frame["age_days"].map(aging_bucket)
        if filters.minimum_age_days is not None:
            frame = frame[frame["age_days"] >= filters.minimum_age_days]
        frame["_severity_rank"] = frame["severity"].map(SEVERITY_RANK).fillna(99)
        frame["_terminal"] = frame["status"].isin(self.config.terminal_statuses).astype(int)
        return frame.sort_values(["_severity_rank", "_terminal", "detected_at", "exception_id"]).drop(columns=["_severity_rank", "_terminal"]).reset_index(drop=True)

