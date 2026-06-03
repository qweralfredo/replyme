import asyncio
from typing import Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import structlog
import os
import json
from google import genai
from google.genai import types

logger = structlog.get_logger(__name__)

async def run_mcp_agent(email_json: dict, prompt: str, command: str):
    logger.info("Starting MCP Agent execution", command=command)
    parts = command.split(" ")
    cmd = parts[0]
    args = parts[1:]

    server_params = StdioServerParameters(
        command=cmd,
        args=args,
        env=os.environ.copy()
    )

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return "Error: GOOGLE_API_KEY not configured in environment."
        
    client = genai.Client(api_key=api_key)

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Fetch tools
                tools_response = await session.list_tools()
                
                # Convert MCP tools to Gemini tools format
                gemini_tools = []
                for t in tools_response.tools:
                    gemini_tools.append(types.Tool(
                        function_declarations=[types.FunctionDeclaration(
                            name=t.name,
                            description=t.description or "No description",
                            parameters=t.inputSchema
                        )]
                    ))

                # Start chat session
                chat = client.chats.create(model="gemini-2.5-flash", config=types.GenerateContentConfig(
                    tools=gemini_tools if gemini_tools else None,
                    temperature=0.0
                ))
                
                user_msg = f"Aqui estão os dados do email em JSON:\n{json.dumps(email_json)}\n\nInstrução do Usuário: {prompt}"
                
                response = chat.send_message(user_msg)
                
                # Agent loop
                for _ in range(5): # max steps
                    if response.function_calls:
                        for fc in response.function_calls:
                            logger.info("Calling MCP Tool", name=fc.name)
                            try:
                                # MCP expects a dict of args
                                tool_args = {k: v for k, v in fc.args.items()} if fc.args else {}
                                result = await session.call_tool(fc.name, arguments=tool_args)
                                tool_output = result.content[0].text if result.content else "No output"
                            except Exception as e:
                                tool_output = f"Error: {str(e)}"
                            
                            # send back to Gemini
                            response = chat.send_message(types.Part.from_function_response(
                                name=fc.name,
                                response={"result": tool_output}
                            ))
                    else:
                        break # Done
                        
                return response.text
    except Exception as e:
        logger.error("Error in MCP agent execution", error=str(e))
        return f"Error executing MCP Agent: {str(e)}"
