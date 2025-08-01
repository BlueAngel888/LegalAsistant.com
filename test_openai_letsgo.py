#!/usr/bin/env python3
"""
Test pentru a verifica că LETSGO folosește OpenAI API
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_letsgo_with_openai():
    session = requests.Session()
    
    print("🔍 TEST: LETSGO cu OpenAI API\n")
    
    # Step 1: Upload document
    print("1. Upload document...")
    test_doc = """CONTRACT DE VÂNZARE-CUMPĂRARE
    
    Între subsemnații:
    1. VÂNZĂTOR: Ion Popescu
    2. CUMPĂRĂTOR: Maria Ionescu
    
    Obiect: Apartament 2 camere, București
    Preț: 85.000 EUR
    """
    
    files = {"file": ("contract_test.txt", test_doc, "text/plain")}
    data = {
        "document_country": "RO",
        "analysis_language": "ro",
        "submit_type": "file_upload"
    }
    
    upload_resp = session.post(f"{BASE_URL}/upload", files=files, data=data)
    print(f"   Status: {upload_resp.status_code}")
    
    # Step 2: Apply LETSGO code
    print("\n2. Apply LETSGO code...")
    discount_resp = session.post(f"{BASE_URL}/apply-discount", 
                                json={"code": "LETSGO"},
                                headers={"Content-Type": "application/json"})
    
    print(f"   Status: {discount_resp.status_code}")
    print(f"   Response: {discount_resp.json()}")
    
    # Step 3: Submit free access
    print("\n3. Submit free access (OpenAI API call)...")
    start_time = time.time()
    
    free_resp = session.post(f"{BASE_URL}/free-access", 
                            data={"free_code": "LETSGO"})
    
    elapsed = time.time() - start_time
    print(f"   Status: {free_resp.status_code}")
    print(f"   Timp răspuns: {elapsed:.2f} secunde")
    
    if free_resp.status_code == 200:
        # Check if we got real OpenAI analysis
        if "GlobalLegalAnalyserGPT" in free_resp.text or "ANALIZĂ JURIDICĂ" in free_resp.text:
            print("\n✅ SUCCES: Analiza folosește OpenAI API!")
            
            # Check for real estate detection
            if "imobil" in free_resp.text.lower() or "real estate" in free_resp.text.lower():
                print("   ✅ Contract imobiliar detectat corect")
        else:
            print("\n⚠️ ATENȚIE: Nu s-a găsit analiză OpenAI în răspuns")
            
    elif free_resp.status_code == 500:
        print("\n❌ EROARE 500: Probabil timeout OpenAI")
        print("   Verificați log-urile pentru detalii")
    
    # Step 4: Check analysis content
    if free_resp.status_code == 200:
        print("\n4. Verificare conținut analiză...")
        
        # Count analysis sections
        sections = [
            "IDENTIFICAREA",
            "STRUCTURA",
            "VERIFICAREA",
            "ANALIZA",
            "ASPECTE"
        ]
        
        found_sections = 0
        for section in sections:
            if section in free_resp.text.upper():
                found_sections += 1
        
        print(f"   Secțiuni găsite: {found_sections}/5")
        
        if elapsed > 5:
            print(f"   ℹ️ Timpul de răspuns ({elapsed:.1f}s) indică folosirea OpenAI API")

if __name__ == "__main__":
    test_letsgo_with_openai()