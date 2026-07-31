"""Mock corporate tools server - the systems our gateway will protect."""
import json
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("corp-tools")

DATA = Path(__file__).parent / "data"
SANDBOX = Path(__file__).parent / "sandbox"

DOCUMENTS = {
    "DOC-1": "Q2 Financial Summary: Revenue up 8%...",
    "DOC-2": "Onboarding Checklist: 1. Issue laptop 2. Create accounts...",
}


# ---- LOW RISK: read-only ----

@mcp.tool()
def lookup_employee(name: str) -> str:
    """Look up an employee's record by name."""
    employees = json.loads((DATA / "employees.json").read_text())
    for emp in employees:
        if emp["name"].lower() == name.lower():
            return json.dumps(emp)
    return f"No employee found matching '{name}'"


@mcp.tool()
def read_document(doc_id: str) -> str:
    """Read a company document by its ID (e.g. DOC-1)."""
    return DOCUMENTS.get(doc_id, f"Document '{doc_id}' not found")


# ---- MEDIUM RISK: sends something outbound ----

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email (mock - just records it)."""
    outbox = DATA / "outbox.json"
    sent = json.loads(outbox.read_text()) if outbox.exists() else []
    sent.append({"to": to, "subject": subject, "body": body})
    outbox.write_text(json.dumps(sent, indent=2))
    return f"Email sent to {to}: '{subject}'"


# ---- HIGH RISK: mutates or destroys ----

@mcp.tool()
def reset_password(username: str) -> str:
    """Reset a user's password (mock - updates the user store)."""
    users_file = DATA / "users.json"
    users = json.loads(users_file.read_text())
    for user in users:
        if user["username"] == username:
            user["password_last_reset"] = date.today().isoformat()
            users_file.write_text(json.dumps(users, indent=2))
            return f"Password reset for {username}. Temp password issued."
    return f"User '{username}' not found"


@mcp.tool()
def delete_file(path: str) -> str:
    """Delete a file by path."""
    target = Path(__file__).parent / path
    if target.is_file():
        target.unlink()
        return f"Deleted {path}"
    return f"File '{path}' not found"


if __name__ == "__main__":
    mcp.run()