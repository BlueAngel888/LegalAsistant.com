import os
import logging
import re
from openai import OpenAI
from config import OPENAI_API_KEY

# Initialize OpenAI client with timeout settings
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=120.0,  # 120 second timeout for large documents
    max_retries=3   # Retry failed requests 3 times
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
            # max_tokens=4000  # LIMITARE PRINCIPALĂ - controlează lungimea analizei
        )
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

        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"Error generating document summary: {str(e)}")
        return "Unable to generate document summary."

def get_legal_chat_response(message: str, analysis_context: str = '', conversation_history: list = None, language: str = 'ro') -> str:
    """
    Generate a legal chat response strictly on the analyzed document context.
    """
    try:
        if not message.strip():
            return "Vă rugăm să introduceți o întrebare validă despre documentul analizat."

        if conversation_history is None:
            conversation_history = []

        # Extract country code from analysis context for country-specific responses
        country_indicators = {
            'România': 'RO', 'Germany': 'DE', 'Franța': 'FR', 'Italia': 'IT',
            'EAU': 'AE', 'SUA': 'US', 'Marea Britanie': 'UK'
        }

        detected_country = 'RO'  # Default
        for country, code in country_indicators.items():
            if country in analysis_context:
                detected_country = code
                break

        # Create ultra-focused system prompt for document-specific legal chat
        system_prompt = f"""
        Ești un consultant juridic expert specializat în analiza documentelor din {detected_country}, cu acces complet la analiza documentului clientului.

        CONTEXT STRICT AL DOCUMENTULUI ANALIZAT:
        {analysis_context[:4000] if analysis_context else 'EROARE: Contextul documentului nu este disponibil.'}

        REGULI STRICTE PENTRU RĂSPUNS:
        1. Răspunde EXCLUSIV pe baza informațiilor din analiza documentului de mai sus
        2. Dacă întrebarea nu poate fi răspunsă pe baza analizei documentului, spune clar "Nu pot răspunde pe baza documentului analizat"
        3. Citează secțiuni specifice din analiza documentului în răspunsul tău
        4. Oferă sfaturi concrete și aplicabile bazate pe documentul specific
        5. Limitează răspunsul la maximum 300 de cuvinte
        6. NU folosești simboluri markdown (#, *, **, etc.)
        7. Structurează răspunsul clar:
           - Răspuns direct la întrebare
           - Informații relevante din analiza documentului
           - Acțiuni concrete recomandate (dacă aplicabil)
        8. Pentru aspecte critice folosește: ATENȚIE, IMPORTANT, URGENT

        TIPURI DE ÎNTREBĂRI PERMISE (doar dacă sunt în legătură cu documentul analizat):
        - Clauze și condiții specifice din document
        - Drepturi și obligații ale părților identificate
        - Riscuri și probleme identificate în analiză
        - Termene și deadline-uri menționate în document
        - Proceduri legale aplicabile documentului specific
        - Consecințe juridice identificate în analiză
        - Modalități de protecție bazate pe documentul analizat
        - Clauze frauduloase sau problematice identificate
        - Aspecte de nulitate menționate în analiză

        INTERZIS SĂ RĂSPUNZI LA:
        - Întrebări generale despre legislație
        - Situații ipotetice nerelationate de document
        - Alte documente sau contracte
        - Sfaturi juridice generale
        - Întrebări despre proceduri care nu sunt menționate în analiza documentului

        IMPORTANT: Răspunsul tău trebuie să demonstreze că este bazat direct pe analiza documentului specific al clientului.
        """

        # Build conversation for API
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (limited)
        for msg in conversation_history[-4:]:  # Last 4 messages for context
            if 'role' in msg and 'content' in msg:
                messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": message})

        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
            temperature=0.3,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )

        chat_response = response.choices[0].message.content.strip()

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