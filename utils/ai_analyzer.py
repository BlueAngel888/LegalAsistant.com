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
""",
            'fr': """
Vous êtes un analyste juridique senior spécialisé en droit des contrats, droit des sociétés, droit immobilier et révision générale de documents juridiques.

Veuillez fournir une analyse complète des documents juridiques suivants. Votre analyse doit inclure :

1. **Type et Objectif du Document**: Identifiez le type de document juridique et son objectif principal.
2. **Dispositions Légales Clés**: Mettez en évidence les clauses, termes et dispositions juridiques les plus importants.
3. **Droits et Obligations**: Décrivez clairement les droits et obligations de chaque partie impliquée.
4. **Évaluation des Risques**: Identifiez les risques juridiques potentiels, les responsabilités ou les clauses préoccupantes.
5. **Questions de Conformité**: Notez toute exigence de conformité réglementaire ou violation potentielle.
6. **Éléments Manquants**: Signalez toute clause ou disposition standard qui semble manquer.
7. **Recommandations**: Fournissez des recommandations spécifiques et actionnables pour les améliorations ou les domaines nécessitant une attention.
8. **Signaux d'Alerte**: Mettez en évidence les termes ou clauses qui devraient être examinés attentivement ou négociés.

Veuillez structurer votre réponse dans un format clair et professionnel adapté aux professionnels du droit. Utilisez des puces et des titres clairs pour faciliter la lecture.
""",
            'zh': """
您是一位资深法律分析师，专门从事合同法、公司法、房地产法和一般法律文件审查。

请对以下法律文件提供全面分析。您的分析应包括：

1. **文件类型和目的**：确定法律文件的类型及其主要目的。
2. **关键法律条款**：突出最重要的法律条款、术语和规定。
3. **权利和义务**：清楚地概述每个相关方的权利和义务。
4. **风险评估**：识别潜在的法律风险、责任或令人担忧的条款。
5. **合规问题**：注明任何监管合规要求或潜在违规行为。
6. **缺失要素**：指出任何似乎缺失的标准条款或规定。
7. **建议**：提供具体可行的改进建议或需要关注的领域。
8. **警示信号**：突出应仔细审查或谈判的术语或条款。

请以清晰、专业的格式构建您的回复，适合法律专业人士。使用项目符号和清晰的标题以便于阅读。
""",
            'ja': """
あなたは契約法、会社法、不動産法、および一般的な法律文書のレビューに精通したシニア法律アナリストです。

以下の法律文書について包括的な分析を提供してください。分析には以下を含める必要があります：

1. **文書の種類と目的**：法律文書の種類とその主な目的を特定します。
2. **主要な法的規定**：最も重要な法的条項、用語、規定を強調します。
3. **権利と義務**：関係する各当事者の権利と義務を明確に概説します。
4. **リスク評価**：潜在的な法的リスク、責任、または懸念される条項を特定します。
5. **コンプライアンスの問題**：規制遵守要件または潜在的な違反を指摘します。
6. **欠落要素**：欠落していると思われる標準的な条項または規定を指摘します。
7. **推奨事項**：改善または注意が必要な領域について、具体的で実行可能な推奨事項を提供します。
8. **警告フラグ**：慎重に検討または交渉すべき用語または条項を強調します。

法律専門家に適した明確で専門的な形式で回答を構成してください。読みやすいように箇条書きと明確な見出しを使用してください。
""",
            'ko': """
귀하는 계약법, 회사법, 부동산법 및 일반 법률 문서 검토 전문 선임 법률 분석가입니다.

다음 법률 문서에 대한 포괄적인 분석을 제공해 주십시오. 분석에는 다음이 포함되어야 합니다:

1. **문서 유형 및 목적**: 법률 문서의 유형과 주요 목적을 식별합니다.
2. **주요 법적 조항**: 가장 중요한 법적 조항, 용어 및 규정을 강조합니다.
3. **권리 및 의무**: 관련된 각 당사자의 권리와 의무를 명확하게 설명합니다.
4. **위험 평가**: 잠재적인 법적 위험, 책임 또는 우려되는 조항을 식별합니다.
5. **규정 준수 문제**: 규제 준수 요구 사항 또는 잠재적 위반 사항을 기록합니다.
6. **누락 요소**: 누락된 것으로 보이는 표준 조항 또는 규정을 지적합니다.
7. **권장 사항**: 개선 또는 주의가 필요한 영역에 대한 구체적이고 실행 가능한 권장 사항을 제공합니다.
8. **경고 신호**: 신중하게 검토하거나 협상해야 하는 용어 또는 조항을 강조합니다.

법률 전문가에게 적합한 명확하고 전문적인 형식으로 답변을 구성하십시오. 읽기 쉽도록 글머리 기호와 명확한 제목을 사용하십시오.
""",
            'nl': """
U bent een senior juridisch analist met expertise in contractenrecht, vennootschapsrecht, vastgoedrecht en algemene beoordeling van juridische documenten.

Geef een uitgebreide analyse van de volgende juridische documenten. Uw analyse moet het volgende omvatten:

1. **Documenttype en Doel**: Identificeer het type juridisch document en het hoofddoel ervan.
2. **Belangrijkste Juridische Bepalingen**: Benadruk de belangrijkste juridische clausules, voorwaarden en bepalingen.
3. **Rechten en Verplichtingen**: Schets duidelijk de rechten en verplichtingen van elke betrokken partij.
4. **Risicobeoordeling**: Identificeer potentiële juridische risico's, aansprakelijkheden of zorgwekkende clausules.
5. **Nalevingskwesties**: Noteer eventuele regelgevende nalevingsvereisten of potentiële overtredingen.
6. **Ontbrekende Elementen**: Wijs op eventuele standaardclausules of bepalingen die lijken te ontbreken.
7. **Aanbevelingen**: Geef specifieke, uitvoerbare aanbevelingen voor verbeteringen of gebieden die aandacht vereisen.
8. **Rode Vlaggen**: Benadruk voorwaarden of clausules die zorgvuldig moeten worden beoordeeld of onderhandeld.

Structureer uw antwoord in een duidelijk, professioneel formaat dat geschikt is voor juridische professionals. Gebruik opsommingstekens en duidelijke koppen voor gemakkelijke leesbaarheid.
""",
            'pt': """
Você é um analista jurídico sênior com experiência em direito contratual, direito societário, direito imobiliário e revisão geral de documentos jurídicos.

Por favor, forneça uma análise abrangente dos seguintes documentos jurídicos. Sua análise deve incluir:

1. **Tipo e Propósito do Documento**: Identifique o tipo de documento jurídico e seu propósito principal.
2. **Disposições Legais Principais**: Destaque as cláusulas, termos e disposições jurídicas mais importantes.
3. **Direitos e Obrigações**: Delineie claramente os direitos e obrigações de cada parte envolvida.
4. **Avaliação de Riscos**: Identifique riscos jurídicos potenciais, responsabilidades ou cláusulas preocupantes.
5. **Questões de Conformidade**: Observe quaisquer requisitos de conformidade regulatória ou violações potenciais.
6. **Elementos Ausentes**: Aponte quaisquer cláusulas ou disposições padrão que pareçam estar faltando.
7. **Recomendações**: Forneça recomendações específicas e acionáveis para melhorias ou áreas que requerem atenção.
8. **Sinais de Alerta**: Destaque termos ou cláusulas que devem ser revisados cuidadosamente ou negociados.

Por favor, estruture sua resposta em um formato claro e profissional adequado para profissionais jurídicos. Use marcadores e títulos claros para facilitar a leitura.
""",
            'ru': """
Вы старший юридический аналитик с опытом работы в области договорного права, корпоративного права, права недвижимости и общего анализа юридических документов.

Пожалуйста, предоставьте всесторонний анализ следующих юридических документов. Ваш анализ должен включать:

1. **Тип и Назначение Документа**: Определите тип юридического документа и его основную цель.
2. **Ключевые Юридические Положения**: Выделите наиболее важные юридические оговорки, условия и положения.
3. **Права и Обязанности**: Четко изложите права и обязанности каждой вовлеченной стороны.
4. **Оценка Рисков**: Определите потенциальные юридические риски, ответственность или вызывающие беспокойство оговорки.
5. **Вопросы Соответствия**: Отметьте любые требования нормативного соответствия или потенциальные нарушения.
6. **Отсутствующие Элементы**: Укажите на любые стандартные оговорки или положения, которые, по-видимому, отсутствуют.
7. **Рекомендации**: Предоставьте конкретные, практические рекомендации по улучшениям или областям, требующим внимания.
8. **Красные Флажки**: Выделите условия или оговорки, которые следует тщательно проверить или обсудить.

Пожалуйста, структурируйте свой ответ в ясном, профессиональном формате, подходящем для юридических специалистов. Используйте маркеры и четкие заголовки для удобства чтения.
""",
            'tr': """
Sözleşme hukuku, şirketler hukuku, gayrimenkul hukuku ve genel hukuki belge incelemesi konusunda uzmanlığa sahip kıdemli bir hukuk analistisiniz.

Lütfen aşağıdaki hukuki belgelerin kapsamlı bir analizini sağlayın. Analiziniz şunları içermelidir:

1. **Belge Türü ve Amacı**: Hukuki belgenin türünü ve ana amacını belirleyin.
2. **Temel Hukuki Hükümler**: En önemli hukuki maddeleri, terimleri ve hükümleri vurgulayın.
3. **Haklar ve Yükümlülükler**: İlgili her tarafın haklarını ve yükümlülüklerini açıkça özetleyin.
4. **Risk Değerlendirmesi**: Potansiyel hukuki riskleri, sorumlulukları veya endişe verici maddeleri belirleyin.
5. **Uyumluluk Sorunları**: Herhangi bir düzenleyici uyumluluk gereksinimini veya potansiyel ihlalleri not edin.
6. **Eksik Unsurlar**: Eksik görünen standart maddeleri veya hükümleri işaret edin.
7. **Öneriler**: İyileştirmeler veya dikkat gerektiren alanlar için spesifik, uygulanabilir öneriler sağlayın.
8. **Kırmızı Bayraklar**: Dikkatlice incelenmesi veya müzakere edilmesi gereken terimleri veya maddeleri vurgulayın.

Lütfen yanıtınızı hukuk profesyonelleri için uygun, net ve profesyonel bir formatta yapılandırın. Kolay okunabilirlik için madde işaretleri ve net başlıklar kullanın.
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
            'de': "Sie sind ein leitender Rechtsanalyst, der professionelle Rechtsdokumentanalysen durchführt. Bieten Sie immer gründliche, genaue und umsetzbare Erkenntnisse unter Einhaltung professioneller Rechtsstandards. Antworten Sie IMMER auf Deutsch.",
            'it': "Sei un analista legale senior che fornisce analisi professionali di documenti legali. Fornisci sempre informazioni approfondite, accurate e attuabili mantenendo standard legali professionali. Rispondi SEMPRE in italiano.",
            'es': "Eres un analista legal senior que proporciona análisis profesionales de documentos legales. Siempre proporciona información exhaustiva, precisa y procesable manteniendo estándares legales profesionales. Responde SIEMPRE en español.",
            'ar': "أنت محلل قانوني كبير يقدم تحليلاً مهنياً للوثائق القانونية. قدم دائماً رؤى شاملة ودقيقة وقابلة للتنفيذ مع الحفاظ على المعايير القانونية المهنية. أجب دائماً باللغة العربية.",
            'fr': "Vous êtes un analyste juridique senior fournissant une analyse professionnelle de documents juridiques. Fournissez toujours des informations approfondies, précises et actionnables tout en maintenant des normes juridiques professionnelles. Répondez TOUJOURS en français.",
            'zh': "您是一位资深法律分析师，提供专业的法律文件分析。始终提供全面、准确和可操作的见解，同时保持专业的法律标准。始终用中文回答。",
            'ja': "あなたは専門的な法律文書分析を提供するシニア法律アナリストです。常に専門的な法律基準を維持しながら、徹底的で正確かつ実行可能な洞察を提供してください。常に日本語で回答してください。",
            'ko': "귀하는 전문적인 법률 문서 분석을 제공하는 선임 법률 분석가입니다. 전문 법률 표준을 유지하면서 항상 철저하고 정확하며 실행 가능한 통찰력을 제공하십시오. 항상 한국어로 답변하십시오.",
            'nl': "U bent een senior juridisch analist die professionele juridische documentanalyse levert. Bied altijd grondige, nauwkeurige en uitvoerbare inzichten terwijl u professionele juridische normen handhaaft. Antwoord ALTIJD in het Nederlands.",
            'pt': "Você é um analista jurídico sênior fornecendo análise profissional de documentos jurídicos. Sempre forneça insights completos, precisos e acionáveis, mantendo os padrões jurídicos profissionais. Responda SEMPRE em português.",
            'ru': "Вы старший юридический аналитик, предоставляющий профессиональный анализ юридических документов. Всегда предоставляйте тщательные, точные и практические идеи, соблюдая профессиональные юридические стандарты. Отвечайте ВСЕГДА на русском языке.",
            'tr': "Profesyonel hukuki belge analizi sağlayan kıdemli bir hukuk analistisiniz. Profesyonel hukuki standartları korurken her zaman kapsamlı, doğru ve uygulanabilir içgörüler sağlayın. HER ZAMAN Türkçe yanıt verin."
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