# MCP Crontab Explorer

A terminal-based UI for exploring and monitoring crontab entries using the Model Context Protocol (MCP). This tool provides an intuitive interface for inspecting scheduled tasks, checking their status, and viewing recent logs without leaving the terminal environment. Built with a client-server architecture, it separates system access from presentation concerns, allowing for clean code organization and maintainable components.

## Features

- **Rich Terminal UI**: Beautiful tables and formatted output
- **Log Viewing**: See recent cron job execution logs
- **Search Functionality**: Find crontab entries containing specific terms

## Architecture

The MCP Crontab Explorer consists of two main components:

1. **Server (`mcp_crontab_server.py`)**: A custom HTTP server that implements the Model Context Protocol. It registers tools using the FastMCP library and exposes them via HTTP endpoints.

2. **Client (`mcp_crontab_client_http.py`)**: A rich terminal UI that communicates with the server using HTTP requests and displays the results using the Rich library for formatting.

This architecture demonstrates:
- Server-side MCP implementation with tool registration
- HTTP-based communication between components
- Clean separation of concerns between system access (server) and presentation (client)

## Installation

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Install Dependencies


pip install rich requests fastmcp

python mcp_crontab_server.py

python mcp_crontab_client_http.py

Once the client is running, you'll see a menu with the following options:

1. **List crontab entries**: Shows all cron jobs
2. **Show recent logs**: View the most recent cron job execution logs
3. **Search crontab entries**: Find entries containing a specific term
4. **Exit**: Close the explorer

### Example Output

        ╭────────────────────────────────────╮
        │ MCP Crontab Explorer (HTTP Client) │
        ╰────────────────────────────────────╯
        A tool for monitoring crontab entries using the Model Control Protocol (MCP).

        Connecting to MCP server at http://127.0.0.1:8000
        Checking if server is running...
        Socket connection successful
        Trying HTTP request with curl...
        Curl HTTP status: 200
        Server is running!
        Checking if server is running...
        Socket connection successful
        Trying HTTP request with curl...
        Curl HTTP status: 200
        Server is running!
        Requesting tools list...
        Tools response status: 200
        Successfully parsed tools: 3 found
        Connected to server. Found 3 available tools.

                                        Available MCP Tools                                  
        ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
        ┃ Tool Name                   ┃ Description                                           ┃
        ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
        │ show_scheduled_task_summary │ Show most recent related cron log output              │
        │ search_crontab_entries      │ Search for crontab entries containing a specific term │
        │ check_server_status         │ Check the status of the MCP server                    │
        └─────────────────────────────┴───────────────────────────────────────────────────────┘

        Available Commands:
            1. Show recent logs
            2. Search crontab entries
            3. Check server status
            4. Exit
            Enter command number [1/2/3/4] (1): 3
            Checking server status...
            JSON Response:
            {
            "status": "online",
            "server_name": "MCP Crontab Explorer Server",
            "version": "1.0.0",
            "tools_available": 3,
            "pid": 516632,
            "timestamp": "2025-03-24T17:00:04.066705"
            }

            Available Commands:
            1. Show recent logs
            2. Search crontab entries
            3. Check server status
            4. Exit
            Enter command number [1/2/3/4] (1): 4
            Exiting MCP Crontab Explorer. Goodbye!

## MCP Conformity

The Crontab Explorer implements the Model Context Protocol in the following ways:

- **Server-Side MCP**: Uses the FastMCP library to register tools with the `@mcp.tool()` decorator
- **Tool Discovery**: Implements the `/tools` endpoint that returns a list of available tools
- **Tool Execution**: Supports calling tools via HTTP POST requests to `/tools/{tool_name}`
- **Standard Response Format**: Returns tool results in a consistent JSON format

The client uses standard HTTP requests rather than an MCP-specific client library, making it compatible with any HTTP client while maintaining the core MCP patterns on the server side.

## Requirements

- fastmcp
- rich
- requests

