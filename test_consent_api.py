import requests
import json

BASE_URL = "http://localhost:8000"

def test_consent_endpoints():
    """Test consent API endpoints."""

    # Test 1: Check consent status for new user
    print("Test 1: Check consent status for new user")
    response = requests.get(f"{BASE_URL}/api/v1/consent/check/test_user_123")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Test 2: Track consent given
    print("Test 2: Track consent given")
    response = requests.post(
        f"{BASE_URL}/api/v1/consent/track",
        json={
            "anonymous_id": "test_user_123",
            "event_type": "consent_given",
            "consent_version": "1.0"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Test 3: Check consent status after giving consent
    print("Test 3: Check consent status after giving consent")
    response = requests.get(f"{BASE_URL}/api/v1/consent/check/test_user_123")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Test 4: Try analytics without consent (should be blocked)
    print("Test 4: Try analytics without consent (should be blocked)")
    response = requests.post(
        f"{BASE_URL}/api/v1/analytics/events",
        json={
            "anonymous_id": "test_user_no_consent",
            "event_type": "page_view",
            "event_name": "test_page",
            "event_data": {"page": "/test"}
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Test 5: Try analytics with consent (should work)
    print("Test 5: Try analytics with consent (should work)")
    response = requests.post(
        f"{BASE_URL}/api/v1/analytics/events",
        json={
            "anonymous_id": "test_user_123",
            "event_type": "page_view",
            "event_name": "test_page",
            "event_data": {"page": "/test"}
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Analytics event logged successfully")
    else:
        print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    test_consent_endpoints()