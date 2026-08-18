"""OAuth credentials for MCP. Replaces Streamlit session_state / secrets.

Never log access tokens, refresh tokens, or authorization codes.
"""

import json
import os
from pathlib import Path
from urllib.parse import urlparse

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow

from src.gmb_app.core.config import (
    GOOGLE_OAUTH_SCOPES,
    get_google_auth_uri,
    get_google_client_id,
    get_google_client_secret,
    get_google_token_uri,
)
from src.gmb_app.core.logging import get_logger

logger = get_logger("gmb_mcp.auth")

SCOPES = list(GOOGLE_OAUTH_SCOPES)
DEFAULT_TOKEN_FILENAME = ".gmb-mcp-token.json"
DEFAULT_MCP_REDIRECT_URI = "http://localhost:8753/"

_session_credentials = None


def default_token_path():
    return Path(os.getenv("GMB_MCP_TOKEN_PATH", DEFAULT_TOKEN_FILENAME)).expanduser()


def reset_session_credentials():
    """Clears in-process credentials. Used by tests."""
    global _session_credentials
    _session_credentials = None


def set_session_credentials(credentials):
    global _session_credentials
    _session_credentials = credentials


def credentials_from_access_token(access_token, refresh_token=None):
    token = (access_token or "").strip()
    if not token:
        raise ValueError("An OAuth access token is required.")
    refresh = refresh_token if refresh_token is not None else os.getenv("GOOGLE_REFRESH_TOKEN", "")
    refresh = (refresh or "").strip() or None
    return Credentials(
        token=token,
        refresh_token=refresh,
        token_uri=get_google_token_uri(),
        client_id=get_google_client_id() or None,
        client_secret=get_google_client_secret() or None,
        scopes=SCOPES,
    )


def _maybe_refresh(credentials):
    if credentials and getattr(credentials, "expired", False) and credentials.refresh_token:
        credentials.refresh(Request())
        logger.info("Refreshed Google OAuth credentials.")
    return credentials


def load_credentials_from_file(path=None):
    token_file = Path(path) if path else default_token_path()
    if not token_file.is_file():
        return None
    data = json.loads(token_file.read_text())
    if not isinstance(data, dict):
        raise ValueError("Token file is not a JSON object.")
    credentials = Credentials.from_authorized_user_info(data, scopes=SCOPES)
    logger.info("Loaded Google OAuth credentials from %s", token_file)
    return _maybe_refresh(credentials)


def save_credentials(credentials, path=None):
    token_file = Path(path) if path else default_token_path()
    token_file.write_text(credentials.to_json())
    try:
        token_file.chmod(0o600)
    except OSError:
        pass
    logger.info("Saved Google OAuth credentials to %s", token_file)
    return token_file


def resolve_credentials(access_token=None):
    """Resolves user OAuth credentials from argument, session, env, or token file."""
    if access_token:
        credentials = _maybe_refresh(credentials_from_access_token(access_token))
        set_session_credentials(credentials)
        return credentials

    if _session_credentials is not None:
        return _maybe_refresh(_session_credentials)

    env_token = os.getenv("GOOGLE_ACCESS_TOKEN", "").strip()
    if env_token:
        credentials = _maybe_refresh(credentials_from_access_token(env_token))
        set_session_credentials(credentials)
        return credentials

    file_credentials = load_credentials_from_file()
    if file_credentials:
        set_session_credentials(file_credentials)
        return file_credentials

    raise ValueError(
        "No Google OAuth credentials. Pass access_token, set GOOGLE_ACCESS_TOKEN, "
        "or run `python mcp_server.py --oauth` / start_oauth + complete_oauth."
    )


def _oauth_redirect_uri(redirect_uri=None):
    return (redirect_uri or os.getenv("GOOGLE_REDIRECT_URI") or DEFAULT_MCP_REDIRECT_URI).strip()


def _client_config(redirect_uri):
    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    if not client_id or not client_secret:
        raise ValueError(
            "OAuth client config not found. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
            "or provide client_secret.json."
        )
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": get_google_auth_uri(),
            "token_uri": get_google_token_uri(),
            "redirect_uris": [redirect_uri],
        }
    }


def build_flow(redirect_uri=None):
    resolved_redirect = _oauth_redirect_uri(redirect_uri)
    client_secret_file = "client_secret.json"
    if os.path.exists(client_secret_file):
        return Flow.from_client_secrets_file(
            client_secret_file,
            scopes=SCOPES,
            redirect_uri=resolved_redirect,
        )
    return Flow.from_client_config(
        _client_config(resolved_redirect),
        scopes=SCOPES,
        redirect_uri=resolved_redirect,
    )


def start_oauth(redirect_uri=None):
    """Returns a Google authorization URL. Does not log tokens."""
    flow = build_flow(redirect_uri)
    authorization_url, _state = flow.authorization_url(
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )
    return {
        "authorization_url": authorization_url,
        "redirect_uri": flow.redirect_uri,
        "instructions": (
            "Open authorization_url, approve access, then call complete_oauth "
            "with the `code` query parameter from the redirect URL."
        ),
    }


def complete_oauth(code, redirect_uri=None):
    """Exchanges an authorization code. Never returns or logs tokens."""
    auth_code = (code or "").strip()
    if not auth_code:
        raise ValueError("OAuth authorization code is required.")
    flow = build_flow(redirect_uri)
    flow.fetch_token(code=auth_code)
    credentials = flow.credentials
    set_session_credentials(credentials)
    token_file = save_credentials(credentials)
    return {
        "authenticated": True,
        "scopes": list(credentials.scopes or SCOPES),
        "token_path": str(token_file),
    }


def run_oauth_cli():
    """Local installed-app OAuth helper. Prints only the saved file path."""
    redirect_uri = _oauth_redirect_uri()
    parsed = urlparse(redirect_uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    if host not in {"localhost", "127.0.0.1"}:
        started = start_oauth(redirect_uri)
        print(started["authorization_url"])
        print()
        print(started["instructions"])
        return 0

    client_secret_file = "client_secret.json"
    if os.path.exists(client_secret_file):
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes=SCOPES)
    else:
        flow = InstalledAppFlow.from_client_config(_client_config(redirect_uri), scopes=SCOPES)

    credentials = flow.run_local_server(
        host=host,
        port=port,
        prompt="consent",
        access_type="offline",
    )
    set_session_credentials(credentials)
    token_file = save_credentials(credentials)
    print(f"Credentials saved to {token_file} (gitignored). Do not commit this file.")
    return 0
