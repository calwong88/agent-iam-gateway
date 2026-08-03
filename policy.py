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

def check_constraints(tool_name: str, arguments: dict) -> str | None:
    """Parameter-level least privilege. Returns a denial reason, or None if OK."""
    cons = _load("policies.yaml").get("constraints", {}).get(tool_name)
    if not cons:
        return None
    if "path_must_start_with" in cons:
        prefix = cons["path_must_start_with"]
        if not str(arguments.get("path", "")).startswith(prefix):
            return f"path must start with '{prefix}'"
    if "to_domain_allowlist" in cons:
        domain = str(arguments.get("to", "")).rsplit("@", 1)[-1]
        if domain not in cons["to_domain_allowlist"]:
            return f"recipient domain '{domain}' not in allowlist"
    return None


def requires_approval(tool_name: str) -> bool:
    return _load("policies.yaml").get("tools", {}).get(tool_name, {}).get("requires_approval", False)