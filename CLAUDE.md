# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP Crontab Server — an MCP server for exploring, explaining, and managing crontab entries. Works with Claude Desktop, Claude Code, and any MCP client out of the box.

## Architecture

**Proper MCP server using FastMCP with stdio transport (default):**

```
src/mcp_crontab_server/
├── __init__.py         # Package version
├── __main__.py         # python -m support
├── server.py           # FastMCP server with 8 tools
└── cron_parser.py      # Cron expression → English translator + validator
```

**Entry point:** `mcp-crontab-server` (defined in `pyproject.toml [project.scripts]`)

**Tools (8):** `list_crontab`, `search_crontab`, `get_cron_logs`, `explain_cron_expression`, `next_runs`, `validate_cron_expression`, `add_cron_entry`, `remove_cron_entry`

**Key design decisions:**
- All tools return `str` (not dicts) — human-readable text for LLMs
- No `print()` to stdout — would corrupt stdio transport
- No shell injection — `subprocess.run()` with `shell=False` everywhere
- Cron explainer is from-scratch (no dependency), croniter used only for next-run calculation

## Running

```bash
# Install in development mode
pip install -e .

# Run server (stdio transport, default)
mcp-crontab-server

# Run with SSE transport
mcp-crontab-server --transport sse

# Test with MCP inspector
fastmcp dev src/mcp_crontab_server/server.py

# Run as module
python -m mcp_crontab_server
```

## Testing

No automated test suite. Test via MCP inspector or Claude Desktop:
```bash
fastmcp dev src/mcp_crontab_server/server.py
```

## Dependencies

Defined in `pyproject.toml`: `fastmcp>=2.0.0`, `croniter>=1.0.0`

## Platform Notes

- Linux/macOS: uses `crontab -l` and `crontab -` commands
- Log retrieval: tries `journalctl` first, falls back to grep `/var/log/syslog`
