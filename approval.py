"""File-based human approval queue. Gateway writes requests; operator decides."""
import asyncio
import json
import uuid
from pathlib import Path

PENDING = Path(__file__).parent / "approvals"
PENDING.mkdir(exist_ok=True)


async def request_approval(agent_id: str, tool_name: str, arguments: dict,
                           timeout_s: int = 60) -> bool:
    req_id = uuid.uuid4().hex[:8]
    req_file = PENDING / f"{req_id}.request.json"
    decision_file = PENDING / f"{req_id}.decision"
    req_file.write_text(json.dumps(
        {"id": req_id, "agent": agent_id, "tool": tool_name, "args": arguments},
        indent=2))
    try:
        for _ in range(timeout_s):
            if decision_file.exists():
                return decision_file.read_text().strip() == "approve"
            await asyncio.sleep(1)
        return False  # timeout -> deny. Fail safe, never fail open.
    finally:
        req_file.unlink(missing_ok=True)
        decision_file.unlink(missing_ok=True)