#!/usr/bin/env python3
"""
Test runner for Legal Assistant application
Provides different test execution modes and detailed reporting
"""

import os
import sys
import argparse
import subprocess
import time
from datetime import datetime

def run_basic_tests():
    """Run basic functionality tests"""
    print("🔍 Running basic functionality tests...")
    
    basic_tests = [
        'TestRoutes.test_index_route',
        'TestRoutes.test_language_setting',
        'TestRoutes.test_discount_code_application',
        'TestFileUpload.test_file_upload_validation',
        'TestDatabaseModels.test_document_analysis_model'
    ]
    
    for test in basic_tests:
        print(f"  Running {test}...")
        result = subprocess.run([
            sys.executable, '-m', 'unittest', f'test_application.{test}', '-v'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ {test} - PASSED")
        else:
            print(f"  ❌ {test} - FAILED")
            print(f"     Error: {result.stderr.strip()}")

def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running integration tests...")
    
    integration_tests = [
        'TestPaymentProcessing',
        'TestAIAnalysis',
        'TestLegalChat',
        'TestDocumentConsistency'
    ]
    
    for test_class in integration_tests:
        print(f"  Running {test_class}...")
        result = subprocess.run([
            sys.executable, '-m', 'unittest', f'test_application.{test_class}', '-v'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ {test_class} - PASSED")
        else:
            print(f"  ❌ {test_class} - FAILED")
            print(f"     Error: {result.stderr.strip()}")

def run_security_tests():
    """Run security and validation tests"""
    print("🔒 Running security tests...")
    
    security_tests = [
        'TestSecurityFeatures',
        'TestErrorHandling'
    ]
    
    for test_class in security_tests:
        print(f"  Running {test_class}...")
        result = subprocess.run([
            sys.executable, '-m', 'unittest', f'test_application.{test_class}', '-v'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✅ {test_class} - PASSED")
        else:
            print(f"  ❌ {test_class} - FAILED")

def run_performance_tests():
    """Run performance tests"""
    print("⚡ Running performance tests...")
    
    result = subprocess.run([
        sys.executable, '-m', 'unittest', 'test_application.TestPerformance', '-v'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("  ✅ Performance tests - PASSED")
    else:
        print("  ❌ Performance tests - FAILED")
        print(f"     Error: {result.stderr.strip()}")

def run_all_tests():
    """Run complete test suite"""
    print("🧪 Running complete test suite...")
    
    start_time = time.time()
    result = subprocess.run([
        sys.executable, 'test_application.py'
    ], capture_output=True, text=True)
    end_time = time.time()
    
    print(f"Test execution time: {end_time - start_time:.2f} seconds")
    print("\n" + result.stdout)
    
    if result.stderr:
        print("STDERR Output:")
        print(result.stderr)
    
    return result.returncode == 0

def check_dependencies():
    """Check if all required dependencies are available"""
    print("📋 Checking dependencies...")
    
    required_modules = [
        'flask',
        'sqlalchemy',
        'stripe',
        'openai',
        'pytesseract',
        'pypdf2',
        'python-docx',
        'pillow'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} - MISSING")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        return False
    
    print("✅ All dependencies available")
    return True

def test_api_keys():
    """Test if API keys are configured"""
    print("🔑 Checking API keys...")
    
    api_keys = {
        'OPENAI_API_KEY': 'OpenAI API',
        'STRIPE_SECRET_KEY': 'Stripe Secret',
        'SESSION_SECRET': 'Session Secret'
    }
    
    missing_keys = []
    for key, name in api_keys.items():
        if os.environ.get(key):
            print(f"  ✅ {name} - Configured")
        else:
            print(f"  ❌ {name} - Missing")
            missing_keys.append(name)
    
    if missing_keys:
        print(f"\n⚠️  Missing API keys: {', '.join(missing_keys)}")
        print("Some tests may fail without proper API keys.")
        return False
    
    return True

def generate_test_report():
    """Generate a comprehensive test report"""
    print("📊 Generating test report...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"test_report_{timestamp}.txt"
    
    with open(report_file, 'w') as f:
        f.write("LEGAL ASSISTANT - TEST REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Run tests and capture output
        result = subprocess.run([
            sys.executable, 'test_application.py'
        ], capture_output=True, text=True)
        
        f.write("TEST RESULTS:\n")
        f.write(result.stdout)
        
        if result.stderr:
            f.write("\nERRORS:\n")
            f.write(result.stderr)
    
    print(f"📄 Test report saved as: {report_file}")
    return report_file

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Legal Assistant Test Runner')
    parser.add_argument('--basic', action='store_true', help='Run basic tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--security', action='store_true', help='Run security tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--check-keys', action='store_true', help='Check API keys')
    parser.add_argument('--report', action='store_true', help='Generate test report')
    
    args = parser.parse_args()
    
    print("🏥 LEGAL ASSISTANT TEST RUNNER")
    print("=" * 40)
    
    # Check dependencies first
    if args.check_deps or not any(vars(args).values()):
        if not check_dependencies():
            print("❌ Cannot run tests without required dependencies")
            return 1
    
    # Check API keys
    if args.check_keys or not any(vars(args).values()):
        test_api_keys()
    
    # Run specific test suites
    success = True
    
    if args.basic:
        run_basic_tests()
    elif args.integration:
        run_integration_tests()
    elif args.security:
        run_security_tests()
    elif args.performance:
        run_performance_tests()
    elif args.all:
        success = run_all_tests()
    elif args.report:
        generate_test_report()
    else:
        # Run all tests by default
        success = run_all_tests()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests completed successfully!")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())