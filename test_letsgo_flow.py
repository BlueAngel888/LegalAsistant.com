#!/usr/bin/env python3
"""
Test script to simulate the full LETSGO code flow
"""
import requests
import json

# Base URL for the application
BASE_URL = "http://localhost:5000"

def test_letsgo_flow():
    """Test the complete LETSGO discount code flow"""
    session = requests.Session()
    
    print("=== Testing LETSGO Discount Code Flow ===")
    
    # Step 1: Get the main page to establish session
    print("1. Getting main page...")
    response = session.get(f"{BASE_URL}/")
    print(f"   Status: {response.status_code}")
    
    # Step 2: Upload a document with proper parameters
    print("2. Uploading test document...")
    files = {'files': ('test.txt', 'Contract de vanzare-cumparare\n\nVanzator: Ion Popescu\nCumparator: Maria Ionescu\nPret: 100000 EUR', 'text/plain')}
    data = {
        'document_country': 'RO',
        'analysis_language': 'ro'
    }
    
    response = session.post(f"{BASE_URL}/upload", files=files, data=data)
    print(f"   Upload Status: {response.status_code}")
    print(f"   Upload Response: {response.url}")
    
    # Check if redirected to checkout
    if 'checkout' in response.url:
        print("   ✓ Successfully redirected to checkout")
        
        # Step 3: Apply LETSGO discount code
        print("3. Applying LETSGO discount code...")
        discount_data = {'code': 'LETSGO'}
        response = session.post(f"{BASE_URL}/apply-discount", 
                              json=discount_data,
                              headers={'Content-Type': 'application/json'})
        
        print(f"   Discount Status: {response.status_code}")
        if response.status_code == 200:
            discount_result = response.json()
            print(f"   Discount Result: {discount_result}")
            
            if discount_result.get('success') and discount_result.get('free_access'):
                print("   ✓ Discount code applied successfully")
                
                # Step 4: Process free access
                print("4. Processing free access...")
                free_access_data = {'free_code': 'LETSGO'}
                response = session.post(f"{BASE_URL}/free-access", data=free_access_data)
                
                print(f"   Free Access Status: {response.status_code}")
                print(f"   Free Access Response URL: {response.url}")
                
                if response.status_code == 200:
                    print("   ✓ Free access processed successfully")
                    print(f"   Final page content length: {len(response.text)}")
                    
                    # Check if we have analysis content
                    if len(response.text) > 5000:  # Should have analysis content
                        print("   ✓ Analysis content received successfully")
                    else:
                        print("   ⚠ Response seems too short - possible error")
                        print(f"   Response preview: {response.text[:500]}...")
                        
                else:
                    print(f"   ✗ Free access failed with status: {response.status_code}")
                    print(f"   Error response: {response.text[:500]}...")
                    
            else:
                print(f"   ✗ Discount application failed: {discount_result}")
        else:
            print(f"   ✗ Discount request failed with status: {response.status_code}")
            print(f"   Error response: {response.text[:200]}...")
            
    else:
        print(f"   ✗ Upload failed - not redirected to checkout")
        print(f"   Response content: {response.text[:500]}...")

if __name__ == "__main__":
    test_letsgo_flow()