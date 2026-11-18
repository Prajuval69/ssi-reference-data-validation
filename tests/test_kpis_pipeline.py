from __future__ import annotations

import sqlite3

import pandas as pd

from ssi_validation.config import RULES
from ssi_validation.kpis import calculate_kpis
from ssi_validation.pipeline import run_pipeline


def test_kpi_calculations(config, references, valid_record):
    records = pd.DataFrame([valid_record])
    validations = pd.DataFrame(
        [
            {
                "record_id": 1,
                "rule_id": rule.rule_id,
                "result": "PASS",
            }
            for rule in RULES
        ]
    )
    exceptions = pd.DataFrame(columns=["status", "severity", "detected_at", "resolved_at", "rule_id", "currency", "market", "record_id"])
    summary, breakdown = calculate_kpis(records, validations, exceptions, config)
    metrics = summary.set_index("metric")["value"].to_dict()
    assert metrics["total_ssi_records"] == 1
    assert metrics["valid_ssi_records"] == 1
    assert metrics["validation_pass_rate"] == 100.0
    assert metrics["exception_count"] == 0
    assert breakdown.empty


def test_full_pipeline_creates_verified_outputs(config):
    result = run_pipeline(config)
    assert result["records"] == config.record_count
    assert result["exceptions"] > 0
    for filename in (
        "validated_ssi.csv",
        "validation_results.csv",
        "exceptions.csv",
        "audit_log.csv",
        "kpi_summary.csv",
        "exception_summary.csv",
    ):
        path = config.output_dir / filename
        assert path.exists()
        assert path.stat().st_size > 0
    with sqlite3.connect(config.database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM ssi_records").fetchone()[0] == config.record_count
        assert connection.execute("SELECT COUNT(*) FROM validation_results").fetchone()[0] == config.record_count * len(RULES)
        assert connection.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] > config.record_count

