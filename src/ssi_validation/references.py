"""Deterministic synthetic reference datasets."""

from __future__ import annotations

import pandas as pd

from .config import SystemConfig


def build_reference_data(config: SystemConfig) -> dict[str, pd.DataFrame]:
    currencies = pd.DataFrame(
        [
            ("SUSD", "Synthetic US Dollar", 2),
            ("SEUR", "Synthetic Euro", 2),
            ("SGBP", "Synthetic Pound", 2),
            ("SJPY", "Synthetic Yen", 0),
            ("SINR", "Synthetic Rupee", 2),
        ],
        columns=["currency", "currency_name", "decimal_places"],
    )
    countries = pd.DataFrame(
        [
            ("SX", "Synthetic Republic X"),
            ("SY", "Synthetic Republic Y"),
            ("SZ", "Synthetic Republic Z"),
            ("SW", "Synthetic Republic W"),
            ("SV", "Synthetic Republic V"),
        ],
        columns=["country", "country_name"],
    )
    markets = pd.DataFrame(
        [
            ("XALP", "Synthetic Alpha Market", "SX"),
            ("XBET", "Synthetic Beta Market", "SY"),
            ("XGAM", "Synthetic Gamma Market", "SZ"),
            ("XDEL", "Synthetic Delta Market", "SW"),
            ("XEPS", "Synthetic Epsilon Market", "SV"),
        ],
        columns=["market", "market_name", "country"],
    )
    settlement_methods = pd.DataFrame(
        [("DVP", "Delivery versus payment"), ("FOP", "Free of payment"), ("RVP", "Receive versus payment")],
        columns=["settlement_method", "description"],
    )
    source_channels = pd.DataFrame(
        [("PORTAL", "Synthetic operations portal"), ("API", "Synthetic controlled API"), ("BATCH", "Synthetic batch intake")],
        columns=["source_channel", "description"],
    )
    statuses = pd.DataFrame(
        [(status, int(status in config.terminal_statuses)) for status in config.allowed_statuses],
        columns=["status", "is_terminal"],
    )
    currency_country = pd.DataFrame(
        [("SX", "SUSD"), ("SY", "SEUR"), ("SZ", "SGBP"), ("SW", "SJPY"), ("SV", "SINR")],
        columns=["country", "currency"],
    )
    transitions = pd.DataFrame(
        [(old, new) for old, destinations in config.workflow_transitions.items() for new in destinations],
        columns=["from_status", "to_status"],
    )
    return {
        "currencies": currencies,
        "countries": countries,
        "markets": markets,
        "settlement_methods": settlement_methods,
        "source_channels": source_channels,
        "statuses": statuses,
        "currency_country": currency_country,
        "workflow_transitions": transitions,
    }

