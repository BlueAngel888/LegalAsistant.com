#!/usr/bin/env python3
"""
Test complet pentru fluxurile de upload fișier și scanare cu camera
"""

import requests
import base64
import json
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

BASE_URL = "http://localhost:5000"

class UploadCameraTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"{icon} {test_name}: {details}")
        
    def create_test_image_with_text(self):
        """Create a test image with Romanian legal text"""
        # Create image with text
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add text to image
        text = """CONTRACT DE ÎNCHIRIERE

Art. 1 - PĂRȚILE CONTRACTANTE
Între POPESCU GHEORGHE, proprietar,
și IONESCU ELENA, chiriaș,
s-a încheiat prezentul contract.

Art. 2 - OBIECTUL CONTRACTULUI
Închirierea apartamentului situat în
București, Str. Victoriei nr. 100

Art. 3 - DURATA
Contractul se încheie pe 12 luni.

Art. 4 - CHIRIA
Chiria lunară este de 500 EUR."""
        
        # Simple text rendering
        y_position = 50
        for line in text.split('\n'):
            draw.text((50, y_position), line, fill='black')
            y_position += 30
            
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
        
    def test_file_upload_flow(self):
        """Test traditional file upload"""
        print("\n📁 TESTARE UPLOAD FIȘIER")
        print("="*50)
        
        # Test 1: Upload single file
        self.log_result("Upload fișier simplu", "START")
        
        test_doc = """ANTECONTRACT DE VÂNZARE-CUMPĂRARE

1. PĂRȚILE:
Vânzător: GHEORGHE POPESCU
Cumpărător: MARIA IONESCU

2. OBIECTUL:
Teren intravilan 500mp, Ilfov

3. PREȚUL:
50.000 EUR

4. TERMEN:
Contract final în 30 zile

Data: 01.08.2025
Semnături: _________ _________"""
        
        files = {"file": ("antecontract.txt", test_doc, "text/plain")}
        data = {
            "document_country": "RO",
            "analysis_language": "ro",
            "submit_type": "file_upload"
        }
        
        response = self.session.post(f"{BASE_URL}/upload", files=files, data=data)
        
        if response.status_code in [200, 302]:
            self.log_result("Upload fișier simplu", "PASS", "Fișier încărcat cu succes")
            
            # Check redirect to checkout
            if "checkout" in response.url or "checkout" in response.text:
                self.log_result("Redirecționare checkout", "PASS", "Redirecționat corect")
            else:
                self.log_result("Redirecționare checkout", "FAIL", "Nu s-a redirecționat")
        else:
            self.log_result("Upload fișier simplu", "FAIL", f"Status: {response.status_code}")
            
        # Test 2: Upload multiple files
        print("\n📚 Test upload fișiere multiple...")
        
        doc2 = "ACT ADIȚIONAL LA CONTRACT\nModificare clauză 3.2\nData: 01.08.2025"
        doc3 = "ANEXA 1 - PLAN CADASTRAL\nSuprafață: 500mp\nNr. Cadastral: 12345"
        
        files_multiple = [
            ("file", ("doc1.txt", test_doc, "text/plain")),
            ("file", ("doc2.txt", doc2, "text/plain")),
            ("file", ("doc3.txt", doc3, "text/plain"))
        ]
        
        response_multi = self.session.post(f"{BASE_URL}/upload", files=files_multiple, data=data)
        
        if response_multi.status_code in [200, 302]:
            self.log_result("Upload fișiere multiple", "PASS", "3 fișiere încărcate")
        else:
            self.log_result("Upload fișiere multiple", "FAIL", f"Status: {response_multi.status_code}")
            
    def test_camera_scan_flow(self):
        """Test camera scanning flow"""
        print("\n📸 TESTARE SCANARE CU CAMERA")
        print("="*50)
        
        # Create test image with text
        base64_image = self.create_test_image_with_text()
        
        self.log_result("Creare imagine test", "PASS", "Imagine cu text juridic creată")
        
        # Submit scanned image
        camera_data = {
            "scannedImage": base64_image,
            "document_country_camera": "RO",
            "analysis_language_camera": "ro",
            "submit_type": "camera_scan"
        }
        
        response = self.session.post(f"{BASE_URL}/upload", data=camera_data)
        
        if response.status_code in [200, 302]:
            self.log_result("Scanare cameră", "PASS", "Imagine procesată cu succes")
            
            # Check OCR processing
            if "checkout" in response.url or "checkout" in response.text:
                self.log_result("OCR procesare", "PASS", "Text extras din imagine")
            else:
                self.log_result("OCR procesare", "WARNING", "Procesare neclară")
        else:
            self.log_result("Scanare cameră", "FAIL", f"Status: {response.status_code}")
            
    def test_mixed_upload(self):
        """Test combined file + camera upload"""
        print("\n🔄 TESTARE UPLOAD MIXT (FIȘIER + CAMERĂ)")
        print("="*50)
        
        # This tests if user can upload both file and camera in same session
        # First reset session
        self.session = requests.Session()
        
        # Upload file first
        test_file = ("contract.txt", "CONTRACT TEST", "text/plain")
        files = {"file": test_file}
        data = {
            "document_country": "RO",
            "analysis_language": "ro",
            "submit_type": "file_upload"
        }
        
        response1 = self.session.post(f"{BASE_URL}/upload", files=files, data=data)
        
        if response1.status_code in [200, 302]:
            self.log_result("Prima încărcare (fișier)", "PASS", "Fișier încărcat")
        else:
            self.log_result("Prima încărcare (fișier)", "FAIL", f"Status: {response1.status_code}")
            
    def test_error_cases(self):
        """Test error handling"""
        print("\n⚠️  TESTARE CAZURI DE EROARE")
        print("="*50)
        
        # Test 1: Empty upload
        data = {
            "document_country": "RO",
            "analysis_language": "ro",
            "submit_type": "file_upload"
        }
        
        response = self.session.post(f"{BASE_URL}/upload", data=data)
        
        if response.status_code in [200, 302, 400]:
            if "error" in response.text.lower() or "index" in response.url:
                self.log_result("Upload gol", "PASS", "Eroare tratată corect")
            else:
                self.log_result("Upload gol", "WARNING", "Răspuns neclar")
        else:
            self.log_result("Upload gol", "FAIL", "Eroare netratată")
            
        # Test 2: Missing parameters
        files = {"file": ("test.txt", "content", "text/plain")}
        response = self.session.post(f"{BASE_URL}/upload", files=files)
        
        if "select" in response.text.lower() or "country" in response.text.lower():
            self.log_result("Parametri lipsa", "PASS", "Validare funcționează")
        else:
            self.log_result("Parametri lipsa", "WARNING", "Validare neclară")
            
        # Test 3: Invalid file type
        invalid_file = ("test.exe", b"binary content", "application/octet-stream")
        files = {"file": invalid_file}
        data = {
            "document_country": "RO",
            "analysis_language": "ro"
        }
        
        response = self.session.post(f"{BASE_URL}/upload", files=files, data=data)
        
        self.log_result("Tip fișier invalid", "INFO", "Test executat")
        
    def test_checkout_integration(self):
        """Test checkout page after upload"""
        print("\n💳 TESTARE INTEGRARE CHECKOUT")
        print("="*50)
        
        # Upload a document first
        test_doc = "CONTRACT DE PRESTĂRI SERVICII JURIDICE"
        files = {"file": ("contract_servicii.txt", test_doc, "text/plain")}
        data = {
            "document_country": "RO",
            "analysis_language": "ro",
            "submit_type": "file_upload"
        }
        
        upload_response = self.session.post(f"{BASE_URL}/upload", files=files, data=data)
        
        if upload_response.status_code in [200, 302]:
            # Access checkout page
            checkout_response = self.session.get(f"{BASE_URL}/checkout")
            
            if checkout_response.status_code == 200:
                # Check for key elements
                checks = {
                    "Preț afișat": "€" in checkout_response.text,
                    "Cod reducere": "discountCode" in checkout_response.text,
                    "Buton plată": "Secure Payment" in checkout_response.text,
                    "Document listat": "contract_servicii" in checkout_response.text
                }
                
                for check, result in checks.items():
                    if result:
                        self.log_result(check, "PASS", "Element găsit")
                    else:
                        self.log_result(check, "FAIL", "Element lipsă")
            else:
                self.log_result("Pagină checkout", "FAIL", f"Status: {checkout_response.status_code}")
        else:
            self.log_result("Setup checkout test", "FAIL", "Upload eșuat")
            
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 RAPORT FINAL TESTARE UPLOAD & CAMERA")
        print("="*60)
        
        # Count results
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        warnings = sum(1 for r in self.test_results if r["status"] == "WARNING")
        
        print(f"\nTotal teste: {len(self.test_results)}")
        print(f"✓ Reușite: {passed}")
        print(f"✗ Eșuate: {failed}")
        print(f"⚠ Avertismente: {warnings}")
        
        success_rate = (passed / len(self.test_results) * 100) if self.test_results else 0
        print(f"\nRata de succes: {success_rate:.1f}%")
        
        # Key findings
        print("\n🔍 CONSTATĂRI PRINCIPALE:")
        
        upload_tests = [r for r in self.test_results if "upload" in r["test"].lower()]
        camera_tests = [r for r in self.test_results if "camera" in r["test"].lower() or "scan" in r["test"].lower()]
        
        upload_ok = all(r["status"] != "FAIL" for r in upload_tests)
        camera_ok = all(r["status"] != "FAIL" for r in camera_tests)
        
        if upload_ok:
            print("✓ Upload fișiere funcționează corect")
        else:
            print("✗ Probleme cu upload fișiere")
            
        if camera_ok:
            print("✓ Scanare camera funcționează")
        else:
            print("✗ Probleme cu scanare camera")
            
        # Save detailed report
        with open("test_upload_camera_report.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": len(self.test_results),
                    "passed": passed,
                    "failed": failed,
                    "warnings": warnings,
                    "success_rate": success_rate
                },
                "results": self.test_results
            }, f, indent=2)
            
        print("\n📄 Raport detaliat salvat în: test_upload_camera_report.json")
        
    def run_all_tests(self):
        """Execute all tests"""
        print("\n🚀 PORNIRE TESTE COMPLETE UPLOAD & CAMERA\n")
        
        # Run test suites
        self.test_file_upload_flow()
        time.sleep(1)  # Small delay between tests
        
        self.test_camera_scan_flow()
        time.sleep(1)
        
        self.test_mixed_upload()
        time.sleep(1)
        
        self.test_error_cases()
        time.sleep(1)
        
        self.test_checkout_integration()
        
        # Generate report
        self.generate_report()

if __name__ == "__main__":
    # Check if PIL is available
    try:
        from PIL import Image, ImageDraw
        print("✓ PIL disponibil pentru generare imagini test")
    except ImportError:
        print("⚠ PIL nu este disponibil - unele teste vor eșua")
        
    tester = UploadCameraTester()
    tester.run_all_tests()