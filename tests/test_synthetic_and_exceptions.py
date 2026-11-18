from __future__ import annotations

import pandas as pd

from ssi_validation.exceptions import create_exceptions
from ssi_validation.synthetic import generate_synthetic_ssi
from ssi_validation.validation import ValidationEngine


def test_generation_is_deterministic(config):
    first = generate_synthetic_ssi(config)
    second = generate_synthetic_ssi(config)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == config.record_count


def test_generator_contains_deliberate_edge_cases(config):
    data = generate_synthetic_ssi(config)
    assert data["ssi_id"].duplicated(keep=False).any()
    assert "BAD" in set(data["currency"])
    assert "ARCHIVED" in set(data["status"])


def test_each_failure_creates_one_exception(config, references):
    data = generate_synthetic_ssi(config)
    results = ValidationEngine(config, references).run(data)
    exceptions = create_exceptions(results, data, config)
    assert len(exceptions) == int((results["result"] == "FAIL").sum())
    assert exceptions["exception_id"].is_unique
    assert set(exceptions["severity"]).issubset({"Critical", "High", "Medium", "Low"})

