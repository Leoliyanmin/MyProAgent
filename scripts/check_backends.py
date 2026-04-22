#!/usr/bin/env python3
"""
Debug script to check backend status
"""
import requests
import sys

def check_backend(url, name):
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} is running at {url}")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️  {name} returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} is NOT running at {url}")
        return False
    except Exception as e:
        print(f"❌ {name} error: {e}")
        return False

def test_auth(url):
    try:
        # Test login endpoint exists
        response = requests.post(
            f"{url}/auth/login",
            json={"email": "test@test.com", "password": "test"},
            timeout=5
        )
        print(f"   Auth endpoint test: {response.status_code}")
        if response.status_code == 401:
            print("   ℹ️  Auth endpoint working (401 is expected for wrong credentials)")
        elif response.status_code == 200:
            print("   ✅ Auth endpoint working")
        elif response.status_code == 404:
            print("   ⚠️  Auth endpoint not found (route issue)")
        else:
            print(f"   Response: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Auth test failed: {e}")

print("=" * 50)
print("ProAgent Backend Health Check")
print("=" * 50)
print()

# Check Local Backend
print("1. Checking Local Backend (port 8002)...")
local_ok = check_backend("http://localhost:8002", "Local Backend")
if local_ok:
    test_auth("http://localhost:8002")
print()

# Check Server Backend
print("2. Checking Server Backend (port 8001)...")
server_ok = check_backend("http://localhost:8001", "Server Backend")
if server_ok:
    test_auth("http://localhost:8001")
print()

# Summary
print("=" * 50)
print("Summary:")
if local_ok:
    print("✅ Local Backend is ready")
else:
    print("❌ Local Backend is not running")
    print("   Start it with: cd local_backend && uvicorn main:app --host 0.0.0.0 --port 8002")

if server_ok:
    print("✅ Server Backend is ready")
else:
    print("⚠️  Server Backend is not running (optional for local use)")
    print("   Start it with: cd server_backend && uvicorn main:app --host 0.0.0.0 --port 8001")

print("=" * 50)
