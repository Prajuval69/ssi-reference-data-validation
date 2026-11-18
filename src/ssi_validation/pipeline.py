"""One-command end-to-end SSI validation pipeline."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pandas as pd

from .audit import record_audit_event
from .config import DEFAULT_CONFIG, SystemConfig
from .database import clear_operational_data, connect, initialize_database, persist_dataframe, persist_reference_data
from .exceptions import ExceptionQueue, create_exceptions
from .kpis import calculate_kpis
from .references import build_reference_data
from .synthetic import generate_synthetic_ssi
from .validation import ValidationEngine
from .workflow import WorkflowManager


def _prepare_directories(config: SystemConfig) -> None:
    for directory in (config.raw_dir, config.reference_dir, config.output_dir):
        directory.mkdir(parents=True, exist_ok=True)


def _write_source_files(records: pd.DataFrame, references: dict[str, pd.DataFrame], config: SystemConfig) -> None:
    records.to_csv(config.raw_dir / "ssi_records.csv", index=False)
    for name, frame in references.items():
        frame.to_csv(config.reference_dir / f"{name}.csv", index=False)


def _initial_audit_events(connection, records: pd.DataFrame, validation_results: pd.DataFrame, exceptions: pd.DataFrame, config: SystemConfig) -> None:
    for row in records.itertuples(index=False):
        record_audit_event(
            connection,
            entity_type="SSI",
            entity_id=str(row.record_id),
            action="CREATED",
            new_state={"ssi_id": row.ssi_id, "status": row.status},
            performed_by=str(row.maker) if pd.notna(row.maker) else "synthetic_generator",
            performed_at=config.business_datetime,
            reason="Deterministic synthetic dataset creation",
        )
    failures_by_record = validation_results[validation_results["result"] == "FAIL"].groupby("record_id")["rule_id"].apply(list).to_dict()
    for row in records.itertuples(index=False):
        failed_rules = failures_by_record.get(row.record_id, [])
        record_audit_event(
            connection,
            entity_type="SSI",
            entity_id=str(row.record_id),
            action="VALIDATION_COMPLETED",
            new_state={"failed_rules": failed_rules, "passed": not failed_rules},
            performed_by="validation_engine",
            performed_at=config.business_datetime,
            reason="Configured SSI validation rules executed",
        )
    for row in exceptions.itertuples(index=False):
        record_audit_event(
            connection,
            entity_type="EXCEPTION",
            entity_id=row.exception_id,
            action="CREATED",
            new_state={"status": row.status, "rule_id": row.rule_id, "severity": row.severity},
            performed_by="validation_engine",
            performed_at=config.business_datetime,
            reason=row.description,
        )
    connection.commit()


def _apply_demo_operations(connection, config: SystemConfig) -> None:
    workflow = WorkflowManager(connection, config)
    rows = connection.execute("SELECT exception_id, severity FROM exceptions ORDER BY exception_id").fetchall()
    for row in rows:
        assignee = "data_quality_lead" if row["severity"] in {"Critical", "High"} else "operations_analyst"
        workflow.assign_exception(row["exception_id"], assignee, "queue_router", "Project severity-based routing rule")
    for index, row in enumerate(rows[:8]):
        exception_id = row["exception_id"]
        workflow.transition_exception(exception_id, "UNDER_REVIEW", "checker_demo", "Synthetic checker review started", event_offset_hours=1)
        if index < 3:
            workflow.transition_exception(
                exception_id,
                "RESOLVED",
                "checker_demo",
                "Synthetic evidence reviewed",
                resolution_notes="Resolved in the deterministic demonstration workflow",
                event_offset_hours=24 + index,
            )
        elif index < 5:
            workflow.transition_exception(exception_id, "REMEDIATION_REQUIRED", "checker_demo", "Synthetic remediation requested", event_offset_hours=4)
        elif index == 5:
            workflow.transition_exception(exception_id, "REJECTED", "checker_demo", "Synthetic instruction rejected", resolution_notes="Rejected in demonstration workflow", event_offset_hours=6)


def run_pipeline(config: SystemConfig = DEFAULT_CONFIG) -> dict[str, object]:
    _prepare_directories(config)
    references = build_reference_data(config)
    records = generate_synthetic_ssi(config)
    _write_source_files(records, references, config)

    validation_results = ValidationEngine(config, references).run(records)
    exceptions = create_exceptions(validation_results, records, config)

    connection = connect(config.database_path)
    try:
        initialize_database(connection)
        clear_operational_data(connection)
        persist_reference_data(connection, references)
        persist_dataframe(connection, records, "ssi_records")
        persist_dataframe(connection, validation_results, "validation_results")
        database_exceptions = exceptions.drop(columns=["client_id", "client_name", "market", "currency", "maker"])
        persist_dataframe(connection, database_exceptions, "exceptions")
        _initial_audit_events(connection, records, validation_results, exceptions, config)
        _apply_demo_operations(connection, config)

        queue = ExceptionQueue(connection, config).query()
        audit_log = pd.read_sql_query("SELECT * FROM audit_log ORDER BY audit_id", connection)
        failed_counts = validation_results[validation_results["result"] == "FAIL"].groupby("record_id").size()
        validated_records = records.copy()
        validated_records["failed_rule_count"] = validated_records["record_id"].map(failed_counts).fillna(0).astype(int)
        validated_records["is_valid"] = validated_records["failed_rule_count"].eq(0)
        kpi_summary, exception_summary = calculate_kpis(records, validation_results, queue, config)

        outputs = {
            "validated_ssi.csv": validated_records,
            "validation_results.csv": validation_results,
            "exceptions.csv": queue,
            "audit_log.csv": audit_log,
            "kpi_summary.csv": kpi_summary,
            "exception_summary.csv": exception_summary,
        }
        for filename, frame in outputs.items():
            frame.to_csv(config.output_dir / filename, index=False)
        return {
            "records": len(records),
            "valid_records": int(validated_records["is_valid"].sum()),
            "exceptions": len(queue),
            "database": str(config.database_path),
            "outputs": [str(config.output_dir / name) for name in outputs],
        }
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the synthetic SSI reference-data validation pipeline")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_CONFIG.data_dir, help="Root directory for generated data and outputs")
    parser.add_argument("--records", type=int, default=DEFAULT_CONFIG.record_count, help="Number of synthetic SSI records (minimum 40)")
    args = parser.parse_args()
    config = replace(DEFAULT_CONFIG, data_dir=args.data_dir, record_count=args.records)
    result = run_pipeline(config)
    print("SSI validation pipeline completed successfully")
    print(f"Records: {result['records']} | Valid: {result['valid_records']} | Exceptions: {result['exceptions']}")
    print(f"Database: {result['database']}")


if __name__ == "__main__":
    main()

