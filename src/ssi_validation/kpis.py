"""Operational KPI calculations with documented, reproducible formulas."""

from __future__ import annotations

import pandas as pd

from .config import SystemConfig


def _safe_rate(numerator: int | float, denominator: int | float) -> float:
    return round((numerator / denominator * 100) if denominator else 0.0, 2)


def calculate_kpis(
    records: pd.DataFrame,
    validation_results: pd.DataFrame,
    exceptions: pd.DataFrame,
    config: SystemConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    total = int(records["record_id"].nunique())
    failed = validation_results[validation_results["result"] == "FAIL"]
    invalid_ids = set(failed["record_id"].astype(int))
    invalid = len(invalid_ids)
    valid = total - invalid
    duplicate_ids = set(failed.loc[failed["rule_id"].isin(["SSI-002", "SSI-003"]), "record_id"].astype(int))
    unresolved_mask = ~exceptions["status"].isin(config.terminal_statuses) if not exceptions.empty else pd.Series(dtype=bool)
    resolved_mask = exceptions["status"].eq("RESOLVED") if not exceptions.empty else pd.Series(dtype=bool)

    if exceptions.empty:
        average_age = average_remediation = 0.0
    else:
        detected = pd.to_datetime(exceptions["detected_at"], utc=True)
        age_days = (pd.Timestamp(config.business_datetime) - detected).dt.total_seconds() / 86400
        average_age = round(float(age_days[unresolved_mask].mean()), 2) if unresolved_mask.any() else 0.0
        resolved_at = pd.to_datetime(exceptions["resolved_at"], errors="coerce", utc=True)
        remediation_days = (resolved_at - detected).dt.total_seconds() / 86400
        average_remediation = round(float(remediation_days[resolved_mask].mean()), 2) if resolved_mask.any() else 0.0

    metrics = [
        ("total_ssi_records", total, "count", "Count of physical SSI records processed"),
        ("valid_ssi_records", valid, "count", "Records with no failed validation rules"),
        ("invalid_ssi_records", invalid, "count", "Records with at least one failed validation rule"),
        ("validation_pass_rate", _safe_rate(valid, total), "percent", "valid_ssi_records / total_ssi_records * 100"),
        ("exception_count", len(exceptions), "count", "Count of failed rule evaluations"),
        ("exception_rate", _safe_rate(len(exceptions), total), "percent", "exception_count / total_ssi_records * 100"),
        ("critical_exception_count", int((exceptions["severity"] == "Critical").sum()) if not exceptions.empty else 0, "count", "Critical exceptions"),
        ("high_exception_count", int((exceptions["severity"] == "High").sum()) if not exceptions.empty else 0, "count", "High exceptions"),
        ("unresolved_exception_count", int(unresolved_mask.sum()) if not exceptions.empty else 0, "count", "Exceptions not resolved or rejected"),
        ("resolved_exception_count", int(resolved_mask.sum()) if not exceptions.empty else 0, "count", "Exceptions in RESOLVED state"),
        ("duplicate_rate", _safe_rate(len(duplicate_ids), total), "percent", "Records failing duplicate ID or active-conflict rules / total records * 100"),
        ("stale_record_count", int(failed.loc[failed["rule_id"] == "SSI-009", "record_id"].nunique()), "count", "Records failing stale-instruction validation"),
        ("expired_instruction_count", int(failed.loc[failed["rule_id"] == "SSI-010", "record_id"].nunique()), "count", "Records failing expiry validation"),
        ("maker_checker_violation_count", int(failed.loc[failed["rule_id"].isin(["SSI-012", "SSI-013"]), "record_id"].nunique()), "count", "Records failing maker-checker completeness or segregation"),
        ("average_exception_age_days", average_age, "days", "Average age of unresolved exceptions"),
        ("average_remediation_time_days", average_remediation, "days", "Average detected-to-resolved duration for resolved exceptions"),
    ]
    summary = pd.DataFrame(metrics, columns=["metric", "value", "unit", "formula"])

    breakdown_frames: list[pd.DataFrame] = []
    if not exceptions.empty:
        dimensions = {
            "rule": "rule_id",
            "currency": "currency",
            "market": "market",
            "severity": "severity",
            "status": "status",
        }
        for label, column in dimensions.items():
            grouped = exceptions.groupby(column, dropna=False).size().reset_index(name="exception_count")
            grouped.insert(0, "summary_type", label)
            grouped = grouped.rename(columns={column: "dimension_value"})
            breakdown_frames.append(grouped)
        source = records[["record_id", "source_channel"]].merge(exceptions[["record_id"]], on="record_id", how="inner")
        grouped = source.groupby("source_channel", dropna=False).size().reset_index(name="exception_count")
        grouped.insert(0, "summary_type", "source_channel")
        breakdown_frames.append(grouped.rename(columns={"source_channel": "dimension_value"}))
    breakdown = pd.concat(breakdown_frames, ignore_index=True) if breakdown_frames else pd.DataFrame(columns=["summary_type", "dimension_value", "exception_count"])
    return summary, breakdown

