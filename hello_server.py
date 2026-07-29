from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hello")

@mcp.tool()
def greet(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    mcp.run()  # speaks MCP over stdin/stdout