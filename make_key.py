"""Generate an API key and its hash. Run once per agent."""
import hashlib
import secrets

key = secrets.token_urlsafe(32)          # cryptographically random key
key_hash = hashlib.sha256(key.encode()).hexdigest()

print(f"API key (give to agent, save it - shown once): {key}")
print(f"SHA-256 hash (store in agents.yaml):           {key_hash}") 