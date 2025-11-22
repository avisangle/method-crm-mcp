"""
Method CRM MCP Server.

This package provides a Model Context Protocol (MCP) server for interacting
with the Method CRM API. It enables LLMs to create, retrieve, update, and
delete data from Method CRM accounts using well-designed tools.

Supported features:
- Table operations (query, get, update, delete)
- File management (upload, list, download, delete)
- User information retrieval
- Event-driven automation
- API key management

Authentication methods:
- API Key (fully implemented)
- OAuth2 (placeholder for future implementation)
"""

__version__ = "0.1.0"
__author__ = "Method CRM MCP Team"

from .server import mcp

__all__ = ["mcp"]
