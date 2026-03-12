#!/usr/bin/env python3
"""
Quick test to check if the server is working
"""

import time
import requests

def test_server():
    try:
        print("Testing server health...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"✗ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Could not connect to server: {e}")
        return False

if __name__ == "__main__":
    print("Waiting for server to start...")
    time.sleep(2)
    test_server()




