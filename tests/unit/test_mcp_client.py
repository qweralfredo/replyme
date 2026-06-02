import pytest
from src.services.mcp_client import MCPClientCore

@pytest.mark.asyncio
async def test_mcp_client_connection_failure():
    # If no server is provided or command is invalid, it should fail
    client = MCPClientCore(command="invalid_mcp_server_command_that_does_not_exist")
    with pytest.raises(Exception):
        async with client.connect():
            pass
