"""Operator console: review and decide pending approval requests."""
import json
from pathlib import Path

PENDING = Path(__file__).parent / "approvals"

requests = sorted(PENDING.glob("*.request.json"))
if not requests:
    print("No pending requests.")

for req_file in requests:
    req = json.loads(req_file.read_text())
    print(json.dumps(req, indent=2))
    answer = input("Approve? [y/N]: ").strip().lower()
    decision = "approve" if answer == "y" else "deny"
    (PENDING / f"{req['id']}.decision").write_text(decision)
    print(f"-> {decision}\n")