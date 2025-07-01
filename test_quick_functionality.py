#!/usr/bin/env python3
"""
Quick functionality test for Legal Assistant
Tests core features without mocking - uses real API calls
"""

import os
import sys
import requests
import json
import tempfile
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_server_running():
    """Test if the Flask server is running"""
    try:
        response = requests.get('http://localhost:5000/', timeout=5)
        print(f"✅ Server running - Status: {response.status_code}")
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"❌ Server not accessible: {e}")
        return False

def test_main_page():
    """Test main page loads correctly"""
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        if response.status_code == 200:
            if 'Legal Assistant' in response.text:
                print("✅ Main page loads with correct content")
                return True
            else:
                print("❌ Main page missing expected content")
                return False
        else:
            print(f"❌ Main page returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing main page: {e}")
        return False

def test_language_switching():
    """Test language switching functionality"""
    try:
        session = requests.Session()
        
        # Test Romanian language
        response = session.post('http://localhost:5000/set-language', 
                               data={'language': 'ro'}, 
                               allow_redirects=False,
                               timeout=10)
        
        if response.status_code == 302:
            print("✅ Language switching works")
            return True
        else:
            print(f"❌ Language switching failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing language switching: {e}")
        return False

def test_discount_codes():
    """Test discount code functionality"""
    try:
        session = requests.Session()
        
        # Set up session with document
        session.get('http://localhost:5000/')
        
        # Test valid discount code
        response = session.post('http://localhost:5000/apply-discount',
                               json={'discount_code': 'letsgo'},
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('discount_percent') == 100:
                print("✅ Discount code 'letsgo' works correctly")
                
                # Test 50% discount
                response2 = session.post('http://localhost:5000/apply-discount',
                                        json={'discount_code': 'letsgo50'},
                                        headers={'Content-Type': 'application/json'},
                                        timeout=10)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    if data2.get('success') and data2.get('discount_percent') == 50:
                        print("✅ Discount code 'letsgo50' works correctly")
                        return True
                
                print("❌ 50% discount code not working properly")
                return False
            else:
                print(f"❌ Discount code response incorrect: {data}")
                return False
        else:
            print(f"❌ Discount code test failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing discount codes: {e}")
        return False

def test_file_upload_endpoint():
    """Test file upload endpoint without actual file processing"""
    try:
        session = requests.Session()
        
        # Create a simple test file
        test_content = b"This is a test legal document for validation purposes."
        files = {'files': ('test.txt', BytesIO(test_content), 'text/plain')}
        data = {
            'country': 'ro',
            'language': 'ro'
        }
        
        response = session.post('http://localhost:5000/upload-file',
                               files=files,
                               data=data,
                               allow_redirects=False,
                               timeout=30)
        
        if response.status_code in [302, 200]:
            print("✅ File upload endpoint responds correctly")
            return True
        else:
            print(f"❌ File upload failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing file upload: {e}")
        return False

def test_api_keys_configured():
    """Test if required API keys are configured"""
    required_keys = {
        'OPENAI_API_KEY': 'OpenAI',
        'STRIPE_SECRET_KEY': 'Stripe',
        'SESSION_SECRET': 'Session'
    }
    
    all_configured = True
    for key, name in required_keys.items():
        if os.environ.get(key):
            print(f"✅ {name} API key configured")
        else:
            print(f"❌ {name} API key missing")
            all_configured = False
    
    return all_configured

def test_openai_connection():
    """Test OpenAI API connection"""
    try:
        from openai import OpenAI
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API key not configured")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, respond with 'API test successful'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        if "successful" in result.lower():
            print("✅ OpenAI API connection working")
            return True
        else:
            print(f"❌ OpenAI API response unexpected: {result}")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

def test_stripe_connection():
    """Test Stripe API connection"""
    try:
        import stripe
        
        api_key = os.environ.get('STRIPE_SECRET_KEY')
        if not api_key:
            print("❌ Stripe API key not configured")
            return False
        
        stripe.api_key = api_key
        
        # Simple test - list products
        products = stripe.Product.list(limit=1)
        print("✅ Stripe API connection working")
        return True
        
    except Exception as e:
        print(f"❌ Stripe API test failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    try:
        from app import app, db
        from models import DocumentAnalysis
        
        with app.app_context():
            # Try to query the database
            count = DocumentAnalysis.query.count()
            print(f"✅ Database connection working - {count} records found")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def run_quick_tests():
    """Run all quick tests"""
    print("🧪 LEGAL ASSISTANT - QUICK FUNCTIONALITY TEST")
    print("=" * 50)
    
    tests = [
        ("Server Status", test_server_running),
        ("Main Page", test_main_page),
        ("Language Switch", test_language_switching),
        ("Discount Codes", test_discount_codes),
        ("File Upload", test_file_upload_endpoint),
        ("API Keys", test_api_keys_configured),
        ("Database", test_database_connection),
        ("OpenAI API", test_openai_connection),
        ("Stripe API", test_stripe_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Application is ready for use.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    return passed == total

if __name__ == '__main__':
    success = run_quick_tests()
    sys.exit(0 if success else 1)