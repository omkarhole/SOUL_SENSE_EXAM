import json
from api.utils.redaction import redact_data

data = {
    "user_id": 1234,
    "name": "Ayaan Shaikh",
    "email": "ayaansalman74@gmail.com",
    "phone_number": "+91 9876543210",
    "ip_address": "192.168.1.100",
    "preferences": {
        "newsletter": True
    },
    "emergency_contact": {
        "name": "Jane Doe",
        "phone": "555-123-4567"
    },
    "logs": [
        {"action": "login", "ip": "10.0.0.51"},
        {"action": "click", "ip_address": "10.0.0.51"}
    ]
}

print("====================================")
print("     ORIGINAL SENSITIVE DATA        ")
print("====================================")
print(json.dumps(data, indent=2))
print("\n")


# 1. Normal user (no PII privileges)
print("====================================")
print("  REDACTED FOR NORMAL APP USERS     ")
print("====================================")
redacted = redact_data(data, roles=["user", "patient"])
print(json.dumps(redacted, indent=2))
print("\n")

# 2. Compliance/Support (has 'pii_viewer' role)
print("====================================")
print("  UN-REDACTED FOR 'pii_viewer' ROLE ")
print("====================================")
viewer_data = redact_data(data, roles=["user", "pii_viewer"])
print(json.dumps(viewer_data, indent=2))

