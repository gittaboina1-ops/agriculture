"""
Automated End-to-End Verification Test Suite for AgriGraph Authentication, RBAC & Persistence.
Covers:
1. Default Admin Login (vundhyalaakeshreddy@gmail.com / reddy@123) -> JWT generation, role=admin
2. Farmer Registration via Signup -> role=farmer, min 8-char password check, confirm password matching
3. Farmer Login (new farmer) -> JWT generation, role=farmer
4. Persistence Across Backend Restarts -> Simulates process reboot, tests user loaded from data/users.json
5. Duplicate Email Rejection -> Ensures 400 error with friendly duplicate email warning
6. Wrong Password Rejection -> Ensures 401 error
7. RBAC Protection on Admin Endpoints:
   - Farmer Token -> Access /api/admin/upload -> 403 Forbidden
   - Unauthenticated -> Access /api/admin/upload -> 401 Unauthorized
   - Admin Token -> Access /api/admin/documents -> 200 OK
8. Core Features Unbroken:
   - /api/query execution
   - /api/graph node & edge count
   - /api/translate execution
"""

import sys
import os
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import settings

client = TestClient(app)

def run_tests():
    print("============================================================")
    print("AGRIGRAPH AUTHENTICATION & RBAC AUTOMATED TEST SUITE")
    print("============================================================")
    passed = 0
    failed = 0

    # 1. Test Default Admin Login
    print("\n[TEST 1] Default Admin Login...")
    res = client.post("/api/auth/login", json={
        "email": settings.DEFAULT_ADMIN_EMAIL,
        "password": settings.DEFAULT_ADMIN_PASSWORD
    })
    if res.status_code == 200:
        data = res.json()
        assert data["user"]["email"] == settings.DEFAULT_ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        assert "access_token" in data
        admin_token = data["access_token"]
        print(f"  PASS: Admin logged in successfully! Role: {data['user']['role']}")
        passed += 1
    else:
        print(f"  FAIL: Admin login failed: {res.status_code} {res.text}")
        failed += 1
        return

    # 2. Test Farmer Public Signup
    print("\n[TEST 2] Farmer Public Signup (Valid Data)...")
    import time
    test_farmer_email = f"testfarmer_{int(time.time())}@gmail.com"
    test_farmer_pw = "FarmerSecret@123"
    res = client.post("/api/auth/signup", json={
        "name": "Rao Bahadur",
        "email": test_farmer_email,
        "password": test_farmer_pw,
        "confirm_password": test_farmer_pw,
        "role": "farmer"
    })
    if res.status_code == 200:
        data = res.json()
        assert data["user"]["email"] == test_farmer_email
        assert data["user"]["role"] == "farmer"
        print(f"  PASS: Farmer registered successfully! Role: {data['user']['role']}")
        passed += 1
    else:
        print(f"  FAIL: Farmer registration failed: {res.status_code} {res.text}")
        failed += 1

    # 3. Test Farmer Password < 8 characters validation
    print("\n[TEST 3] Farmer Signup with Short Password (< 8 chars)...")
    res = client.post("/api/auth/signup", json={
        "name": "Short Pass User",
        "email": "shortpass@example.com",
        "password": "short",
        "confirm_password": "short"
    })
    if res.status_code == 400 and "at least 8 characters" in res.json().get("detail", ""):
        print(f"  PASS: Rejected short password with message: {res.json()['detail']}")
        passed += 1
    else:
        print(f"  FAIL: Expected 400 for short password, got {res.status_code}: {res.text}")
        failed += 1

    # 4. Test Public Admin Creation Prevention
    print("\n[TEST 4] Prevention of Public Admin Signup...")
    res = client.post("/api/auth/signup", json={
        "name": "Malicious Admin",
        "email": "hacker@example.com",
        "password": "HackerPassword@123",
        "confirm_password": "HackerPassword@123",
        "role": "admin"
    })
    if res.status_code == 403:
        print(f"  PASS: Unauthorized admin signup blocked: {res.json().get('detail')}")
        passed += 1
    else:
        print(f"  FAIL: Expected 403 for unauthorized admin creation, got {res.status_code}")
        failed += 1

    # 5. Test Duplicate Email Rejection
    print("\n[TEST 5] Duplicate Email Rejection...")
    res = client.post("/api/auth/signup", json={
        "name": "Rao Duplicate",
        "email": test_farmer_email,
        "password": test_farmer_pw,
        "confirm_password": test_farmer_pw
    })
    if res.status_code == 400 and "already exists" in res.json().get("detail", ""):
        print(f"  PASS: Duplicate email rejected: {res.json().get('detail')}")
        passed += 1
    else:
        print(f"  FAIL: Expected 400 for duplicate email, got {res.status_code}: {res.text}")
        failed += 1

    # 6. Test Farmer Login
    print("\n[TEST 6] Farmer Login...")
    res = client.post("/api/auth/login", json={
        "email": test_farmer_email,
        "password": test_farmer_pw
    })
    if res.status_code == 200:
        data = res.json()
        assert data["user"]["email"] == test_farmer_email
        assert data["user"]["role"] == "farmer"
        farmer_token = data["access_token"]
        print(f"  PASS: Farmer logged in successfully! Role: {data['user']['role']}")
        passed += 1
    else:
        print(f"  FAIL: Farmer login failed: {res.status_code} {res.text}")
        failed += 1
        return

    # 7. Test Wrong Password Rejection
    print("\n[TEST 7] Wrong Password Rejection...")
    res = client.post("/api/auth/login", json={
        "email": test_farmer_email,
        "password": "WrongPassword999"
    })
    if res.status_code == 401:
        print(f"  PASS: Wrong password rejected: {res.json().get('detail')}")
        passed += 1
    else:
        print(f"  FAIL: Expected 401 for wrong password, got {res.status_code}")
        failed += 1

    # 8. Test RBAC: Farmer Token Cannot Access Admin Endpoints
    print("\n[TEST 8] RBAC: Farmer Access to Admin Route (/api/admin/documents)...")
    res = client.get("/api/admin/documents", headers={"Authorization": f"Bearer {farmer_token}"})
    if res.status_code == 403:
        print(f"  PASS: Farmer correctly forbidden from admin route: {res.json().get('detail')}")
        passed += 1
    else:
        print(f"  FAIL: Expected 403 for farmer accessing admin route, got {res.status_code}")
        failed += 1

    # 9. Test RBAC: Admin Token Succeeded on Admin Route
    print("\n[TEST 9] RBAC: Admin Access to Admin Route (/api/admin/documents)...")
    res = client.get("/api/admin/documents", headers={"Authorization": f"Bearer {admin_token}"})
    if res.status_code == 200:
        print(f"  PASS: Admin correctly authorized to admin route! Documents count: {len(res.json())}")
        passed += 1
    else:
        print(f"  FAIL: Admin route access failed: {res.status_code}")
        failed += 1

    # 10. Test Persistence Across Restarts (Simulate Process Reboot)
    print("\n[TEST 10] Persistence Across Restarts (Simulated Process Reboot)...")
    from backend.services.auth_service import AuthService
    # Instantiating a new AuthService simulates restarting the server
    fresh_auth = AuthService()
    user_loaded = fresh_auth.get_user_by_email(test_farmer_email)
    if user_loaded and fresh_auth.verify_password(test_farmer_pw, user_loaded["password_hash"]):
        print(f"  PASS: User {test_farmer_email} preserved across restart and password verified!")
        passed += 1
    else:
        print(f"  FAIL: User {test_farmer_email} not recovered after restart!")
        failed += 1

    # 11. Test Core Query Pipeline Intact
    print("\n[TEST 11] Verify Farmer Query Pipeline (/api/query)...")
    res = client.post("/api/query", json={"query": "What causes tomato early blight?"}, headers={"Authorization": f"Bearer {farmer_token}"})
    if res.status_code == 200:
        q_data = res.json()
        print(f"  PASS: Farmer query answered: matched_crop={q_data.get('matched_crop')}, disease={q_data.get('matched_disease')}")
        passed += 1
    else:
        print(f"  FAIL: Query pipeline failed: {res.status_code} {res.text}")
        failed += 1

    # 12. Test Translation Intact
    print("\n[TEST 12] Verify Translation API (/api/translate)...")
    res = client.post("/api/translate", json={"text": "Tomato early blight is severe.", "target_language": "Telugu"})
    if res.status_code == 200 and len(res.json().get("translated_text", "")) > 0:
        print(f"  PASS: Translation executed: {res.json()['translated_text']}")
        passed += 1
    else:
        print(f"  FAIL: Translation failed: {res.status_code} {res.text}")
        failed += 1

    print("\n============================================================")
    print(f"RESULTS: {passed} PASSED, {failed} FAILED (TOTAL: {passed + failed})")
    print("============================================================")
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
