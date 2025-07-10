#!/usr/bin/env python3
"""
Test script to verify OpenAI GlobalLegalAnalyserGPT format implementation
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from utils.ai_analyzer import analyze_with_gpt4

def test_global_legal_analyser():
    """Test the new GlobalLegalAnalyserGPT format"""
    
    # Sample legal document text
    test_document = """
    countryHint: RO
    
    CONTRACT DE VÂNZARE-CUMPĂRARE
    
    Încheiat astăzi, 10.07.2025, între:
    1. VÂNZĂTOR: Popescu Ion, CNP 1234567890123, domiciliat în București, str. Victoriei nr. 10
    2. CUMPĂRĂTOR: Ionescu Maria, CNP 9876543210987, domiciliată în Cluj-Napoca, str. Eroilor nr. 5
    
    Părțile au convenit următoarele:
    
    Art. 1. Obiectul contractului
    Vânzătorul vinde și cumpărătorul cumpără apartamentul situat în București, str. Mihai Eminescu nr. 15, 
    bloc A, scara B, etaj 3, ap. 12, compus din 3 camere, în suprafață utilă de 75 mp.
    
    Art. 2. Prețul
    Prețul de vânzare este de 100.000 EUR (una sută mii euro), achitat integral la data semnării prezentului contract.
    
    Art. 3. Garanții
    Vânzătorul garantează că imobilul nu este grevat de sarcini și nu face obiectul unor litigii.
    
    Art. 4. Predarea bunului
    Predarea efectivă a apartamentului se va face în termen de 30 de zile de la data semnării contractului.
    
    Prezentul contract s-a încheiat în 3 exemplare originale.
    
    VÂNZĂTOR                    CUMPĂRĂTOR
    Popescu Ion                 Ionescu Maria
    """
    
    print("🔍 Testing GlobalLegalAnalyserGPT format...")
    print("=" * 80)
    
    try:
        # Call the analyze function with Romanian language
        analysis = analyze_with_gpt4(test_document, 'ro')
        
        print("\n✅ ANALYSIS RESULT:")
        print("-" * 80)
        print(analysis[:2000])  # Print first 2000 characters
        print("\n..." if len(analysis) > 2000 else "")
        print("-" * 80)
        
        # Check if analysis contains expected sections
        expected_sections = [
            "METADATE DOCUMENT",
            "BAZĂ LEGALĂ",
            "VERIFICAREA NULITĂŢII",
            "CĂI DE ATAC",
            "CLAUZE",
            "IMPLICAŢII",
            "RECOMANDĂRI",
            "CONCLUZIE"
        ]
        
        print("\n📋 Checking for expected sections:")
        for section in expected_sections:
            if section in analysis.upper():
                print(f"  ✅ Found: {section}")
            else:
                print(f"  ❌ Missing: {section}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_global_legal_analyser()