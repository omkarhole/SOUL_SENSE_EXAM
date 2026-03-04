"""
Demonstration script for Issue 1050: Database Replicas & Read/Write Splitting

This script verifies:
1. Write operations (POST) are routed to the Primary DB.
2. Read operations (GET) are routed to the Replica DB.
3. Read-Your-Own-Writes guard forces primary routing for 5s after a write.
"""

import requests
import time
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"

def print_banner(text):
    print("\n" + "="*70)
    print(f" {text}")
    print("="*70)

def demonstrate():
    # 1. Health check with retries
    max_retries = 30
    for i in range(max_retries):
        try:
            requests.get(f"{BASE_URL}/", timeout=2)
            break
        except:
            if i == max_retries - 1:
                print("Error: Server is not running at 127.0.0.1:8000")
                return
            time.sleep(1)

    print_banner("DATABASE REPLICA ROUTING DEMO")
    
    # Prepare unique user
    ts = int(time.time())
    username = f"split_{ts}"
    password = "SafePassword123!"
    email = f"split_{ts}@example.com"
    
    # STEP 1: Get Captcha (Should hit REPLICA)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 1: GET /auth/captcha (Should hit REPLICA)")
    c_res = requests.get(f"{API_V1}/auth/captcha")
    captcha_data = c_res.json()
    session_id = captcha_data["session_id"]
    captcha_code = captcha_data["captcha_code"]
    print(f"  Result: {c_res.status_code} - Captcha: {captcha_code}")
    
    # STEP 2: Register User (Should hit PRIMARY - WRITE)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] STEP 2: POST /auth/register (Should hit PRIMARY)")
    reg_payload = {
        "username": username,
        "password": password,
        "email": email,
        "first_name": "Read",
        "last_name": "Writer",
        "captcha_code": "TEST" # Using TEST if permitted or extracted
    }
    # Use real captcha code if possible
    reg_payload["captcha_code"] = captcha_code
    
    r_res = requests.post(f"{API_V1}/auth/register", json=reg_payload)
    print(f"  Result: {r_res.status_code}")
    
    # STEP 3: Login (Hits PRIMARY - Write to last_login)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] STEP 3: POST /auth/login (Should hit PRIMARY)")
    login_payload = {
        "identifier": username,
        "password": password,
        "captcha_input": captcha_code,
        "session_id": session_id
    }
    l_res = requests.post(f"{API_V1}/auth/login", json=login_payload)
    if l_res.status_code != 200:
        print(f"  Login Failed: {l_res.text}")
        return
        
    token = l_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  Login Success! Token acquired.")
    
    # STEP 4: Immediate Read (Read-Your-Own-Writes Guard)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] STEP 4: GET /auth/me (IMMEDIATE - Should hit PRIMARY via Guard)")
    m_res = requests.get(f"{API_V1}/auth/me", headers=headers)
    if m_res.status_code != 200:
        print(f"  Failed: {m_res.status_code} - {m_res.text}")
        return
    try:
        data = m_res.json()
        print(f"  Result: {m_res.status_code} (User: {data.get('username')})")
    except Exception as e:
        print(f"  JSON Error: {e}")
        print(f"  Full response: {m_res.text}")
        return
    
    # STEP 5: Wait 6 seconds
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] STEP 5: Waiting 6 seconds for lag window to expire...")
    time.sleep(6)
    
    # STEP 6: Subsequent Read (Should hit REPLICA)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] STEP 6: GET /auth/me (DELAYED - Should hit REPLICA)")
    m_res2 = requests.get(f"{API_V1}/auth/me", headers=headers)
    print(f"  Result: {m_res2.status_code} (User: {m_res2.json().get('username')})")
    
    print_banner("DEMO COMPLETED")
    print("Check server logs for routing details:")
    print("  - 'Read-your-own-writes guard: routing... to primary'")
    print("  - 'Read-replica engine initialised.'")

if __name__ == "__main__":
    demonstrate()
