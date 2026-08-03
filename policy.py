"""AuthN + AuthZ decisions. The gateway asks; this module answers."""
import hashlib
import hmac
from pathlib import Path

import yaml

BASE = Path(__file__).parent


def _load(name: str) -> dict:
    return yaml.safe_load((BASE / name).read_text())


def authenticate(api_key: str) -> dict | None:
    """AuthN: who is this? Returns the agent record, or None if unknown."""
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    for agent in _load("agents.yaml")["agents"]:
        if hmac.compare_digest(agent["api_key_hash"], key_hash):
            return agent
    return None


def authorize(role: str, tool_name: str) -> bool:
    """AuthZ: is this role allowed to use this tool? Deny by default."""
    roles = _load("policies.yaml")["roles"]
    return tool_name in roles.get(role, {}).get("allow", [])