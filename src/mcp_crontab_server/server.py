"""MCP server for exploring, explaining, and managing crontab entries."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from typing import Annotated

from croniter import croniter
from fastmcp import FastMCP
from pydantic import Field

from mcp_crontab_server.cron_parser import explain_cron, validate_cron

mcp = FastMCP(
    "Crontab Explorer",
    instructions=(
        "This server lets you inspect, search, explain, validate, "
        "and modify the current user's crontab. Use explain_cron and "
        "next_runs to help users understand cron schedules."
    ),
)


def _read_crontab() -> str | None:
    """Read the current user's crontab. Returns None if empty."""
    result = subprocess.run(
        ["crontab", "-l"], capture_output=True, text=True
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return result.stdout


def _write_crontab(contents: str) -> str:
    """Write contents to the current user's crontab via `crontab -`."""
    result = subprocess.run(
        ["crontab", "-"],
        input=contents,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to write crontab: {result.stderr.strip()}")
    return "ok"


@mcp.tool()
def list_crontab() -> str:
    """List all crontab entries for the current user with line numbers."""
    raw = _read_crontab()
    if raw is None:
        return "No crontab entries found for the current user."

    lines = raw.splitlines()
    parts: list[str] = []
    entry_num = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            parts.append(line)
            continue
        entry_num += 1
        parts.append(f"[{entry_num}] {line}")

    header = f"Found {entry_num} active crontab entries:\n"
    return header + "\n".join(parts)


@mcp.tool()
def search_crontab(
    keyword: Annotated[str, Field(description="Text to search for in crontab entries")],
) -> str:
    """Search crontab entries containing a keyword (case-insensitive)."""
    raw = _read_crontab()
    if raw is None:
        return "No crontab entries found for the current user."

    keyword_lower = keyword.lower()
    matches = [
        line
        for line in raw.splitlines()
        if keyword_lower in line.lower() and line.strip() and not line.strip().startswith("#")
    ]

    if not matches:
        return f"No crontab entries matching '{keyword}'."

    return f"Found {len(matches)} matching entries:\n" + "\n".join(matches)


@mcp.tool()
def get_cron_logs(
    lines: Annotated[int, Field(description="Number of log lines to return", ge=1, le=200)] = 25,
) -> str:
    """Get recent cron execution logs from the system."""
    # Try journalctl first (systemd), fall back to syslog
    result = subprocess.run(
        ["journalctl", "-u", "cron", "-n", str(lines), "--no-pager", "-q"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    # Fallback: grep CRON from syslog
    try:
        result = subprocess.run(
            ["grep", "CRON", "/var/log/syslog"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            log_lines = result.stdout.strip().splitlines()
            return "\n".join(log_lines[-lines:])
    except FileNotFoundError:
        pass

    return "No cron logs found. The system may use a different logging mechanism."


@mcp.tool()
def explain_cron_expression(
    expression: Annotated[str, Field(description="Cron expression to explain, e.g. '*/15 9-17 * * 1-5'")],
) -> str:
    """Explain a cron expression in plain English. Supports 5-field cron and special strings like @daily."""
    try:
        return explain_cron(expression)
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
def next_runs(
    expression: Annotated[str, Field(description="Cron expression, e.g. '0 9 * * *'")],
    count: Annotated[int, Field(description="Number of upcoming runs to show", ge=1, le=50)] = 5,
) -> str:
    """Calculate the next N execution times for a cron expression."""
    valid, msg = validate_cron(expression)
    if not valid:
        return f"Invalid cron expression: {msg}"

    try:
        cron = croniter(expression, datetime.now())
        runs = [cron.get_next(datetime) for _ in range(count)]
        lines = [f"  {i+1}. {run.strftime('%Y-%m-%d %H:%M:%S %A')}" for i, run in enumerate(runs)]
        return f"Next {count} runs for '{expression}':\n" + "\n".join(lines)
    except (ValueError, KeyError) as e:
        return f"Error calculating next runs: {e}"


@mcp.tool()
def validate_cron_expression(
    expression: Annotated[str, Field(description="Cron expression to validate")],
) -> str:
    """Check if a cron expression is syntactically valid. Returns specific errors for invalid fields."""
    valid, msg = validate_cron(expression)
    if valid:
        try:
            description = explain_cron(expression)
            return f"Valid. Meaning: {description}"
        except ValueError:
            return "Valid cron expression."
    return f"Invalid: {msg}"


@mcp.tool()
def add_cron_entry(
    schedule: Annotated[str, Field(description="Cron schedule expression, e.g. '0 9 * * *'")],
    command: Annotated[str, Field(description="Command to run")],
) -> str:
    """Add a new entry to the current user's crontab."""
    valid, msg = validate_cron(schedule)
    if not valid:
        return f"Invalid schedule: {msg}"

    new_line = f"{schedule} {command}"
    raw = _read_crontab()
    if raw is None:
        contents = new_line + "\n"
    else:
        # Ensure trailing newline before appending
        contents = raw.rstrip("\n") + "\n" + new_line + "\n"

    try:
        _write_crontab(contents)
    except RuntimeError as e:
        return str(e)

    return f"Added crontab entry: {new_line}"


@mcp.tool()
def remove_cron_entry(
    pattern: Annotated[str, Field(description="Text pattern to match the entry to remove")],
) -> str:
    """Remove crontab entries matching a pattern. Shows what will be removed."""
    raw = _read_crontab()
    if raw is None:
        return "No crontab entries found."

    lines = raw.splitlines()
    pattern_lower = pattern.lower()
    kept: list[str] = []
    removed: list[str] = []

    for line in lines:
        if line.strip() and not line.strip().startswith("#") and pattern_lower in line.lower():
            removed.append(line)
        else:
            kept.append(line)

    if not removed:
        return f"No entries matching '{pattern}' found."

    try:
        _write_crontab("\n".join(kept) + "\n")
    except RuntimeError as e:
        return str(e)

    removed_str = "\n".join(f"  - {r}" for r in removed)
    return f"Removed {len(removed)} entries:\n{removed_str}"


def main() -> None:
    """Entry point for the MCP crontab server."""
    transport = "stdio"
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        if idx + 1 < len(sys.argv):
            transport = sys.argv[idx + 1]

    mcp.run(transport=transport)
