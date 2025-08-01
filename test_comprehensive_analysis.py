#!/usr/bin/env python3
"""
Comprehensive Test Suite for Legal Assistant Application
Tests all major functionality paths and generates detailed report
"""

import requests
import json
import time
import os
from datetime import datetime
from urllib.parse import urljoin

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_DOCUMENT = """CONTRACT DE VÂNZARE-CUMPĂRARE

I. PĂRȚILE CONTRACTANTE
Între subsemnatul POPESCU ION, domiciliat în București, str. Victoriei nr. 10, 
identificat cu CI seria RR nr. 123456, în calitate de VÂNZĂTOR,

și

IONESCU MARIA, domiciliată în Cluj-Napoca, str. Eroilor nr. 25, 
identificată cu CI seria KX nr. 789012, în calitate de CUMPĂRĂTOR,

a intervenit prezentul contract de vânzare-cumpărare.

II. OBIECTUL CONTRACTULUI
Vânzătorul vinde și cumpărătorul cumpără apartamentul situat în București, 
str. Unirii nr. 15, bl. A1, sc. B, et. 3, ap. 12, compus din 3 camere, 
în suprafață de 75 mp.

III. PREȚUL
Prețul convenit este de 95.000 EUR (nouăzeci și cinci mii euro), 
achitat integral la data semnării prezentului contract.

IV. CLAUZE SPECIALE
1. Vânzătorul garantează că imobilul este liber de sarcini.
2. Predarea imobilului se va face în termen de 30 de zile.
3. Cheltuielile notariale vor fi suportate în mod egal de ambele părți.

Data: 01.08.2025
Semnături: _____________    _____________
"""

class LegalAssistantTester:
    def __init__(self):
        self.session = requests.Session()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        
    def log_test(self, test_name, status, details="", error=None):
        """Log test results"""
        test_result = {
            "name": test_name,
            "status": status,
            "details": details,
            "error": str(error) if error else None,
            "timestamp": datetime.now().isoformat()
        }
        self.results["tests"].append(test_result)
        self.results["summary"]["total"] += 1
        
        if status == "PASS":
            self.results["summary"]["passed"] += 1
            print(f"✓ {test_name} - PASSED")
        elif status == "FAIL":
            self.results["summary"]["failed"] += 1
            print(f"✗ {test_name} - FAILED: {error}")
        elif status == "WARNING":
            self.results["summary"]["warnings"] += 1
            print(f"⚠ {test_name} - WARNING: {details}")
            
    def test_homepage(self):
        """Test homepage accessibility"""
        try:
            response = self.session.get(BASE_URL)
            if response.status_code == 200:
                self.log_test("Homepage Access", "PASS", "Homepage loaded successfully")
                # Check for key elements
                if "Legal Document Analysis" in response.text:
                    self.log_test("Homepage Content", "PASS", "Key content found")
                else:
                    self.log_test("Homepage Content", "WARNING", "Expected content not found")
            else:
                self.log_test("Homepage Access", "FAIL", error=f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Homepage Access", "FAIL", error=str(e))
            
    def test_file_upload_flow(self):
        """Test file upload with LETSGO code"""
        try:
            # Create test file
            test_file = ("test_contract.txt", TEST_DOCUMENT, "text/plain")
            
            # Upload document
            files = {"file": test_file}
            data = {
                "document_country": "RO",
                "analysis_language": "ro",
                "submit_type": "file_upload"
            }
            
            response = self.session.post(f"{BASE_URL}/upload", files=files, data=data)
            
            if response.status_code == 200:
                self.log_test("File Upload", "PASS", "Document uploaded successfully")
                
                # Check if redirected to checkout
                if "/checkout" in response.url or "checkout" in response.text:
                    self.log_test("Checkout Redirect", "PASS", "Redirected to checkout page")
                    
                    # Test LETSGO code
                    checkout_response = self.session.get(f"{BASE_URL}/checkout")
                    if "LETSGO" in checkout_response.text:
                        self.log_test("LETSGO Code Display", "PASS", "LETSGO code is displayed")
                        
                        # Submit free access code
                        free_data = {"free_code": "LETSGO"}
                        free_response = self.session.post(f"{BASE_URL}/free-access", data=free_data)
                        
                        if free_response.status_code in [200, 302]:
                            self.log_test("Free Access", "PASS", "LETSGO code accepted")
                            
                            # Check analysis result
                            if "/success" in free_response.url or free_response.status_code == 200:
                                success_response = self.session.get(f"{BASE_URL}/success")
                                if "GlobalLegalAnalyserGPT" in success_response.text or "ANALIZĂ JURIDICĂ" in success_response.text:
                                    self.log_test("Analysis Result", "PASS", "Analysis completed successfully")
                                else:
                                    self.log_test("Analysis Result", "WARNING", "Analysis page loaded but content unclear")
                        else:
                            self.log_test("Free Access", "FAIL", error=f"Status: {free_response.status_code}")
                    else:
                        self.log_test("LETSGO Code Display", "WARNING", "LETSGO code not visible on checkout")
                else:
                    self.log_test("Checkout Redirect", "FAIL", error="Not redirected to checkout")
            else:
                self.log_test("File Upload", "FAIL", error=f"Upload failed with status: {response.status_code}")
                
        except Exception as e:
            self.log_test("File Upload Flow", "FAIL", error=str(e))
            
    def test_camera_upload_flow(self):
        """Test camera capture flow"""
        try:
            # Simulate camera capture with base64 image
            camera_data = {
                "scannedImage": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                "document_country_camera": "RO",
                "analysis_language_camera": "ro",
                "submit_type": "camera_scan"
            }
            
            response = self.session.post(f"{BASE_URL}/upload", data=camera_data)
            
            if response.status_code in [200, 302]:
                self.log_test("Camera Upload", "PASS", "Camera image processed")
            else:
                self.log_test("Camera Upload", "FAIL", error=f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Camera Upload Flow", "FAIL", error=str(e))
            
    def test_api_endpoints(self):
        """Test API endpoints"""
        # Test language change
        try:
            lang_response = self.session.post(f"{BASE_URL}/set-language", 
                                            json={"language": "ro"})
            if lang_response.status_code == 200:
                self.log_test("Language API", "PASS", "Language change successful")
            else:
                self.log_test("Language API", "FAIL", error=f"Status: {lang_response.status_code}")
        except Exception as e:
            self.log_test("Language API", "FAIL", error=str(e))
            
        # Test discount code validation
        try:
            discount_response = self.session.post(f"{BASE_URL}/apply-discount",
                                                json={"code": "LETSGO"})
            if discount_response.status_code == 200:
                data = discount_response.json()
                if data.get("success") and data.get("free_access"):
                    self.log_test("Discount API", "PASS", "LETSGO code validated")
                else:
                    self.log_test("Discount API", "FAIL", error="Invalid response data")
            else:
                self.log_test("Discount API", "FAIL", error=f"Status: {discount_response.status_code}")
        except Exception as e:
            self.log_test("Discount API", "FAIL", error=str(e))
            
    def test_error_handling(self):
        """Test error handling"""
        # Test empty upload
        try:
            response = self.session.post(f"{BASE_URL}/upload", data={})
            if response.status_code in [200, 302, 400]:
                if "error" in response.text.lower() or response.status_code == 400:
                    self.log_test("Empty Upload Handling", "PASS", "Error handled correctly")
                else:
                    self.log_test("Empty Upload Handling", "WARNING", "No clear error message")
            else:
                self.log_test("Empty Upload Handling", "FAIL", error="Unexpected response")
        except Exception as e:
            self.log_test("Empty Upload Handling", "FAIL", error=str(e))
            
    def test_legal_chat(self):
        """Test legal chat functionality"""
        try:
            # First need to have an analysis
            chat_data = {
                "message": "Ce clauze abuzive are acest contract?",
                "analysis_context": "Contract de vânzare-cumpărare imobiliar",
                "conversation_history": []
            }
            
            response = self.session.post(f"{BASE_URL}/legal-chat", 
                                       json=chat_data,
                                       headers={"Content-Type": "application/json"})
            
            if response.status_code == 403:
                self.log_test("Legal Chat Access", "PASS", "Correctly requires document analysis first")
            elif response.status_code == 200:
                self.log_test("Legal Chat", "PASS", "Chat responded successfully")
            else:
                self.log_test("Legal Chat", "FAIL", error=f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Legal Chat", "FAIL", error=str(e))
            
    def test_database_connectivity(self):
        """Test database endpoints"""
        try:
            response = self.session.get(f"{BASE_URL}/debug-info")
            if response.status_code == 200:
                data = response.json()
                if data.get("database_url"):
                    self.log_test("Database Connection", "PASS", "Database configured")
                else:
                    self.log_test("Database Connection", "WARNING", "Database URL not set")
                    
                if data.get("openai_configured"):
                    self.log_test("OpenAI Configuration", "PASS", "OpenAI API configured")
                else:
                    self.log_test("OpenAI Configuration", "WARNING", "OpenAI API not configured")
                    
                if data.get("stripe_configured"):
                    self.log_test("Stripe Configuration", "PASS", "Stripe API configured")
                else:
                    self.log_test("Stripe Configuration", "WARNING", "Stripe API not configured")
            else:
                self.log_test("Debug Info", "FAIL", error=f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Debug Info", "FAIL", error=str(e))
            
    def generate_report(self):
        """Generate comprehensive test report"""
        report = f"""
===========================================
LEGAL ASSISTANT COMPREHENSIVE TEST REPORT
===========================================
Timestamp: {self.results['timestamp']}

SUMMARY
-------
Total Tests: {self.results['summary']['total']}
Passed: {self.results['summary']['passed']} ✓
Failed: {self.results['summary']['failed']} ✗
Warnings: {self.results['summary']['warnings']} ⚠

Success Rate: {(self.results['summary']['passed'] / self.results['summary']['total'] * 100):.1f}%

DETAILED RESULTS
----------------
"""
        for test in self.results['tests']:
            status_icon = "✓" if test['status'] == "PASS" else "✗" if test['status'] == "FAIL" else "⚠"
            report += f"\n{status_icon} {test['name']}"
            if test['details']:
                report += f"\n  Details: {test['details']}"
            if test['error']:
                report += f"\n  Error: {test['error']}"
                
        # Add recommendations
        report += "\n\nRECOMMENDATIONS\n---------------\n"
        
        if self.results['summary']['failed'] > 0:
            report += "1. Fix critical failures in core functionality\n"
        if self.results['summary']['warnings'] > 0:
            report += "2. Address configuration warnings for optimal performance\n"
        if self.results['summary']['passed'] == self.results['summary']['total']:
            report += "✓ All tests passed! Application is functioning correctly.\n"
            
        # Add specific findings
        report += "\nKEY FINDINGS\n------------\n"
        
        # Check for specific issues
        openai_issues = [t for t in self.results['tests'] if 'OpenAI' in t['name'] and t['status'] != 'PASS']
        if openai_issues:
            report += "- OpenAI configuration needs attention\n"
            
        stripe_issues = [t for t in self.results['tests'] if 'Stripe' in t['name'] and t['status'] != 'PASS']
        if stripe_issues:
            report += "- Stripe payment system needs configuration\n"
            
        upload_issues = [t for t in self.results['tests'] if 'Upload' in t['name'] and t['status'] == 'FAIL']
        if upload_issues:
            report += "- File upload functionality has critical issues\n"
            
        return report
        
    def run_all_tests(self):
        """Execute all tests"""
        print("\n🔍 Starting comprehensive testing of Legal Assistant...\n")
        
        # Run test suites
        self.test_homepage()
        self.test_api_endpoints()
        self.test_database_connectivity()
        self.test_file_upload_flow()
        self.test_camera_upload_flow()
        self.test_legal_chat()
        self.test_error_handling()
        
        # Generate and save report
        report = self.generate_report()
        
        # Save to file
        with open("test_report.txt", "w") as f:
            f.write(report)
            
        # Also save JSON results
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
            
        print(report)
        
        return self.results['summary']['failed'] == 0

if __name__ == "__main__":
    tester = LegalAssistantTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)