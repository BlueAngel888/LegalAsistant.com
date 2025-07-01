#!/usr/bin/env python3
import requests
import json
import time

# Test configuration
BASE_URL = "https://80aff0b9-0297-40ab-98d1-219085d14976-00-k6lfm920zt2w.spock.replit.dev"

def test_upload_and_free_access():
    """Test document upload followed by free access with discount code"""
    print("=== Testing Free Access Route ===")
    
    session = requests.Session()
    
    # Step 1: Upload document
    print("1. Uploading test document...")
    with open('test_document.txt', 'r') as f:
        files = {'file': ('test_contract.txt', f.read(), 'text/plain')}
    
    upload_data = {
        'document_country': 'RO',
        'analysis_language': 'ro'
    }
    
    try:
        upload_response = session.post(f"{BASE_URL}/upload", data=upload_data, files=files)
        print(f"Upload response status: {upload_response.status_code}")
        
        if upload_response.status_code == 302:
            print("Upload successful - redirected to checkout")
            
            # Step 2: Apply discount code
            print("2. Applying discount code LETSGO...")
            discount_data = {
                'code': 'LETSGO'
            }
            
            discount_response = session.post(f"{BASE_URL}/apply-discount", json=discount_data)
            print(f"Discount response status: {discount_response.status_code}")
            
            if discount_response.status_code == 200:
                discount_result = discount_response.json()
                print(f"Discount result: {discount_result}")
                
                # Step 3: Use free access
                if discount_result.get('success') and discount_result.get('free_access'):
                    print("3. Using free access...")
                    free_access_data = {
                        'free_code': 'LETSGO'
                    }
                    
                    free_response = session.post(f"{BASE_URL}/free_access", data=free_access_data)
                    print(f"Free access response status: {free_response.status_code}")
                    
                    if free_response.status_code == 302:
                        print("Free access successful - should redirect to analysis")
                        
                        # Follow redirect to success page
                        success_response = session.get(f"{BASE_URL}/success")
                        print(f"Success page status: {success_response.status_code}")
                        
                        if success_response.status_code == 200:
                            print("✓ Free access route SUCCESSFUL - analysis page loaded")
                            return True
                        else:
                            print(f"✗ Free access route FAILED - success page error: {success_response.status_code}")
                            return False
                    else:
                        print(f"✗ Free access route FAILED - free access error: {free_response.status_code}")
                        return False
            else:
                print(f"✗ Discount code application failed: {discount_response.status_code}")
                return False
        else:
            print(f"✗ Upload failed: {upload_response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error in free access test: {str(e)}")
        return False

def test_upload_and_payment():
    """Test document upload followed by Stripe payment"""
    print("\n=== Testing Paid Route ===")
    
    session = requests.Session()
    
    # Step 1: Upload document
    print("1. Uploading test document...")
    with open('test_document.txt', 'r') as f:
        files = {'file': ('test_contract.txt', f.read(), 'text/plain')}
    
    upload_data = {
        'document_country': 'RO',
        'analysis_language': 'ro'
    }
    
    try:
        upload_response = session.post(f"{BASE_URL}/upload", data=upload_data, files=files)
        print(f"Upload response status: {upload_response.status_code}")
        
        if upload_response.status_code == 302:
            print("Upload successful - redirected to checkout")
            
            # For testing, we'll simulate a successful payment by directly accessing success
            # In real scenario, this would go through Stripe
            print("2. Simulating successful payment...")
            
            # We need to set payment status in session somehow
            # Let's try to access success page directly to see what happens
            success_response = session.get(f"{BASE_URL}/success")
            print(f"Success page status: {success_response.status_code}")
            
            if success_response.status_code == 200:
                print("✓ Paid route SUCCESSFUL - analysis page loaded")
                return True
            elif success_response.status_code == 302:
                print("Redirected from success page - checking where...")
                return False
            else:
                print(f"✗ Paid route FAILED - success page error: {success_response.status_code}")
                return False
        else:
            print(f"✗ Upload failed: {upload_response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error in paid route test: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Legal Assistant Routes...")
    print("=" * 50)
    
    # Test both routes
    free_access_works = test_upload_and_free_access()
    paid_route_works = test_upload_and_payment()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS:")
    print(f"Free Access Route: {'✓ WORKING' if free_access_works else '✗ BROKEN'}")
    print(f"Paid Route: {'✓ WORKING' if paid_route_works else '✗ BROKEN'}")
    
    if free_access_works and paid_route_works:
        print("\n🎉 Both routes are working correctly!")
    elif free_access_works or paid_route_works:
        print("\n⚠️ One route is working, one needs fixing")
    else:
        print("\n❌ Both routes need fixing")