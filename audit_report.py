"""Summarize the audit log - a mini SOC report."""
import json
from collections import Counter

import audit

events = [json.loads(l) for l in open("audit.jsonl", encoding="utf-8")]

print(f"Total events: {len(events)}")
print(f"Chain integrity: {'OK' if audit.verify_chain() else '*** TAMPERED ***'}\n")

by_agent = Counter(e["agent"] for e in events)
denies = [e for e in events if e["decision"] == "DENY"]

print("Calls per agent:")
for agent, n in by_agent.most_common():
    agent_denies = sum(1 for e in denies if e["agent"] == agent)
    print(f"  {agent}: {n} calls, {agent_denies} denied")

print("\nTop denial reasons:")
for reason, n in Counter(e["reason"] for e in denies).most_common():
    print(f"  {n}x {reason}")