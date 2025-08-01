#!/usr/bin/env python3
"""
Test rapid pentru OpenAI GlobalLegalAnalyserGPT
"""

import time
from openai import OpenAI
from config import OPENAI_API_KEY

def test_globalanalyser():
    print("🔍 TEST OPENAI GLOBALANALYSER\n")
    
    # Initialize client
    client = OpenAI(api_key=OPENAI_API_KEY, timeout=60.0)
    
    # Simple test document
    test_doc = """countryHint: RO

CONTRACT DE VÂNZARE-CUMPĂRARE

Între:
1. VÂNZĂTOR: Ion Popescu, CNP 1234567890123
2. CUMPĂRĂTOR: Maria Ionescu, CNP 2345678901234

Obiect: Apartament 2 camere, situat în București, Sector 3
Preț: 85.000 EUR
Termen plată: 30 zile
"""
    
    # Test with simplified prompt
    print("1. Test cu prompt simplificat...")
    start = time.time()
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ești GlobalLegalAnalyserGPT. Analizează documentul juridic în format structurat."
                },
                {
                    "role": "user",
                    "content": f"Analizează acest contract de vânzare-cumpărare din România:\n\n{test_doc}\n\nOferă o analiză SCURTĂ în 5 secțiuni principale."
                }
            ],
            max_tokens=1000,  # Limit response length
            temperature=0.3
        )
        
        elapsed = time.time() - start
        print(f"   ✅ Succes în {elapsed:.2f} secunde")
        print(f"   Tokens folosiți: {response.usage.total_tokens}")
        print("\n   Răspuns (primele 200 caractere):")
        print(f"   {response.choices[0].message.content[:200]}...")
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ Eroare după {elapsed:.2f} secunde: {str(e)}")
    
    # Test with full GlobalLegalAnalyserGPT prompt
    print("\n\n2. Test cu prompt complet GlobalLegalAnalyserGPT...")
    start = time.time()
    
    full_prompt = """Ești **GlobalLegalAnalyserGPT**, un asistent juridic avansat. 
Analizează documentul folosind structura exactă de mai jos, fără a folosi "N/A":

**ANALIZĂ JURIDICĂ COMPLETĂ**

**1. METADATA DOCUMENTULUI**
• Tip document: [identifică tipul]
• Jurisdicție: România
• Data analizei: [data curentă]
• Părți implicate: [listează părțile]

**2. BAZA LEGALĂ ȘI VALIDITATEA**
• Cadru legal: [menționează legile aplicabile]
• Elemente esențiale: [verifică elementele]
• Validitate formală: [evaluează validitatea]

**3. VERIFICAREA LEGALITĂȚII**
• Conformitate legală: [analizează conformitatea]
• Clauze standard: [verifică prezența]
• Deficiențe formale: [identifică problemele]

**4. IMPLICAȚII JURIDICE**
• Drepturi și obligații: [detaliază pentru fiecare parte]
• Riscuri juridice: [identifică riscurile]
• Remedii legale: [sugerează soluții]

**5. ASPECTE FISCALE ȘI CIVILE**
• Obligații fiscale: [specifică taxele]
• Implicații civile: [analizează aspectele]
• Recomandări practice: [oferă sfaturi concrete]

Document de analizat:
""" + test_doc
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ești un expert juridic care analizează documente legale pentru România."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            max_tokens=2000,  # Reasonable limit
            temperature=0.3
        )
        
        elapsed = time.time() - start
        print(f"   ✅ Succes în {elapsed:.2f} secunde")
        print(f"   Tokens folosiți: {response.usage.total_tokens}")
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"   ❌ Eroare după {elapsed:.2f} secunde: {str(e)}")

if __name__ == "__main__":
    test_globalanalyser()