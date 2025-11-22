# Quick Start Guide - Method CRM MCP Server

## Installation (2 minutes)

```bash
# 1. Clone and navigate to project
git clone https://github.com/YOUR_USERNAME/method-crm-mcp.git
cd method-crm-mcp

# 2. Install dependencies
pip install -e .

# 3. Configure environment
cp .env.example .env

# 4. Edit .env and add your API key
nano .env  # or your preferred editor
# Set: METHOD_API_KEY=your_api_key_here
```

## Get Your API Key (1 minute)

1. Log in to Method CRM: https://app.method.me/
2. Go to **Settings** → **API Settings**
3. Click **Create API Key** (requires Admin role)
4. Name it "MCP Server"
5. Copy the key immediately (shown only once!)
6. Paste into `.env` file

## Test the Server (1 minute)

```bash
# Test with MCP Inspector
npx @modelcontextprotocol/inspector python src/method_mcp/server.py

# Or test Python import
python3 -c "from method_mcp.server import mcp; print('✓ Server loads successfully')"
```

## Use with Claude Desktop (2 minutes)

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

**Important**: Replace `/absolute/path/to/method-crm-mcp` with actual path!

Restart Claude Desktop. You should see "method-crm" in available tools.

## Try Your First Query

Ask Claude:

```
List the first 10 customers from Method CRM
```

Claude will use `method_tables_query` to fetch customers!

## Common Commands

```bash
# Run server in stdio mode (default)
python src/method_mcp/server.py

# Run server in HTTP mode
METHOD_TRANSPORT=http METHOD_HTTP_PORT=8000 python src/method_mcp/server.py

# Test syntax
python3 -m py_compile src/method_mcp/*.py

# Check installed dependencies
pip list | grep -E 'fastmcp|pydantic|httpx'
```

## Available Tools (Quick Reference)

**Tables**: query, get, update, delete
**Files**: upload, list, download, get_url, update_link, delete
**User**: get_info
**Events**: create_routine, list_routines
**API Keys**: create, list

See README.md for detailed tool documentation.

## Troubleshooting

### "Authentication failed"
→ Check `METHOD_API_KEY` in `.env` matches your Method CRM key

### "Module not found: fastmcp"
→ Run `pip install -e .` to install dependencies

### "Permission denied" when creating API key
→ API key creation requires Administrator role

### Claude Desktop doesn't show tools
→ Check config path is absolute, restart Claude Desktop

## Next Steps

1. Read `README.md` for comprehensive documentation
2. Review `evaluations/method_crm_eval.xml` for example queries
3. Check `decisions.md` for architectural details
4. Try uploading a file with `method_files_upload`

## Support

- 📖 Full docs: See `README.md`
- 🐛 Report bugs: See `bug.md`
- 📝 Progress: See `progress.md`
- 🎯 Architecture: See `decisions.md`

---

**You're ready to use Method CRM with Claude!** 🚀
