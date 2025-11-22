"""
Event-driven automation tools for Method CRM MCP server.

This module provides tools for creating, listing, retrieving, and deleting
event routines that enable automated workflows and integrations.
"""

import json

from ..server import mcp
from ..models import (
    EventRoutineCreateInput,
    EventRoutineListInput,
    EventRoutineGetInput,
    EventRoutineDeleteInput,
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
    name="method_events_create_routine",
    annotations={
        "title": "Create Event-Driven Automation Routine",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def method_events_create_routine(params: EventRoutineCreateInput) -> str:
    """
    Create an event-driven automation routine in Method CRM.

    This tool creates automated workflows that trigger actions based on events
    like record creation, updates, or custom triggers. Event routines enable
    integration with external services and automated business processes.

    Args:
        params (EventRoutineCreateInput): Validated input parameters containing:
            - name (str): Name of the event routine
            - description (Optional[str]): Description of the routine
            - trigger_config (Dict): Trigger configuration (event type, conditions)
            - actions (List[Dict]): Actions to execute when triggered
            - enabled (bool): Whether routine is enabled (default: true)

    Returns:
        str: JSON formatted response with routine details

            Success:
            {
                "success": true,
                "message": "Event routine created successfully",
                "data": {
                    "RoutineId": "...",
                    "Name": "...",
                    "Description": "...",
                    "Enabled": bool,
                    "CreatedAt": "..."
                }
            }

    Examples:
        - Send email on new customer:
          params with name="New Customer Welcome", trigger_config={"event": "record_created", "table": "Customer"},
          actions=[{"action": "send_email", "template": "welcome", "to_field": "Email"}]

        - Update status on invoice paid:
          params with name="Mark Paid", trigger_config={"event": "field_updated", "table": "Invoice", "field": "PaymentStatus"},
          actions=[{"action": "update_record", "fields": {"Status": "Completed"}}]

        - Webhook notification:
          params with name="Notify External System", trigger_config={"event": "record_created", "table": "Order"},
          actions=[{"action": "webhook", "url": "https://api.example.com/notify", "method": "POST"}]

    Error Handling:
        - Validates trigger_config structure
        - Validates actions array
        - Requires appropriate permissions
        - Provides examples for common automation patterns
    """
    try:
        client = get_client()

        # Build payload
        payload = {
            "Name": params.name,
            "TriggerConfig": params.trigger_config,
            "Actions": params.actions,
            "Enabled": params.enabled,
        }

        if params.description:
            payload["Description"] = params.description

        # Make API request
        result = await client.post("eda/event-routines", json_data=payload)

        # Format response
        response_data = {
            "RoutineId": result.get("Id"),
            "Name": params.name,
            "Description": params.description,
            "TriggerConfig": params.trigger_config,
            "Actions": params.actions,
            "Enabled": params.enabled,
            "CreatedAt": result.get("CreatedDate"),
        }

        return format_json_response(
            response_data,
            message=f"Event routine '{params.name}' created successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_events_list_routines",
    annotations={
        "title": "List Event Automation Routines",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_events_list_routines(params: EventRoutineListInput) -> str:
    """
    List all event-driven automation routines in Method CRM.

    This tool retrieves all configured event routines with their trigger
    configurations and actions, supporting pagination.

    Args:
        params (EventRoutineListInput): Validated input parameters containing:
            - top (Optional[int]): Max routines to return (1-100, default: 20)
            - skip (Optional[int]): Routines to skip for pagination (default: 0)
            - response_format (ResponseFormat): 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted list of event routines

            Success (JSON):
            {
                "success": true,
                "data": {
                    "total": int,
                    "count": int,
                    "has_more": bool,
                    "routines": [
                        {
                            "Id": "...",
                            "Name": "...",
                            "Description": "...",
                            "TriggerConfig": {...},
                            "Actions": [...],
                            "Enabled": bool,
                            "CreatedDate": "...",
                            "LastTriggered": "..."
                        },
                        ...
                    ]
                }
            }

            Success (Markdown):
            # Event Routines (X of Y)

            ## Routine Name 1
            - **Description**: ...
            - **Enabled**: Yes/No
            - **Trigger**: ...
            - **Actions**: ...
            ...

    Examples:
        - List all routines: params with no filters
        - Paginate routines: params with top=50, skip=100
        - View in markdown: params with response_format="markdown"

    Error Handling:
        - Returns empty list if no routines found
        - Handles pagination correctly
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
        response = await client.get("eda/event-routines", params=query_params)

        # Extract routines and metadata
        routines = response.get("value", [])
        total = response.get("@odata.count", len(routines))

        # Format pagination info
        pagination = format_pagination_info(
            total=total,
            count=len(routines),
            offset=params.skip or 0,
            limit=params.top or 20,
        )

        # Format response based on requested format
        if params.response_format.value == "markdown":
            if not routines:
                return "# Event Routines\n\nNo event routines configured."

            routines_md = format_markdown_list(
                data=routines,
                title_field="Name",
                fields=["Id", "Description", "Enabled", "TriggerConfig", "Actions", "CreatedDate", "LastTriggered"],
                title=f"Event Routines ({pagination['count']} of {pagination['total']})"
            )

            footer = f"\n\n**Pagination**: Showing routines {params.skip or 0 + 1}-{params.skip or 0 + len(routines)} of {total}"
            if pagination["has_more"]:
                footer += f" | Next offset: {pagination['next_offset']}"

            return routines_md + footer
        else:
            # JSON format
            result = {
                **pagination,
                "routines": routines,
            }
            return format_json_response(result)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_events_get_routine",
    annotations={
        "title": "Get Event Routine Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_events_get_routine(params: EventRoutineGetInput) -> str:
    """
    Get detailed information about a specific event routine.

    This tool retrieves the complete configuration of an event routine, including
    trigger settings, actions, and execution history.

    Args:
        params (EventRoutineGetInput): Parameters containing:
            - routine_id: ID of the event routine to retrieve
            - response_format: 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted routine details

    Example Usage:
        Get routine details:
        {
            "routine_id": "routine-abc123",
            "response_format": "json"
        }

        View in markdown:
        {
            "routine_id": "routine-abc123",
            "response_format": "markdown"
        }

    Response Includes:
        - Routine ID and name
        - Description
        - Enabled status
        - Trigger configuration (event type, table, filters)
        - Action list (what happens when triggered)
        - Creation date and creator
        - Last triggered date
        - Execution statistics
        - Error logs (if any)

    Use Cases:
        - Debug automation issues
        - Review routine configuration
        - Verify trigger conditions
        - Check execution history
        - Audit automation workflows

    Error Handling:
        - Returns 404 if routine_id not found
        - Requires appropriate permissions
        - Handles malformed routine IDs
    """
    try:
        client = get_client()

        # Make API request
        endpoint = f"eda/event-routines/{params.routine_id}"
        result = await client.get(endpoint)

        # Format response based on requested format
        if params.response_format.value == "markdown":
            # Format as markdown
            md_output = f"# Event Routine: {result.get('Name', 'Unnamed')}\n\n"
            md_output += f"**ID**: {result.get('Id')}\n"
            md_output += f"**Status**: {'✅ Enabled' if result.get('Enabled') else '❌ Disabled'}\n"
            md_output += f"**Description**: {result.get('Description', 'No description')}\n\n"

            md_output += "## Trigger Configuration\n"
            trigger = result.get('TriggerConfig', {})
            md_output += f"- **Event Type**: {trigger.get('event')}\n"
            md_output += f"- **Table**: {trigger.get('table')}\n"
            if trigger.get('filters'):
                md_output += f"- **Filters**: {json.dumps(trigger.get('filters'), indent=2)}\n"
            md_output += "\n"

            md_output += "## Actions\n"
            actions = result.get('Actions', [])
            for i, action in enumerate(actions, 1):
                md_output += f"{i}. **{action.get('action')}**\n"
                md_output += f"   - Template: {action.get('template', 'N/A')}\n"
            md_output += "\n"

            md_output += "## Metadata\n"
            md_output += f"- **Created**: {result.get('CreatedDate')}\n"
            md_output += f"- **Created By**: {result.get('CreatedBy')}\n"
            md_output += f"- **Last Triggered**: {result.get('LastTriggered', 'Never')}\n"

            return md_output
        else:
            # JSON format
            return format_json_response(
                result,
                message="Event routine retrieved successfully"
            )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_events_delete_routine",
    annotations={
        "title": "Delete Event Routine",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_events_delete_routine(params: EventRoutineDeleteInput) -> str:
    """
    Delete an event-driven automation routine permanently.

    This tool permanently removes an event routine, preventing it from triggering
    any future actions. This action cannot be undone.

    **IMPORTANT**: This is a destructive operation. The routine will be immediately
    deactivated and removed. Any pending triggers will be cancelled.

    Args:
        params (EventRoutineDeleteInput): Parameters containing:
            - routine_id: ID of the event routine to delete

    Returns:
        str: JSON formatted confirmation message

    Example Usage:
        Delete a broken routine:
        {
            "routine_id": "routine-abc123"
        }

    Use Cases:
        - Remove broken or misconfigured automations
        - Clean up deprecated workflows
        - Prevent unwanted trigger actions
        - Decommission old integrations
        - Remove test/development routines from production

    Best Practices:
        - Review routine configuration before deleting (use get_routine first)
        - Document reason for deletion
        - Consider disabling instead of deleting for testing
        - Backup routine configuration if you might need it again
        - Notify stakeholders affected by the automation

    Error Handling:
        - Returns 404 if routine_id not found
        - Returns 403 if lacking permission to delete
        - Provides confirmation of successful deletion

    Notes:
        - This action is permanent and cannot be undone
        - All execution history for this routine will be preserved
        - Pending triggers will be cancelled
        - Consider disabling the routine first to test impact
    """
    try:
        client = get_client()

        # Make API request
        endpoint = f"eda/event-routines/{params.routine_id}"
        await client.delete(endpoint)

        # Format success response
        response_data = {
            "RoutineId": params.routine_id,
            "Status": "Deleted",
            "Message": "Event routine has been permanently deleted",
            "Warning": "⚠️  This action is permanent. The routine will no longer trigger any actions.",
            "NextSteps": [
                "Verify that dependent workflows are updated",
                "Document the reason for deletion",
                "Monitor for any unexpected behavior from removed automation"
            ]
        }

        return format_json_response(
            response_data,
            message="Event routine deleted successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg
