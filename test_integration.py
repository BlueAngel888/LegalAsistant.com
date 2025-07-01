#!/usr/bin/env python3
"""
Integration test for Legal Assistant
Tests the complete user workflow from file upload to analysis and chat
"""

import os
import sys
import requests
import json
import time
from io import BytesIO

def create_test_session():
    """Create a session and simulate document upload"""
    session = requests.Session()
    
    # Get main page to establish session
    response = session.get('http://localhost:5000/')
    if response.status_code != 200:
        print("❌ Cannot establish session")
        return None
    
    print("✅ Session established")
    return session

def test_complete_workflow():
    """Test the complete user workflow"""
    print("🔄 Testing complete user workflow...")
    
    session = create_test_session()
    if not session:
        return False
    
    # Step 1: Test file upload with proper form data
    print("📁 Step 1: Testing file upload...")
    
    # Create test document content
    test_content = """
    CONTRACT DE PRESTĂRI SERVICII
    
    Între:
    1. SC COMPANY SRL, cu sediul în București, str. Exemplu nr. 123
    2. JOHN DOE, cu domiciliul în București, str. Test nr. 456
    
    Se încheie prezentul contract care conține următoarele clauze:
    
    Art. 1. Obiectul contractului
    Prestatorul se obligă să furnizeze servicii de consultanță juridică.
    
    Art. 2. Durata contractului
    Contractul se încheie pe o perioadă de 12 luni.
    
    Art. 3. Valoarea contractului
    Valoarea totală este de 10.000 EUR.
    """
    
    files = {'files': ('contract_test.txt', BytesIO(test_content.encode('utf-8')), 'text/plain')}
    data = {
        'document_country': 'ro',
        'analysis_language': 'ro'
    }
    
    upload_response = session.post('http://localhost:5000/upload',
                                  files=files,
                                  data=data,
                                  allow_redirects=False,
                                  timeout=30)
    
    if upload_response.status_code == 302:
        print("✅ File upload successful - redirected to checkout")
    else:
        print(f"❌ File upload failed - Status: {upload_response.status_code}")
        return False
    
    # Step 2: Test discount code application
    print("💰 Step 2: Testing discount code...")
    
    discount_response = session.post('http://localhost:5000/apply-discount',
                                   json={'discount_code': 'letsgo'},
                                   headers={'Content-Type': 'application/json'},
                                   timeout=10)
    
    if discount_response.status_code == 200:
        discount_data = discount_response.json()
        if discount_data.get('success') and discount_data.get('discount_percent') == 100:
            print("✅ Free access discount code works")
        else:
            print(f"❌ Discount code failed: {discount_data}")
            return False
    else:
        print(f"❌ Discount request failed - Status: {discount_response.status_code}")
        return False
    
    # Step 3: Test free access processing
    print("🆓 Step 3: Testing free access...")
    
    free_response = session.post('http://localhost:5000/free-access',
                                data={'discount_code': 'letsgo'},
                                allow_redirects=False,
                                timeout=30)
    
    if free_response.status_code == 302:
        print("✅ Free access processing initiated")
        
        # Get the redirect location (should be success page)
        redirect_url = free_response.headers.get('Location', '')
        if 'success' in redirect_url:
            print("✅ Redirected to success page")
        else:
            print(f"❌ Unexpected redirect: {redirect_url}")
            return False
    else:
        print(f"❌ Free access failed - Status: {free_response.status_code}")
        return False
    
    # Step 4: Test success page with analysis
    print("📊 Step 4: Testing analysis results...")
    
    success_response = session.get('http://localhost:5000/success', timeout=30)
    
    if success_response.status_code == 200:
        success_content = success_response.text
        if 'Identificarea și validitatea formală' in success_content:
            print("✅ Analysis results displayed with Romanian format")
        elif 'Document Analysis' in success_content or 'Legal Analysis' in success_content:
            print("✅ Analysis results displayed")
        else:
            print("❌ Analysis results not found in success page")
            return False
    else:
        print(f"❌ Success page failed - Status: {success_response.status_code}")
        return False
    
    # Step 5: Test legal chat functionality
    print("💬 Step 5: Testing legal chat...")
    
    chat_response = session.post('http://localhost:5000/legal-chat',
                                json={
                                    'message': 'Care sunt obligațiile mele din acest contract?',
                                    'analysis_context': 'Contract analysis context',
                                    'conversation_history': []
                                },
                                headers={'Content-Type': 'application/json'},
                                timeout=30)
    
    if chat_response.status_code == 200:
        chat_data = chat_response.json()
        if chat_data.get('success') and chat_data.get('response'):
            print("✅ Legal chat responds correctly")
            print(f"   Sample response: {chat_data['response'][:100]}...")
        else:
            print(f"❌ Chat response invalid: {chat_data}")
            return False
    else:
        print(f"❌ Legal chat failed - Status: {chat_response.status_code}")
        return False
    
    print("🎉 Complete workflow test passed!")
    return True

def test_error_handling():
    """Test error handling scenarios"""
    print("🚨 Testing error handling...")
    
    session = create_test_session()
    if not session:
        return False
    
    # Test invalid discount code
    response = session.post('http://localhost:5000/apply-discount',
                           json={'discount_code': 'invalid_code'},
                           headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        data = response.json()
        if not data.get('success'):
            print("✅ Invalid discount code handled correctly")
        else:
            print("❌ Invalid discount code accepted")
            return False
    else:
        print(f"❌ Discount validation failed - Status: {response.status_code}")
        return False
    
    # Test chat without document
    chat_response = session.post('http://localhost:5000/legal-chat',
                                json={'message': 'Test question'},
                                headers={'Content-Type': 'application/json'})
    
    if chat_response.status_code == 403:
        print("✅ Chat without document properly blocked")
    else:
        print(f"❌ Chat security failed - Status: {chat_response.status_code}")
        return False
    
    print("✅ Error handling tests passed")
    return True

def test_performance():
    """Test basic performance metrics"""
    print("⚡ Testing performance...")
    
    # Test main page load time
    start_time = time.time()
    response = requests.get('http://localhost:5000/', timeout=10)
    load_time = time.time() - start_time
    
    if response.status_code == 200 and load_time < 2.0:
        print(f"✅ Main page loads in {load_time:.2f}s")
    else:
        print(f"❌ Main page slow or failed: {load_time:.2f}s, status: {response.status_code}")
        return False
    
    return True

def run_integration_tests():
    """Run all integration tests"""
    print("🧪 LEGAL ASSISTANT - INTEGRATION TESTS")
    print("=" * 50)
    
    tests = [
        ("Complete Workflow", test_complete_workflow),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} test passed")
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nResults: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("The application is working correctly end-to-end.")
    else:
        print("⚠️  Some integration tests failed.")
        print("Check the specific test failures above.")
    
    return passed == total

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)