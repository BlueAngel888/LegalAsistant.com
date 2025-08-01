#!/usr/bin/env python3
"""
Manual test for LETSGO code flow - simulates user interaction
"""

import requests
import time
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_letsgo_flow():
    """Test complete LETSGO flow"""
    session = requests.Session()
    
    print("\n🚀 TESTING LETSGO CODE FLOW\n")
    print("="*50)
    
    # Step 1: Visit homepage
    print("1. Accessing homepage...")
    homepage = session.get(BASE_URL)
    if homepage.status_code == 200:
        print("   ✓ Homepage loaded successfully")
    else:
        print(f"   ✗ Homepage failed: {homepage.status_code}")
        return
    
    # Step 2: Upload document
    print("\n2. Uploading test document...")
    test_document = """CONTRACT DE VÂNZARE-CUMPĂRARE
    
Părțile: POPESCU ION (vânzător) și IONESCU MARIA (cumpărător)
Obiect: Apartament 3 camere, București, str. Unirii nr. 15
Preț: 95.000 EUR
Data: 01.08.2025"""
    
    files = {"file": ("contract_test.txt", test_document, "text/plain")}
    data = {
        "document_country": "RO",
        "analysis_language": "ro",
        "submit_type": "file_upload"
    }
    
    upload_response = session.post(f"{BASE_URL}/upload", files=files, data=data)
    
    if upload_response.status_code in [200, 302]:
        print("   ✓ Document uploaded successfully")
        
        # Check if redirected to checkout
        if upload_response.url and "checkout" in upload_response.url:
            print("   ✓ Redirected to checkout page")
        elif "checkout" in upload_response.text:
            print("   ✓ Checkout page loaded")
    else:
        print(f"   ✗ Upload failed: {upload_response.status_code}")
        return
    
    # Step 3: Get checkout page
    print("\n3. Accessing checkout page...")
    checkout_page = session.get(f"{BASE_URL}/checkout")
    
    if checkout_page.status_code == 200:
        print("   ✓ Checkout page loaded")
        
        # Check for discount code field
        if "discountCode" in checkout_page.text:
            print("   ✓ Discount code field found")
        else:
            print("   ⚠ Discount code field not found")
    else:
        print(f"   ✗ Checkout page failed: {checkout_page.status_code}")
        return
    
    # Step 4: Apply LETSGO code
    print("\n4. Applying LETSGO discount code...")
    discount_data = {"code": "LETSGO"}
    headers = {"Content-Type": "application/json"}
    
    discount_response = session.post(f"{BASE_URL}/apply-discount", 
                                    json=discount_data, 
                                    headers=headers)
    
    if discount_response.status_code == 200:
        result = discount_response.json()
        if result.get("success"):
            print(f"   ✓ LETSGO code accepted: {result.get('discount_percent', 0)}% discount")
            if result.get("free_access"):
                print("   ✓ FREE ACCESS granted!")
        else:
            print(f"   ✗ Code rejected: {result.get('message', 'Unknown error')}")
            return
    else:
        print(f"   ✗ Discount API failed: {discount_response.status_code}")
        return
    
    # Step 5: Submit free access
    print("\n5. Submitting free access...")
    free_data = {"free_code": "LETSGO"}
    
    free_response = session.post(f"{BASE_URL}/free-access", data=free_data)
    
    if free_response.status_code in [200, 302]:
        print("   ✓ Free access request accepted")
        
        # Check if redirected to success
        if free_response.url and "success" in free_response.url:
            print("   ✓ Redirected to success page")
        
        # Get success page
        print("\n6. Accessing analysis results...")
        success_page = session.get(f"{BASE_URL}/success")
        
        if success_page.status_code == 200:
            print("   ✓ Analysis page loaded")
            
            # Check for analysis content
            if "GlobalLegalAnalyserGPT" in success_page.text:
                print("   ✓ GlobalLegalAnalyserGPT analysis found!")
            elif "ANALIZĂ JURIDICĂ" in success_page.text:
                print("   ✓ Legal analysis found!")
            elif "contract" in success_page.text.lower():
                print("   ✓ Contract analysis content found")
            else:
                print("   ⚠ Analysis content unclear")
                
            # Check for chat system
            if "legal-chat" in success_page.text:
                print("   ✓ Legal chat system available")
            
            # Count analysis sections
            sections = ["IDENTIFICARE", "ANALIZ", "VERIFIC", "IMPLIC", "ASPECTE"]
            found_sections = sum(1 for section in sections if section in success_page.text.upper())
            print(f"   ℹ Found {found_sections}/5 analysis sections")
            
        else:
            print(f"   ✗ Success page failed: {success_page.status_code}")
            
    else:
        print(f"   ✗ Free access failed: {free_response.status_code}")
        print(f"   Response: {free_response.text[:200]}...")
    
    print("\n" + "="*50)
    print("TEST COMPLETE")
    print("="*50)

if __name__ == "__main__":
    test_letsgo_flow()