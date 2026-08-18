"""JSON-only helpers. MCP tools never return DataFrame, Plotly, or PDF objects."""

import json
from datetime import date, datetime


def parse_date(value):
    """Parses an ISO date or date/datetime into datetime.date."""
    if value is None or value == "":
        raise ValueError("A date is required (YYYY-MM-DD).")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Use YYYY-MM-DD.") from exc


def dataframe_to_records(frame):
    """Converts a pandas DataFrame (or None) into JSON-safe list[dict]."""
    if frame is None:
        return []
    empty = getattr(frame, "empty", None)
    if empty is True or len(frame) == 0:
        return []
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def json_ready(value):
    """Recursively converts common Google/pandas values into JSON types."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if hasattr(value, "item"):
        try:
            return json_ready(value.item())
        except (ValueError, AttributeError):
            pass
    return value
