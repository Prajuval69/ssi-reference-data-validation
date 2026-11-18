"""Configurable, independent SSI validation rules."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .config import REQUIRED_COLUMNS, RULES, RuleDefinition, SystemConfig
from .errors import InputSchemaError


@dataclass(frozen=True)
class RuleOutcome:
    passed: bool
    reason: str = ""


RuleFunction = Callable[[pd.Series, "ValidationContext"], RuleOutcome]


@dataclass
class ValidationContext:
    data: pd.DataFrame
    references: dict[str, pd.DataFrame]
    config: SystemConfig
    duplicate_ids: set[str]
    conflicting_record_ids: set[int]


def _missing(value: Any) -> bool:
    return pd.isna(value) or (isinstance(value, str) and not value.strip())


def _as_utc(value: Any) -> pd.Timestamp | None:
    if _missing(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    return None if pd.isna(parsed) else parsed


def validate_required(row: pd.Series, _: ValidationContext) -> RuleOutcome:
    missing = [column for column in REQUIRED_COLUMNS if _missing(row.get(column))]
    return RuleOutcome(not missing, "Missing mandatory fields: " + ", ".join(missing) if missing else "")


def validate_duplicate_id(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    duplicate = str(row["ssi_id"]) in context.duplicate_ids
    return RuleOutcome(not duplicate, "Duplicate SSI identifier" if duplicate else "")


def validate_active_conflict(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    conflict = int(row["record_id"]) in context.conflicting_record_ids
    return RuleOutcome(not conflict, "Multiple active instructions share the configured business key" if conflict else "")


def validate_currency(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    allowed = set(context.references["currencies"]["currency"])
    passed = not _missing(row["currency"]) and row["currency"] in allowed
    return RuleOutcome(passed, "Currency is not supported" if not passed else "")


def validate_account(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    value = "" if _missing(row["account_number"]) else str(row["account_number"])
    passed = bool(pd.Series([value]).str.fullmatch(context.config.account_regex).iloc[0])
    return RuleOutcome(passed, "Account number does not match the synthetic account format" if not passed else "")


def validate_settlement_method(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    allowed = set(context.references["settlement_methods"]["settlement_method"])
    passed = row["settlement_method"] in allowed
    return RuleOutcome(passed, "Settlement method is not supported" if not passed else "")


def validate_source(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    allowed = set(context.references["source_channels"]["source_channel"])
    passed = row["source_channel"] in allowed
    return RuleOutcome(passed, "Source channel is not authorized" if not passed else "")


def validate_dates(row: pd.Series, _: ValidationContext) -> RuleOutcome:
    effective = _as_utc(row["effective_date"])
    expiry = _as_utc(row["expiry_date"])
    reasons: list[str] = []
    if effective is None:
        reasons.append("effective_date is missing or invalid")
    if not _missing(row["expiry_date"]) and expiry is None:
        reasons.append("expiry_date is invalid")
    if effective is not None and expiry is not None and expiry < effective:
        reasons.append("expiry_date is before effective_date")
    return RuleOutcome(not reasons, "; ".join(reasons))


def validate_stale(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    updated = _as_utc(row["updated_at"])
    if updated is None:
        return RuleOutcome(False, "updated_at is missing or invalid")
    cutoff = pd.Timestamp(context.config.business_datetime) - pd.Timedelta(days=context.config.stale_days)
    stale = updated < cutoff
    return RuleOutcome(not stale, f"Instruction is older than {context.config.stale_days} days" if stale else "")


def validate_expired(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    expiry = _as_utc(row["expiry_date"])
    if expiry is None:
        return RuleOutcome(True)
    expired = context.config.business_datetime.date() > expiry.date()
    return RuleOutcome(not expired, "Instruction expiry date has passed" if expired else "")


def validate_currency_country(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    allowed = set(context.references["currency_country"][["country", "currency"]].itertuples(index=False, name=None))
    pair = (row["country"], row["currency"])
    passed = pair in allowed
    return RuleOutcome(passed, "Currency is not allowed for the country" if not passed else "")


def validate_maker_checker_present(row: pd.Series, _: ValidationContext) -> RuleOutcome:
    missing_roles = [field for field in ("maker", "checker") if _missing(row[field])]
    return RuleOutcome(not missing_roles, "Missing workflow role(s): " + ", ".join(missing_roles) if missing_roles else "")


def validate_maker_checker_segregation(row: pd.Series, _: ValidationContext) -> RuleOutcome:
    if _missing(row["maker"]) or _missing(row["checker"]):
        return RuleOutcome(True)
    same = str(row["maker"]).strip().casefold() == str(row["checker"]).strip().casefold()
    return RuleOutcome(not same, "Maker and checker are the same user" if same else "")


def validate_status(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    passed = row["status"] in context.config.allowed_statuses
    return RuleOutcome(passed, "Status is not in the allowed workflow status set" if not passed else "")


def validate_market_country(row: pd.Series, context: ValidationContext) -> RuleOutcome:
    markets = context.references["markets"]
    countries = set(context.references["countries"]["country"])
    market_country = set(markets[["market", "country"]].itertuples(index=False, name=None))
    if row["country"] not in countries:
        return RuleOutcome(False, "Country is not supported")
    if row["market"] not in set(markets["market"]):
        return RuleOutcome(False, "Market is not supported")
    passed = (row["market"], row["country"]) in market_country
    return RuleOutcome(passed, "Market is not allowed for the country" if not passed else "")


RULE_FUNCTIONS: dict[str, RuleFunction] = {
    "SSI-001": validate_required,
    "SSI-002": validate_duplicate_id,
    "SSI-003": validate_active_conflict,
    "SSI-004": validate_currency,
    "SSI-005": validate_account,
    "SSI-006": validate_settlement_method,
    "SSI-007": validate_source,
    "SSI-008": validate_dates,
    "SSI-009": validate_stale,
    "SSI-010": validate_expired,
    "SSI-011": validate_currency_country,
    "SSI-012": validate_maker_checker_present,
    "SSI-013": validate_maker_checker_segregation,
    "SSI-014": validate_status,
    "SSI-015": validate_market_country,
}


class ValidationEngine:
    def __init__(self, config: SystemConfig, references: dict[str, pd.DataFrame]):
        self.config = config
        self.references = references

    def _validate_schema(self, data: pd.DataFrame) -> None:
        missing = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
        if missing:
            raise InputSchemaError("Input is missing required columns: " + ", ".join(missing))
        if "record_id" not in data.columns:
            raise InputSchemaError("Input is missing required internal column: record_id")

    def _context(self, data: pd.DataFrame) -> ValidationContext:
        duplicate_ids = set(data.loc[data["ssi_id"].duplicated(keep=False), "ssi_id"].astype(str))
        active = data[data["status"].isin(self.config.active_statuses)].copy()
        conflict_mask = active.duplicated(list(self.config.business_key), keep=False)
        conflicting_record_ids = set(active.loc[conflict_mask, "record_id"].astype(int))
        return ValidationContext(data, self.references, self.config, duplicate_ids, conflicting_record_ids)

    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        if data.empty:
            self._validate_schema(data)
            return pd.DataFrame(
                columns=["validation_id", "record_id", "ssi_id", "rule_id", "rule_name", "result", "severity", "exception_reason", "validated_at"]
            )
        self._validate_schema(data)
        context = self._context(data)
        validated_at = self.config.business_datetime.isoformat()
        rows: list[dict[str, object]] = []
        counter = 1
        for record in data.to_dict("records"):
            series = pd.Series(record)
            for definition in RULES:
                outcome = RULE_FUNCTIONS[definition.rule_id](series, context)
                rows.append(
                    {
                        "validation_id": f"VAL-{counter:07d}",
                        "record_id": int(series["record_id"]),
                        "ssi_id": series["ssi_id"],
                        "rule_id": definition.rule_id,
                        "rule_name": definition.rule_name,
                        "result": "PASS" if outcome.passed else "FAIL",
                        "severity": definition.severity,
                        "exception_reason": outcome.reason,
                        "validated_at": validated_at,
                    }
                )
                counter += 1
        return pd.DataFrame(rows)
