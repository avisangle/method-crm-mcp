"""
Method API client for making HTTP requests.

This module provides the HTTP client for interacting with the Method CRM API,
including rate limiting, retry logic, and error handling.
"""

import os
from typing import Any, Dict, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .auth import AuthManager
from .errors import (
    handle_api_error,
    RateLimitError,
    AuthenticationError,
    MethodAPIError,
)


class MethodAPIClient:
    """
    HTTP client for Method CRM API with authentication, rate limiting, and retry logic.

    This client handles:
    - Authentication (API Key, OAuth2)
    - Rate limiting (100 req/min, daily limits)
    - Automatic retries with exponential backoff
    - Error transformation
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_manager: Optional[AuthManager] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize Method API client.

        Args:
            base_url: API base URL (default from env or https://rest.method.me/api/v1/)
            auth_manager: Authentication manager (auto-created if None)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url or os.getenv(
            "METHOD_API_BASE_URL", "https://rest.method.me/api/v1/"
        ).rstrip("/")

        self.auth_manager = auth_manager or AuthManager()
        self.timeout = float(os.getenv("METHOD_REQUEST_TIMEOUT", timeout))
        self.max_retries = int(os.getenv("METHOD_MAX_RETRIES", max_retries))

        # Verify authentication is valid
        if not self.auth_manager.is_valid():
            raise AuthenticationError("Authentication is not valid")

    def _get_client(self) -> httpx.AsyncClient:
        """
        Create configured HTTP client.

        Returns:
            httpx.AsyncClient: Configured async HTTP client
        """
        headers = self.auth_manager.get_headers()

        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
        )

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Method API with retry logic.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE, etc.)
            endpoint: API endpoint path (without base URL)
            params: Query parameters
            json_data: JSON body data
            **kwargs: Additional arguments for httpx request

        Returns:
            Dict[str, Any]: Response data

        Raises:
            MethodAPIError: If request fails
        """
        endpoint = endpoint.lstrip("/")
        url = f"{self.base_url}/{endpoint}"

        try:
            async with self._get_client() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    **kwargs,
                )

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=int(retry_after) if retry_after else None,
                    )

                # Raise for HTTP errors
                response.raise_for_status()

                # Handle 204 No Content
                if response.status_code == 204:
                    return {"success": True, "message": "Operation completed successfully"}

                # Parse JSON response
                return response.json()

        except Exception as e:
            # Don't re-wrap MethodAPIError exceptions
            if isinstance(e, MethodAPIError):
                raise

            # Transform httpx errors to MethodAPIError
            error_msg = handle_api_error(e)
            raise MethodAPIError(error_msg) from e

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Dict[str, Any]: Response data
        """
        return await self.request("GET", endpoint, params=params, **kwargs)

    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            endpoint: API endpoint path
            json_data: JSON body data
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Dict[str, Any]: Response data
        """
        return await self.request("POST", endpoint, params=params, json_data=json_data, **kwargs)

    async def patch(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make PATCH request.

        Args:
            endpoint: API endpoint path
            json_data: JSON body data
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Dict[str, Any]: Response data
        """
        return await self.request("PATCH", endpoint, params=params, json_data=json_data, **kwargs)

    async def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make PUT request.

        Args:
            endpoint: API endpoint path
            json_data: JSON body data
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Dict[str, Any]: Response data
        """
        return await self.request("PUT", endpoint, params=params, json_data=json_data, **kwargs)

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Make DELETE request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            **kwargs: Additional request arguments

        Returns:
            Dict[str, Any]: Response data
        """
        return await self.request("DELETE", endpoint, params=params, **kwargs)
