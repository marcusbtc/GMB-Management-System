import os

DEFAULT_REDIRECT_URI = "http://localhost:8501"
DEFAULT_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
DEFAULT_TOKEN_URI = "https://oauth2.googleapis.com/token"
DEFAULT_LOG_LEVEL = "INFO"

GOOGLE_OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/business.manage",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


def get_env(name, default=""):
    return os.getenv(name, default).strip()


def get_google_client_id():
    return get_env("GOOGLE_CLIENT_ID")


def get_google_client_secret():
    return get_env("GOOGLE_CLIENT_SECRET")


def get_google_redirect_uri():
    return get_env("GOOGLE_REDIRECT_URI", DEFAULT_REDIRECT_URI)


def get_google_auth_uri():
    return get_env("GOOGLE_AUTH_URI", DEFAULT_AUTH_URI)


def get_google_token_uri():
    return get_env("GOOGLE_TOKEN_URI", DEFAULT_TOKEN_URI)


def get_gemini_api_key():
    return get_env("GEMINI_API_KEY")


def get_log_level():
    return get_env("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
