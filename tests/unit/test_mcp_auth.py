import logging
from unittest.mock import MagicMock, patch

import pytest

from src.gmb_mcp import auth


@pytest.fixture(autouse=True)
def _reset_auth_state(monkeypatch):
    auth.reset_session_credentials()
    monkeypatch.delenv("GOOGLE_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("GOOGLE_REFRESH_TOKEN", raising=False)
    yield
    auth.reset_session_credentials()


def test_credentials_from_access_token_rejects_blank():
    with pytest.raises(ValueError, match="access token"):
        auth.credentials_from_access_token("   ")


def test_resolve_credentials_uses_argument_token():
    creds = auth.resolve_credentials("user-access-token")
    assert creds.token == "user-access-token"


def test_resolve_credentials_uses_env_token(monkeypatch):
    monkeypatch.setenv("GOOGLE_ACCESS_TOKEN", "env-access-token")
    creds = auth.resolve_credentials()
    assert creds.token == "env-access-token"


def test_resolve_credentials_missing_raises():
    with pytest.raises(ValueError, match="No Google OAuth credentials"):
        auth.resolve_credentials()


def test_complete_oauth_rejects_blank_code():
    with pytest.raises(ValueError, match="authorization code"):
        auth.complete_oauth(" ")


def test_auth_helpers_do_not_log_secrets(caplog):
    caplog.set_level(logging.DEBUG)
    token = "super-secret-access-token"
    auth.resolve_credentials(token)
    combined = " ".join(record.getMessage() for record in caplog.records)
    assert token not in combined
    assert "refresh-token-value" not in combined


@patch("src.gmb_mcp.auth.build_flow")
@patch("src.gmb_mcp.auth.save_credentials")
def test_complete_oauth_does_not_return_tokens(mock_save, mock_build_flow, tmp_path):
    fake_creds = MagicMock()
    fake_creds.scopes = auth.SCOPES
    fake_creds.token = "must-not-appear"
    fake_creds.refresh_token = "must-not-appear-refresh"
    fake_flow = MagicMock()
    fake_flow.credentials = fake_creds
    mock_build_flow.return_value = fake_flow
    token_file = tmp_path / "token.json"
    mock_save.return_value = token_file

    result = auth.complete_oauth("oauth-code-value")

    fake_flow.fetch_token.assert_called_once_with(code="oauth-code-value")
    assert result["authenticated"] is True
    assert "token" not in result
    assert "access_token" not in result
    assert "refresh_token" not in result
    assert "must-not-appear" not in str(result)
