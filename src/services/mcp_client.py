import structlog
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = structlog.get_logger(__name__)

class MCPClientCore:
    def __init__(self, command: str, args: list[str] = None):
        self.command = command
        self.args = args or []
        self._session = None

    @asynccontextmanager
    async def connect(self):
        logger.info("Starting MCP server process", command=self.command)
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self._session = session
                    logger.info("MCP Session initialized successfully")
                    yield session
        except Exception as e:
            logger.error("Failed to initialize MCP Session", error=str(e))
            raise e
        finally:
            self._session = None
            logger.info("MCP Session closed")

    async def get_user_context(self, email: str) -> dict:
        if not self._session:
            raise RuntimeError("Not connected to MCP server")
        # Simulating a tool call
        logger.info("Calling get_user_context", email=email)
        # In a real scenario we'd do: result = await self._session.call_tool("get_user_context", {"email": email})
        return {"status": "premium_user", "tickets": 0}
