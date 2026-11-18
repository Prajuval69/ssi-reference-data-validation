from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pandas as pd
import pytest

from ssi_validation.config import DEFAULT_CONFIG
from ssi_validation.references import build_reference_data


@pytest.fixture
def config(tmp_path):
    return replace(DEFAULT_CONFIG, data_dir=tmp_path / "data", record_count=50)


@pytest.fixture
def references(config):
    return build_reference_data(config)


@pytest.fixture
def valid_record(config):
    now = config.business_datetime
    return {
        "record_id": 1,
        "ssi_id": "SSI-TEST-001",
        "client_id": "CL-TEST-001",
        "client_name": "Synthetic Test Client",
        "market": "XALP",
        "country": "SX",
        "currency": "SUSD",
        "account_number": "SYN-SX-0000000001",
        "custodian": "Synthetic Custodian Test",
        "beneficiary_name": "Synthetic Beneficiary Test",
        "settlement_method": "DVP",
        "source_channel": "PORTAL",
        "effective_date": (now - timedelta(days=10)).date().isoformat(),
        "expiry_date": (now + timedelta(days=100)).date().isoformat(),
        "status": "NEW",
        "maker": "maker_test",
        "checker": "checker_test",
        "created_at": (now - timedelta(days=20)).isoformat(),
        "updated_at": (now - timedelta(days=1)).isoformat(),
    }


def result_for(engine, rows, rule_id):
    results = engine.run(pd.DataFrame(rows))
    return results[results["rule_id"] == rule_id].reset_index(drop=True)

