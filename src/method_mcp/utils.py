"""
Utility functions for Method CRM MCP server.

This module provides shared helper functions for:
- Pagination handling
- Response formatting (JSON/Markdown)
- Query building
- Field selection
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def format_pagination_info(
    total: Optional[int],
    count: int,
    offset: int,
    limit: int,
) -> Dict[str, Any]:
    """
    Format pagination information for responses.

    Args:
        total: Total number of records available (None if unknown)
        count: Number of records in current response
        offset: Current offset value
        limit: Maximum records per page

    Returns:
        Dict with pagination metadata including has_more and next_offset

    Note:
        When total is None (API doesn't provide it), has_more is determined
        by checking if we received a full page of results.
    """
    # If total is known, use it to determine has_more
    if total is not None:
        has_more = total > offset + count
    else:
        # If total is unknown, assume has_more if we got a full page
        has_more = count == limit

    next_offset = offset + count if has_more else None

    return {
        "total": total,
        "count": count,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "next_offset": next_offset,
    }


def format_json_response(
    data: Any,
    success: bool = True,
    message: Optional[str] = None,
) -> str:
    """
    Format data as JSON string for tool responses.

    Args:
        data: The data to format
        success: Whether the operation was successful
        message: Optional message to include

    Returns:
        str: Formatted JSON string
    """
    response = {"success": success}

    if message:
        response["message"] = message

    if isinstance(data, dict) and "error" in data:
        response["error"] = data["error"]
    else:
        response["data"] = data

    return json.dumps(response, indent=2, default=str)


def format_markdown_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> str:
    """
    Format data as a markdown table.

    Args:
        data: List of records to format
        columns: Optional list of columns to include (uses all keys if None)
        title: Optional title for the table

    Returns:
        str: Formatted markdown table
    """
    if not data:
        return "No records found."

    # Determine columns
    if not columns:
        columns = list(data[0].keys())

    lines = []

    # Add title if provided
    if title:
        lines.append(f"## {title}")
        lines.append("")

    # Add header
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    lines.append(header)
    lines.append(separator)

    # Add rows
    for record in data:
        row_values = []
        for col in columns:
            value = record.get(col, "")
            # Format value for markdown
            if value is None:
                value = ""
            elif isinstance(value, bool):
                value = "✓" if value else "✗"
            elif isinstance(value, (list, dict)):
                value = json.dumps(value)
            else:
                value = str(value)
            # Escape pipe characters
            value = value.replace("|", "\\|")
            row_values.append(value)

        row = "| " + " | ".join(row_values) + " |"
        lines.append(row)

    return "\n".join(lines)


def format_markdown_list(
    data: List[Dict[str, Any]],
    title_field: str = "name",
    fields: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> str:
    """
    Format data as a markdown list with sections.

    Args:
        data: List of records to format
        title_field: Field to use for section titles
        fields: Fields to include in each section
        title: Optional title for the list

    Returns:
        str: Formatted markdown list
    """
    if not data:
        return "No records found."

    lines = []

    # Add title if provided
    if title:
        lines.append(f"# {title}")
        lines.append("")

    # Add each record as a section
    for i, record in enumerate(data, 1):
        # Section title
        section_title = record.get(title_field, f"Record {i}")
        lines.append(f"## {section_title}")
        lines.append("")

        # Fields
        display_fields = fields if fields else [k for k in record.keys() if k != title_field]
        for field in display_fields:
            value = record.get(field)
            if value is not None:
                # Format value
                if isinstance(value, bool):
                    value = "Yes" if value else "No"
                elif isinstance(value, (list, dict)):
                    value = json.dumps(value, indent=2)
                elif isinstance(value, datetime):
                    value = value.isoformat()

                field_name = field.replace("_", " ").title()
                lines.append(f"- **{field_name}**: {value}")

        lines.append("")

    return "\n".join(lines)


def build_query_filter(filters: Dict[str, Any]) -> str:
    """
    Build Method API filter expression from dictionary.

    Converts a dictionary of filters into Method API OData-style filter syntax.

    Example:
        {"name": "John", "age__gt": 25} -> "name eq 'John' and age gt 25"

    Supported operators (use as suffixes):
        - (none): eq (equals)
        - __gt: greater than
        - __gte: greater than or equal
        - __lt: less than
        - __lte: less than or equal
        - __ne: not equal
        - __contains: contains substring
        - __startswith: starts with
        - __endswith: ends with

    Args:
        filters: Dictionary of field filters

    Returns:
        str: OData filter expression
    """
    if not filters:
        return ""

    expressions = []

    for key, value in filters.items():
        # Parse operator from key
        if "__" in key:
            field, op = key.rsplit("__", 1)
            op_map = {
                "gt": "gt",
                "gte": "ge",
                "lt": "lt",
                "lte": "le",
                "ne": "ne",
                "contains": "contains",
                "startswith": "startswith",
                "endswith": "endswith",
            }
            operator = op_map.get(op, "eq")
        else:
            field = key
            operator = "eq"

        # Format value based on type
        if value is None:
            expressions.append(f"{field} eq null")
        elif isinstance(value, bool):
            expressions.append(f"{field} eq {str(value).lower()}")
        elif isinstance(value, (int, float)):
            expressions.append(f"{field} {operator} {value}")
        elif isinstance(value, str):
            # String functions use different syntax
            if operator in ["contains", "startswith", "endswith"]:
                expressions.append(f"{operator}({field}, '{value}')")
            else:
                expressions.append(f"{field} {operator} '{value}'")

    return " and ".join(expressions)


def select_fields(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    fields: Optional[List[str]] = None,
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Select specific fields from data records.

    Args:
        data: Single record or list of records
        fields: List of fields to include (None = all fields)

    Returns:
        Filtered data with only selected fields
    """
    if fields is None:
        return data

    def filter_record(record: Dict[str, Any]) -> Dict[str, Any]:
        return {k: v for k, v in record.items() if k in fields}

    if isinstance(data, list):
        return [filter_record(record) for record in data]
    else:
        return filter_record(data)


def format_datetime(dt: Union[str, datetime, None]) -> Optional[str]:
    """
    Format datetime to human-readable string.

    Args:
        dt: Datetime string, datetime object, or None

    Returns:
        Formatted datetime string or None
    """
    if dt is None:
        return None

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except Exception:
            return dt

    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    return str(dt)


def parse_boolean(value: Any) -> bool:
    """
    Parse various boolean representations.

    Args:
        value: Value to parse as boolean

    Returns:
        bool: Parsed boolean value
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1", "on")

    return bool(value)


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        str: Truncated string
    """
    if len(s) <= max_length:
        return s

    return s[: max_length - len(suffix)] + suffix


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Safely get nested dictionary value using dot notation.

    Example:
        safe_get({"user": {"name": "John"}}, "user.name") -> "John"

    Args:
        data: Dictionary to query
        path: Dot-separated path (e.g., "user.name")
        default: Default value if path not found

    Returns:
        Value at path or default
    """
    keys = path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value
