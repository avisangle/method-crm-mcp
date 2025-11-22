"""
Table operations tools for Method CRM MCP server.

This module provides tools for querying, retrieving, creating, updating, and deleting
records from Method CRM tables.
"""

import json
from typing import Dict, Any

from ..server import mcp
from ..models import (
    TableQueryInput,
    TableGetInput,
    TableCreateInput,
    TableUpdateInput,
    TableDeleteInput,
)
from ..client import MethodAPIClient
from ..errors import handle_api_error
from ..utils import (
    format_json_response,
    format_markdown_table,
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
    name="method_tables_query",
    annotations={
        "title": "Query Method CRM Table Records",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_tables_query(params: TableQueryInput) -> str:
    """
    Query records from a Method CRM table with filtering, pagination, and aggregation.

    This tool allows you to search and retrieve records from any Method CRM table
    (Customer, Invoice, Item, etc.) with powerful filtering, sorting, and pagination
    capabilities. It supports OData-style queries for complex filtering.

    Args:
        params (TableQueryInput): Validated input parameters containing:
            - table (str): Table name (e.g., 'Customer', 'Invoice', 'Item')
            - filter (Optional[str]): OData filter expression for querying
            - select (Optional[str]): Comma-separated fields to return
            - top (Optional[int]): Max records to return (1-100, default: 20)
            - skip (Optional[int]): Records to skip for pagination (default: 0)
            - orderby (Optional[str]): Field and direction for sorting
            - expand (Optional[str]): Related tables to expand
            - aggregate (Optional[str]): Aggregation expression (count, sum, avg, etc.)
            - response_format (ResponseFormat): 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted response containing:
            Success (JSON):
            {
                "success": true,
                "data": {
                    "total": int,          # Total matching records
                    "count": int,          # Records in this response
                    "offset": int,         # Current offset
                    "limit": int,          # Max per page
                    "has_more": bool,      # More records available
                    "next_offset": int,    # Offset for next page
                    "records": [...]       # List of records
                }
            }

            Error:
            "Error: <detailed error message with suggestions>"

    Examples:
        - Find active customers: params with table="Customer", filter="Status eq 'Active'"
        - Get recent invoices: params with table="Invoice", filter="CreatedDate gt '2024-01-01'", orderby="CreatedDate desc"
        - Count by status: params with table="Customer", aggregate="groupby((Status),aggregate($count as Total))"
        - Paginate results: params with table="Item", top=50, skip=100

    Error Handling:
        - Returns actionable error messages for invalid table names
        - Handles rate limiting with retry suggestions
        - Validates filter syntax and provides examples
    """
    try:
        client = get_client()

        # Build query parameters
        query_params = {}

        if params.filter:
            query_params["$filter"] = params.filter

        if params.select:
            query_params["$select"] = params.select

        if params.top:
            query_params["$top"] = params.top

        if params.skip:
            query_params["$skip"] = params.skip

        if params.orderby:
            query_params["$orderby"] = params.orderby

        if params.expand:
            query_params["$expand"] = params.expand

        if params.aggregate:
            query_params["$apply"] = params.aggregate

        # Make API request
        endpoint = f"tables/{params.table}"
        response = await client.get(endpoint, params=query_params)

        # Extract records and metadata
        records = response.get("value", [])

        # Method CRM API response includes:
        # - count: number of records in THIS response
        # - nextLink: URL for next page (if more records exist)
        # - value: array of records
        # Note: API does NOT provide total count across all pages
        count = response.get("count", len(records))
        next_link = response.get("nextLink")
        has_more = next_link is not None

        # Total is unknown - API doesn't provide it
        total = None

        # Format pagination info
        pagination = format_pagination_info(
            total=total,
            count=count,
            offset=params.skip or 0,
            limit=params.top or 10,  # API default is 10
        )

        # Override has_more from nextLink
        pagination["has_more"] = has_more
        pagination["next_link"] = next_link

        # Format response based on requested format
        if params.response_format.value == "markdown":
            if not records:
                return f"# Query Results: {params.table}\n\nNo records found matching the query."

            # Format title based on whether total is known
            if total is not None:
                title = f"Query Results: {params.table} ({pagination['count']} of {pagination['total']} records)"
            else:
                title = f"Query Results: {params.table} ({pagination['count']} records)"

            table_md = format_markdown_table(data=records, title=title)

            # Format footer
            start_record = (params.skip or 0) + 1
            end_record = (params.skip or 0) + len(records)

            if total is not None:
                footer = f"\n\n**Pagination**: Showing records {start_record}-{end_record} of {total}"
            else:
                footer = f"\n\n**Pagination**: Showing records {start_record}-{end_record}"

            if pagination["has_more"]:
                footer += f" | More records available | Next offset: {pagination['next_offset']}"
            else:
                footer += " | No more records"

            return table_md + footer
        else:
            # JSON format
            result = {
                **pagination,
                "records": records,
            }
            return format_json_response(result)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_tables_create",
    annotations={
        "title": "Create Method CRM Table Record",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def method_tables_create(params: TableCreateInput) -> str:
    """
    Create a new record in a Method CRM table.

    This tool allows you to create new records in any Method CRM table by
    providing the table name and field values.

    Args:
        params (TableCreateInput): Parameters for creating the record:
            - table: Name of the table (e.g., 'Customer', 'Invoice', 'ItemInventory')
            - fields: Dictionary of field names and values
            - related_records: Optional list of related records to create in batch
            - response_format: 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted response containing the created record details

    Example Usage:
        Create a new customer:
        {
            "table": "Customer",
            "fields": {
                "Name": "John Doe",
                "Email": "john@example.com",
                "Phone": "555-0123",
                "CompanyName": "Acme Corp"
            }
        }

        Create an inventory item:
        {
            "table": "ItemInventory",
            "fields": {
                "Name": "New Product",
                "Sku": "SKU-001",
                "SalesDesc": "Product description",
                "SalesPrice": 99.99,
                "COGSAccount": "Computer Equipment",
                "AssetAccount": "Inventory",
                "IsActive": true
            }
        }

    Notes:
        - Required fields vary by table - check Method CRM documentation
        - RecordId is auto-generated by Method CRM
        - Maximum 50 related records can be created in a single request
        - Some fields may have validation rules (email format, date format, etc.)
        - Custom fields follow naming pattern: 'CustomField_Name'
        - For ItemInventory: Sku, COGSAccount, and AssetAccount are required
        - Account fields must reference existing QuickBooks account names

    Error Handling:
        - Returns detailed error messages for validation failures
        - Indicates which fields are missing or invalid
        - Provides recovery suggestions
    """
    try:
        client = get_client()

        # Prepare payload
        payload = params.fields.copy()

        # Add related records if provided
        if params.related_records:
            payload["RelatedRecords"] = params.related_records

        # Make API request
        endpoint = f"tables/{params.table}"
        result = await client.post(endpoint, json_data=payload)

        # Format response
        if params.response_format.value == "markdown":
            # Create markdown table for the created record
            record = result if isinstance(result, dict) else {}
            table_md = format_markdown_table([record])
            return f"✅ **Record Created Successfully**\n\n{table_md}"
        else:
            return format_json_response(
                result,
                message="Record created successfully"
            )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_tables_get",
    annotations={
        "title": "Get Method CRM Table Record by ID",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_tables_get(params: TableGetInput) -> str:
    """
    Retrieve a specific record from a Method CRM table by its ID.

    This tool fetches complete details for a single record, with optional expansion
    of related records from other tables.

    Args:
        params (TableGetInput): Validated input parameters containing:
            - table (str): Table name (e.g., 'Customer', 'Invoice')
            - record_id (str): Unique ID of the record
            - expand (Optional[str]): Related tables to expand
            - select (Optional[str]): Fields to return
            - response_format (ResponseFormat): 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted response containing the record

            Success (JSON):
            {
                "success": true,
                "data": {
                    "RecordId": "...",
                    "Name": "...",
                    ...
                }
            }

            Error:
            "Error: Resource not found..." with suggestions

    Examples:
        - Get customer details: params with table="Customer", record_id="12345"
        - Get invoice with lines: params with table="Invoice", record_id="INV-001", expand="InvoiceLines"
        - Get specific fields: params with table="Item", record_id="ITEM-123", select="Name,Price,Quantity"

    Error Handling:
        - Returns 404 error with suggestions if record not found
        - Validates record_id format
        - Handles permission errors
    """
    try:
        client = get_client()

        # Build query parameters
        query_params = {}

        if params.expand:
            query_params["$expand"] = params.expand

        if params.select:
            query_params["$select"] = params.select

        # Make API request
        endpoint = f"tables/{params.table}/{params.record_id}"
        record = await client.get(endpoint, params=query_params)

        # Format response
        if params.response_format.value == "markdown":
            lines = [f"# {params.table} Record: {params.record_id}", ""]

            for key, value in record.items():
                if value is not None:
                    field_name = key.replace("_", " ").title()
                    if isinstance(value, (dict, list)):
                        value_str = json.dumps(value, indent=2)
                    else:
                        value_str = str(value)
                    lines.append(f"**{field_name}**: {value_str}")

            return "\n".join(lines)
        else:
            return format_json_response(record)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_tables_update",
    annotations={
        "title": "Update Method CRM Table Record",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def method_tables_update(params: TableUpdateInput) -> str:
    """
    Update a record in a Method CRM table with new field values.

    This tool updates existing record fields and optionally updates related records
    in a batch operation (max 50 related records per request).

    Args:
        params (TableUpdateInput): Validated input parameters containing:
            - table (str): Table name (e.g., 'Customer', 'Invoice')
            - record_id (str): Unique ID of the record to update
            - fields (Dict[str, Any]): Dictionary of field names and new values
            - related_records (Optional[List[Dict]]): Related records to update (max 50)

    Returns:
        str: JSON formatted response confirming the update

            Success:
            {
                "success": true,
                "message": "Record updated successfully",
                "data": {
                    "RecordId": "...",
                    "UpdatedFields": [...]
                }
            }

            Error:
            "Error: Validation failed..." with field-specific guidance

    Examples:
        - Update customer email: params with table="Customer", record_id="123", fields={"Email": "new@example.com"}
        - Update invoice status: params with table="Invoice", record_id="INV-001", fields={"Status": "Paid", "PaidDate": "2024-01-15"}
        - Batch update with lines: params with table="Invoice", record_id="INV-001", fields={...}, related_records=[{...}]

    Error Handling:
        - Validates field names and types
        - Returns specific errors for read-only fields
        - Handles concurrent update conflicts
        - Respects 50 related records limit
    """
    try:
        client = get_client()

        # Build update payload
        payload = params.fields.copy()

        if params.related_records:
            payload["RelatedRecords"] = params.related_records

        # Make API request
        endpoint = f"tables/{params.table}/{params.record_id}"
        result = await client.patch(endpoint, json_data=payload)

        # Format response
        response_data = {
            "RecordId": params.record_id,
            "Table": params.table,
            "UpdatedFields": list(params.fields.keys()),
            "Result": result,
        }

        return format_json_response(
            response_data,
            message="Record updated successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_tables_delete",
    annotations={
        "title": "Delete Method CRM Table Record",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_tables_delete(params: TableDeleteInput) -> str:
    """
    Delete a record from a Method CRM table.

    **WARNING**: This operation is destructive and cannot be undone. Use with caution.

    This tool permanently removes a record from the specified table. The record
    and its data will be deleted and cannot be recovered.

    Args:
        params (TableDeleteInput): Validated input parameters containing:
            - table (str): Table name (e.g., 'Customer', 'Invoice')
            - record_id (str): Unique ID of the record to delete

    Returns:
        str: JSON formatted response confirming the deletion

            Success:
            {
                "success": true,
                "message": "Record deleted successfully",
                "data": {
                    "RecordId": "...",
                    "Table": "..."
                }
            }

            Error:
            "Error: Resource not found..." or permission error

    Examples:
        - Delete draft invoice: params with table="Invoice", record_id="DRAFT-001"
        - Remove obsolete item: params with table="Item", record_id="OLD-123"

    Error Handling:
        - Returns 404 if record doesn't exist (idempotent)
        - Prevents deletion of records with dependencies
        - Requires appropriate permissions
        - Provides recovery suggestions if applicable
    """
    try:
        client = get_client()

        # Make API request
        endpoint = f"tables/{params.table}/{params.record_id}"
        await client.delete(endpoint)

        # Format response
        response_data = {
            "RecordId": params.record_id,
            "Table": params.table,
            "DeletedAt": "now",
        }

        return format_json_response(
            response_data,
            message="Record deleted successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg
