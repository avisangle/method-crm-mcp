"""
Pydantic models for Method CRM MCP server.

This module defines all input and output models for the 15 MCP tools,
providing type safety and validation for API interactions.
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import json


# ====================
# Enums
# ====================

class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# ====================
# Tables Tools Models
# ====================

class TableQueryInput(BaseModel):
    """Input model for querying table records."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table: str = Field(
        ...,
        description="Name of the table to query (e.g., 'Customer', 'Invoice', 'Item')",
        min_length=1,
        max_length=100
    )

    filter: Optional[str] = Field(
        default=None,
        description=(
            "OData-style filter expression. Examples: "
            "\"Name eq 'John'\" | \"CreatedDate gt '2024-01-01'\" | "
            "\"Status eq 'Active' and Email ne null\". "
            "Operators: eq, ne, gt, ge, lt, le, and, or, not. "
            "Functions: startswith, endswith, contains"
        ),
        max_length=1000
    )

    select: Optional[str] = Field(
        default=None,
        description=(
            "Comma-separated list of fields to return (e.g., 'Name,Email,Status'). "
            "If omitted, all fields are returned"
        ),
        max_length=500
    )

    top: Optional[int] = Field(
        default=20,
        description="Maximum number of records to return (1-100)",
        ge=1,
        le=100
    )

    skip: Optional[int] = Field(
        default=0,
        description="Number of records to skip for pagination",
        ge=0
    )

    orderby: Optional[str] = Field(
        default=None,
        description=(
            "Field to sort by with optional direction. "
            "Examples: 'CreatedDate desc' | 'Name asc' | 'Status'"
        ),
        max_length=200
    )

    expand: Optional[str] = Field(
        default=None,
        description=(
            "Comma-separated list of related tables to expand "
            "(e.g., 'InvoiceLines,Payments')"
        ),
        max_length=200
    )

    aggregate: Optional[str] = Field(
        default=None,
        description=(
            "Aggregation expression. Examples: "
            "'count()' | 'sum(Amount)' | 'average(Total)' | "
            "'min(Date),max(Date)' | 'groupby((Status),aggregate($count as Total))'"
        ),
        max_length=500
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' for structured data or 'markdown' for human-readable"
    )


class TableGetInput(BaseModel):
    """Input model for getting a specific table record."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table: str = Field(
        ...,
        description="Name of the table (e.g., 'Customer', 'Invoice')",
        min_length=1,
        max_length=100
    )

    record_id: str = Field(
        ...,
        description="Unique ID of the record to retrieve",
        min_length=1,
        max_length=100
    )

    expand: Optional[str] = Field(
        default=None,
        description="Comma-separated list of related tables to expand",
        max_length=200
    )

    select: Optional[str] = Field(
        default=None,
        description="Comma-separated list of fields to return",
        max_length=500
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' or 'markdown'"
    )


class TableUpdateInput(BaseModel):
    """Input model for updating a table record."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table: str = Field(
        ...,
        description="Name of the table (e.g., 'Customer', 'Invoice')",
        min_length=1,
        max_length=100
    )

    record_id: str = Field(
        ...,
        description="Unique ID of the record to update",
        min_length=1,
        max_length=100
    )

    fields: Dict[str, Any] = Field(
        ...,
        description=(
            "Dictionary of field names and values to update. "
            "Example: {'Name': 'John Doe', 'Email': 'john@example.com', 'Status': 'Active'}"
        )
    )

    related_records: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "Optional list of related records to update in batch (max 50). "
            "Each record should have 'RecordId' and fields to update"
        ),
        max_length=50
    )


class TableCreateInput(BaseModel):
    """Input model for creating a new table record."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table: str = Field(
        ...,
        description="Name of the table (e.g., 'Customer', 'Invoice', 'ItemInventory')",
        min_length=1,
        max_length=100
    )

    fields: Dict[str, Any] = Field(
        ...,
        description=(
            "Dictionary of field names and values for the new record. "
            "Example: {'Name': 'John Doe', 'Email': 'john@example.com', 'Status': 'Active'}"
        )
    )

    related_records: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "Optional list of related records to create in batch (max 50). "
            "Each record should have the required fields for creation"
        ),
        max_length=50
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Response format: 'json' or 'markdown'"
    )


class TableDeleteInput(BaseModel):
    """Input model for deleting a table record."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table: str = Field(
        ...,
        description="Name of the table (e.g., 'Customer', 'Invoice')",
        min_length=1,
        max_length=100
    )

    record_id: str = Field(
        ...,
        description="Unique ID of the record to delete",
        min_length=1,
        max_length=100
    )


# ====================
# Files Tools Models
# ====================

class FileUploadInput(BaseModel):
    """Input model for uploading a file."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    filename: str = Field(
        ...,
        description="Name of the file to upload (e.g., 'invoice.pdf', 'contract.docx')",
        min_length=1,
        max_length=255
    )

    content: str = Field(
        ...,
        description=(
            "Base64-encoded file content. File size limit: 50MB. "
            "Use standard base64 encoding for binary files"
        )
    )

    link_table: str = Field(
        ...,
        description="Table name to link this file to (e.g., 'Customer', 'Invoice') - REQUIRED",
        min_length=1,
        max_length=100
    )

    link_record_id: str = Field(
        ...,
        description="Record ID to link this file to - REQUIRED",
        min_length=1,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        description="Optional description of the file",
        max_length=500
    )


class FileListInput(BaseModel):
    """Input model for listing files."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    table: Optional[str] = Field(
        default=None,
        description="Filter files by linked table name",
        max_length=100
    )

    record_id: Optional[str] = Field(
        default=None,
        description="Filter files by linked record ID",
        max_length=100
    )

    filename_contains: Optional[str] = Field(
        default=None,
        description="Filter files by filename substring",
        max_length=255
    )

    top: Optional[int] = Field(
        default=20,
        description="Maximum number of files to return (1-100)",
        ge=1,
        le=100
    )

    skip: Optional[int] = Field(
        default=0,
        description="Number of files to skip for pagination",
        ge=0
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' or 'markdown'"
    )


class FileDownloadInput(BaseModel):
    """Input model for downloading a file."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    file_id: str = Field(
        ...,
        description="Unique ID of the file to download",
        min_length=1,
        max_length=100
    )

    return_content: bool = Field(
        default=True,
        description=(
            "If true, returns base64-encoded content. "
            "If false, returns only file metadata"
        )
    )


class FileGetURLInput(BaseModel):
    """Input model for getting file download URL."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    file_id: str = Field(
        ...,
        description="Unique ID of the file",
        min_length=1,
        max_length=100
    )


class FileUpdateLinkInput(BaseModel):
    """Input model for updating file link details."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    file_id: str = Field(
        ...,
        description="Unique ID of the file",
        min_length=1,
        max_length=100
    )

    link_table: str = Field(
        ...,
        description="New table name to link this file to",
        min_length=1,
        max_length=100
    )

    link_record_id: str = Field(
        ...,
        description="New record ID to link this file to",
        min_length=1,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        description="Updated description of the file",
        max_length=500
    )


class FileDeleteInput(BaseModel):
    """Input model for deleting a file."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    file_id: str = Field(
        ...,
        description="Unique ID of the file to delete",
        min_length=1,
        max_length=100
    )


# ====================
# User Tools Models
# ====================

class UserInfoInput(BaseModel):
    """Input model for getting user information."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' or 'markdown'"
    )


# ====================
# Events Tools Models
# ====================

class EventRoutineCreateInput(BaseModel):
    """Input model for creating an event routine."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    name: str = Field(
        ...,
        description="Name of the event routine",
        min_length=1,
        max_length=200
    )

    description: Optional[str] = Field(
        default=None,
        description="Description of what this routine does",
        max_length=1000
    )

    trigger_config: Dict[str, Any] = Field(
        ...,
        description=(
            "Trigger configuration defining when the routine executes. "
            "Example: {'event': 'record_created', 'table': 'Customer'}"
        )
    )

    actions: List[Dict[str, Any]] = Field(
        ...,
        description=(
            "List of actions to execute when triggered. "
            "Example: [{'action': 'send_email', 'to': 'admin@example.com'}]"
        ),
        min_length=1
    )

    enabled: bool = Field(
        default=True,
        description="Whether the routine is enabled"
    )


class EventRoutineListInput(BaseModel):
    """Input model for listing event routines."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    top: Optional[int] = Field(
        default=20,
        description="Maximum number of routines to return (1-100)",
        ge=1,
        le=100
    )

    skip: Optional[int] = Field(
        default=0,
        description="Number of routines to skip for pagination",
        ge=0
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' or 'markdown'"
    )


# ====================
# API Keys Tools Models
# ====================

class APIKeyCreateInput(BaseModel):
    """Input model for creating an API key."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    name: str = Field(
        ...,
        description="Name for the API key (e.g., 'Production Server', 'Mobile App')",
        min_length=1,
        max_length=200
    )

    description: Optional[str] = Field(
        default=None,
        description="Description of what this key will be used for",
        max_length=1000
    )

    permissions: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of permissions for this key. "
            "If omitted, key inherits user's permissions"
        )
    )


class APIKeyListInput(BaseModel):
    """Input model for listing API keys."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    top: Optional[int] = Field(
        default=20,
        description="Maximum number of keys to return (1-100)",
        ge=1,
        le=100
    )

    skip: Optional[int] = Field(
        default=0,
        description="Number of keys to skip for pagination",
        ge=0
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' or 'markdown'"
    )


class APIKeyUpdateInput(BaseModel):
    """Input model for updating an API key."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    key_id: str = Field(
        ...,
        description="ID of the API key to update",
        min_length=1,
        max_length=100
    )

    name: Optional[str] = Field(
        default=None,
        description="New name for the API key",
        min_length=1,
        max_length=200
    )

    description: Optional[str] = Field(
        default=None,
        description="New description for the API key",
        max_length=1000
    )

    permissions: Optional[List[str]] = Field(
        default=None,
        description="Updated list of permissions for this key"
    )

    is_active: Optional[bool] = Field(
        default=None,
        description="Enable or disable the API key"
    )


class APIKeyDeleteInput(BaseModel):
    """Input model for deleting an API key."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    key_id: str = Field(
        ...,
        description="ID of the API key to delete/revoke",
        min_length=1,
        max_length=100
    )


class EventRoutineGetInput(BaseModel):
    """Input model for getting a specific event routine."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    routine_id: str = Field(
        ...,
        description="ID of the event routine to retrieve",
        min_length=1,
        max_length=100
    )

    response_format: ResponseFormat = Field(
        default=ResponseFormat.JSON,
        description="Output format: 'json' or 'markdown'"
    )


class EventRoutineDeleteInput(BaseModel):
    """Input model for deleting an event routine."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    routine_id: str = Field(
        ...,
        description="ID of the event routine to delete",
        min_length=1,
        max_length=100
    )


# ====================
# Response Models
# ====================

class PaginatedResponse(BaseModel):
    """Model for paginated responses."""

    total: int = Field(..., description="Total number of records available")
    count: int = Field(..., description="Number of records in this response")
    offset: int = Field(..., description="Current offset")
    limit: int = Field(..., description="Maximum records per page")
    has_more: bool = Field(..., description="Whether more records are available")
    next_offset: Optional[int] = Field(None, description="Offset for next page if has_more is true")
    data: List[Any] = Field(..., description="List of records")


class SuccessResponse(BaseModel):
    """Model for successful operation responses."""

    success: bool = Field(default=True, description="Whether operation succeeded")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Any] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Model for error responses."""

    success: bool = Field(default=False, description="Whether operation succeeded")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
