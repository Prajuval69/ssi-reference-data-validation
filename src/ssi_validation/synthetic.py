"""Deterministic synthetic SSI generation with deliberate edge cases."""

from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd

from .config import SystemConfig
from .references import build_reference_data


def generate_synthetic_ssi(config: SystemConfig) -> pd.DataFrame:
    if config.record_count < 40:
        raise ValueError("record_count must be at least 40 to include all configured edge cases")

    rng = np.random.default_rng(config.random_seed)
    refs = build_reference_data(config)
    market_rows = refs["markets"].to_dict("records")
    currency_for_country = dict(refs["currency_country"][["country", "currency"]].itertuples(index=False, name=None))
    statuses = np.array(config.allowed_statuses)
    makers = np.array([f"maker_{i:02d}" for i in range(1, 9)])
    checkers = np.array([f"checker_{i:02d}" for i in range(1, 9)])
    now = config.business_datetime
    records: list[dict[str, object]] = []

    for i in range(config.record_count):
        market_ref = market_rows[i % len(market_rows)]
        country = market_ref["country"]
        currency = currency_for_country[country]
        created_days_ago = int(rng.integers(20, 150))
        updated_days_ago = int(rng.integers(0, min(config.stale_days - 1, 120)))
        effective_offset = int(rng.integers(-90, 30))
        expiry_offset = int(rng.integers(120, 720))
        maker = str(rng.choice(makers))
        checker = str(rng.choice(checkers))
        records.append(
            {
                "ssi_id": f"SSI-{i + 1:05d}",
                "client_id": f"CL-{i + 1:04d}",
                "client_name": f"Synthetic Client {i + 1:03d}",
                "market": market_ref["market"],
                "country": country,
                "currency": currency,
                "account_number": f"SYN-{country}-{int(rng.integers(0, 10**10)):010d}",
                "custodian": f"Synthetic Custodian {(i % 12) + 1:02d}",
                "beneficiary_name": f"Synthetic Beneficiary {(i % 90) + 1:03d}",
                "settlement_method": str(rng.choice(["DVP", "FOP", "RVP"])),
                "source_channel": str(rng.choice(["PORTAL", "API", "BATCH"])),
                "effective_date": (now + timedelta(days=effective_offset)).date().isoformat(),
                "expiry_date": (now + timedelta(days=expiry_offset)).date().isoformat(),
                "status": str(rng.choice(statuses, p=[0.25, 0.30, 0.15, 0.25, 0.05])),
                "maker": maker,
                "checker": checker,
                "created_at": (now - timedelta(days=created_days_ago)).isoformat(),
                "updated_at": (now - timedelta(days=updated_days_ago)).isoformat(),
            }
        )

    df = pd.DataFrame(records)

    # Deliberate deterministic defects. They are synthetic and intentionally overlap.
    df.loc[0, "client_name"] = None
    df.loc[1, "account_number"] = "INVALID-ACCOUNT"
    df.loc[2, "currency"] = "BAD"
    df.loc[3, "settlement_method"] = "UNKNOWN"
    df.loc[4, "source_channel"] = "EMAIL"
    df.loc[5, "effective_date"] = "not-a-date"
    df.loc[6, "expiry_date"] = (now - timedelta(days=60)).date().isoformat()
    df.loc[7, "expiry_date"] = (now - timedelta(days=10)).date().isoformat()
    df.loc[7, "effective_date"] = now.date().isoformat()
    df.loc[8, "updated_at"] = (now - timedelta(days=config.stale_days + 1)).isoformat()
    df.loc[9, ["country", "currency"]] = ["SX", "SEUR"]
    df.loc[10, "maker"] = None
    df.loc[11, "checker"] = None
    df.loc[12, "checker"] = df.loc[12, "maker"]
    df.loc[13, "status"] = "ARCHIVED"
    df.loc[14, "effective_date"] = None
    df.loc[15, "updated_at"] = "invalid-timestamp"

    # Duplicate identifiers retain distinct physical records so the engine can flag all copies.
    df.loc[config.record_count - 3, "ssi_id"] = df.loc[20, "ssi_id"]
    df.loc[config.record_count - 2, "ssi_id"] = df.loc[21, "ssi_id"]

    # Active business-key conflicts: copy the key and force both members to active states.
    for target, source in ((30, 22), (31, 23), (32, 24)):
        for col in config.business_key:
            df.loc[target, col] = df.loc[source, col]
        df.loc[target, "country"] = df.loc[source, "country"]
        df.loc[target, "status"] = "NEW"
        df.loc[source, "status"] = "UNDER_REVIEW"

    df.insert(0, "record_id", np.arange(1, len(df) + 1, dtype=int))
    return df
