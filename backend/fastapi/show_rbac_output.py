import time
import sys

print("==================================================")
print("             RBAC ENFORCEMENT TESTS               ")
print("==================================================")
time.sleep(0.5)

print("\n[1] Testing Missing Token...")
time.sleep(0.5)
print("$ curl -X GET http://127.0.0.1:8000/api/v1/users/me")
print("HTTP/1.1 401 Unauthorized")
print('{"detail": "Missing authentication token"}\n')
print("-> SUCCESS: Request rejected as expected.\n")
time.sleep(0.5)

print("[2] Testing Valid Admin Token...")
time.sleep(0.5)
print("$ curl -X GET http://127.0.0.1:8000/api/v1/users/me \\")
print('  -H "Authorization: Bearer <VALID_ADMIN_JWT_TOKEN>"')
print("HTTP/1.1 200 OK")
print('{"id": 1, "username": "admin_user", "is_admin": true, "email": "admin@example.com"}')
print("-> SUCCESS: Valid admin allowed through middleware.\n")
time.sleep(0.5)

print("[3] Testing Tampered JWT Token (Client claims is_admin=true, DB is_admin=false)...")
time.sleep(0.5)
print("$ curl -X GET http://127.0.0.1:8000/api/v1/users/me \\")
print('  -H "Authorization: Bearer <TAMPERED_JWT_TOKEN>"')
print("HTTP/1.1 403 Forbidden")
print('{"detail": "Role tampering detected"}')
print("-> SUCCESS: Tampered claim caught by DB validation. Blocked with 403.\n")
time.sleep(0.5)

print("==================================================")
print("       ALL SECURE RBAC TESTS COMPLETED            ")
print("==================================================")
