import os
import logging
from openai import OpenAI
from config import OPENAI_API_KEY

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
Ești un analist juridic senior cu expertiză în dreptul contractelor, dreptul societar, dreptul imobiliar și revizuirea generală a documentelor juridice.

Te rog să furnizezi o analiză cuprinzătoare a următorului/următoarelor document(e) juridic(e). Analiza ta trebuie să includă:

1. **Tipul și Scopul Documentului**: Identifică tipul documentului juridic și scopul său principal.
2. **Prevederi Juridice Cheie**: Evidențiază cele mai importante clauze, termeni și prevederi juridice.
3. **Drepturi și Obligații**: Prezintă clar drepturile și obligațiile fiecărei părți implicate.
4. **Evaluarea Riscurilor**: Identifică riscurile juridice potențiale, răspunderile sau clauzele îngrijorătoare.
5. **Probleme de Conformitate**: Notează cerințele de conformitate cu reglementările sau potențialele încălcări.
6. **Elemente Lipsă**: Indică orice clauze sau prevederi standard care par să lipsească.
7. **Recomandări**: Oferă recomandări specifice și aplicabile pentru îmbunătățiri sau domenii care necesită atenție.
8. **Semnale de Alarmă**: Evidențiază termenii sau clauzele care ar trebui revizuite cu atenție sau negociate.

Te rog să structurezi răspunsul într-un format clar și profesional, potrivit pentru profesioniștii juridici. Folosește puncte și titluri clare pentru o lectură ușoară.
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
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
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
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
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
            model="gpt-4o",
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
    Generate a legal chat response based on user question and document analysis context.
    """
    try:
        if not message.strip():
            return "Vă rugăm să introduceți o întrebare validă."
        
        if conversation_history is None:
            conversation_history = []
        
        # Create system prompt for legal assistant
        system_prompt = f"""
        Ești un asistent legal virtual specializat în analiza documentelor juridice românești.
        
        IMPORTANT: Răspunde DOAR la întrebări care sunt strict legate de aspectele legale ale documentului analizat.
        
        Contextul documentului analizat:
        {analysis_context[:3000] if analysis_context else 'Nu este disponibil contextul documentului.'}
        
        Instrucțiuni:
        1. Răspunde doar la întrebări despre aspectele legale ale documentului specific
        2. Dacă întrebarea nu este legată de document, explică că nu poți răspunde
        3. Oferă răspunsuri practice și clare
        4. Menționează că sfaturile sunt generale și nu înlocuiesc consultarea unui avocat
        5. Folosește limba română
        6. Limitează răspunsul la 300 de cuvinte maximum
        7. Evidențiază riscurile importante cu ⚠️
        8. Folosește puncte pentru claritate
        
        Exemple de întrebări la care poți răspunde:
        - Obligațiile părților din contract
        - Termene și deadline-uri importante
        - Clauze problematice sau riscante
        - Drepturi și responsabilități
        - Consecințe legale
        - Proceduri de reziliere
        
        Nu răspunde la:
        - Întrebări generale despre drept fără legătură cu documentul
        - Solicitări de consiliere juridică specifică
        - Întrebări despre alte documente
        - Subiecte non-juridice
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
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=messages,
            max_tokens=500,
            temperature=0.3,
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        chat_response = response.choices[0].message.content.strip()
        
        # Add disclaimer to response
        if not "consultați un avocat" in chat_response.lower():
            chat_response += "\n\n💡 **Disclaimer**: Aceste informații sunt generale. Pentru sfaturi juridice specifice, consultați un avocat calificat."
        
        return chat_response
        
    except Exception as e:
        logging.error(f"Error in legal chat response: {str(e)}")
        if "rate limit" in str(e).lower():
            return "Momentan sistemul este suprasolicitat. Vă rugăm să încercați din nou în câteva momente."
        elif "api" in str(e).lower():
            return "Ne pare rău, serviciul este temporar indisponibil. Vă rugăm să încercați din nou mai târziu."
        else:
            return "A apărut o eroare neașteptată. Vă rugăm să reformulați întrebarea sau să încercați din nou."
