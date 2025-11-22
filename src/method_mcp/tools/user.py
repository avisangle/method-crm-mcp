"""
User information tools for Method CRM MCP server.

This module provides tools for retrieving current authenticated user information.
"""

import json

from ..server import mcp
from ..models import UserInfoInput
from ..client import MethodAPIClient
from ..errors import handle_api_error
from ..utils import format_json_response


# Initialize API client (will be created on first use)
_client: MethodAPIClient = None


def get_client() -> MethodAPIClient:
    """Get or create API client instance."""
    global _client
    if _client is None:
        _client = MethodAPIClient()
    return _client


@mcp.tool(
    name="method_user_get_info",
    annotations={
        "title": "Get Current User Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_user_get_info(params: UserInfoInput) -> str:
    """
    Retrieve information about the currently authenticated user.

    This tool fetches details about the user account associated with the current
    API authentication, including name, email, permissions, and account information.

    Args:
        params (UserInfoInput): Validated input parameters containing:
            - response_format (ResponseFormat): 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted user information

            Success (JSON):
            {
                "success": true,
                "data": {
                    "UserId": "...",
                    "UserName": "...",
                    "Email": "...",
                    "FullName": "...",
                    "Role": "...",
                    "Permissions": [...],
                    "AccountId": "...",
                    "CompanyName": "...",
                    "IsActive": bool,
                    "CreatedDate": "...",
                    "LastLogin": "..."
                }
            }

            Success (Markdown):
            # User Information

            **Name**: John Doe
            **Email**: john@example.com
            **Role**: Administrator
            ...

    Examples:
        - Check current user: params with response_format="json"
        - Display user profile: params with response_format="markdown"
        - Verify permissions: Get user info and check Permissions array

    Error Handling:
        - Returns authentication error if token invalid/expired
        - Handles network errors gracefully
    """
    try:
        client = get_client()

        # Make API request
        result = await client.get("me")

        # Format response based on requested format
        if params.response_format.value == "markdown":
            lines = ["# User Information", ""]

            # Format key fields
            if result.get("FullName"):
                lines.append(f"**Name**: {result['FullName']}")
            if result.get("UserName"):
                lines.append(f"**Username**: {result['UserName']}")
            if result.get("Email"):
                lines.append(f"**Email**: {result['Email']}")
            if result.get("Role"):
                lines.append(f"**Role**: {result['Role']}")
            if result.get("CompanyName"):
                lines.append(f"**Company**: {result['CompanyName']}")

            lines.append("")
            lines.append("## Account Details")
            lines.append("")

            if result.get("AccountId"):
                lines.append(f"**Account ID**: {result['AccountId']}")
            if result.get("IsActive") is not None:
                status = "Active" if result.get("IsActive") else "Inactive"
                lines.append(f"**Status**: {status}")
            if result.get("CreatedDate"):
                lines.append(f"**Account Created**: {result['CreatedDate']}")
            if result.get("LastLogin"):
                lines.append(f"**Last Login**: {result['LastLogin']}")

            if result.get("Permissions"):
                lines.append("")
                lines.append("## Permissions")
                lines.append("")
                for perm in result["Permissions"]:
                    lines.append(f"- {perm}")

            return "\n".join(lines)
        else:
            # JSON format
            return format_json_response(result)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg
