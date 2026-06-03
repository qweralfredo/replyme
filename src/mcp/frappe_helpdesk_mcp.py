import sys
import os
import requests
from typing import Any
from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("frappe-helpdesk")

# Frappe URL (internal docker network)
FRAPPE_URL = os.environ.get("FRAPPE_URL", "http://helpdesk_app:8000")
FRAPPE_USER = os.environ.get("FRAPPE_USER", "Administrator")
FRAPPE_PASS = os.environ.get("FRAPPE_PASS", "admin")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="create_hd_ticket",
            description="Create a Helpdesk Ticket in Frappe via REST API.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "Short subject or title of the ticket."
                    },
                    "description": {
                        "type": "string",
                        "description": "Full details or content of the ticket."
                    },
                    "raised_by": {
                        "type": "string",
                        "description": "Email address of the person who raised the ticket."
                    }
                },
                "required": ["subject", "description", "raised_by"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name != "create_hd_ticket":
        raise ValueError(f"Unknown tool: {name}")

    subject = arguments.get("subject")
    description = arguments.get("description")
    raised_by = arguments.get("raised_by")

    try:
        session = requests.Session()
        
        # 1. Login to Frappe to get session cookie
        login_url = f"{FRAPPE_URL}/api/method/login"
        login_data = {
            "usr": FRAPPE_USER,
            "pwd": FRAPPE_PASS
        }
        res = session.post(login_url, data=login_data)
        if res.status_code != 200:
            return [TextContent(type="text", text=f"Failed to authenticate with Frappe Helpdesk: {res.text}")]
        
        # 2. Create the ticket
        create_url = f"{FRAPPE_URL}/api/resource/HD Ticket"
        ticket_data = {
            "subject": subject,
            "description": description,
            "raised_by": raised_by,
            "status": "Open"
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        create_res = session.post(create_url, json=ticket_data, headers=headers)
        
        if create_res.status_code == 200:
            ticket_info = create_res.json().get("data", {})
            ticket_name = ticket_info.get("name", "Unknown ID")
            return [TextContent(type="text", text=f"Success! Created HD Ticket: {ticket_name}")]
        else:
            return [TextContent(type="text", text=f"Failed to create ticket. Status: {create_res.status_code}, Response: {create_res.text}")]
            
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing Frappe API call: {str(e)}")]

if __name__ == "__main__":
    import asyncio
    
    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
            
    asyncio.run(main())
