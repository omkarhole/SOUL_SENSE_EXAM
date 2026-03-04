import os
import sys

# Ensure this file runs in the correct path context to absolute imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from unittest.mock import patch
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta, timezone

from api.main import app
from api.config import get_settings_instance

settings = get_settings_instance()
client = TestClient(app)

def create_token(username: str, is_admin: bool):
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {
        "sub": username,
        "is_admin": is_admin,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.jwt_algorithm)
    return encoded_jwt

# Create a mock User object
class MockUser:
    def __init__(self, username, is_admin):
        self.id = 1
        self.username = username
        self.is_admin = is_admin

# Mock the database execute/scalar_one_or_none
class MockResult:
    def __init__(self, user):
        self.user = user
    def scalar_one_or_none(self):
        return self.user

class MockDB:
    def __init__(self, user):
        self.user = user
    async def execute(self, stmt):
        return MockResult(self.user)

async def mock_get_db(request):
    yield getattr(request.state, 'mock_db', MockDB(None))

print("\n========== RBAC ENFORCEMENT TESTS ==========\n")

# Test 1: Missing Token
response = client.get("/api/v1/users/me")
print("[TEST: Missing Token]")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}\n")

# Let's hit a protected route, patching the DB locally
with patch('api.middleware.rbac_middleware.get_db', side_effect=mock_get_db):
    
    # Test 2: Valid Admin Token
    token = create_token("admin_user", True)
    
    # Simple middleware workaround for testclient testing
    @app.middleware("http")
    async def inject_mock_db_admin(request, call_next):
        if hasattr(request.state, 'mock_db'):
            pass # already injected
        # In reality we just simulate DB response inside get_db patch instead
        request.state.mock_db = MockDB(MockUser("admin_user", True))
        return await call_next(request)
        
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print("[TEST: Valid Admin Token (DB is_admin: True, Token is_admin: True)]")
    # if it's not 401 or 403, our RBAC middleware let it through
    status_label = "Proceeds Normally" if response.status_code not in [401, 403] else f"Blocked ({response.status_code})"
    print(f"Middleware Status: {status_label}")
    print(f"Actual Response Code: {response.status_code}\n")

    # Test 3: Tampered Token (Client claims admin, DB says normal user)
    token = create_token("attacker", True)
    
    # re-patch mock db behavior
    async def mock_get_db_attacker(request):
        yield MockDB(MockUser("attacker", False))
        
    with patch('api.middleware.rbac_middleware.get_db', side_effect=mock_get_db_attacker):
        response_attacker = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("[TEST: Tampered Token (Token claims is_admin: True, DB thinks it is False)]")
        print(f"Middleware Status: Blocked ({response_attacker.status_code})" if response_attacker.status_code == 403 else f"Evaded! {response_attacker.status_code}")
        print(f"Response: {response_attacker.json()}\n")

print("========== TESTS FINISHED ==========\n")
