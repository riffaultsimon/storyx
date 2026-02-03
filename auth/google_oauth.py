"""Google OAuth 2.0 authentication."""

import logging
import secrets
from urllib.parse import urlencode

import requests

from config import (
    APP_BASE_URL,
    GOOGLE_OAUTH_CLIENT_ID,
    GOOGLE_OAUTH_CLIENT_SECRET,
)

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

SCOPES = ["openid", "email", "profile"]


def is_google_oauth_configured() -> bool:
    """Check if Google OAuth credentials are configured."""
    return bool(GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET)


def generate_auth_url(state: str | None = None) -> str:
    """Generate the Google OAuth authorization URL.

    Args:
        state: Optional state parameter for CSRF protection.

    Returns:
        The authorization URL to redirect the user to.
    """
    if not state:
        state = secrets.token_urlsafe(32)

    params = {
        "client_id": GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": f"{APP_BASE_URL}/?google_callback=1",
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "access_type": "online",
        "prompt": "select_account",  # Always show account selector
    }

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}", state


def exchange_code_for_tokens(code: str) -> dict | None:
    """Exchange the authorization code for access tokens.

    Args:
        code: The authorization code from Google.

    Returns:
        Token response dict or None on error.
    """
    try:
        response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{APP_BASE_URL}/?google_callback=1",
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Failed to exchange code for tokens: %s", e)
        return None


def get_user_info(access_token: str) -> dict | None:
    """Get user information from Google.

    Args:
        access_token: The access token from the token exchange.

    Returns:
        User info dict with id, email, name, picture, or None on error.
    """
    try:
        response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Failed to get user info: %s", e)
        return None


def authenticate_with_google(code: str) -> dict | None:
    """Complete the Google OAuth flow and return user info.

    Args:
        code: The authorization code from Google callback.

    Returns:
        Dict with google_id, email, name, picture or None on error.
    """
    tokens = exchange_code_for_tokens(code)
    if not tokens or "access_token" not in tokens:
        return None

    user_info = get_user_info(tokens["access_token"])
    if not user_info:
        return None

    return {
        "google_id": user_info.get("id"),
        "email": user_info.get("email"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture"),
    }
