"""
Authentication module for Method CRM MCP server.

This module provides authentication handlers for different auth methods:
- API Key (fully implemented)
- OAuth2 Authorization Code (placeholder)
- OAuth2 Client Credentials (placeholder)
- OAuth2 Implicit Flow (placeholder)
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict
from datetime import datetime, timedelta

from .errors import AuthenticationError


class AuthBase(ABC):
    """Base class for authentication handlers."""

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.

        Returns:
            Dict[str, str]: Headers dictionary with authentication
        """
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """
        Check if authentication is valid.

        Returns:
            bool: True if authentication is valid
        """
        pass


class APIKeyAuth(AuthBase):
    """
    API Key authentication handler (fully implemented).

    This is the simplest authentication method using a static API key.
    The key is passed as 'APIKey <key>' in the Authorization header.
    """

    def __init__(self, api_key: str):
        """
        Initialize API Key authentication.

        Args:
            api_key: The Method CRM API key

        Raises:
            AuthenticationError: If API key is empty or invalid
        """
        if not api_key or not api_key.strip():
            raise AuthenticationError("API key cannot be empty")

        self.api_key = api_key.strip()

    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers with API key.

        Returns:
            Dict[str, str]: Headers with Authorization APIKey token
        """
        return {
            "Authorization": f"APIKey {self.api_key}",
            "Content-Type": "application/json",
        }

    def is_valid(self) -> bool:
        """
        Check if API key is valid.

        Returns:
            bool: True if API key exists (actual validation happens on API call)
        """
        return bool(self.api_key)


class OAuth2AuthorizationCodeAuth(AuthBase):
    """
    OAuth2 Authorization Code Flow authentication handler (PLACEHOLDER).

    This flow is used for server-side applications where users authorize
    the application to access their Method CRM data.

    TODO: Implement OAuth2 authorization code flow:
    1. Redirect user to METHOD_OAUTH_AUTHORIZE_URL
    2. Handle callback with authorization code
    3. Exchange code for access token at METHOD_OAUTH_TOKEN_URL
    4. Refresh token when expired
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        authorize_url: str,
        token_url: str,
    ):
        """
        Initialize OAuth2 Authorization Code authentication.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: Redirect URI for callback
            authorize_url: Authorization endpoint URL
            token_url: Token endpoint URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers (placeholder)."""
        raise NotImplementedError(
            "OAuth2 Authorization Code Flow is not yet implemented. "
            "Please use API Key authentication (METHOD_API_KEY) for now. "
            "OAuth2 support is coming in a future release."
        )

    def is_valid(self) -> bool:
        """Check if authentication is valid (placeholder)."""
        return False


class OAuth2ClientCredentialsAuth(AuthBase):
    """
    OAuth2 Client Credentials Flow authentication handler (PLACEHOLDER).

    This flow is used for machine-to-machine authentication where no
    user interaction is required.

    TODO: Implement OAuth2 client credentials flow:
    1. Request access token from METHOD_OAUTH_TOKEN_URL
    2. Use client_id and client_secret for authentication
    3. Refresh token when expired (1 hour lifetime)
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
    ):
        """
        Initialize OAuth2 Client Credentials authentication.

        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token_url: Token endpoint URL
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers (placeholder)."""
        raise NotImplementedError(
            "OAuth2 Client Credentials Flow is not yet implemented. "
            "Please use API Key authentication (METHOD_API_KEY) for now. "
            "OAuth2 support is coming in a future release."
        )

    def is_valid(self) -> bool:
        """Check if authentication is valid (placeholder)."""
        return False


class OAuth2ImplicitAuth(AuthBase):
    """
    OAuth2 Implicit Flow authentication handler (PLACEHOLDER).

    This flow is used for browser-based single-page applications (SPAs).
    The access token is returned directly in the URL fragment.

    TODO: Implement OAuth2 implicit flow:
    1. Redirect to METHOD_OAUTH_AUTHORIZE_URL with response_type=token
    2. Extract access token from URL fragment
    3. Handle token expiration (no refresh token in implicit flow)
    """

    def __init__(
        self,
        client_id: str,
        authorize_url: str,
    ):
        """
        Initialize OAuth2 Implicit Flow authentication.

        Args:
            client_id: OAuth2 client ID
            authorize_url: Authorization endpoint URL
        """
        self.client_id = client_id
        self.authorize_url = authorize_url
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers (placeholder)."""
        raise NotImplementedError(
            "OAuth2 Implicit Flow is not yet implemented. "
            "Please use API Key authentication (METHOD_API_KEY) for now. "
            "OAuth2 support is coming in a future release."
        )

    def is_valid(self) -> bool:
        """Check if authentication is valid (placeholder)."""
        return False


class AuthManager:
    """
    Authentication manager that auto-detects and manages auth methods.

    This manager examines environment variables to determine which
    authentication method to use and provides a unified interface.
    """

    def __init__(self):
        """
        Initialize authentication manager.

        Auto-detects authentication method from environment variables
        in the following priority order:
        1. API Key (METHOD_API_KEY)
        2. OAuth2 Client Credentials (METHOD_CLIENT_ID + METHOD_CLIENT_SECRET)
        3. OAuth2 Authorization Code (METHOD_CLIENT_ID + METHOD_REDIRECT_URI)
        4. OAuth2 Implicit (METHOD_CLIENT_ID only)

        Raises:
            AuthenticationError: If no valid authentication method is found
        """
        self.auth: Optional[AuthBase] = None

        # Try API Key first (fully implemented)
        api_key = os.getenv("METHOD_API_KEY")
        if api_key:
            self.auth = APIKeyAuth(api_key)
            self.auth_method = "api_key"
            return

        # Try OAuth2 methods (placeholders)
        client_id = os.getenv("METHOD_CLIENT_ID")
        client_secret = os.getenv("METHOD_CLIENT_SECRET")
        redirect_uri = os.getenv("METHOD_REDIRECT_URI")

        if client_id and client_secret and redirect_uri:
            # OAuth2 Authorization Code
            authorize_url = os.getenv(
                "METHOD_OAUTH_AUTHORIZE_URL",
                "https://rest.method.me/oauth/authorize"
            )
            token_url = os.getenv(
                "METHOD_OAUTH_TOKEN_URL",
                "https://rest.method.me/oauth/token"
            )
            self.auth = OAuth2AuthorizationCodeAuth(
                client_id, client_secret, redirect_uri, authorize_url, token_url
            )
            self.auth_method = "oauth2_authorization_code"
            return

        if client_id and client_secret:
            # OAuth2 Client Credentials
            token_url = os.getenv(
                "METHOD_OAUTH_TOKEN_URL",
                "https://rest.method.me/oauth/token"
            )
            self.auth = OAuth2ClientCredentialsAuth(
                client_id, client_secret, token_url
            )
            self.auth_method = "oauth2_client_credentials"
            return

        if client_id:
            # OAuth2 Implicit
            authorize_url = os.getenv(
                "METHOD_OAUTH_AUTHORIZE_URL",
                "https://rest.method.me/oauth/authorize"
            )
            self.auth = OAuth2ImplicitAuth(client_id, authorize_url)
            self.auth_method = "oauth2_implicit"
            return

        # No authentication found
        raise AuthenticationError(
            "No authentication credentials found. Please set one of:\n"
            "1. METHOD_API_KEY for API key authentication (recommended)\n"
            "2. METHOD_CLIENT_ID and METHOD_CLIENT_SECRET for OAuth2 (coming soon)\n"
            "See .env.example for configuration details."
        )

    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers from configured auth method.

        Returns:
            Dict[str, str]: Authentication headers

        Raises:
            AuthenticationError: If no auth method is configured
        """
        if not self.auth:
            raise AuthenticationError("No authentication method configured")

        return self.auth.get_headers()

    def is_valid(self) -> bool:
        """
        Check if current authentication is valid.

        Returns:
            bool: True if authentication is valid
        """
        if not self.auth:
            return False

        return self.auth.is_valid()

    def get_auth_method(self) -> str:
        """
        Get the name of the current authentication method.

        Returns:
            str: Authentication method name
        """
        return getattr(self, "auth_method", "none")
