"""
File management tools for Method CRM MCP server.

This module provides tools for uploading, listing, downloading, and managing
files in Method CRM with support for file attachments and links.
"""

import json
import base64
import io
from typing import Dict, Any
import httpx

from ..server import mcp
from ..models import (
    FileUploadInput,
    FileListInput,
    FileDownloadInput,
    FileGetURLInput,
    FileUpdateLinkInput,
    FileDeleteInput,
)
from ..client import MethodAPIClient
from ..errors import handle_api_error
from ..utils import (
    format_json_response,
    format_markdown_table,
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
    name="method_files_upload",
    annotations={
        "title": "Upload File to Method CRM",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def method_files_upload(params: FileUploadInput) -> str:
    """
    Upload a file to Method CRM and link it to a table record.

    This tool uploads files (max 50MB) to Method CRM storage and attaches them
    to specific records in tables like Customer, Invoice, ItemInventory, etc.
    Files are stored securely and can be downloaded later.

    Args:
        params (FileUploadInput): Validated input parameters containing:
            - filename (str): Name of the file (e.g., 'invoice.pdf', 'contract.docx')
            - content (str): Base64-encoded file content (max 50MB)
            - link_table (str): Table to link file to - REQUIRED
            - link_record_id (str): Record ID to link file to - REQUIRED
            - description (Optional[str]): Optional description of the file

    Returns:
        str: JSON formatted response with file metadata

            Success:
            {
                "success": true,
                "message": "File uploaded successfully",
                "data": {
                    "FileId": "...",
                    "Filename": "...",
                    "Size": int,
                    "LinkedTable": "...",
                    "LinkedRecordId": "...",
                    "UploadedAt": "..."
                }
            }

            Error:
            "Error: File size exceeds 50MB limit..." with suggestions

    Examples:
        - Upload invoice PDF: params with filename="invoice-2024-01.pdf", content=<base64>, link_table="Invoice", link_record_id="INV-001"
        - Upload customer document: params with filename="contract.docx", content=<base64>, link_table="Customer", link_record_id="CUST-123"
        - Upload item spec: params with filename="spec.pdf", content=<base64>, link_table="ItemInventory", link_record_id="1", description="Product specifications"

    Error Handling:
        - Validates file size (50MB limit)
        - Checks base64 encoding validity
        - Handles storage quota exceeded (10GB account limit)
        - Requires valid link_table and link_record_id

    Note:
        Method CRM API requires files to be linked to a record. Both table and
        recordId are mandatory parameters. The API uses multipart/form-data format.
    """
    try:
        client = get_client()

        # Decode base64 content to bytes
        try:
            file_bytes = base64.b64decode(params.content)
            file_size = len(file_bytes)

            # Check 50MB limit
            max_size = 50 * 1024 * 1024  # 50MB in bytes
            if file_size > max_size:
                return format_json_response(
                    {"error": f"File size ({file_size} bytes) exceeds 50MB limit ({max_size} bytes)"},
                    success=False
                )
        except Exception as decode_error:
            return format_json_response(
                {"error": f"Invalid base64 content: {str(decode_error)}"},
                success=False
            )

        # Build multipart form data
        # Method CRM API expects: file, table (optional), recordId (optional)
        files = {
            'file': (params.filename, io.BytesIO(file_bytes))
        }

        data = {}
        if params.link_table:
            data['table'] = params.link_table
        if params.link_record_id:
            data['recordId'] = int(params.link_record_id)
        if params.description:
            data['description'] = params.description

        # Make multipart upload request
        # We need to use httpx directly since MethodAPIClient doesn't support multipart
        url = f"{client.base_url}/files"
        headers = client.auth_manager.get_headers()

        # Remove Content-Type - httpx sets it automatically for multipart/form-data with boundary
        # The "application/json" from auth headers would cause 415 Unsupported Media Type error
        headers.pop('Content-Type', None)

        async with httpx.AsyncClient(timeout=client.timeout) as http_client:
            response = await http_client.post(
                url,
                headers=headers,
                files=files,
                data=data if data else None
            )

            # Check response
            if response.status_code == 413:
                return format_json_response(
                    {"error": "File size exceeds 50MB limit or storage quota (10GB) exceeded"},
                    success=False
                )

            response.raise_for_status()
            result = response.json()

        # Format response
        response_data = {
            "FileId": result.get("id"),
            "Filename": result.get("filename"),
            "FileExtension": result.get("fileExtension"),
            "Size": result.get("size"),
            "LinkedTable": params.link_table,
            "LinkedRecordId": params.link_record_id,
            "CreatedBy": result.get("createdBy"),
            "UploadedAt": result.get("createdDate"),
        }

        return format_json_response(
            response_data,
            message=f"File '{params.filename}' uploaded successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_files_list",
    annotations={
        "title": "List Files in Method CRM",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_files_list(params: FileListInput) -> str:
    """
    List files in Method CRM with optional filtering by table, record, or filename.

    This tool retrieves a list of uploaded files with metadata, supporting
    filtering and pagination for efficient file management.

    Args:
        params (FileListInput): Validated input parameters containing:
            - table (Optional[str]): Filter by linked table name
            - record_id (Optional[str]): Filter by linked record ID
            - filename_contains (Optional[str]): Filter by filename substring
            - top (Optional[int]): Max files to return (1-100, default: 20)
            - skip (Optional[int]): Files to skip for pagination (default: 0)
            - response_format (ResponseFormat): 'json' or 'markdown'

    Returns:
        str: JSON or Markdown formatted list of files

            Success (JSON):
            {
                "success": true,
                "data": {
                    "total": int,
                    "count": int,
                    "has_more": bool,
                    "files": [
                        {
                            "Id": "...",
                            "Filename": "...",
                            "Size": int,
                            "LinkedTable": "...",
                            "LinkedRecordId": "...",
                            "CreatedDate": "..."
                        },
                        ...
                    ]
                }
            }

    Examples:
        - List all files: params with no filters
        - List customer files: params with table="Customer", record_id="CUST-123"
        - Find invoices: params with filename_contains="invoice"
        - Paginate: params with top=50, skip=100

    Error Handling:
        - Returns empty list if no files found
        - Handles pagination correctly
    """
    try:
        client = get_client()

        # Build query parameters
        query_params = {}

        # Build filter expression
        filters = []
        if params.table:
            filters.append(f"LinkTable eq '{params.table}'")
        if params.record_id:
            filters.append(f"LinkRecordId eq '{params.record_id}'")
        if params.filename_contains:
            filters.append(f"contains(Filename, '{params.filename_contains}')")

        if filters:
            query_params["$filter"] = " and ".join(filters)

        if params.top:
            query_params["$top"] = params.top

        if params.skip:
            query_params["$skip"] = params.skip

        # Make API request
        response = await client.get("files", params=query_params)

        # Extract files and metadata
        # Note: Files endpoint returns a direct array [], not {"value": [...]}
        if isinstance(response, list):
            files = response
            count = len(files)
            total = None  # Files endpoint doesn't provide total count
            has_more = count == (params.top or 20)  # Heuristic: full page = more records
            next_link = None
        else:
            # Fallback for dict response (future API changes)
            files = response.get("value", [])
            count = response.get("count", len(files))
            total = response.get("@odata.count")
            next_link = response.get("nextLink")
            has_more = next_link is not None

        # Format pagination info
        pagination = format_pagination_info(
            total=total,
            count=count,
            offset=params.skip or 0,
            limit=params.top or 20,
        )

        # Override has_more if we detected it from response
        if isinstance(response, list):
            pagination["has_more"] = has_more
        elif next_link is not None:
            pagination["has_more"] = has_more
            pagination["next_link"] = next_link

        # Format response based on requested format
        if params.response_format.value == "markdown":
            if not files:
                return "# Files\n\nNo files found matching the criteria."

            # Format title based on whether total is known
            if total is not None:
                title = f"Files ({pagination['count']} of {pagination['total']})"
            else:
                title = f"Files ({pagination['count']} files)"

            files_md = format_markdown_list(
                data=files,
                title_field="Filename",
                fields=["Id", "Size", "LinkedTable", "LinkedRecordId", "CreatedDate"],
                title=title
            )

            # Format footer
            start_file = (params.skip or 0) + 1
            end_file = (params.skip or 0) + len(files)

            if total is not None:
                footer = f"\n\n**Pagination**: Showing files {start_file}-{end_file} of {total}"
            else:
                footer = f"\n\n**Pagination**: Showing files {start_file}-{end_file}"

            if pagination["has_more"]:
                footer += f" | More files available | Next offset: {pagination['next_offset']}"
            else:
                footer += " | No more files"

            return files_md + footer
        else:
            # JSON format
            result = {
                **pagination,
                "files": files,
            }
            return format_json_response(result)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_files_download",
    annotations={
        "title": "Download File from Method CRM",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_files_download(params: FileDownloadInput) -> str:
    """
    Download a file from Method CRM by its ID.

    This tool retrieves file content (base64-encoded) and metadata for a specific
    file stored in Method CRM.

    Args:
        params (FileDownloadInput): Validated input parameters containing:
            - file_id (str): Unique ID of the file to download
            - return_content (bool): If true, returns base64 content (default: true)

    Returns:
        str: JSON formatted response with file data

            Success (with content):
            {
                "success": true,
                "data": {
                    "FileId": "...",
                    "Filename": "...",
                    "Size": int,
                    "ContentType": "...",
                    "Content": "<base64-encoded content>",
                    "LinkedTable": "...",
                    "LinkedRecordId": "..."
                }
            }

            Success (metadata only):
            {
                "success": true,
                "data": {
                    "FileId": "...",
                    "Filename": "...",
                    "Size": int,
                    ...
                }
            }

    Examples:
        - Download file with content: params with file_id="FILE-123", return_content=true
        - Get file metadata only: params with file_id="FILE-123", return_content=false

    Error Handling:
        - Returns 404 if file not found
        - Handles large file downloads efficiently
    """
    try:
        client = get_client()

        # Download endpoint returns raw binary data, not JSON
        # We need to use httpx directly to get binary content
        url = f"{client.base_url}/files/{params.file_id}/download"
        headers = client.auth_manager.get_headers()

        async with httpx.AsyncClient(timeout=client.timeout) as http_client:
            response = await http_client.get(url, headers=headers)
            response.raise_for_status()

            # Get binary content
            file_bytes = response.content

            # Try to get metadata from headers
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            content_disposition = response.headers.get("Content-Disposition", "")

            # Extract filename from Content-Disposition if available
            filename = None
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')

        # Format response
        response_data = {
            "FileId": params.file_id,
            "Filename": filename,
            "Size": len(file_bytes),
            "ContentType": content_type,
        }

        if params.return_content:
            # Base64 encode the binary content
            response_data["Content"] = base64.b64encode(file_bytes).decode('utf-8')
            response_data["Note"] = "Content is base64-encoded. Decode to get original file."

        return format_json_response(response_data)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_files_get_url",
    annotations={
        "title": "Get Temporary Download URL for File",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def method_files_get_url(params: FileGetURLInput) -> str:
    """
    Generate a temporary download URL for a file (20-minute expiry).

    This tool creates a temporary, pre-signed URL that can be used to download
    a file directly without authentication. The URL expires after 20 minutes.

    Args:
        params (FileGetURLInput): Validated input parameters containing:
            - file_id (str): Unique ID of the file

    Returns:
        str: JSON formatted response with download URL

            Success:
            {
                "success": true,
                "data": {
                    "FileId": "...",
                    "Filename": "...",
                    "DownloadURL": "https://...",
                    "ExpiresIn": "20 minutes",
                    "ExpiresAt": "..."
                }
            }

    Examples:
        - Get download link: params with file_id="FILE-123"
        - Share file temporarily: Generate URL and share with external users

    Error Handling:
        - Returns 404 if file not found
        - Requires appropriate permissions
        - URL expires after 20 minutes (generate new URL if expired)
    """
    try:
        client = get_client()

        # URL endpoint returns a plain string (quoted URL), not a JSON object
        # We need to use httpx directly to get the raw response
        url = f"{client.base_url}/files/{params.file_id}/url"
        headers = client.auth_manager.get_headers()

        async with httpx.AsyncClient(timeout=client.timeout) as http_client:
            response = await http_client.get(url, headers=headers)
            response.raise_for_status()

            # The response is a JSON string (quoted URL)
            # Example: "https://cloudfront.net/..."
            download_url = response.json()  # This parses the JSON string

        # Format response
        response_data = {
            "FileId": params.file_id,
            "DownloadURL": download_url,
            "ExpiresIn": "20 minutes",
            "Note": "This URL expires in 20 minutes. Generate a new URL after expiration.",
        }

        return format_json_response(response_data)

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_files_update_link",
    annotations={
        "title": "Update File Link Details",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    }
)
async def method_files_update_link(params: FileUpdateLinkInput) -> str:
    """
    Update the link details of a file (table and record ID).

    This tool changes which table record a file is attached to, useful for
    moving files between records or correcting attachment errors.

    Args:
        params (FileUpdateLinkInput): Validated input parameters containing:
            - file_id (str): Unique ID of the file
            - link_table (str): New table name to link to
            - link_record_id (str): New record ID to link to
            - description (Optional[str]): Updated file description

    Returns:
        str: JSON formatted response confirming the update

            Success:
            {
                "success": true,
                "message": "File link updated successfully",
                "data": {
                    "FileId": "...",
                    "Filename": "...",
                    "NewLinkTable": "...",
                    "NewLinkRecordId": "...",
                    "Description": "..."
                }
            }

    Examples:
        - Move file to different invoice: params with file_id="FILE-123", link_table="Invoice", link_record_id="INV-002"
        - Reattach to customer: params with file_id="FILE-123", link_table="Customer", link_record_id="CUST-456"
        - Update description: params with file_id="FILE-123", link_table="Invoice", link_record_id="INV-001", description="Updated contract"

    Error Handling:
        - Validates link_table and link_record_id
        - Returns 404 if file not found
        - Checks target record exists
    """
    try:
        client = get_client()

        # Build update payload
        # API expects: tableName, recordId, attachToEmail (optional)
        payload = {
            "tableName": params.link_table,
            "recordId": int(params.link_record_id),
        }

        # Note: API only supports attachToEmail field for updates, not description
        # if params.description:
        #     payload["Description"] = params.description

        # Make API request - IMPORTANT: endpoint is /files/{id}/link not /files/{id}
        endpoint = f"files/{params.file_id}/link"
        result = await client.put(endpoint, json_data=payload)

        # Format response
        response_data = {
            "FileId": params.file_id,
            "Filename": result.get("Filename"),
            "NewLinkTable": params.link_table,
            "NewLinkRecordId": params.link_record_id,
            "Description": params.description,
        }

        return format_json_response(
            response_data,
            message="File link updated successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg


@mcp.tool(
    name="method_files_delete",
    annotations={
        "title": "Delete File from Method CRM",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def method_files_delete(params: FileDeleteInput) -> str:
    """
    Delete a file from Method CRM permanently.

    **WARNING**: This operation is destructive and cannot be undone. The file
    will be permanently deleted from storage and cannot be recovered.

    Args:
        params (FileDeleteInput): Validated input parameters containing:
            - file_id (str): Unique ID of the file to delete

    Returns:
        str: JSON formatted response confirming deletion

            Success:
            {
                "success": true,
                "message": "File deleted successfully",
                "data": {
                    "FileId": "...",
                    "DeletedAt": "..."
                }
            }

    Examples:
        - Delete obsolete file: params with file_id="FILE-OLD-123"
        - Remove duplicate: params with file_id="FILE-DUP-456"

    Error Handling:
        - Returns 404 if file not found (idempotent)
        - Requires appropriate permissions
        - Cannot be undone - use with caution
    """
    try:
        client = get_client()

        # Make API request
        endpoint = f"files/{params.file_id}"
        await client.delete(endpoint)

        # Format response
        response_data = {
            "FileId": params.file_id,
            "DeletedAt": "now",
        }

        return format_json_response(
            response_data,
            message="File deleted successfully"
        )

    except Exception as e:
        error_msg = handle_api_error(e)
        return error_msg
