import asyncio
import os
import sys
import json

# Set PYTHONPATH
test_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(test_dir, "backend", "fastapi")
sys.path.insert(0, project_root)

def test_redaction():
    from api.utils.redaction import redact_data
    
    data = {
        "user": {
            "id": 1,
            "username": "tester",
            "email": "ayaan@example.com",
            "phone_number": "+1234567890",
            "metadata": {
                "ip_address": "127.0.0.1",
                "nested_email": "hidden@secret.com"
            }
        },
        "other": "content"
    }
    
    # 1. Non-admin view
    print("--- Redacted View (Non-Admin) ---")
    redacted = redact_data(data, ["user"])
    print(json.dumps(redacted, indent=2))
    
    # 2. Admin view
    print("\n--- Full View (Admin) ---")
    admin_view = redact_data(data, ["admin"])
    print(json.dumps(admin_view, indent=2))

if __name__ == "__main__":
    test_redaction()
