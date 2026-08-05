"""Gateway v1: all agent traffic flows through here - allowlist enforced."""
import json
import sys
import policy
import yaml
import approval
from pathlib import Path
import time
import audit
from collections import defaultdict, deque

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

gateway = FastMCP("agent-iam-gateway")

RATE_LIMIT = 10   # calls per agent
WINDOW_S = 60     # per rolling window
_call_log = defaultdict(deque)

def _rate_limited(agent_id: str) -> bool:
    now = time.time()
    q = _call_log[agent_id]
    while q and now - q[0] > WINDOW_S:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return True
    q.append(now)
    return False


# How to launch the downstream server we protect
CORP_TOOLS = StdioServerParameters(
    command=sys.executable,  # the current Python interpreter
    args=[str(Path(__file__).parent / "corp_tools.py")],
)

# v1 policy: a hardcoded allowlist. Everything else is denied.
# ALLOWED = {"lookup_employee", "read_document"}


async def _forward(tool_name: str, arguments: dict) -> str:
    """Open a connection to corp_tools, call one tool, return the result."""
    async with stdio_client(CORP_TOOLS) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result.content[0].text if result.content else "(no output)"


@gateway.tool()
async def list_available_tools(api_key: str) -> str:
    """List the tools your role permits."""
    agent = policy.authenticate(api_key)
    if agent is None:
        return "DENIED: unknown agent."
    roles = yaml.safe_load((Path(__file__).parent / "policies.yaml").read_text())["roles"]
    return json.dumps(roles.get(agent["role"], {}).get("allow", []))


@gateway.tool()
async def call_tool(api_key: str, tool_name: str, arguments: dict) -> str:
    """Call a corporate tool. Requires your agent API key."""
    agent = policy.authenticate(api_key)
    if agent is None:
        audit.log_event("unknown", "-", tool_name, arguments, "DENY", "unknown agent")
        return "DENIED: unknown agent."
    aid, role = agent["id"], agent["role"]

    if _rate_limited(aid):
        audit.log_event(aid, role, tool_name, arguments, "DENY", "rate limit")
        return "DENIED: rate limit exceeded."
    if not policy.authorize(role, tool_name):
        audit.log_event(aid, role, tool_name, arguments, "DENY", "not in role allowlist")
        return f"DENIED: role '{role}' is not permitted to use '{tool_name}'."
    reason = policy.check_constraints(tool_name, arguments)
    if reason:
        audit.log_event(aid, role, tool_name, arguments, "DENY", f"constraint: {reason}")
        return f"DENIED: constraint violation - {reason}."
    if policy.requires_approval(tool_name):
        if not await approval.request_approval(aid, tool_name, arguments):
            audit.log_event(aid, role, tool_name, arguments, "DENY", "operator denied/timeout")
            return "DENIED: not approved by operator (or timed out)."
        audit.log_event(aid, role, tool_name, arguments, "ALLOW", "operator approved")
    else:
        audit.log_event(aid, role, tool_name, arguments, "ALLOW", "policy")
    return await _forward(tool_name, arguments)

if __name__ == "__main__":
    gateway.run()