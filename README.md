# Method CRM MCP Server

A production-ready Model Context Protocol (MCP) server for Method CRM API integration. This server enables LLMs to interact with Method CRM data through well-designed tools for tables, files, users, events, and API key management.

## Features

- **20 Comprehensive Tools** covering all Method CRM operations
- **API Key Authentication** (fully implemented) with OAuth2 placeholders
- **Dual Transport Support**: stdio (local) and streamable HTTP (remote)
- **Rate Limiting & Retry Logic**: Automatic handling of API limits
- **Type-Safe**: Full Pydantic validation for all inputs
- **Actionable Errors**: Clear error messages with suggestions
- **Pagination Support**: Efficient handling of large datasets
- **Multiple Response Formats**: JSON and Markdown outputs

## Installation

### Prerequisites

- Python 3.10 or higher
- Method CRM account with API access
- API key (obtain from Method CRM dashboard)

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/method-crm-mcp.git
cd method-crm-mcp

# Install dependencies
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Configuration

### 1. Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Authentication

Edit `.env` and set your API key:

```bash
# Required: Method CRM API Key
METHOD_API_KEY=your_api_key_here

# Optional: Customize API base URL
METHOD_API_BASE_URL=https://rest.method.me/api/v1/

# Optional: Transport configuration
METHOD_TRANSPORT=stdio        # or 'http'
METHOD_HTTP_PORT=8000         # only used if TRANSPORT=http
```

### 3. Get Your API Key

1. Log in to your Method CRM account
2. Navigate to **Settings** → **API Settings**
3. Click **Create API Key** (requires Administrator role)
4. Name your key (e.g., "MCP Server")
5. Copy the generated key immediately (it won't be shown again)
6. Paste it into `.env` as `METHOD_API_KEY`

## Usage

### Running the Server

#### stdio Transport (Local Use)

Default mode for use with MCP clients like Claude Desktop:

```bash
python -m method_mcp.server
```

Or using the module directly:

```bash
python src/method_mcp/server.py
```

#### HTTP Transport (Remote Access)

For remote access or multiple clients:

```bash
# Set transport in .env
METHOD_TRANSPORT=http
METHOD_HTTP_PORT=8000

# Start server
python -m method_mcp.server
```

The server will listen on `http://localhost:8000`

### MCP Client Configuration

#### Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "method-crm": {
      "command": "python",
      "args": [
        "-m",
        "method_mcp.server"
      ],
      "cwd": "/absolute/path/to/method-crm-mcp",
      "env": {
        "METHOD_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

#### MCP Inspector (Testing)

Test tools using MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python src/method_mcp/server.py
```

## Available Tools

### Table Operations (5 tools)

| Tool | Description | Read-Only | Destructive |
|------|-------------|-----------|-------------|
| `method_tables_query` | Query records with filtering, pagination, aggregation | ✅ | ❌ |
| `method_tables_get` | Get specific record by ID with optional expansion | ✅ | ❌ |
| `method_tables_create` | Create new record in any table | ❌ | ❌ |
| `method_tables_update` | Update record fields (batch support: 50 records) | ❌ | ❌ |
| `method_tables_delete` | Delete record permanently | ❌ | ✅ |

**Example**: Query active customers
```json
{
  "table": "Customer",
  "filter": "Status eq 'Active'",
  "top": 50,
  "orderby": "CreatedDate desc",
  "response_format": "json"
}
```

**Example**: Create new inventory item
```json
{
  "table": "ItemInventory",
  "fields": {
    "Name": "New Product",
    "Sku": "SKU-001",
    "SalesDesc": "Product description",
    "SalesPrice": 99.99,
    "PurchaseCost": 80,
    "PurchaseDesc": "Purchase description",
    "IsActive": true,
    "IncomeAccount": "Sales of Product Income",
    "COGSAccount": "Cost of Goods Sold",
    "AssetAccount": "Inventory",
    "PurchaseTaxCode": "Tax on Purchases",
    "SalesTaxCode": "Tax on Sales",
    "IsUsedOnPurchaseTransaction": true,
    "IsUsedOnSalesTransaction": true,
    "IsTrackQtyOnHand": true,
    "TenantID": 1
  },
  "response_format": "json"
}
```
**Note**: Required fields vary by table. For `ItemInventory`:
- **Required**: `Sku` (must be unique), `COGSAccount`, `AssetAccount`, `TenantID`
- **Recommended**: `IncomeAccount`, tax codes, transaction flags
- Account fields must match existing QuickBooks account names exactly

### File Management (6 tools)

| Tool | Description | Read-Only | Destructive |
|------|-------------|-----------|-------------|
| `method_files_upload` | Upload file (max 50MB) with optional record linking | ❌ | ❌ |
| `method_files_list` | List files with filtering and pagination | ✅ | ❌ |
| `method_files_download` | Download file content (base64-encoded) | ✅ | ❌ |
| `method_files_get_url` | Generate temporary download URL (20-min expiry) | ✅ | ❌ |
| `method_files_update_link` | Update file link to different table/record | ❌ | ❌ |
| `method_files_delete` | Delete file permanently | ❌ | ✅ |

**Example**: Upload invoice PDF
```json
{
  "filename": "invoice-2024-01.pdf",
  "content": "<base64-encoded content>",
  "link_table": "Invoice",
  "link_record_id": "INV-12345",
  "description": "January 2024 invoice"
}
```

### User Information (1 tool)

| Tool | Description | Read-Only |
|------|-------------|-----------|
| `method_user_get_info` | Get current authenticated user information | ✅ |

### Event Automation (4 tools)

| Tool | Description | Read-Only | Destructive |
|------|-------------|-----------|-------------|
| `method_events_create_routine` | Create event-driven automation routine | ❌ | ❌ |
| `method_events_list_routines` | List all event routines with pagination | ✅ | ❌ |
| `method_events_get_routine` | Get specific routine details by ID | ✅ | ❌ |
| `method_events_delete_routine` | Delete event routine permanently | ❌ | ✅ |

**Example**: Send email on new customer
```json
{
  "name": "New Customer Welcome",
  "description": "Send welcome email to new customers",
  "trigger_config": {
    "event": "record_created",
    "table": "Customer"
  },
  "actions": [
    {
      "action": "send_email",
      "template": "welcome",
      "to_field": "Email"
    }
  ],
  "enabled": true
}
```

### API Key Management (4 tools)

| Tool | Description | Read-Only | Destructive | Admin Required |
|------|-------------|-----------|-------------|----------------|
| `method_apikeys_create` | Create new API key (returns key once) | ❌ | ❌ | ✅ |
| `method_apikeys_list` | List API keys (keys masked for security) | ✅ | ❌ | ❌ |
| `method_apikeys_update` | Update key metadata (name, permissions, status) | ❌ | ❌ | ✅ |
| `method_apikeys_delete` | Delete/revoke API key permanently | ❌ | ✅ | ✅ |

**Example**: Create production API key
```json
{
  "name": "Production Server",
  "description": "Main API integration key",
  "permissions": ["read:all", "write:all"]
}
```

## API Rate Limits

Method CRM enforces the following limits:

- **Per-minute**: 100 requests per account
- **Daily**: 5,000-25,000 requests (varies by license count)
- **File size**: 50MB per file
- **Storage**: 10GB total per account
- **Batch updates**: 50 related records maximum

The MCP server automatically handles rate limiting with:
- Exponential backoff retry logic
- Clear error messages with retry-after timing
- Actionable suggestions for rate limit errors

## Error Handling

All tools return actionable error messages with suggestions:

**Example error responses**:

```
Error: Rate limit exceeded (100 requests/minute or daily limit reached).
Retry-After: 45 seconds
Suggestion: Wait before making more requests. Method CRM limits: 100 req/min per account, 5,000-25,000 daily depending on licenses.
```

```
Error: Resource not found - Record 'CUST-999' not found in table 'Customer'
Suggestion: Verify that the table name, record ID, or file ID is correct. Use list/query tools to find the correct identifier.
```

```
Error: Permission denied - Your account doesn't have Admin role required for this operation
Suggestion: Your account doesn't have permission to perform this operation. Check that you have the required role (e.g., Admin for API key creation) or that the resource belongs to your account.
```

## Advanced Features

### OData Query Filtering

Use powerful OData-style filters for queries:

```
# Equality
"Status eq 'Active'"

# Comparison
"CreatedDate gt '2024-01-01'"
"Total ge 1000"

# Logical operators
"Status eq 'Active' and Total gt 500"
"Type eq 'Invoice' or Type eq 'Estimate'"

# String functions
"startswith(Name, 'John')"
"contains(Email, '@example.com')"
"endswith(Status, 'ed')"

# Null checks
"Email ne null"
```

### Aggregations

Perform aggregations directly in queries:

```
# Count records
"count()"

# Sum amounts
"sum(Amount)"

# Group by with aggregation
"groupby((Status),aggregate($count as Total))"

# Multiple aggregations
"sum(Amount),average(Total),count()"
```

### Pagination

All list/query tools support pagination:

```json
{
  "table": "Customer",
  "top": 100,
  "skip": 0
}
```

Responses include pagination metadata:

```json
{
  "total": 500,
  "count": 100,
  "offset": 0,
  "has_more": true,
  "next_offset": 100
}
```

### Response Formats

Choose between JSON (structured) and Markdown (human-readable):

```json
{
  "response_format": "json"    // or "markdown"
}
```

## Architecture

```
method-crm-mcp/
├── src/method_mcp/
│   ├── server.py           # FastMCP server initialization
│   ├── client.py           # HTTP client with retry logic
│   ├── auth.py             # Authentication (API Key + OAuth2 placeholders)
│   ├── models.py           # Pydantic models (20 tools)
│   ├── errors.py           # Error handling utilities
│   ├── utils.py            # Shared helpers (pagination, formatting)
│   └── tools/
│       ├── tables.py       # 5 table operation tools (CRUD)
│       ├── files.py        # 6 file management tools
│       ├── user.py         # 1 user info tool
│       ├── events.py       # 4 event automation tools (complete CRUD)
│       └── apikeys.py      # 4 API key management tools (complete CRUD)
├── tests/                  # Unit and integration tests
├── evaluations/            # Evaluation questions for testing
├── pyproject.toml          # Dependencies and project metadata
├── .env.example            # Environment configuration template
└── README.md               # This file
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src/method_mcp --cov-report=html
```

### Code Quality

```bash
# Type checking
mypy src/method_mcp

# Linting
ruff check src/method_mcp

# Formatting
black src/method_mcp
```

## Troubleshooting

### Authentication Errors

**Problem**: `Error: Authentication failed. Your API key or access token is invalid or expired.`

**Solutions**:
- Verify `METHOD_API_KEY` is set correctly in `.env`
- Check that the key hasn't been revoked in Method CRM dashboard
- Ensure no extra whitespace in the key value

### Rate Limiting

**Problem**: `Error: Rate limit exceeded (100 requests/minute)`

**Solutions**:
- Wait for the retry-after period (check error message)
- Reduce request frequency in your application
- Use pagination to reduce total requests
- Consider upgrading Method CRM license for higher limits

### File Upload Errors

**Problem**: `Error: File size exceeds 50MB limit`

**Solutions**:
- Compress files before uploading
- Split large files into smaller chunks
- Use external storage (S3, etc.) and store URLs in Method CRM

### Connection Errors

**Problem**: `Error: Unable to connect to Method API`

**Solutions**:
- Check internet connection
- Verify `METHOD_API_BASE_URL` is correct
- Check if Method CRM is experiencing downtime
- Verify firewall/proxy settings

## Security Best Practices

1. **API Key Storage**
   - Store in environment variables, never in code
   - Use `.env` file (never commit to version control)
   - Rotate keys periodically (every 90 days recommended)

2. **Access Control**
   - Use separate API keys for different environments (dev/staging/prod)
   - Revoke unused keys promptly
   - Monitor key usage via `method_apikeys_list`

3. **File Handling**
   - Validate file types before upload
   - Scan uploaded files for malware
   - Enforce file size limits in application logic

4. **Error Messages**
   - Don't expose sensitive information in logs
   - Use debug mode only in development

## OAuth2 Support (Coming Soon)

OAuth2 authentication is planned for a future release:

- **Authorization Code Flow**: User-based authentication
- **Client Credentials Flow**: Machine-to-machine with token refresh
- **Implicit Flow**: Browser-based SPAs

Placeholders are already in the codebase (`auth.py`).

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## Support

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: https://developer.method.me/
- **Method CRM Support**: https://help.method.me/

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.0 (2025-11-22)

**Initial Public Release**
- ✅ 20 fully implemented tools (complete API coverage)
- ✅ API Key authentication
- ✅ Dual transport support (stdio + HTTP)
- ✅ Rate limiting and retry logic
- ✅ Comprehensive error handling
- ✅ Pydantic validation for all inputs
- ✅ Pagination support with cursor-based navigation
- ✅ Multiple response formats (JSON/Markdown)
- ✅ File operations with multipart/form-data support
- ✅ Complete CRUD for tables, events, and API keys
- ⏳ OAuth2 support (placeholders added)

---

**Built with** ❤️ **using** [FastMCP](https://github.com/modelcontextprotocol/python-sdk) **and the** [Model Context Protocol](https://modelcontextprotocol.io)
