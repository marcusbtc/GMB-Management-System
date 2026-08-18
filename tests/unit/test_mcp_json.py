from datetime import date

import pandas as pd
import pytest

from src.gmb_mcp.jsonutil import dataframe_to_records, json_ready, parse_date


def test_parse_date_accepts_iso_string():
    assert parse_date("2026-01-15") == date(2026, 1, 15)


def test_parse_date_rejects_invalid_value():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        parse_date("not-a-date")


def test_dataframe_to_records_is_json_safe():
    frame = pd.DataFrame(
        [
            {"date": pd.Timestamp("2026-01-02"), "WEBSITE_CLICKS": 3},
            {"date": pd.Timestamp("2026-01-03"), "WEBSITE_CLICKS": 0},
        ]
    )
    records = dataframe_to_records(frame)
    assert records[0]["WEBSITE_CLICKS"] == 3
    assert "2026-01-02" in records[0]["date"]


def test_dataframe_to_records_empty():
    assert dataframe_to_records(pd.DataFrame()) == []
    assert dataframe_to_records(None) == []


def test_json_ready_nested_values():
    payload = {"when": date(2026, 2, 1), "items": ({"ok": True},)}
    assert json_ready(payload) == {"when": "2026-02-01", "items": [{"ok": True}]}
