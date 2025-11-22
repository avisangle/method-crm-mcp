"""
Main MCP server for Method CRM.

This module initializes the FastMCP server and registers all tools.
It supports both stdio and streamable HTTP transports.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("method_mcp")

# Import all tool modules to register tools AFTER mcp is created
# These imports will register tools with the @mcp.tool decorator
# Import must happen at module level for tools to be registered
import method_mcp.tools.tables
import method_mcp.tools.files
import method_mcp.tools.user
import method_mcp.tools.events
import method_mcp.tools.apikeys


def main():
    """
    Main entry point for the MCP server.

    Reads transport configuration from environment and starts the server.
    """
    # Get transport configuration from environment
    transport = os.getenv("METHOD_TRANSPORT", "stdio").lower()
    port = int(os.getenv("METHOD_HTTP_PORT", "8000"))

    # Print startup information to stderr (not visible in MCP protocol)
    debug = os.getenv("METHOD_DEBUG", "false").lower() == "true"
    if debug:
        print(f"[Method MCP] Starting server with transport: {transport}", file=sys.stderr)
        if transport == "http":
            print(f"[Method MCP] HTTP server will listen on port: {port}", file=sys.stderr)

    # Start server with appropriate transport
    if transport == "http":
        mcp.run(transport="streamable_http", port=port)
    else:
        # Default to stdio
        mcp.run()


# Support both direct execution and module execution
if __name__ == "__main__":
    main()
elif __name__ == "method_mcp.server":
    # When imported as module, tools are already registered
    pass
