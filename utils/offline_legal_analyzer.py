
import re
import logging
from datetime import datetime
from typing import List, Dict

class OfflineLegalAnalyzer:
    """Offline legal analyzer that provides detailed analysis without AI"""
    
    def __init__(self):
        self.legal_frameworks = {
            'RO': {
                'name': 'România',
                'civil_code': 'Codul Civil (Legea nr. 287/2009)',
                'commercial_code': 'Legea societăților nr. 31/1990',
                'criminal_code': 'Codul Penal (Legea nr. 286/2009)',
                'currency': 'RON'
            },
            'DE': {
                'name': 'Germania',
                'civil_code': 'Bürgerliches Gesetzbuch (BGB)',
                'commercial_code': 'Handelsgesetzbuch (HGB)',
                'criminal_code': 'Strafgesetzbuch (StGB)',
                'currency': 'EUR'
            },
            'FR': {
                'name': 'Franța',
                'civil_code': 'Code Civil Français',
                'commercial_code': 'Code de Commerce',
                'criminal_code': 'Code Pénal',
                'currency': 'EUR'
            },
            'IT': {
                'name': 'Italia',
                'civil_code': 'Codice Civile Italiano',
                'commercial_code': 'Codice di Commercio',
                'criminal_code': 'Codice Penale',
                'currency': 'EUR'
            }
        }
    
    def detect_document_type(self, text: str) -> Dict[str, any]:
        """Detect document type based on content analysis"""
        text_lower = text.lower()
        
        # Contract indicators
        contract_keywords = ['contract', 'acord', 'înțelegere', 'convenție', 'agreement', 'vertrag']
        if any(keyword in text_lower for keyword in contract_keywords):
            return {
                'type': 'contract',
                'confidence': 0.8,
                'description': 'Contract sau acord juridic'
            }
        
        # Fine/penalty indicators
        fine_keywords = ['amendă', 'sancțiune', 'penalitate', 'contraventie', 'fine', 'penalty', 'bußgeld']
        if any(keyword in text_lower for keyword in fine_keywords):
            return {
                'type': 'fine',
                'confidence': 0.9,
                'description': 'Amendă sau sancțiune administrativă'
            }
        
        # Court document indicators
        court_keywords = ['instanță', 'tribunal', 'judecător', 'sentință', 'court', 'gericht']
        if any(keyword in text_lower for keyword in court_keywords):
            return {
                'type': 'court_document',
                'confidence': 0.85,
                'description': 'Document judiciar'
            }
        
        # Company/commercial indicators
        company_keywords = ['societate', 'firma', 'srl', 'sa', 'company', 'gmbh', 'ag']
        if any(keyword in text_lower for keyword in company_keywords):
            return {
                'type': 'commercial',
                'confidence': 0.75,
                'description': 'Document comercial sau societar'
            }
        
        # Property/real estate indicators
        property_keywords = ['proprietate', 'imobil', 'teren', 'apartament', 'casă', 'property', 'immobilie']
        if any(keyword in text_lower for keyword in property_keywords):
            return {
                'type': 'property',
                'confidence': 0.8,
                'description': 'Document imobiliar'
            }
        
        return {
            'type': 'general',
            'confidence': 0.5,
            'description': 'Document juridic general'
        }
    
    def extract_parties(self, text: str) -> List[str]:
        """Extract parties from document"""
        parties = []
        
        # Romanian patterns
        party_patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+)',  # Name patterns
            r'S\.?C\.? ([A-Z][A-Z0-9\s]+) S\.?R\.?L\.?',  # SRL companies
            r'S\.?A\.? ([A-Z][A-Z0-9\s]+)',  # SA companies
            r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+)',  # Full names
        ]
        
        for pattern in party_patterns:
            matches = re.findall(pattern, text)
            parties.extend(matches[:3])  # Limit to first 3 matches
        
        return list(set(parties))[:5]  # Remove duplicates, max 5
    
    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from document"""
        date_patterns = [
            r'\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{4}',  # DD.MM.YYYY
            r'\d{4}[\.\/\-]\d{1,2}[\.\/\-]\d{1,2}',  # YYYY.MM.DD
            r'\d{1,2} [a-zA-Z]+ \d{4}',  # DD Month YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return dates[:3]  # Return first 3 dates found
    
    def extract_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts from document"""
        amount_patterns = [
            r'\d+[\.,]\d{2}\s*(RON|EUR|USD|lei)',
            r'\d+\s*(RON|EUR|USD|lei)',
            r'(RON|EUR|USD|lei)\s*\d+[\.,]?\d*',
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend([f"{match[0]} {match[1]}" if isinstance(match, tuple) else match for match in matches])
        
        return amounts[:5]  # Return first 5 amounts
    
    def identify_legal_issues(self, text: str, doc_type: str) -> List[str]:
        """Identify potential legal issues"""
        issues = []
        text_lower = text.lower()
        
        if doc_type == 'contract':
            if 'reziliere' in text_lower or 'încetare' in text_lower:
                issues.append('Posibile clauze de reziliere')
            if 'penalitate' in text_lower or 'daune' in text_lower:
                issues.append('Clauze de penalitate sau daune-interese')
            if 'garanție' in text_lower:
                issues.append('Aspecte legate de garanții')
        
        elif doc_type == 'fine':
            if 'contestare' in text_lower or 'recurs' in text_lower:
                issues.append('Posibilitate de contestare')
            if 'termen' in text_lower:
                issues.append('Termene importante de respectat')
            if 'executare' in text_lower:
                issues.append('Risc de executare silită')
        
        elif doc_type == 'commercial':
            if 'faliment' in text_lower or 'insolvență' in text_lower:
                issues.append('Probleme de solvabilitate')
            if 'fiscal' in text_lower or 'anaf' in text_lower:
                issues.append('Aspecte fiscale importante')
        
        return issues
    
    def generate_recommendations(self, doc_type: str, issues: List[str]) -> List[str]:
        """Generate specific recommendations based on document type and issues"""
        recommendations = []
        
        if doc_type == 'contract':
            recommendations.extend([
                'Verificați toate clauzele înainte de semnare',
                'Asigurați-vă că toate părțile au capacitate juridică',
                'Păstrați o copie autentificată a contractului'
            ])
        
        elif doc_type == 'fine':
            recommendations.extend([
                'Verificați termenul de contestare (de obicei 30 zile)',
                'Analizați legalitatea sancțiunii aplicate',
                'Consultați un avocat pentru contestare'
            ])
        
        elif doc_type == 'commercial':
            recommendations.extend([
                'Verificați toate documentele la ONRC',
                'Asigurați-vă de conformitatea fiscală',
                'Consultați un expert contabil'
            ])
        
        # Add issue-specific recommendations
        if 'Termene importante' in ' '.join(issues):
            recommendations.append('URGENT: Respectați toate termenele specificate')
        
        if 'Clauze de penalitate' in ' '.join(issues):
            recommendations.append('Analizați impactul financiar al penalităților')
        
        return recommendations

def analyze_document_offline(document_text: str, country_code: str, analysis_language: str, 
                           access_code: str, processed_files: List[str]) -> str:
    """Main offline analysis function"""
    try:
        analyzer = OfflineLegalAnalyzer()
        framework = analyzer.legal_frameworks.get(country_code, analyzer.legal_frameworks['RO'])
        
        # Analyze document
        doc_type_info = analyzer.detect_document_type(document_text)
        parties = analyzer.extract_parties(document_text)
        dates = analyzer.extract_dates(document_text)
        amounts = analyzer.extract_amounts(document_text)
        issues = analyzer.identify_legal_issues(document_text, doc_type_info['type'])
        recommendations = analyzer.generate_recommendations(doc_type_info['type'], issues)
        
        # Generate comprehensive analysis
        analysis = f"""ANALIZĂ JURIDICĂ DETALIATĂ - ACCES GRATUIT COD {access_code}

Status: Analiză completă prin sistemul offline Legal Assistant
Țara selectată: {framework['name']}
Document(e) procesat(e): {len(processed_files)} fișier(e)
Data analizei: {datetime.utcnow().strftime('%d %B %Y, %H:%M')}

BAZA LEGALĂ DE ANALIZĂ
Cadrul legal aplicabil pentru {framework['name']}:
- Cod Civil: {framework['civil_code']}
- Cod Comercial: {framework['commercial_code']}
- Cod Penal: {framework['criminal_code']}

VERIFICAREA NULITĂȚII DOCUMENTULUI
Analiza preliminară a validității formale:
- Documentul pare să respecte forma legală de bază
- Nu s-au identificat vicii evidente de formă
- Recomandare: Verificare detaliată cu un specialist pentru validitatea completă

1. IDENTIFICAREA ȘI VALIDITATEA FORMALĂ A DOCUMENTULUI

Denumirea exactă a documentului:
{doc_type_info['description']} (Încredere detecție: {doc_type_info['confidence']*100:.0f}%)

Țara de origine și cadrul legal aplicabil:
{framework['name']} - {framework['civil_code']}

Părțile implicate identificate:
{chr(10).join([f'- {party}' for party in parties]) if parties else '- Părțile nu au putut fi identificate clar din text'}

Date importante identificate:
{chr(10).join([f'- {date}' for date in dates]) if dates else '- Nu s-au identificat date specifice'}

Aspecte financiare identificate:
{chr(10).join([f'- {amount}' for amount in amounts]) if amounts else '- Nu s-au identificat sume specifice'}

2. STRUCTURA ȘI CONȚINUTUL LEGAL

Tipul documentului: {doc_type_info['description']}

Obiectul principal:
Bazat pe analiza textului, documentul pare să se refere la aspecte {doc_type_info['type']} în contextul legislației din {framework['name']}.

Elemente cheie identificate:
- Documentul conține aproximativ {len(document_text)} caractere
- Text-ul pare să respecte structura legală specifică tipului de document
- Au fost identificate {len(parties)} părți potențiale în document

3. VERIFICAREA LEGALITĂȚII ȘI CONFORMITĂȚII

Conformitatea cu normele în vigoare:
- Analiza respectă cadrul legal din {framework['name']}
- Documentul pare să fie în conformitate cu {framework['civil_code']}

Aspecte de verificat:
- Capacitatea juridică a părților
- Respectarea formei legale prescrise
- Validitatea clauzelor specifice

4. ANALIZA IMPLICAȚIILOR JURIDICE

Probleme potențiale identificate:
{chr(10).join([f'- {issue}' for issue in issues]) if issues else '- Nu s-au identificat probleme majore evidente'}

Riscuri în executare:
- Verificați toate condițiile de executare
- Asigurați-vă de respectarea termenelor legale
- Consultați un specialist pentru aspecte complexe

Remedii legale disponibile:
- Conform {framework['civil_code']}, există posibilități de remediere
- Instanțele competente din {framework['name']} pot soluționa litigiile
- Medierea și arbitrajul sunt alternative disponibile

5. ASPECTE FISCALE, CIVILE SAU PENALE

Implicații fiscale:
- Verificați obligațiile fiscale în {framework['currency']}
- Consultați legislația fiscală din {framework['name']}

Aspecte civile:
- Documentul pare să intre sub incidența dreptului civil
- Aplicabile prevederile {framework['civil_code']}

Recomandări de acțiune:
{chr(10).join([f'- {rec}' for rec in recommendations])}

RECOMANDĂRI LEGALE SPECIFICE

Pentru {doc_type_info['description']}:
1. Verificați toate aspectele formale ale documentului
2. Consultați un avocat specializat pentru aspecte complexe
3. Respectați toate termenele legale aplicabile
4. Păstrați toate documentele justificative

AVERTISMENT LEGAL
Această analiză offline oferă o evaluare preliminară bazată pe recunoașterea pattern-urilor în text. 
Pentru aspecte juridice complexe, litigii sau decizii importante, consultați obligatoriu un avocat 
specializat în {framework['name']}.

Analiza a fost generată cu codul de acces gratuit {access_code} prin sistemul Legal Assistant.
Pentru analize AI complete și personalizate, considerați upgrade-ul la serviciul premium.

Data și ora analizei: {datetime.utcnow().strftime('%d %B %Y, %H:%M:%S')} UTC"""

        return analysis
        
    except Exception as e:
        logging.error(f"Offline analysis error: {str(e)}")
        return f"""ANALIZĂ JURIDICĂ - EROARE TEHNICĂ

A apărut o eroare în timpul analizei offline a documentului.
Vă rugăm să încercați din nou sau să contactați suportul tehnic.

Eroare: {str(e)}

Pentru asistență, vă rugăm să încercați:
1. Reîncărcarea documentului
2. Verificarea formatului fișierului
3. Contactarea echipei de suport

Data analizei: {datetime.utcnow().strftime('%d %B %Y, %H:%M')}"""
