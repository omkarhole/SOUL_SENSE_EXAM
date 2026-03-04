import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta

from api.main import app
from api.config import get_settings_instance

settings = get_settings_instance()

client = TestClient(app)

# Helper to create token
def create_token(user_id: int, username: str, is_admin: bool):
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {
        "sub": username,
        "is_admin": is_admin,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.jwt_algorithm)
    return encoded_jwt

print("\n--- Running RBAC Middleware Checks ---\n")

# 1. Missing token
response = client.get("/api/v1/users/me")
print("1. Missing token result:")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
print("-" * 40)

# We need a user in the DB. Given this is a testing context, the DB might be empty or not fully initialized.
# Alternatively, I can mock the get_db dependency to simulate DB behavior.
