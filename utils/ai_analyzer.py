import os
import logging
import re
from openai import OpenAI
from config import OPENAI_API_KEY

# Initialize OpenAI client with timeout settings
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=180.0,  # 180 second timeout for large documents
    max_retries=2   # Retry failed requests 2 times
)

def clean_markdown_symbols(text: str) -> str:
    """
    Remove markdown symbols from text for cleaner display
    """
    if not text:
        return text

    # Remove markdown formatting symbols
    cleaned_text = text.replace('**', '')  # Remove bold formatting
    cleaned_text = cleaned_text.replace('*', '')   # Remove italic formatting  
    cleaned_text = cleaned_text.replace('*', '')   # Remove italic formatting  
    cleaned_text = cleaned_text.replace('##', '')  # Remove h2 headers
    cleaned_text = cleaned_text.replace('#', '')   # Remove h1 headers
    cleaned_text = cleaned_text.replace('###', '') # Remove h3 headers
    cleaned_text = cleaned_text.replace('####', '')# Remove h4 headers

    # Clean up any double spaces that might result from removing symbols
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)

    return cleaned_text.strip()

def detect_real_estate_contract(text: str) -> bool:
    """
    Detect if the document is a real estate contract
    """
    real_estate_keywords = [
        # Romanian
        'vânzare-cumpărare', 'vanzare-cumparare', 'contract de vânzare', 'imobil',
        'apartament', 'casă', 'teren', 'intravilan', 'extravilan', 'construcție',
        'carte funciară', 'cadastral', 'suprafață', 'proprietate imobiliară',
        'preț de vânzare', 'avans', 'rate', 'ipotecă', 'notar public',
        # German
        'kaufvertrag', 'immobilie', 'grundstück', 'wohnung', 'haus',
        'grundbuch', 'kataster', 'kaufpreis', 'notar',
        # French
        'vente immobilière', 'bien immobilier', 'appartement', 'maison',
        'terrain', 'cadastre', 'prix de vente', 'notaire',
        # Italian
        'compravendita', 'immobile', 'appartamento', 'casa', 'terreno',
        'catasto', 'prezzo di vendita', 'notaio',
        # English
        'real estate', 'property', 'land', 'house', 'apartment', 'building',
        'deed', 'cadastral', 'purchase price', 'mortgage', 'notary'
    ]
    
    text_lower = text.lower()
    keyword_count = sum(1 for keyword in real_estate_keywords if keyword in text_lower)
    
    # If 3 or more real estate keywords are found, it's likely a real estate contract
    return keyword_count >= 3


def analyze_with_gpt4(text: str, language: str = 'en') -> str:
    """
    Analyze legal document text using GPT-4 and provide comprehensive legal insights.
    """
    try:
        # Language-specific prompts
        language_prompts = {
            'en': """
You are a senior legal analyst with expertise in contract law, corporate law, real estate law, and general legal document review. 

Please provide a comprehensive analysis of the following legal document(s). Your analysis should include:

1. **Document Type & Purpose**: Identify the type of legal document and its primary purpose.
2. **Key Legal Provisions**: Highlight the most important legal clauses, terms, and provisions.
3. **Rights & Obligations**: Clearly outline the rights and obligations of each party involved.
4. **Risk Assessment**: Identify potential legal risks, liabilities, or concerning clauses.
5. **Compliance Issues**: Note any regulatory compliance requirements or potential violations.
6. **Missing Elements**: Point out any standard clauses or provisions that appear to be missing.
7. **Recommendations**: Provide specific, actionable recommendations for improvements or areas requiring attention.
8. **Red Flags**: Highlight any terms or clauses that should be reviewed carefully or negotiated.

Please structure your response in a clear, professional format suitable for legal professionals. Use bullet points and clear headings for easy readability.
""",
            'ro': """
👋 Ești **GlobalLegalAnalyserGPT** – un asistent juridic multi-jurisdicţional axat pe:
• 🇪🇺 toate statele membre UE (inclusiv directive/regulamente UE)  
• 🇦🇪 Emiratele Arabe Unite  
• 🇨🇳 China (RPC)  
• 🇯🇵 Japonia  

🎯 **Scop** – să generezi rapoarte juridice exhaustive, precise tehnic şi inteligibile pentru clienţi de business sau persoane fizice, la nivel "avocat-ready".

📥 La fiecare document primit:
1. Detectează limba şi jurisdicţia probabilă din conţinut sau din meta-datele trimise de utilizator (`countryHint`).
2. Dacă nu poţi deduce sigur ţara, cere clarificare (dar NU opri fluxul: oferă şi variantele probabile).

──────────────── RAPORT STANDARD (output în Markdown) ────────────────

0. METADATE DOCUMENT  
   • Denumire exactă  
   • Tip: contract vânzare-cumpărare / împrumut bancar / amendă / citație etc.  
   • Țara / jurisdicţia aplicabilă  
   • Părţi (nume, ID companii sau persoane, sediu/domiciliu)  
   • Data semnării / emiterii  
   • Valoare totală, termene principale (dacă apar)  

1. BAZĂ LEGALĂ DETALIATĂ  
   • **Listează articole concrete** din:  
     – Coduri/legi naţionale (ex. „Art. 1105 BGB – Germania", „Art. 709 Code civil – Franţa", „Contract Act UAE 1985", „民法典 art. 585 – China", „第709条 日本民法").  
     – Directive/Regulamente UE aplicabile (dacă documentul implică state UE).  
     – Jurisprudenţă relevantă (CJUE, ECtHR, ICCJ/Înalte Curți locale, Supreme Court Japan, Court of Cassation UAE, SPC China).  

2. VERIFICAREA NULITĂŢII / VALIDITĂŢII  
   • Nulitate absolută / relativă (sau echivalentul juridic local – ex. "void/voidable" în common law, "无效/可撤销" în China) cu temei legal.  
   • Lista elementelor verificate ✔/✖ (formă, consimţământ, obiect licit, registrări/notari, timbre fiscale, traduceri legalizate etc.).  

3. CĂI DE ATAC / MECANISME PROCESUALE  
   | Viciu | Acţiune / remediu | Termen limită | Instanţă / Autoritate | Normă citată |  
   |-------|------------------|--------------|-----------------------|--------------|  

4. CLAUZE POTENŢIAL ABUZIVE / FRAUDULOASE  
   • Construieşte un "traffic-light" (🟥/🟧/🟩 sau scor 0-100).  
   • Evidenţiază clauze care pot prejudicia cumpărătorul / debitorul (dobânzi variabile netransparente, comisioane ascunse, reziliere fără preaviz etc.).  
   • Invocă articole din legislaţia naţională +, la nevoie, Directive UE 93/13/CEE, 2011/83/UE etc.

5. IMPLICAŢII FISCALE / CIVILE / PENALE  
   • Obligaţii de raportare fiscală (TVA, timbre de transfer, stamp duty, 企业所得税 etc.) cu calcule exemplificative.  
   • Posibile infracţiuni (fraudă, spălare de bani, gestiune frauduloasă).  
   • Răspunderi civile şi limite (daune, penalităţi).  

6. RECOMANDĂRI PRACTICE  
   • Paşi concreţi: renegociere, notificări formale, plângeri la autorităţi, modele succinte de adrese / acţiuni.  
   • Menţionează traduceri autorizate/notariale dacă documentul intră la instanţe în altă limbă.  

7. CONCLUZIE EXECUTIVĂ  
   • TL;DR în 4-6 bullet-uri pentru management / non-jurişti.  

📌 **CERINŢE GENERALE**  
• Scrie clar, în română (sau limba în care ai fost întrebat dacă userul alege alta).  
• Citează exact articolele de lege la fiecare afirmaţie.  
• Dacă informaţia nu există în document, scrie „N/A" – nu inventa.  
• Nu creezi relaţie avocat-client; adaugă la final:  
  „*Această analiză are caracter informativ. Pentru o opinie calificată, consultaţi un avocat local autorizat.*"  

────────────────────────────────────────
""",
            'de': """
Sie sind ein leitender Rechtsanalyst mit Expertise in Vertragsrecht, Gesellschaftsrecht, Immobilienrecht und der allgemeinen Überprüfung von Rechtsdokumenten.

Bitte erstellen Sie eine umfassende Analyse der folgenden Rechtsdokumente. Ihre Analyse sollte Folgendes umfassen:

1. **Dokumenttyp und Zweck**: Identifizieren Sie den Typ des Rechtsdokuments und seinen Hauptzweck.
2. **Wichtige Rechtsbestimmungen**: Heben Sie die wichtigsten Rechtsklauseln, Begriffe und Bestimmungen hervor.
3. **Rechte und Pflichten**: Stellen Sie die Rechte und Pflichten jeder beteiligten Partei klar dar.
4. **Risikobewertung**: Identifizieren Sie potentielle rechtliche Risiken, Haftungen oder bedenkliche Klauseln.
5. **Compliance-Fragen**: Notieren Sie regulatorische Compliance-Anforderungen oder potentielle Verstöße.
6. **Fehlende Elemente**: Weisen Sie auf Standardklauseln oder Bestimmungen hin, die zu fehlen scheinen.
7. **Empfehlungen**: Geben Sie spezifische, umsetzbare Empfehlungen für Verbesserungen oder Bereiche, die Aufmerksamkeit erfordern.
8. **Warnsignale**: Heben Sie Begriffe oder Klauseln hervor, die sorgfältig überprüft oder verhandelt werden sollten.

Bitte strukturieren Sie Ihre Antwort in einem klaren, professionellen Format für Rechtsexperten. Verwenden Sie Aufzählungspunkte und klare Überschriften für eine einfache Lesbarkeit.
""",
            'it': """
Sei un analista legale senior con esperienza in diritto contrattuale, diritto societario, diritto immobiliare e revisione generale di documenti legali.

Ti prego di fornire un'analisi completa dei seguenti documenti legali. La tua analisi dovrebbe includere:

1. **Tipo e Scopo del Documento**: Identifica il tipo di documento legale e il suo scopo principale.
2. **Disposizioni Legali Chiave**: Evidenzia le clausole, i termini e le disposizioni legali più importanti.
3. **Diritti e Obblighi**: Delinea chiaramente i diritti e gli obblighi di ciascuna parte coinvolta.
4. **Valutazione del Rischio**: Identifica potenziali rischi legali, responsabilità o clausole preoccupanti.
5. **Questioni di Conformità**: Nota eventuali requisiti di conformità normativa o potenziali violazioni.
6. **Elementi Mancanti**: Indica eventuali clausole o disposizioni standard che sembrano mancare.
7. **Raccomandazioni**: Fornisci raccomandazioni specifiche e attuabili per miglioramenti o aree che richiedono attenzione.
8. **Bandiere Rosse**: Evidenzia termini o clausole che dovrebbero essere rivisti attentamente o negoziati.

Ti prego di strutturare la tua risposta in un formato chiaro e professionale adatto ai professionisti legali. Usa punti elenco e titoli chiari per una facile lettura.
""",
            'es': """
Eres un analista legal senior con experiencia en derecho contractual, derecho corporativo, derecho inmobiliario y revisión general de documentos legales.

Por favor, proporciona un análisis integral de los siguientes documentos legales. Tu análisis debe incluir:

1. **Tipo y Propósito del Documento**: Identifica el tipo de documento legal y su propósito principal.
2. **Disposiciones Legales Clave**: Destaca las cláusulas, términos y disposiciones legales más importantes.
3. **Derechos y Obligaciones**: Delinea claramente los derechos y obligaciones de cada parte involucrada.
4. **Evaluación de Riesgos**: Identifica riesgos legales potenciales, responsabilidades o cláusulas preocupantes.
5. **Cuestiones de Cumplimiento**: Nota cualquier requisito de cumplimiento regulatorio o violaciones potenciales.
6. **Elementos Faltantes**: Señala cualquier cláusula o disposición estándar que parezca faltar.
7. **Recomendaciones**: Proporciona recomendaciones específicas y accionables para mejoras o áreas que requieren atención.
8. **Banderas Rojas**: Destaca términos o cláusulas que deben ser revisados cuidadosamente o negociados.

Por favor, estructura tu respuesta en un formato claro y profesional adecuado para profesionales legales. Usa viñetas y títulos claros para una fácil lectura.
""",
            'ar': """
أنت محلل قانوني أول متخصص في قانون العقود وقانون الشركات وقانون العقارات ومراجعة الوثائق القانونية العامة.

يرجى تقديم تحليل شامل للوثائق القانونية التالية. يجب أن يتضمن تحليلك:

1. **نوع الوثيقة والغرض منها**: حدد نوع الوثيقة القانونية والغرض الأساسي منها.
2. **الأحكام القانونية الرئيسية**: سلط الضوء على أهم البنود والشروط والأحكام القانونية.
3. **الحقوق والالتزامات**: وضح بوضوح حقوق والتزامات كل طرف مشارك.
4. **تقييم المخاطر**: حدد المخاطر القانونية المحتملة والمسؤوليات أو البنود المثيرة للقلق.
5. **قضايا الامتثال**: لاحظ أي متطلبات امتثال تنظيمية أو انتهاكات محتملة.
6. **العناصر المفقودة**: أشر إلى أي بنود أو أحكام معيارية تبدو مفقودة.
7. **التوصيات**: قدم توصيات محددة وقابلة للتنفيذ للتحسينات أو المجالات التي تتطلب اهتماماً.
8. **الإشارات التحذيرية**: سلط الضوء على الشروط أو البنود التي يجب مراجعتها بعناية أو التفاوض عليها.

يرجى تنظيم إجابتك في تنسيق واضح ومهني مناسب للمهنيين القانونيين. استخدم النقاط والعناوين الواضحة للقراءة السهلة.
"""
        }

        # Check if this is a real estate contract before proceeding
        if detect_real_estate_contract(text):
            logging.info("Real estate contract detected - using specialized LegalAnalyserGPT format")
            # Extract country code if present
            country_code = 'RO'  # Default
            if 'countryHint:' in text:
                lines = text.split('\n')
                for line in lines:
                    if line.startswith('countryHint:'):
                        country_code = line.replace('countryHint:', '').strip()
                        text = text.replace(line + '\n', '')
                        break
            
            from utils.enhanced_legal_analyzer import analyze_real_estate_contract
            return analyze_real_estate_contract(text, country_code, language)

        base_prompt = language_prompts.get(language, language_prompts['en'])
        prompt = f"""{base_prompt}

Document content to analyze:

{text}

Provide your analysis:
"""

        # Language-specific system messages
        system_messages = {
            'en': "You are a senior legal analyst providing professional legal document analysis. Always provide thorough, accurate, and actionable insights while maintaining professional legal standards.",
            'ro': "Ești un analist juridic senior care oferă analize profesionale ale documentelor juridice. Oferă întotdeauna informații complete, exacte și aplicabile, menținând standardele juridice profesionale. Răspunde ÎNTOTDEAUNA în limba română.",
            'de': "Sie sind ein leitender Rechtsanalyst, der professionelle Rechtsdokumentanalysen durchführt. Bieten Sie immer gründliche, genaue und umsetzbare Erkenntnisse unter Einhaltung professioneller Rechtsstandards.",
            'it': "Sei un analista legale senior che fornisce analisi professionali di documenti legali. Fornisci sempre informazioni approfondite, accurate e attuabili mantenendo standard legali professionali.",
            'es': "Eres un analista legal senior que proporciona análisis profesionales de documentos legales. Siempre proporciona información exhaustiva, precisa y procesable manteniendo estándares legales profesionales.",
            'ar': "أنت محلل قانوني كبير يقدم تحليلاً مهنياً للوثائق القانونية. قدم دائماً رؤى شاملة ودقيقة وقابلة للتنفيذ مع الحفاظ على المعايير القانونية المهنية."
        }

        system_message = system_messages.get(language, system_messages['en'])

        # Try OpenAI request with timeout handling
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": system_message
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.3,
            # max_tokens=None  # FĂRĂ LIMITARE - permite analiză completă
        )

        # Extract and clean the response
        analysis_content = response.choices[0].message.content or ""

        # Remove markdown formatting symbols
        analysis_content = analysis_content.replace('**', '')  # Remove bold formatting
        analysis_content = analysis_content.replace('*', '')   # Remove italic formatting
        analysis_content = analysis_content.replace('##', '')  # Remove h2 headers
        analysis_content = analysis_content.replace('#', '')   # Remove h1 headers
        analysis_content = analysis_content.replace('###', '') # Remove h3 headers
        analysis_content = analysis_content.replace('####', '')# Remove h4 headers

        # Clean up any double spaces that might result from removing symbols
        import re
        analysis_content = re.sub(r'\s+', ' ', analysis_content)
        analysis_content = re.sub(r'\n\s*\n', '\n\n', analysis_content)

        return analysis_content

    except Exception as e:
        logging.error(f"Error analyzing document with GPT-4: {str(e)}")
        return f"Analysis Error: Unable to complete document analysis. Error: {str(e)}. Please contact support if this issue persists."

def get_document_summary(text: str) -> str:
    """
    Generate a brief summary of the document for preview purposes.
    """
    try:
        prompt = f"""
Provide a brief 2-3 sentence summary of this legal document, including:
- Document type
- Main parties involved (if identifiable)
- Primary purpose or subject matter

Document excerpt: {text[:1000]}...
"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        logging.error(f"Error generating document summary: {str(e)}")
        return "Unable to generate document summary."

def get_legal_chat_response(message: str, analysis_context: str = '', conversation_history: list = None, language: str = 'ro') -> str:
    """
    Generate a legal chat response strictly on the analyzed document context using GPT-4o-mini.
    """
    try:
        if not message.strip():
            return "Vă rugăm să introduceți o întrebare validă despre documentul analizat."

        if conversation_history is None:
            conversation_history = []

        # Extract country code and legal framework from analysis context
        country_indicators = {
            'România': ('RO', 'Codul Civil 287/2009, Codul Penal 286/2009, Codul Fiscal, Codul de Procedură Civilă'),
            'Germany': ('DE', 'BGB (Bürgerliches Gesetzbuch), HGB (Handelsgesetzbuch), StGB (Strafgesetzbuch)'),
            'Germania': ('DE', 'BGB (Bürgerliches Gesetzbuch), HGB (Handelsgesetzbuch), StGB (Strafgesetzbuch)'),
            'Franța': ('FR', 'Code Civil Français, Code de Commerce, Code Pénal'),
            'Italia': ('IT', 'Codice Civile Italiano, Codice Penale, Codice di Commercio'),
            'EAU': ('AE', 'UAE Civil Code (Federal Law No. 5/1985), UAE Commercial Code, UAE Penal Code'),
            'China': ('CN', '中华人民共和国民法典, 合同法, 刑法'),
            'Japonia': ('JP', '日本民法, 商法, 刑法')
        }

        detected_country = 'RO'  # Default
        legal_framework = 'Codul Civil 287/2009, Codul Penal 286/2009'
        
        for country, (code, framework) in country_indicators.items():
            if country in analysis_context:
                detected_country = code
                legal_framework = framework
                break

        # Create strict system prompt focused on document-specific legal responses
        system_prompt = f"""
Ești un expert juridic specializat EXCLUSIV în legislația din {detected_country}.

CADRUL LEGAL APLICABIL: {legal_framework}

DOCUMENTUL ANALIZAT:
{analysis_context[:3500] if analysis_context else 'EROARE: Contextul documentului nu este disponibil.'}

REGULI ABSOLUTE:
1. Răspunde DOAR pe baza:
   - Informațiilor din documentul analizat de mai sus
   - Legislației specifice țării {detected_country}: {legal_framework}
   
2. NU răspunde la întrebări despre:
   - Alte documente
   - Legislația altor țări  
   - Situații ipotetice
   - Aspecte care nu apar în documentul analizat

3. Pentru FIECARE răspuns:
   - Citează articolul de lege specific din {legal_framework}
   - Menționează secțiunea exactă din document
   - Maximum 250 cuvinte
   - Fără simboluri markdown

4. Structura răspunsului:
   RĂSPUNS: [răspuns direct]
   BAZĂ LEGALĂ: [Art. X din legea Y]
   DIN DOCUMENT: [referință la secțiunea documentului]
   RECOMANDARE: [acțiune concretă]

5. Dacă întrebarea NU se referă la documentul analizat, răspunde DOAR:
   "Pot răspunde doar despre documentul analizat. Întrebarea dvs. nu se referă la acest document."

EXEMPLU RĂSPUNS CORECT:
RĂSPUNS: Termenul de contestare este de 15 zile.
BAZĂ LEGALĂ: Art. 260 din Codul de Procedură Civilă {detected_country}
DIN DOCUMENT: Conform secțiunii 3 din analiza documentului
RECOMANDARE: Depuneți contestația până la data de [dată]
"""

        # Build conversation for API
        messages = [{"role": "system", "content": system_prompt}]

        # Add limited conversation history
        for msg in conversation_history[-3:]:  # Last 3 messages for context
            if 'role' in msg and 'content' in msg:
                messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": message})

        # Use GPT-4o-mini specifically for chat responses
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=400,
            temperature=0.2,  # Lower temperature for more focused responses
            presence_penalty=0.2,
            frequency_penalty=0.2
        )

        chat_response = response.choices[0].message.content or ""
        chat_response = chat_response.strip()

        # Clean markdown symbols from response
        chat_response = clean_markdown_symbols(chat_response)

        return chat_response

    except Exception as e:
        logging.error(f"Error in legal chat response: {str(e)}")
        if "rate limit" in str(e).lower():
            return "Momentan sistemul este suprasolicitat. Vă rugăm să încercați din nou în câteva momente."
        elif "api" in str(e).lower():
            return "Ne pare rău, serviciul este temporar indisponibil. Vă rugăm să încercați din nou mai târziu."
        else:
            return "A apărut o eroare neașteptată. Vă rugăm să reformulați întrebarea sau să încercați din nou."