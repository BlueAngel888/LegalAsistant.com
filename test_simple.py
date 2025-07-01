#!/usr/bin/env python3
import requests
import time

BASE_URL = "https://80aff0b9-0297-40ab-98d1-219085d14976-00-k6lfm920zt2w.spock.replit.dev"

def test_discount_flow():
    """Test complete discount code flow"""
    session = requests.Session()
    
    print("=== Testing Discount Code Flow ===")
    
    # Step 1: Upload document
    print("1. Uploading document...")
    with open('test_document.txt', 'r') as f:
        files = {'file': ('contract.txt', f.read(), 'text/plain')}
    
    upload_data = {
        'document_country': 'RO',
        'analysis_language': 'ro'
    }
    
    upload_response = session.post(f"{BASE_URL}/upload", data=upload_data, files=files)
    print(f"Upload status: {upload_response.status_code}")
    
    # Step 2: Apply discount code
    print("2. Applying discount code...")
    discount_data = {
        'code': 'LETSGO'
    }
    
    discount_response = session.post(f"{BASE_URL}/apply-discount", json=discount_data)
    print(f"Discount status: {discount_response.status_code}")
    
    if discount_response.status_code == 200:
        result = discount_response.json()
        print(f"Discount result: {result}")
        
        # Step 3: Use free access
        if result.get('free_access'):
            print("3. Using free access...")
            free_data = {'free_code': 'LETSGO'}
            
            free_response = session.post(f"{BASE_URL}/free-access", data=free_data)
            print(f"Free access status: {free_response.status_code}")
            
            # Step 4: Try success page
            print("4. Accessing analysis results...")
            success_response = session.get(f"{BASE_URL}/success")
            print(f"Success page status: {success_response.status_code}")
            
            if success_response.status_code == 200:
                if "analysis" in success_response.text.lower():
                    print("✓ SUCCESS: Analysis page loaded correctly!")
                    return True
                else:
                    print("✗ Analysis page loaded but no analysis content found")
                    return False
            else:
                print(f"✗ Failed to load analysis page: {success_response.status_code}")
                return False
    
    return False

if __name__ == "__main__":
    success = test_discount_flow()
    print(f"\nFinal result: {'✓ WORKING' if success else '✗ BROKEN'}")