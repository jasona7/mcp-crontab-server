# MCP Crontab Server

An MCP server for exploring, explaining, and managing crontab entries. Works with Claude Desktop, Claude Code, and any MCP client.

**Standout features:** Explain cron expressions in plain English and calculate upcoming execution times — no more guessing what `*/15 9-17 * * 1-5` means.

## Quick Start

### Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "crontab": {
      "command": "uvx",
      "args": ["mcp-crontab-server"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add crontab -- uvx mcp-crontab-server
```

### Install from source

```bash
git clone https://github.com/jalloway/mcp-crontab-server.git
cd mcp-crontab-server
pip install -e .
mcp-crontab-server
```

## Tools

| Tool | Description |
|---|---|
| `list_crontab` | List all crontab entries for the current user |
| `search_crontab` | Search entries by keyword (case-insensitive) |
| `get_cron_logs` | Recent cron execution logs (journalctl / syslog) |
| `explain_cron_expression` | Explain a cron expression in plain English |
| `next_runs` | Calculate the next N execution times |
| `validate_cron_expression` | Check if an expression is syntactically valid |
| `add_cron_entry` | Add a new entry to the user's crontab |
| `remove_cron_entry` | Remove entries matching a pattern |

## Example Conversations

**"What does this cron expression mean?"**

> `explain_cron_expression("*/15 9-17 * * 1-5")`
>
> Every 15 minutes, from 9:00 AM through 5:59 PM, Monday through Friday

**"When will this job run next?"**

> `next_runs("0 2 * * 0", count=3)`
>
> Next 3 runs for '0 2 * * 0':
>   1. 2026-03-01 02:00:00 Sunday
>   2. 2026-03-08 02:00:00 Sunday
>   3. 2026-03-15 02:00:00 Sunday

**"Is this valid?"**

> `validate_cron_expression("60 * * * *")`
>
> Invalid: Value 60 out of range (0-59) in minute field

## Development

```bash
pip install -e .

# Run with MCP inspector
fastmcp dev src/mcp_crontab_server/server.py

# Run directly (stdio transport, default)
mcp-crontab-server

# Run with SSE transport
mcp-crontab-server --transport sse
```

## Requirements

- Python 3.10+
- Linux/macOS (uses `crontab` command)
- `fastmcp>=2.0.0`, `croniter>=1.0.0`
