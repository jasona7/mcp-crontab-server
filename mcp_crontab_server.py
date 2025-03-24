#!/usr/bin/env python3
"""
MCP Crontab Explorer Server

This server implements the Model Context Protocol (MCP) to allow AI systems
to interact with crontab functionality.
"""
import subprocess
import sys
import datetime
import os
import socket
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from fastmcp import FastMCP
import time

# Initialize FastMCP server for tool registration
mcp = FastMCP("Crontab Explorer", log_level="DEBUG")

# Server configuration
HOST = "0.0.0.0"
PORT = 8000

# Add this function after initializing the mcp object
def get_registered_tools():
    """Get a list of registered tool names"""
    # This is a workaround since FastMCP doesn't expose tools directly
    # We need to look for functions decorated with @mcp.tool()
    tools = []
    
    # Debug output to help diagnose the issue
    print("\n=== TOOL DISCOVERY ===")
    print("Looking for registered tools...")
    
    # First try to find tools by examining function attributes
    for name, func in globals().items():
        if callable(func):
            print(f"Checking function: {name}")
            
            # Check if this is a tool function
            is_tool = False
            tool_attrs = []
            
            # Check for various MCP-related attributes
            for attr_name in dir(func):
                if attr_name.startswith('__mcp') or 'mcp' in attr_name.lower():
                    tool_attrs.append(attr_name)
                    is_tool = True
            
            if tool_attrs:
                print(f"  Found MCP-related attributes: {', '.join(tool_attrs)}")
            
            # Also check for known tool names
            if name in ['fetch__crontab_entries', 'fetch__crontab_entries_count', 
                       'show_scheduled_task_summary', 'check_server_status', 'search_crontab_entries']:
                print(f"  Recognized as known tool by name")
                is_tool = True
            
            if is_tool:
                tools.append(name)
                print(f"  ✓ Added tool: {name}")
    
    # If we still don't find any tools, use hardcoded list
    if not tools:
        print("\n⚠️ WARNING: No tools found via function attributes!")
        print("Falling back to hardcoded tool list")
        tools = [
            'fetch__crontab_entries',
            'fetch__crontab_entries_count',
            'show_scheduled_task_summary',
            'check_server_status',
            'search_crontab_entries'
        ]
        for tool in tools:
            print(f"  ✓ Added hardcoded tool: {tool}")
    
    print(f"\nFinal result: Found {len(tools)} tools: {tools}")
    print("=== END TOOL DISCOVERY ===\n")
    return tools

# Add this method to the FastMCP class
mcp.get_registered_tools = get_registered_tools

@mcp.tool()
def fetch__crontab_contents():
    """Fetch cron jobs for the app"""
    print(f"Tool call: fetch_crontab_contents at {datetime.datetime.now()}")
    try:
        command = "crontab -l"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            entries = result.stdout.splitlines()
            # Return structured JSON response
            return {
                "status": "success",
                "type": "crontab_entries",
                "count": len(entries),
                "entries": entries,
                "raw_data": result.stdout,
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "warning",
                "type": "crontab_entries",
                "count": 0,
                "message": "No crontab entries found or error occurred.",
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error in fetch_crontab_contents: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def show_scheduled_task_summary():
    """Show most recent related cron log output"""
    print(f"Tool call: show_scheduled_task_summary at {datetime.datetime.now()}")
    try:
        command = "tail -n 10 /var/log/syslog"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            # Return structured JSON response
            return {
                "status": "success",
                "type": "log_entries",
                "count": len(result.stdout.splitlines()),
                "data": result.stdout,
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "warning",
                "message": "No recent cron logs found or error occurred.",
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error in show_scheduled_task_summary: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def search_crontab_entries(search_term):
    """Search for crontab entries containing a specific term"""
    print(f"Tool call: search_crontab_entries with term '{search_term}' at {datetime.datetime.now()}")
    try:
        command = f"crontab -l | grep {search_term}"
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            entries = result.stdout.splitlines()
            # Return structured JSON response
            return {
                "status": "success",
                "type": "search_results",
                "query": search_term,
                "count": len(entries),
                "entries": entries,
                "raw_data": result.stdout,
                "timestamp": datetime.datetime.now().isoformat()
            }
        else:
            return {
                "status": "warning",
                "type": "search_results",
                "query": search_term,
                "count": 0,
                "message": f"No crontab entries found containing '{search_term}' or error occurred.",
                "timestamp": datetime.datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error in search_crontab_entries: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

@mcp.tool()
def check_server_status():
    """Check the status of the MCP server"""
    print(f"Tool call: check_server_status at {datetime.datetime.now()}")
    try:
        # Already returns a structured JSON object
        return {
            "status": "online",
            "server_name": "MCP Crontab Explorer Server",
            "version": "1.0.0",
            "tools_available": len(get_registered_tools()),
            "pid": os.getpid(),
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error in check_server_status: {str(e)}")
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "timestamp": datetime.datetime.now().isoformat()
        }

# Create a custom HTTP request handler for MCP
class MCPHTTPHandler(BaseHTTPRequestHandler):
    # Add server version and protocol headers
    server_version = "MCPServer/1.0"
    protocol_version = "HTTP/1.1"
    
    def log_message(self, format, *args):
        """Log messages to stdout"""
        print(f"{self.address_string()} - {format % args}")
    
    def _set_headers(self, content_type="application/json"):
        """Set response headers"""
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'close')
        self.send_header('Content-Length', '0')
        self.end_headers()
    
    def _send_json_response(self, data):
        """Send a JSON response with proper headers"""
        # Format the JSON with indentation for better readability
        response = json.dumps(data, indent=2)
        response_bytes = response.encode('utf-8')
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Connection', 'close')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        
        print(f"Sending JSON response:")
        print(json.dumps(data, indent=2))  # Pretty print the JSON in server logs
        self.wfile.write(response_bytes)
    
    def _handle_error(self, status_code, message):
        """Handle error responses"""
        error_data = {"error": message}
        error_json = json.dumps(error_data).encode('utf-8')
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Connection', 'close')
        self.send_header('Content-Length', str(len(error_json)))
        self.end_headers()
        
        self.wfile.write(error_json)
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"Received GET request: {self.path}")
        
        if self.path == "/tools":
            # List available tools
            print(f"MCP tool discovery request received at {datetime.datetime.now()}")
            tools_list = []
            
            # Get the list of registered tools
            registered_tools = get_registered_tools()
            
            for tool_name in registered_tools:
                # Get the function object if possible
                tool_func = globals().get(tool_name)
                
                # Get the description from the docstring if available
                description = "No description available"
                if tool_func and tool_func.__doc__:
                    description = tool_func.__doc__.strip()
                
                # Hardcoded descriptions as fallback
                if description == "No description available":
                    if tool_name == "fetch_crontab_entries":
                        description = "Fetch cron jobs for the  app"
                    elif tool_name == "fetch_crontab_entries_count":
                        description = "Fetch the count of cron jobs for the  app"
                    elif tool_name == "show_scheduled_task_summary":
                        description = "Show most recent  related cron log output"
                    elif tool_name == "check_server_status":
                        description = "Check the status of the MCP server"
                
                tools_list.append({
                    "name": tool_name,
                    "description": description
                })
            
            self._send_json_response(tools_list)
        else:
            # For any other path, just return a simple success message
            info = {
                "name": "MCP Crontab Explorer Server",
                "version": "1.0.0",
                "status": "online"
            }
            self._send_json_response(info)

    def do_POST(self):
        """Handle POST requests"""
        print(f"Received POST request: {self.path}")
        
        if self.path.startswith("/tools/"):
            tool_name = self.path.split("/")[-1]
            print(f"Tool request for: {tool_name}")
            
            # Check if tool exists
            registered_tools = get_registered_tools()
            if tool_name not in registered_tools:
                self._handle_error(404, f"Tool '{tool_name}' not found")
                return
            
            # Get request body
            content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = json.loads(post_data) if post_data else {}
            
            # Call the tool
            print(f"Calling tool: {tool_name} with params: {params}")
            try:
                # Get the tool function
                tool_func = globals().get(tool_name)
                if not tool_func:
                    self._handle_error(500, f"Tool function '{tool_name}' not found in globals")
                    return
                
                # Call the tool function
                result = tool_func(**params)
                print(f"Tool result: {result}")
                
                # Send the response
                self._send_json_response(result)
            except Exception as e:
                print(f"Error calling tool: {e}")
                self._handle_error(500, f"Error calling tool: {str(e)}")
        else:
            self._handle_error(404, "Invalid endpoint")

def check_port_in_use(host, port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def main():
    """Main function to start the MCP server"""
    print(f"Starting MCP Crontab Explorer Server v1.0.0...")
    print("This server implements the Model Context Protocol for crontab operations.")
    print("Compatible with Claude Desktop and other MCP clients.")
    print(f"Server PID: {os.getpid()}")
    
    # Check if port is already in use
    if check_port_in_use(HOST, PORT):
        print(f"WARNING: Port {PORT} is already in use. The server may not start correctly.")
        # Try to kill the process using the port
        try:
            print("Attempting to free the port...")
            if sys.platform.startswith('linux'):
                os.system(f"fuser -k {PORT}/tcp")
                print(f"Killed process using port {PORT}")
            else:
                print("Automatic port freeing only supported on Linux")
        except Exception as e:
            print(f"Error freeing port: {e}")
    
    print(f"Binding to {HOST}:{PORT}...")
    
    try:
        # Create and start HTTP server
        server = HTTPServer((HOST, PORT), MCPHTTPHandler)
        print(f"Server started at http://{HOST}:{PORT}")
        print("Press Ctrl+C to stop the server")
        
        # Start the server in a separate thread to avoid blocking
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Print a message every 10 seconds to show the server is still running
        try:
            while True:
                time.sleep(10)
                print(f"Server running at http://{HOST}:{PORT} (PID: {os.getpid()})")
        except KeyboardInterrupt:
            print("Server stopped by user")
            server.shutdown()
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
