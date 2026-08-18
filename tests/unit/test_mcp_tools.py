import base64
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd

from src.gmb_mcp import tools


def test_list_accounts_wraps_fetcher():
    with patch("src.gmb_mcp.tools.data_fetcher.get_accounts", return_value=[{"name": "accounts/1"}]):
        assert tools.list_accounts("creds") == {"accounts": [{"name": "accounts/1"}]}


def test_list_locations_passes_account_name():
    with patch(
        "src.gmb_mcp.tools.data_fetcher.get_locations",
        return_value=[{"name": "accounts/1/locations/2"}],
    ) as mocked:
        result = tools.list_locations("creds", "accounts/1")
    mocked.assert_called_once_with("creds", "accounts/1")
    assert result["locations"][0]["name"].endswith("/locations/2")


def test_get_daily_metrics_returns_records_not_dataframe():
    frame = pd.DataFrame([{"date": pd.Timestamp("2026-03-01"), "CALL_CLICKS": 4}])
    with patch("src.gmb_mcp.tools.data_fetcher.get_daily_metrics", return_value=frame) as mocked:
        result = tools.get_daily_metrics("creds", "locations/2", "2026-03-01", "2026-03-31")
    mocked.assert_called_once()
    _, location_id, start, end = mocked.call_args.args
    assert location_id == "locations/2"
    assert start == date(2026, 3, 1)
    assert end == date(2026, 3, 31)
    assert isinstance(result["metrics"], list)
    assert result["metrics"][0]["CALL_CLICKS"] == 4


def test_list_reviews_uses_resolve_location_parent():
    with (
        patch(
            "src.gmb_mcp.tools.data_fetcher.resolve_location_parent",
            return_value="accounts/1/locations/2",
        ) as mocked_parent,
        patch("src.gmb_mcp.tools.data_fetcher.get_reviews", return_value=[{"name": "reviews/9"}]),
    ):
        result = tools.list_reviews("creds", "locations/2", "accounts/1")
    mocked_parent.assert_called_once_with("creds", "locations/2", "accounts/1")
    assert result["parent"] == "accounts/1/locations/2"
    assert result["reviews"][0]["name"] == "reviews/9"


def test_create_local_post_builds_payload_and_calls_fetcher():
    payload = {"summary": "hello", "topicType": "STANDARD", "languageCode": "pt-BR"}
    with (
        patch(
            "src.gmb_mcp.tools.data_fetcher.resolve_location_parent",
            return_value="accounts/1/locations/2",
        ),
        patch("src.gmb_mcp.tools.data_fetcher.build_local_post_payload", return_value=payload),
        patch(
            "src.gmb_mcp.tools.data_fetcher.create_local_post",
            return_value={"name": "accounts/1/locations/2/localPosts/3"},
        ) as mocked_create,
    ):
        result = tools.create_local_post("creds", "locations/2", "hello", account_name="accounts/1")
    mocked_create.assert_called_once()
    assert result["post"]["name"].endswith("localPosts/3")
    assert result["payload"]["summary"] == "hello"


def test_upload_image_to_drive_uses_drive_helper():
    raw = b"fake-image-bytes"
    encoded = base64.b64encode(raw).decode("ascii")
    with (
        patch(
            "src.gmb_mcp.tools.drive_helper.upload_file_to_folder",
            return_value={"id": "file-1", "name": "pic.jpg", "webViewLink": "https://drive.example/view"},
        ) as mocked_upload,
        patch("src.gmb_mcp.tools.drive_helper.set_file_public") as mocked_public,
        patch(
            "src.gmb_mcp.tools.drive_helper.build_public_file_url",
            return_value="https://drive.google.com/uc?export=view&id=file-1",
        ),
        patch("src.gmb_mcp.tools.drive_helper.validate_public_url", return_value=True),
    ):
        result = tools.upload_image_to_drive(
            "creds",
            "pic.jpg",
            encoded,
            "image/jpeg",
            folder_id="folder-9",
        )
    mocked_upload.assert_called_once()
    assert mocked_upload.call_args.args[2] == "pic.jpg"
    assert mocked_upload.call_args.args[3] == raw
    mocked_public.assert_called_once_with("creds", "file-1")
    assert result["public_url"].endswith("file-1")
    assert result["public_url_ok"] is True


def test_reply_to_review_delegates_to_data_fetcher():
    with patch(
        "src.gmb_mcp.tools.data_fetcher.reply_to_review",
        return_value={"comment": "Thanks"},
    ) as mocked:
        result = tools.reply_to_review(
            "creds",
            "reviews/99",
            "Thanks",
            location_id="locations/2",
            account_name="accounts/1",
        )
    mocked.assert_called_once_with(
        "creds",
        review_name="reviews/99",
        comment="Thanks",
        location_id="locations/2",
        account_name="accounts/1",
    )
    assert result == {"reply": {"comment": "Thanks"}}


def test_profile_health_check_uses_existing_analyzer():
    location = {"name": "accounts/1/locations/2", "title": "Cafe"}
    checks = [{"title": "Website", "status": "Good", "score": 100}]
    with (
        patch("src.gmb_mcp.tools.data_fetcher.get_location_details", return_value=location),
        patch("src.gmb_mcp.tools.data_fetcher.get_reviews", return_value=[]),
        patch("src.gmb_mcp.tools.data_fetcher.get_posts", return_value=[]),
        patch("src.gmb_mcp.tools.data_fetcher.get_media", return_value=[]),
        patch("src.gmb_mcp.tools.data_fetcher.get_questions", return_value=[]),
        patch("src.gmb_mcp.tools.health_check.analyze_profile_health", return_value=checks) as mocked,
    ):
        result = tools.profile_health_check("creds", "locations/2", "accounts/1")
    mocked.assert_called_once()
    assert result["overall_score"] == 100
    assert result["checks"] == checks


def test_reply_to_review_in_data_fetcher_resolves_parent():
    reviews = MagicMock()
    service = MagicMock()
    service.accounts.return_value.locations.return_value.reviews.return_value = reviews
    reviews.updateReply.return_value.execute.return_value = {"comment": "Ok"}

    import data_fetcher

    with (
        patch.object(data_fetcher, "get_mybusiness_service", return_value=service),
        patch.object(
            data_fetcher,
            "resolve_location_parent",
            return_value="accounts/1/locations/2",
        ) as mocked_parent,
    ):
        result = data_fetcher.reply_to_review(
            "creds",
            "reviews/99",
            "Ok",
            location_id="locations/2",
            account_name="accounts/1",
        )
    mocked_parent.assert_called_once_with("creds", "locations/2", "accounts/1")
    reviews.updateReply.assert_called_once_with(
        name="accounts/1/locations/2/reviews/99",
        body={"comment": "Ok"},
    )
    assert result["comment"] == "Ok"


def test_mcp_sources_do_not_import_streamlit_or_plotly():
    import ast
    from pathlib import Path

    banned = {"streamlit", "plotly", "fpdf"}
    root = Path("src/gmb_mcp")
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                assert name not in banned, f"{path} imports {name}"
