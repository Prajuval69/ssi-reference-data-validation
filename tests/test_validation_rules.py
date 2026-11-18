from __future__ import annotations

from copy import deepcopy
from datetime import timedelta

import pandas as pd
import pytest

from conftest import result_for
from ssi_validation.config import REQUIRED_COLUMNS, RULE_BY_ID
from ssi_validation.errors import InputSchemaError
from ssi_validation.validation import ValidationEngine


def test_all_rules_pass_for_valid_record(config, references, valid_record):
    results = ValidationEngine(config, references).run(pd.DataFrame([valid_record]))
    assert len(results) == 15
    assert set(results["result"]) == {"PASS"}


def test_empty_well_formed_input_returns_empty_results(config, references):
    frame = pd.DataFrame(columns=["record_id", *REQUIRED_COLUMNS])
    results = ValidationEngine(config, references).run(frame)
    assert results.empty
    assert "validation_id" in results.columns


def test_all_records_can_fail_the_same_rule(config, references, valid_record):
    rows = []
    for record_id in (1, 2, 3):
        row = deepcopy(valid_record)
        row.update(record_id=record_id, ssi_id=f"SSI-FAIL-{record_id}", client_id=f"CL-FAIL-{record_id}", currency="BAD")
        rows.append(row)
    result = result_for(ValidationEngine(config, references), rows, "SSI-004")
    assert result["result"].tolist() == ["FAIL", "FAIL", "FAIL"]


def test_severity_catalog_is_explicit():
    assert RULE_BY_ID["SSI-002"].severity == "Critical"
    assert RULE_BY_ID["SSI-006"].severity == "Medium"


@pytest.mark.parametrize("field", ["client_name", "beneficiary_name", "maker"])
def test_mandatory_field_validation(config, references, valid_record, field):
    row = deepcopy(valid_record)
    row[field] = None
    result = result_for(ValidationEngine(config, references), [row], "SSI-001")
    assert result.loc[0, "result"] == "FAIL"
    assert field in result.loc[0, "exception_reason"]


def test_missing_input_column_is_informative(config, references, valid_record):
    frame = pd.DataFrame([valid_record]).drop(columns=["currency"])
    with pytest.raises(InputSchemaError, match="currency"):
        ValidationEngine(config, references).run(frame)


def test_duplicate_identifier_flags_all_copies(config, references, valid_record):
    other = deepcopy(valid_record)
    other["record_id"] = 2
    other["client_id"] = "CL-OTHER"
    results = result_for(ValidationEngine(config, references), [valid_record, other], "SSI-002")
    assert results["result"].tolist() == ["FAIL", "FAIL"]


def test_business_key_conflict_only_for_active_records(config, references, valid_record):
    other = deepcopy(valid_record)
    other.update(record_id=2, ssi_id="SSI-TEST-002", status="UNDER_REVIEW")
    results = result_for(ValidationEngine(config, references), [valid_record, other], "SSI-003")
    assert results["result"].tolist() == ["FAIL", "FAIL"]
    other["status"] = "RESOLVED"
    results = result_for(ValidationEngine(config, references), [valid_record, other], "SSI-003")
    assert results["result"].tolist() == ["PASS", "PASS"]


@pytest.mark.parametrize(
    ("field", "value", "rule_id"),
    [
        ("currency", "BAD", "SSI-004"),
        ("account_number", "123", "SSI-005"),
        ("settlement_method", "BAD", "SSI-006"),
        ("source_channel", "EMAIL", "SSI-007"),
        ("status", "ARCHIVED", "SSI-014"),
    ],
)
def test_reference_and_format_rules(config, references, valid_record, field, value, rule_id):
    row = deepcopy(valid_record)
    row[field] = value
    result = result_for(ValidationEngine(config, references), [row], rule_id)
    assert result.loc[0, "result"] == "FAIL"


@pytest.mark.parametrize(
    ("effective", "expiry", "reason_fragment"),
    [
        (None, "2027-01-01", "effective_date"),
        ("bad-date", "2027-01-01", "effective_date"),
        ("2027-01-02", "2027-01-01", "before"),
        ("2026-01-01", "bad-date", "expiry_date"),
    ],
)
def test_date_consistency(config, references, valid_record, effective, expiry, reason_fragment):
    row = deepcopy(valid_record)
    row["effective_date"] = effective
    row["expiry_date"] = expiry
    result = result_for(ValidationEngine(config, references), [row], "SSI-008")
    assert result.loc[0, "result"] == "FAIL"
    assert reason_fragment in result.loc[0, "exception_reason"]


def test_stale_boundary_is_not_stale_until_older(config, references, valid_record):
    row = deepcopy(valid_record)
    row["updated_at"] = (config.business_datetime - timedelta(days=config.stale_days)).isoformat()
    result = result_for(ValidationEngine(config, references), [row], "SSI-009")
    assert result.loc[0, "result"] == "PASS"
    row["updated_at"] = (config.business_datetime - timedelta(days=config.stale_days, seconds=1)).isoformat()
    result = result_for(ValidationEngine(config, references), [row], "SSI-009")
    assert result.loc[0, "result"] == "FAIL"


def test_expired_instruction(config, references, valid_record):
    row = deepcopy(valid_record)
    row["expiry_date"] = (config.business_datetime - timedelta(days=1)).date().isoformat()
    result = result_for(ValidationEngine(config, references), [row], "SSI-010")
    assert result.loc[0, "result"] == "FAIL"


def test_currency_country_consistency(config, references, valid_record):
    row = deepcopy(valid_record)
    row["currency"] = "SEUR"
    result = result_for(ValidationEngine(config, references), [row], "SSI-011")
    assert result.loc[0, "result"] == "FAIL"


@pytest.mark.parametrize(
    ("field", "value", "reason_fragment"),
    [("market", "BADM", "Market"), ("country", "QQ", "Country"), ("country", "SY", "not allowed")],
)
def test_market_country_reference_validation(config, references, valid_record, field, value, reason_fragment):
    row = deepcopy(valid_record)
    row[field] = value
    result = result_for(ValidationEngine(config, references), [row], "SSI-015")
    assert result.loc[0, "result"] == "FAIL"
    assert reason_fragment in result.loc[0, "exception_reason"]


def test_maker_checker_rules(config, references, valid_record):
    missing = deepcopy(valid_record)
    missing["checker"] = None
    completeness = result_for(ValidationEngine(config, references), [missing], "SSI-012")
    assert completeness.loc[0, "result"] == "FAIL"
    same = deepcopy(valid_record)
    same["checker"] = same["maker"]
    segregation = result_for(ValidationEngine(config, references), [same], "SSI-013")
    assert segregation.loc[0, "result"] == "FAIL"
