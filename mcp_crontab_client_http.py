#!/usr/bin/env python3
"""
MCP Crontab Explorer HTTP Client

This client connects to the MCP Crontab Explorer Server using HTTP.
It's designed to work with the mcp_crontab_server.py that uses
a custom HTTP implementation of the MCP protocol.
"""
import sys
import requests
import json
import socket
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich.panel import Panel
import time

# Server address
SERVER_HOST = "127.0.0.1"  # Use IP address instead of hostname
SERVER_PORT = 8000
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

console = Console()

def call_tool(tool_name, params=None):
    """
    Calls a tool on the MCP server using HTTP.
    
    Args:
        tool_name: The name of the tool to call
        params: A dictionary of parameters to pass to the tool
    
    Returns:
        The response from the server, or None on error
    """
    try:
        if params is None:
            params = {}
        
        url = f"{BASE_URL}/tools/{tool_name}"
        response = requests.post(url, json=params, timeout=10)
        
        if response.status_code == 200:
            if not response.text:
                console.print("[bold red]Error: Server returned empty response[/bold red]")
                return None
            try:
                return response.json()
            except json.JSONDecodeError:
                console.print(f"[bold red]Error: Invalid JSON response: {response.text}[/bold red]")
                return None
        else:
            console.print(f"[bold red]Error: Server returned status code {response.status_code}[/bold red]")
            console.print(f"Response: {response.text}")
            return None
    except requests.RequestException as e:
        console.print(f"[bold red]Request error: {e}[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        return None

def list_tools():
    """Lists all available tools on the server"""
    try:
        # First verify the server is running with a simple request
        if not check_server_running():
            console.print("[bold red]Server is not responding to basic requests[/bold red]")
            return None
            
        # Now try to get the tools
        print("Requesting tools list...")
        response = requests.get(f"{BASE_URL}/tools", timeout=2)
        print(f"Tools response status: {response.status_code}")
        
        if response.status_code == 200:
            if not response.text:
                console.print("[bold red]Error: Server returned empty response[/bold red]")
                return None
            try:
                tools = response.json()
                print(f"Successfully parsed tools: {len(tools)} found")
                return tools
            except json.JSONDecodeError:
                console.print(f"[bold red]Error: Invalid JSON response: {response.text}[/bold red]")
                return None
        else:
            console.print(f"[bold red]Error: Server returned status code {response.status_code}[/bold red]")
            return None
    except requests.exceptions.Timeout:
        console.print("[bold red]Request timed out - server might be busy[/bold red]")
        return None
    except requests.exceptions.ConnectionError:
        console.print("[bold red]Connection error - server not running[/bold red]")
        return None
    except requests.RequestException as e:
        console.print(f"[bold red]Request error: {e}[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        return None

def check_server_running():
    """Check if the server is running and accessible"""
    try:
        print("Checking if server is running...")
        # Try a direct socket connection first
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((SERVER_HOST, SERVER_PORT))
            if result != 0:
                print(f"Socket connection failed with error code {result}")
                return False
            print("Socket connection successful")
        
        # Now try a simple HTTP request with curl-like behavior
        try:
            print("Trying HTTP request with curl...")
            import subprocess
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", f"{BASE_URL}/"],
                capture_output=True,
                text=True,
                timeout=2
            )
            status_code = result.stdout.strip()
            print(f"Curl HTTP status: {status_code}")
            
            if status_code == "200":
                print("Server is running!")
                return True
            else:
                print(f"Server returned unexpected status code: {status_code}")
                return False
        except subprocess.SubprocessError as e:
            print(f"Curl request failed: {e}")
            
            # Fall back to requests if curl fails
            try:
                print("Falling back to requests...")
                response = requests.get(BASE_URL, timeout=1)
                print(f"HTTP response status: {response.status_code}")
                return response.status_code == 200
            except Exception as e:
                print(f"HTTP request failed: {e}")
                return False
    except Exception as e:
        print(f"Error checking server: {e}")
        return False

def display_header():
    """Display the application header."""
    console.print()
    header = Panel("MCP Crontab Explorer (HTTP Client)", style="bold blue", expand=False)
    console.print(header)
    console.print("A tool for monitoring crontab entries using the Model Control Protocol (MCP).\n")

def display_tools_table(tools):
    """Display a table of available tools."""
    table = Table(title="Available MCP Tools")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Description", style="green")
    
    for tool in tools:
        table.add_row(tool["name"], tool["description"])
    
    console.print(table)

def main():
    """Main function for the MCP Crontab Explorer client."""
    display_header()
    
    console.print(f"Connecting to MCP server at {BASE_URL}")
    
    # Check if server is running
    if not check_server_running():
        console.print("[bold red]Server is not running or not accessible.[/bold red]")
        console.print("Please start the server with: python scripts/mcp/mcp_crontab_server.py")
        console.print("Waiting for server to start...", end="")
        
        # Wait for up to 30 seconds for the server to start
        for i in range(15):
            console.print(".", end="")
            sys.stdout.flush()
            time.sleep(2)  # Wait longer between checks
            if check_server_running():
                console.print("\n[green]Server is now running![/green]")
                break
        else:
            console.print("\n[bold red]Timed out waiting for server. Please start it manually.[/bold red]")
            return 1
    
    # Check if server is available
    try:
        tools = list_tools()
        if tools is None:
            console.print("[bold red]Could not connect to server. Make sure it's running.[/bold red]")
            return 1
        
        console.print(f"[green]Connected to server. Found {len(tools)} available tools.[/green]")
        display_tools_table(tools)
    except Exception as e:
        console.print(f"[bold red]Error connecting to server: {e}[/bold red]")
        return 1
    
    # Main command loop
    while True:
        console.print("\n[bold]Available Commands:[/bold]")
        console.print("1. Show recent logs")
        console.print("2. Search crontab entries")
        console.print("3. Exit")

        choice = Prompt.ask("Enter command number", choices=["1", "2", "3"], default="1")

        if choice == "1":
            console.print("[yellow]Fetching recent logs...[/yellow]")
            logs = call_tool("show_scheduled_task_summary")
            if logs:
                console.print("[bold]Recent Logs:[/bold]")
                console.print(logs)
            else:
                console.print("[yellow]No logs found or error occurred.[/yellow]")

        elif choice == "2":
            search_term = Prompt.ask("[yellow]Enter search term[/yellow]")
            console.print(f"[yellow]Searching for crontab entries containing '{search_term}'...[/yellow]")
            results = call_tool("search_crontab_entries", {"search_term": search_term})
            if results:
                console.print("[bold]Search Results:[/bold]")
                console.print(results)
            else:
                console.print("[yellow]No results found or error occurred.[/yellow]")

        elif choice == "3":
            console.print("[bold green]Exiting MCP Crontab Explorer. Goodbye![/bold green]")
            break
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 