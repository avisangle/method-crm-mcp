"""
Error handling utilities for Method CRM MCP server.

This module provides error transformation and handling utilities to convert
API errors into actionable messages for LLM agents.
"""

from typing import Optional
import httpx


class MethodAPIError(Exception):
    """Base exception for Method API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class AuthenticationError(MethodAPIError):
    """Raised when authentication fails."""
    pass


class RateLimitError(MethodAPIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ValidationError(MethodAPIError):
    """Raised when request validation fails."""
    pass


class NotFoundError(MethodAPIError):
    """Raised when resource is not found."""
    pass


class PermissionError(MethodAPIError):
    """Raised when user lacks permission."""
    pass


def handle_api_error(e: Exception) -> str:
    """
    Transform API errors into actionable error messages for LLM agents.

    This function converts various exception types into clear, actionable
    messages that help agents understand what went wrong and how to fix it.

    Args:
        e: The exception to handle

    Returns:
        str: A clear, actionable error message
    """
    # Handle HTTP status errors from httpx
    if isinstance(e, httpx.HTTPStatusError):
        status_code = e.response.status_code

        # Try to extract error details from response
        try:
            error_data = e.response.json()
            error_message = error_data.get("error", {}).get("message", str(e))
        except Exception:
            error_message = str(e)

        if status_code == 400:
            return (
                f"Error: Validation failed - {error_message}\n"
                "Suggestion: Check that all required fields are provided and have valid values. "
                "Review the API documentation for parameter requirements."
            )
        elif status_code == 401:
            return (
                "Error: Authentication failed. Your API key or access token is invalid or expired.\n"
                "Suggestion: Check that METHOD_API_KEY is correctly set in your environment. "
                "If using OAuth2, ensure your token hasn't expired and refresh if needed."
            )
        elif status_code == 403:
            return (
                f"Error: Permission denied - {error_message}\n"
                "Suggestion: Your account doesn't have permission to perform this operation. "
                "Check that you have the required role (e.g., Admin for API key creation) or "
                "that the resource belongs to your account."
            )
        elif status_code == 404:
            return (
                f"Error: Resource not found - {error_message}\n"
                "Suggestion: Verify that the table name, record ID, or file ID is correct. "
                "Use list/query tools to find the correct identifier."
            )
        elif status_code == 429:
            retry_after = e.response.headers.get("Retry-After", "unknown")
            return (
                f"Error: Rate limit exceeded (100 requests/minute or daily limit reached).\n"
                f"Retry-After: {retry_after} seconds\n"
                "Suggestion: Wait before making more requests. Method CRM limits: "
                "100 req/min per account, 5,000-25,000 daily depending on licenses."
            )
        elif status_code == 500:
            return (
                "Error: Method API server error occurred.\n"
                "Suggestion: This is a temporary server issue. Wait a moment and retry. "
                "If the problem persists, check Method CRM status page or contact support."
            )
        elif status_code == 503:
            return (
                "Error: Method API service temporarily unavailable.\n"
                "Suggestion: The API is undergoing maintenance or experiencing high load. "
                "Wait a few minutes and retry your request."
            )
        else:
            return f"Error: API request failed with status {status_code} - {error_message}"

    # Handle timeout errors
    elif isinstance(e, httpx.TimeoutException):
        return (
            "Error: Request timed out while waiting for Method API response.\n"
            "Suggestion: The API might be slow or your network connection interrupted. "
            "Try again, or increase METHOD_REQUEST_TIMEOUT in your configuration."
        )

    # Handle connection errors
    elif isinstance(e, httpx.ConnectError):
        return (
            "Error: Unable to connect to Method API.\n"
            "Suggestion: Check your internet connection and verify that METHOD_API_BASE_URL "
            "is correct (default: https://rest.method.me/api/v1/)."
        )

    # Handle custom Method API errors
    elif isinstance(e, AuthenticationError):
        return f"Error: {e.message}\nSuggestion: Verify your authentication credentials."

    elif isinstance(e, RateLimitError):
        retry_msg = f" Retry after {e.retry_after} seconds." if e.retry_after else ""
        return (
            f"Error: {e.message}{retry_msg}\n"
            "Suggestion: Wait before making more requests to respect rate limits."
        )

    elif isinstance(e, ValidationError):
        return f"Error: {e.message}\nSuggestion: Check your input parameters and try again."

    elif isinstance(e, NotFoundError):
        return f"Error: {e.message}\nSuggestion: Verify the resource ID and try again."

    elif isinstance(e, PermissionError):
        return f"Error: {e.message}\nSuggestion: Check your account permissions."

    elif isinstance(e, MethodAPIError):
        return f"Error: {e.message}"

    # Handle unexpected errors
    else:
        error_type = type(e).__name__
        error_msg = str(e)
        return (
            f"Error: Unexpected {error_type} occurred - {error_msg}\n"
            "Suggestion: This is an unexpected error. Check your input parameters and "
            "ensure the Method API is accessible. If the problem persists, report this issue."
        )


def format_success_response(data: dict, message: Optional[str] = None) -> str:
    """
    Format a successful API response as JSON string.

    Args:
        data: The response data from the API
        message: Optional success message to include

    Returns:
        str: Formatted JSON string
    """
    import json

    response = {"success": True}
    if message:
        response["message"] = message
    response["data"] = data

    return json.dumps(response, indent=2)


def format_error_response(error_message: str) -> str:
    """
    Format an error message as JSON string.

    Args:
        error_message: The error message

    Returns:
        str: Formatted JSON error response
    """
    import json

    response = {
        "success": False,
        "error": error_message
    }

    return json.dumps(response, indent=2)
