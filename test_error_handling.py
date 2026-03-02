#!/usr/bin/env python
"""
Interactive test script for standardized error responses.
Run this to see the error responses in action.
"""

import sys
import json
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from backend.fastapi.api.main import app

def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_response(response, description):
    print(f"\n{description}")
    print(f"  Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"  Response Body:")
        print(json.dumps(data, indent=4))
        
        # Verify structure
        checks = [
            ("Has 'success' field", "success" in data),
            ("success is False", data.get("success") is False),
            ("Has 'error' field", "error" in data),
            ("Has 'error.code'", "code" in data.get("error", {})),
            ("Has 'error.message'", "message" in data.get("error", {})),
            ("Has 'error.request_id'", "request_id" in data.get("error", {})),
        ]
        
        print("\n  Structure Validation:")
        all_passed = True
        for check_name, result in checks:
            status = "[OK]" if result else "[FAIL]"
            print(f"    {status} {check_name}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n  ✅ All structure checks passed!")
        else:
            print("\n  ❌ Some checks failed!")
            
    except Exception as e:
        print(f"  Error parsing response: {e}")
        print(f"  Raw response: {response.text[:200]}")

def main():
    client = TestClient(app)
    
    print_header("Testing Standardized API Error Responses")
    
    # Test 1: Validation Error (422)
    print_header("Test 1: Validation Error (POST /api/v1/auth/register)")
    response = client.post(
        "/api/v1/auth/register",
        json={},  # Missing required fields
        headers={"Host": "localhost"}
    )
    print_response(response, "Empty registration body triggers validation error:")
    
    # Test 2: Not Found Error (404)
    print_header("Test 2: Not Found Error (GET /api/v1/questions/categories/99999)")
    response = client.get(
        "/api/v1/questions/categories/99999",
        headers={"Host": "localhost"}
    )
    print_response(response, "Non-existent category triggers not found:")
    
    # Test 3: Business Logic Validation (422)
    print_header("Test 3: Business Logic Error (GET /api/v1/questions/by-age/5)")
    response = client.get(
        "/api/v1/questions/by-age/5",
        headers={"Host": "localhost"}
    )
    print_response(response, "Invalid age (5) triggers validation error:")
    
    # Test 4: Authentication Error (401)
    print_header("Test 4: Authentication Error (GET /api/v1/users/me)")
    response = client.get(
        "/api/v1/users/me",
        headers={"Host": "localhost"}
    )
    print_response(response, "Missing auth token triggers authentication error:")
    
    print_header("Summary")
    print("""
All error responses now follow the standardized format:

{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": [...],          // Optional
        "request_id": "req-uuid"   // For debugging
    }
}

Frontend can reliably use error.code for translations and error handling!
""")

if __name__ == "__main__":
    main()
