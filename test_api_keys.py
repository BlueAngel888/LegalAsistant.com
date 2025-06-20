#!/usr/bin/env python3
"""
Test script to verify OpenAI and Stripe API keys are working correctly
"""
import os
import logging
from openai import OpenAI
import stripe
from config import OPENAI_API_KEY, STRIPE_SECRET_KEY

logging.basicConfig(level=logging.INFO)

def test_openai_api():
    """Test OpenAI API connectivity and key validity"""
    try:
        print("Testing OpenAI API...")
        print(f"API Key present: {bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith('sk-default'))}")
        
        if not OPENAI_API_KEY or OPENAI_API_KEY.startswith('sk-default'):
            print("❌ OpenAI API key not properly configured")
            return False
            
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Test with a simple request
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello, this is a test. Please respond with 'API test successful'."}],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenAI API test successful: {result}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        return False

def test_stripe_api():
    """Test Stripe API connectivity and key validity"""
    try:
        print("\nTesting Stripe API...")
        print(f"API Key present: {bool(STRIPE_SECRET_KEY and not STRIPE_SECRET_KEY.startswith('sk_test_default'))}")
        
        if not STRIPE_SECRET_KEY or STRIPE_SECRET_KEY.startswith('sk_test_default'):
            print("❌ Stripe API key not properly configured")
            return False
            
        stripe.api_key = STRIPE_SECRET_KEY
        
        # Test with a simple API call
        account = stripe.Account.retrieve()
        print(f"✅ Stripe API test successful - Account ID: {account.id}")
        return True
        
    except Exception as e:
        print(f"❌ Stripe API test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== API Key Testing ===")
    
    openai_ok = test_openai_api()
    stripe_ok = test_stripe_api()
    
    print("\n=== Results ===")
    print(f"OpenAI API: {'✅ Working' if openai_ok else '❌ Failed'}")
    print(f"Stripe API: {'✅ Working' if stripe_ok else '❌ Failed'}")
    
    if not openai_ok or not stripe_ok:
        print("\n⚠️  Some API keys need attention. Check the error messages above.")
        print("Please verify your API keys in the Secrets panel.")
    else:
        print("\n🎉 All API keys are working correctly!")