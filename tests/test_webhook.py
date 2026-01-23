#!/usr/bin/env python
"""
Test script to verify webhook is working.
Tests both:
1. Authentication (valid API key)
2. Request handling
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import requests
import json
from datetime import datetime

# Configuration
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyjOR-JUYuSTEIuInChx8uxhZk0RDreiHZrBS4jWINKCV9lXu0ylxXaFf4m_DBhCn7zeQ/exec"
API_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

def test_webhook():
    """Test webhook connectivity and authentication."""
    print("=" * 70)
    print("🧪 WEBHOOK TEST")
    print("=" * 70)
    print()
    
    # Test 1: With valid API key
    print("📋 Test 1: Valid API Key")
    print("-" * 70)
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "action": "test",
        "api_key": API_KEY,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    print(f"URL: {WEBHOOK_URL}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        print(f"✅ Status Code: {response.status_code}")
        print(f"Response:\n{response.text}")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    # Test 2: Invalid API key (should fail)
    print("📋 Test 2: Invalid API Key (should fail)")
    print("-" * 70)
    
    bad_headers = {
        "X-API-Key": "wrong-api-key",
        "Content-Type": "application/json"
    }
    
    print(f"Headers: {json.dumps(bad_headers, indent=2)}")
    print()
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=bad_headers,
            json=payload,
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{response.text}")
        if "UNAUTHORIZED" in response.text or response.status_code >= 400:
            print("✅ Correctly rejected invalid key")
        print()
    except Exception as e:
        print(f"Error: {e}")
        print()

if __name__ == "__main__":
    test_webhook()
