"""Tamper-evident audit log: one JSON line per decision, hash-chained."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).parent / "audit.jsonl"


def _last_line_hash() -> str:
    """Hash of the most recent log line (or a fixed 'genesis' value)."""
    if not LOG.exists() or not LOG.read_text().strip():
        return "0" * 16
    last = LOG.read_text().strip().splitlines()[-1]
    return hashlib.sha256(last.encode()).hexdigest()[:16]


def log_event(agent: str, role: str, tool: str, arguments: dict,
              decision: str, reason: str = "") -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent": agent,
        "role": role,
        "tool": tool,
        "args_hash": hashlib.sha256(
            json.dumps(arguments, sort_keys=True).encode()).hexdigest()[:16],
        "decision": decision,   # ALLOW / DENY
        "reason": reason,
        "prev": _last_line_hash(),
    }
    with LOG.open("a") as f:
        f.write(json.dumps(event) + "\n")


def verify_chain() -> bool:
    """Recompute the hash chain. False means the log was edited or a line removed."""
    if not LOG.exists():
        return True
    lines = LOG.read_text().strip().splitlines()
    expected = "0" * 16
    for line in lines:
        if json.loads(line)["prev"] != expected:
            return False
        expected = hashlib.sha256(line.encode()).hexdigest()[:16]
    return True