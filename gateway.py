"""Gateway v1: all agent traffic flows through here - allowlist enforced."""
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

gateway = FastMCP("agent-iam-gateway")

# How to launch the downstream server we protect
CORP_TOOLS = StdioServerParameters(
    command=sys.executable,  # the current Python interpreter
    args=[str(Path(__file__).parent / "corp_tools.py")],
)

# v1 policy: a hardcoded allowlist. Everything else is denied.
ALLOWED = {"lookup_employee", "read_document"}


async def _forward(tool_name: str, arguments: dict) -> str:
    """Open a connection to corp_tools, call one tool, return the result."""
    async with stdio_client(CORP_TOOLS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "(no output)"


@gateway.tool()
async def list_available_tools() -> str:
    """List the tools permitted through this gateway."""
    return json.dumps(sorted(ALLOWED))


@gateway.tool()
async def call_tool(tool_name: str, arguments: dict) -> str:
    """Call a corporate tool by name, e.g. call_tool("lookup_employee", {"name": "Jordan Smith"})."""
    if tool_name not in ALLOWED:
        return f"DENIED: '{tool_name}' is not permitted through this gateway."
    return await _forward(tool_name, arguments)


if __name__ == "__main__":
    gateway.run()