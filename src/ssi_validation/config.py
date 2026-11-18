"""Central configuration for the synthetic SSI simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


REQUIRED_COLUMNS = (
    "ssi_id",
    "client_id",
    "client_name",
    "market",
    "country",
    "currency",
    "account_number",
    "custodian",
    "beneficiary_name",
    "settlement_method",
    "source_channel",
    "effective_date",
    "expiry_date",
    "status",
    "maker",
    "checker",
    "created_at",
    "updated_at",
)


@dataclass(frozen=True)
class RuleDefinition:
    rule_id: str
    rule_name: str
    description: str
    severity: str


RULES: tuple[RuleDefinition, ...] = (
    RuleDefinition("SSI-001", "Mandatory fields", "Required values must be present.", "High"),
    RuleDefinition("SSI-002", "Duplicate SSI ID", "SSI identifiers must not be duplicated.", "Critical"),
    RuleDefinition("SSI-003", "Active instruction conflict", "Only one active instruction may exist per business key.", "Critical"),
    RuleDefinition("SSI-004", "Supported currency", "Currency must exist in reference data.", "High"),
    RuleDefinition("SSI-005", "Account format", "Account number must match the configured synthetic format.", "High"),
    RuleDefinition("SSI-006", "Settlement method", "Settlement method must be supported.", "Medium"),
    RuleDefinition("SSI-007", "Authorized source", "Source channel must be authorized.", "High"),
    RuleDefinition("SSI-008", "Date consistency", "Effective and expiry dates must be valid and ordered.", "High"),
    RuleDefinition("SSI-009", "Stale instruction", "Last update must be within the configured age threshold.", "Medium"),
    RuleDefinition("SSI-010", "Expired instruction", "Instruction must not be past its expiry date.", "High"),
    RuleDefinition("SSI-011", "Currency/country consistency", "Currency must be allowed for the country.", "Medium"),
    RuleDefinition("SSI-012", "Maker/checker completeness", "Maker and checker must both be present.", "High"),
    RuleDefinition("SSI-013", "Maker/checker segregation", "Maker and checker must be different.", "Critical"),
    RuleDefinition("SSI-014", "Workflow status", "Status must be in the allowed status set.", "High"),
    RuleDefinition("SSI-015", "Market/country consistency", "Market and country must exist and form an allowed pair.", "Medium"),
)


@dataclass(frozen=True)
class SystemConfig:
    random_seed: int = 20260923
    record_count: int = 250
    stale_days: int = 180
    account_regex: str = r"^SYN-[A-Z]{2}-\d{10}$"
    business_key: tuple[str, ...] = ("client_id", "market", "currency", "settlement_method")
    active_statuses: tuple[str, ...] = ("NEW", "UNDER_REVIEW", "REMEDIATION_REQUIRED")
    terminal_statuses: tuple[str, ...] = ("RESOLVED", "REJECTED")
    workflow_transitions: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: {
            "NEW": ("UNDER_REVIEW",),
            "UNDER_REVIEW": ("REMEDIATION_REQUIRED", "RESOLVED", "REJECTED"),
            "REMEDIATION_REQUIRED": ("UNDER_REVIEW",),
            "RESOLVED": (),
            "REJECTED": (),
        }
    )
    business_datetime: datetime = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    data_dir: Path = Path("data")

    @property
    def allowed_statuses(self) -> tuple[str, ...]:
        return tuple(self.workflow_transitions)

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def reference_dir(self) -> Path:
        return self.data_dir / "reference"

    @property
    def output_dir(self) -> Path:
        return self.data_dir / "outputs"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "ssi_validation.db"


DEFAULT_CONFIG = SystemConfig()
RULE_BY_ID = {rule.rule_id: rule for rule in RULES}
