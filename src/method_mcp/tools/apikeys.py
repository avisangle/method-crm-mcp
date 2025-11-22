"""
API key management tools for Method CRM MCP server.

This module provides tools for creating, listing, updating, and deleting API keys.
Note: API key creation and management require Administrator permissions.
"""

import json

from ..server import mcp
from ..models import (
    APIKeyCreateInput,
    APIKeyListInput,
    APIKeyUpdateInput,
    APIKeyDeleteInput,
)
from ..client import MethodAPIClient
from ..errors import handle_api_error
from ..utils import (
    format_json_response,
    format_markdown_list,
    format_pagination_info,
)


# Initialize API client (will be created on first use)
_client: MethodAPIClient = None


def get_client() -> MethodAPIClient:
    """Get or create API client instance."""
    global _client
    if _client is None:
        _client = MethodAPIClient()
    return _client


@mcp.tool(
    name="method_apikeys_create",
    annotations={
        "title": "Create Method CRM API Key",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def method_apikeys_create(params: APIKeyCreateInput) -> str:
    """
    Create a new API key for Method CRM access.

    **IMPORTANT**: This operation requires Administrator permissions. Only users
    with Admin role can create API keys.

    This tool generates a new API key that can be used for machine-to-machine
    authentication with the Method CRM API. API keys inherit the creator's
    permissions unless specific permissions are provided.

    Args:
        params (APIKeyCreateInput): Validated input parameters containing:
            - name (str): Name for the API key (e.g., 'Production Server', 'Mobile App')
            - description (Optional[str]): Description of key usage
            - permissions (Optional[List[str]]): Specific permissions (inherits user permissions if omitted)

    Returns:
        str: JSON formatted response with API key details

            Success:
            {
                "success": true,
                "message": "API key created successfully",
                "data": {
                    "KeyId": "...",
                    "Name": "...",
                    "Description": "...",
                    "ApiKey": "...",      # The actual key - SAVE THIS!
                    "Permissions": [...],
                    "CreatedAt": "...",
                    "CreatedBy": "...",
                    "Warning": "Save this key securely. It won't be shown again."
                }
            }

            Error:
            "Error: Permission denied. API key creation requires Admin role..."

    Examples:
        - Create production key: params with name="Production Server", description="Main API integration"
        - Create mobile app key: params with name="Mobile App v2.0", description="iOS and Android app"
        - Create limited key: params with name="Reporting Tool", permissions=["read:customers", "read:invoices"]

    Error Handling:
        - Returns 403 error if user is not Admin
        - Validates name uniqueness
        - Returns the API key only once (cannot be retrieved later)
        - Provides security best practices in response

    Security Notes:
        - Store the API key securely immediately after creation
        - The key cannot be retrieved again after the response
        - Use environment variables to store keys in applications
        - Rotate keys periodically for security
        - Revoke unused keys promptly
    """
    try:
        client = get_client()

        # Build payload
        payload = {
            "Name": params.name,
        }

        if params.description:
            payload["Description"] = params.description

        if params.permissions:
            payload["Permissions"] = params.permissions

        # Make API request
        result = await client.post("apikeys", json_data=payload)

        # Format response with security warning
        response_data = {
            "KeyId": result.get("Id"),
            "Name": params.name,
            "Description": params.description,
            "ApiKey": result.get("ApiKey"),
            "Permissions": result.get("Permissions", []),
            "CreatedAt": result.get("CreatedDate"),
            "CreatedBy": result.get("CreatedBy"),
            "Warning": "⚠️  IMPORTANT: Save this API key securely. It will not be shown again!",
            "SecurityTips": [
                "Store the key in a secure environment variable (METHOD_API_KEY)",
                "Never commit API keys to version control",
                "Rotate keys periodically for security",
                "Revoke this key immediately if compromised",
                "Use separate keys for different environments (dev/staging/prod)"
            ]
        }

        return format_json_response(
            response_data,
            message=f"API key '{params.name}' created successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_apikeys_list",
    annotations={
        "title": "List Method CRM API Keys",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_apikeys_list(params: APIKeyListInput) -> str:
    """
    List all API keys for the Method CRM account.

    This tool retrieves metadata for all API keys in the account. For security
    reasons, the actual key values are masked and only partial key info is shown.

    Args:
        params (APIKeyListInput): Validated input parameters containing:
            - top (Optional[int]): Max keys to return (1-100, default: 20)
            - skip (Optional[int]): Keys to skip for pagination (default: 0)
            - response_format (ResponseFormat): 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted list of API keys

            Success (JSON):
            {
                "success": true,
                "data": {
                    "total": int,
                    "count": int,
                    "has_more": bool,
                    "api_keys": [
                        {
                            "Id": "...",
                            "Name": "...",
                            "Description": "...",
                            "MaskedKey": "••••••••1234",  # Last 4 digits only
                            "Permissions": [...],
                            "CreatedDate": "...",
                            "CreatedBy": "...",
                            "LastUsed": "...",
                            "IsActive": bool
                        },
                        ...
                    ]
                }
            }

            Success (Markdown):
            # API Keys (X of Y)

            ## Key Name 1
            - **Masked Key**: ••••••••1234
            - **Created**: ...
            - **Last Used**: ...
            - **Status**: Active/Inactive
            ...

    Examples:
        - List all keys: params with no filters
        - Paginate keys: params with top=50, skip=100
        - View in markdown: params with response_format="markdown"

    Error Handling:
        - Returns empty list if no keys found
        - Handles pagination correctly
        - Requires appropriate permissions to view keys

    Security Notes:
        - Only metadata is returned (keys are masked)
        - Use LastUsed date to identify unused keys for revocation
        - Monitor key usage for security auditing
    """
    try:
        client = get_client()

        # Build query parameters
        query_params = {}

        if params.top:
            query_params["$top"] = params.top

        if params.skip:
            query_params["$skip"] = params.skip

        # Make API request
        response = await client.get("apikeys", params=query_params)

        # Extract keys and metadata
        api_keys = response.get("value", [])
        total = response.get("@odata.count", len(api_keys))

        # Format pagination info
        pagination = format_pagination_info(
            total=total,
            count=len(api_keys),
            offset=params.skip or 0,
            limit=params.top or 20,
        )

        # Format response based on requested format
        if params.response_format.value == "markdown":
            if not api_keys:
                return "# API Keys\n\nNo API keys found."

            keys_md = format_markdown_list(
                data=api_keys,
                title_field="Name",
                fields=["Id", "Description", "MaskedKey", "Permissions", "CreatedDate", "CreatedBy", "LastUsed", "IsActive"],
                title=f"API Keys ({pagination['count']} of {pagination['total']})"
            )

            footer = f"\n\n**Pagination**: Showing keys {params.skip or 0 + 1}-{params.skip or 0 + len(api_keys)} of {total}"
            if pagination["has_more"]:
                footer += f" | Next offset: {pagination['next_offset']}"

            footer += "\n\n**Security Note**: For security reasons, actual API keys are masked. Keys are only shown once during creation."

            return keys_md + footer
        else:
            # JSON format
            result = {
                **pagination,
                "api_keys": api_keys,
                "security_note": "Actual API keys are masked for security. Keys are only shown once during creation."
            }
            return format_json_response(result)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_apikeys_update",
    annotations={
        "title": "Update Method CRM API Key",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_apikeys_update(params: APIKeyUpdateInput) -> str:
    """
    Update an existing API key's metadata.

    This tool allows you to modify API key properties such as name, description,
    permissions, or active status. The actual API key value cannot be changed.

    Args:
        params (APIKeyUpdateInput): Parameters for updating the API key:
            - key_id: ID of the API key to update
            - name: New name for the key (optional)
            - description: New description (optional)
            - permissions: Updated permissions list (optional)
            - is_active: Enable/disable the key (optional)

    Returns:
        str: JSON formatted response with updated key details

    Example Usage:
        Update key name:
        {
            "key_id": "abc123",
            "name": "Production Server v2"
        }

        Disable a key temporarily:
        {
            "key_id": "abc123",
            "is_active": false
        }

        Update permissions:
        {
            "key_id": "abc123",
            "permissions": ["read:customers", "write:invoices"]
        }

    Notes:
        - At least one field (name, description, permissions, is_active) must be provided
        - Requires appropriate permissions to update keys
        - Key value itself cannot be changed (create new key if needed)
        - Disabling a key prevents it from authenticating requests

    Error Handling:
        - Returns 404 if key_id not found
        - Returns 403 if lacking permission to update
        - Validates permission format if provided
    """
    try:
        client = get_client()

        # Build update payload with only provided fields
        payload = {}
        if params.name is not None:
            payload["Name"] = params.name
        if params.description is not None:
            payload["Description"] = params.description
        if params.permissions is not None:
            payload["Permissions"] = params.permissions
        if params.is_active is not None:
            payload["IsActive"] = params.is_active

        # Validate at least one field provided
        if not payload:
            return "Error: No fields provided for update. Specify at least one field to update (name, description, permissions, or is_active)."

        # Make API request
        endpoint = f"apikeys/{params.key_id}"
        result = await client.put(endpoint, json_data=payload)

        return format_json_response(
            result,
            message="API key updated successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_apikeys_delete",
    annotations={
        "title": "Delete Method CRM API Key",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_apikeys_delete(params: APIKeyDeleteInput) -> str:
    """
    Delete (revoke) an API key permanently.

    This tool permanently revokes an API key, preventing any further authentication
    using that key. This action cannot be undone.

    **IMPORTANT**: This is a destructive operation. The key will be immediately
    invalidated and cannot be restored. Any applications using this key will
    lose access.

    Args:
        params (APIKeyDeleteInput): Parameters containing:
            - key_id: ID of the API key to delete/revoke

    Returns:
        str: JSON formatted confirmation message

    Example Usage:
        Revoke a compromised key:
        {
            "key_id": "abc123"
        }

    Use Cases:
        - Revoke compromised keys immediately
        - Clean up unused or old keys
        - Remove keys for deprecated integrations
        - Deactivate keys for terminated employees
        - Part of regular key rotation process

    Security Best Practices:
        - Revoke keys immediately if compromised
        - Remove unused keys to reduce attack surface
        - Rotate keys periodically (quarterly or annually)
        - Document key deletion in security logs
        - Notify relevant teams before deleting production keys

    Error Handling:
        - Returns 404 if key_id not found
        - Returns 403 if lacking permission to delete
        - Provides confirmation of successful deletion

    Notes:
        - This action is permanent and cannot be undone
        - Applications using this key will immediately lose access
        - Consider disabling the key first (via update) to test impact
        - Create a replacement key before deleting if needed
    """
    try:
        client = get_client()

        # Make API request
        endpoint = f"apikeys/{params.key_id}"
        await client.delete(endpoint)

        # Format success response
        response_data = {
            "KeyId": params.key_id,
            "Status": "Revoked",
            "Message": "API key has been permanently deleted and revoked",
            "Warning": "⚠️  This action is permanent. Any applications using this key will lose access immediately.",
            "NextSteps": [
                "Update applications to use a different API key if needed",
                "Document this revocation in your security logs",
                "Monitor for any authentication failures from affected applications"
            ]
        }

        return format_json_response(
            response_data,
            message="API key deleted successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg
