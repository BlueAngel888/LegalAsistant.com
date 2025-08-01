#!/usr/bin/env python3
"""
Investigare eroare Internal Server Error
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def investigate_error():
    session = requests.Session()
    
    print("🔍 INVESTIGARE EROARE INTERNAL SERVER ERROR\n")
    
    # Step 1: Upload document
    print("1. Upload document...")
    test_doc = "CONTRACT TEST PENTRU INVESTIGARE EROARE"
    files = {"file": ("test.txt", test_doc, "text/plain")}
    data = {
        "document_country": "RO",
        "analysis_language": "ro",
        "submit_type": "file_upload"
    }
    
    upload_resp = session.post(f"{BASE_URL}/upload", files=files, data=data)
    print(f"   Upload status: {upload_resp.status_code}")
    
    # Step 2: Apply LETSGO code
    print("\n2. Apply LETSGO code...")
    discount_resp = session.post(f"{BASE_URL}/apply-discount", 
                                json={"code": "LETSGO"},
                                headers={"Content-Type": "application/json"})
    
    if discount_resp.status_code == 200:
        print(f"   Discount applied: {discount_resp.json()}")
    
    # Step 3: Try free access
    print("\n3. Submit free access...")
    free_resp = session.post(f"{BASE_URL}/free-access", 
                            data={"free_code": "LETSGO"})
    
    print(f"   Free access status: {free_resp.status_code}")
    
    if free_resp.status_code == 500:
        print("\n❌ ERROR 500 DETECTED!")
        print("   Response headers:", dict(free_resp.headers))
        print("\n   Response content (first 500 chars):")
        print(free_resp.text[:500])
        
        # Check if it's a redirect
        if free_resp.history:
            print("\n   Redirect history:")
            for r in free_resp.history:
                print(f"   - {r.status_code} -> {r.url}")
    
    # Step 4: Check session state
    print("\n4. Check debug info...")
    debug_resp = session.get(f"{BASE_URL}/debug-info")
    if debug_resp.status_code == 200:
        debug_data = debug_resp.json()
        print("   Session keys:", debug_data.get('session_keys', []))
        print("   OpenAI configured:", debug_data.get('openai_configured', False))
        print("   Database URL set:", debug_data.get('database_url', False))
    
    # Step 5: Try direct success route
    print("\n5. Try direct success route...")
    success_resp = session.get(f"{BASE_URL}/success")
    print(f"   Success route status: {success_resp.status_code}")
    
    if success_resp.status_code == 500:
        print("\n   ⚠️ Success route also returns 500")
        print("   This suggests the error happens during analysis")
    elif success_resp.status_code == 200:
        # Check if analysis is present
        if "ANALIZĂ JURIDICĂ" in success_resp.text:
            print("   ✓ Analysis present in response")
        else:
            print("   ⚠️ No analysis found in response")

if __name__ == "__main__":
    investigate_error()