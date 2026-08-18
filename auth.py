import os

import streamlit as st
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

from src.gmb_app.core import config
from src.gmb_app.core.config import GOOGLE_OAUTH_SCOPES
from src.gmb_app.core.logging import get_logger

logger = get_logger("auth")

# Scopes required for Google Business Profile and Drive
SCOPES = GOOGLE_OAUTH_SCOPES


def _has_required_scopes(creds):
    """Checks whether credentials include all required scopes."""
    granted = set(getattr(creds, "scopes", []) or [])
    return set(SCOPES).issubset(granted)


def _build_env_oauth_web_config():
    """Builds OAuth web config from environment variables."""
    client_id = config.get_google_client_id()
    client_secret = config.get_google_client_secret()
    if not client_id or not client_secret:
        return None, None

    redirect_uri = config.get_google_redirect_uri()
    auth_uri = config.get_google_auth_uri()
    token_uri = config.get_google_token_uri()

    web_config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "auth_uri": auth_uri,
        "token_uri": token_uri,
        "redirect_uris": [redirect_uri],
    }
    return {"web": web_config}, redirect_uri

def get_flow():
    """Creates a Google OAuth2 Flow instance."""
    default_redirect_uri = config.get_google_redirect_uri()
    client_secret_file = "client_secret.json"
    
    # Check if client_secret.json exists
    if os.path.exists(client_secret_file):
        flow = Flow.from_client_secrets_file(
            client_secret_file,
            scopes=SCOPES,
            redirect_uri=default_redirect_uri
        )
        return flow

    # Try to get from secrets
    try:
        if "web" in st.secrets:
            client_config = {"web": st.secrets["web"]}
            # Get redirect_uri from secrets or default
            redirect_uri = st.secrets["web"].get("redirect_uris", ["http://localhost:8501"])[0]
            
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=redirect_uri
            )
            return flow
    except Exception as e:
        logger.exception("Failed loading OAuth config from Streamlit secrets")
        st.error(f"Error loading secrets: {e}")
        return None

    # Try env-based OAuth config
    env_config, redirect_uri = _build_env_oauth_web_config()
    if env_config:
        try:
            flow = Flow.from_client_config(
                env_config,
                scopes=SCOPES,
                redirect_uri=redirect_uri,
            )
            return flow
        except Exception as e:
            logger.exception("Failed loading OAuth config from environment variables")
            st.error(f"Error loading OAuth config from environment variables: {e}")
            return None
    
    return None

def authenticate():
    """Handles the authentication flow."""
    
    if "credentials" not in st.session_state:
        st.session_state.credentials = None

    if st.session_state.credentials:
        creds = st.session_state.credentials
        if not _has_required_scopes(creds):
            st.session_state.credentials = None
            st.warning("Reconnect Google account to grant Drive access.")
            return None
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            st.session_state.credentials = creds
        return creds

    # If not authenticated, show login button
    flow = get_flow()
    if not flow:
        st.warning(
            "OAuth credentials not found. Configure one of: `client_secret.json`, "
            "Streamlit `secrets.toml`, or GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET env vars."
        )
        return None

    auth_url, _ = flow.authorization_url(prompt='consent')
    
    st.markdown(f"[Login with Google]({auth_url})")
    
    # In a real app, we'd handle the callback code here. 
    # Streamlit's query params can be used to capture the code.
    # For this simple implementation, we might need a more robust callback handler 
    # or instruct the user to copy-paste the code if we use OOB (which is deprecated)
    # or just use the localhost redirect.
    
    # Simplified for this context:
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state.credentials = creds
        # Clear query params to avoid re-using code
        st.query_params.clear()
        st.rerun()
        
    return None
