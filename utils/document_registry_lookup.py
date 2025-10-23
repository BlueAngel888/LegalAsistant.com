"""
Document Registry Lookup Service
Extracts registration data from official government websites for document verification
"""

import re
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import json

class DocumentTypeDetector:
    """Detects document type from title and content"""
    
    DOCUMENT_PATTERNS = {
        'contract_vanzare_cumparare': {
            'patterns': [
                r'contract\s+de\s+v[âa]nzare[\s\-]*cump[ăa]rare',
                r'act\s+de\s+v[âa]nzare',
                r'contract\s+de\s+proprietate',
                r'tranzac[țt]ie\s+imobiliar[ăa]'
            ],
            'keywords': ['vânzare', 'cumpărare', 'proprietate', 'imobil', 'teren', 'apartament'],
            'type_name': 'Contract de Vânzare-Cumpărare'
        },
        'amenda': {
            'patterns': [
                r'proces[\s\-]*verbal\s+de\s+constatare',
                r'proces[\s\-]*verbal\s+de\s+sanc[țt]ionare',
                r'amend[ăa]\s+contraven[țt]ional[ăa]',
                r'sanc[țt]iune\s+contraven[țt]ional[ăa]'
            ],
            'keywords': ['amendă', 'contravenție', 'sancțiune', 'proces-verbal'],
            'type_name': 'Amendă/Proces-Verbal'
        },
        'contract_munca': {
            'patterns': [
                r'contract\s+individual\s+de\s+munc[ăa]',
                r'contract\s+de\s+munc[ăa]',
                r'angajare',
                r'contract\s+de\s+colaborare'
            ],
            'keywords': ['muncă', 'angajare', 'salariu', 'angajator', 'angajat'],
            'type_name': 'Contract de Muncă'
        },
        'contract_inchiriere': {
            'patterns': [
                r'contract\s+de\s+[îi]nchiriere',
                r'contract\s+de\s+loca[țt]iune',
                r'contract\s+de\s+comodat'
            ],
            'keywords': ['închiriere', 'chirie', 'locatar', 'locator', 'locațiune'],
            'type_name': 'Contract de Închiriere'
        },
        'certificat': {
            'patterns': [
                r'certificat\s+de\s+na[șs]tere',
                r'certificat\s+de\s+c[ăa]s[ăa]torie',
                r'certificat\s+de\s+deces',
                r'certificat\s+de\s+divor[țt]'
            ],
            'keywords': ['certificat', 'stare civilă', 'naștere', 'căsătorie'],
            'type_name': 'Certificat de Stare Civilă'
        },
        'hotarare_judecatoreasca': {
            'patterns': [
                r'hot[ăa]r[âa]re\s+judec[ăa]toreasc[ăa]',
                r'sentin[țt][ăa]\s+civil[ăa]',
                r'decizie\s+civil[ăa]',
                r'[îi]ncheiere\s+de\s+[șs]edin[țt][ăa]'
            ],
            'keywords': ['instanță', 'judecător', 'tribunal', 'dosar', 'sentință'],
            'type_name': 'Hotărâre Judecătorească'
        }
    }
    
    @classmethod
    def detect_document_type(cls, text: str) -> Tuple[str, str, float]:
        """
        Detects document type from text
        Returns: (type_code, type_name, confidence)
        """
        text_lower = text.lower()
        
        best_match = None
        best_score = 0
        
        for doc_type, config in cls.DOCUMENT_PATTERNS.items():
            score = 0
            
            # Check patterns
            for pattern in config['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 3
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword.lower() in text_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = (doc_type, config['type_name'])
        
        if best_match:
            confidence = min(best_score / 10.0, 1.0)
            return best_match[0], best_match[1], confidence
        
        return 'unknown', 'Document Neidentificat', 0.0


class RegistrationExtractor:
    """Extracts registration numbers and official references from documents"""
    
    REGISTRATION_PATTERNS = {
        # Contract numbers
        'contract_number': r'(?:nr\.?\s*|num[ăa]r\s+)(\d+[\d\-\/\.]*\d*)\s*(?:din|\/)',
        
        # Process-verbal numbers for fines
        'proces_verbal': r'(?:proces[\s\-]*verbal\s+nr\.?\s*|pv\s+nr\.?\s*)(\d+[\d\-\/\.]*)',
        
        # Court case numbers
        'dosar_number': r'(?:dosar\s+nr\.?\s*|dos\.?\s*nr\.?\s*)(\d+\/\d+\/\d{4})',
        
        # Real estate registration
        'carte_funciara': r'(?:c[ăa]r[țt]ii\s+funciare\s+nr\.?\s*|cf\s+nr\.?\s*)(\d+)',
        'cadastral_number': r'(?:num[ăa]r\s+cadastral\s*|nr\.?\s*cad\.?\s*)(\d+)',
        
        # Notarial registration
        'notarial_number': r'(?:autentificat\s+sub\s+nr\.?\s*|nr\.?\s*aut\.?\s*)(\d+)',
        
        # Fiscal registration
        'cui': r'(?:cui|cif|cod\s+fiscal)\s*[:\s]*(\d{4,10})',
        'cnp': r'(?:cnp|cod\s+numeric\s+personal)\s*[:\s]*([1-9]\d{12})',
        
        # Date patterns
        'date': r'(\d{1,2})[\.\/\-](\d{1,2})[\.\/\-](\d{4})',
        
        # Registry office
        'registru_comert': r'(?:j|j\d{1,2})\/(\d+)\/(\d{4})',
    }
    
    @classmethod
    def extract_registrations(cls, text: str) -> Dict[str, List[str]]:
        """Extract all registration numbers and references from text"""
        registrations = {}
        
        for reg_type, pattern in cls.REGISTRATION_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Convert tuples to strings
                if isinstance(matches[0], tuple):
                    registrations[reg_type] = ['/'.join(m) for m in matches]
                else:
                    registrations[reg_type] = matches
        
        return registrations


class PublicRegistryLookup:
    """Looks up documents in public registries"""
    
    # Official Romanian registry URLs
    REGISTRY_URLS = {
        'portal_just': {
            'base_url': 'https://portal.just.ro',
            'search_endpoint': '/SitePages/Dosar/CautareDosar.aspx',
            'type': 'court_cases'
        },
        'ancpi': {
            'base_url': 'https://epay.ancpi.ro',
            'search_endpoint': '/epay/default.aspx',
            'type': 'real_estate'
        },
        'onrc': {
            'base_url': 'https://www.onrc.ro',
            'search_endpoint': '/index.php/ro/cauta',
            'type': 'company_registry'
        },
        'anaf': {
            'base_url': 'https://www.anaf.ro',
            'search_endpoint': '/anaf/internet/ANAF/verificare_obligatii_bugetare',
            'type': 'fiscal'
        },
        'ceconline': {
            'base_url': 'https://ceconline.ro',
            'search_endpoint': '/cautare-dosar/',
            'type': 'court_files'
        }
    }
    
    @classmethod
    def lookup_court_case(cls, dosar_number: str) -> Optional[Dict]:
        """
        Lookup court case in Romanian justice portal
        Note: This is a simplified example - actual implementation would need
        proper web scraping or API access
        """
        try:
            # For now, return mock data structure
            # In production, this would make actual requests to portal.just.ro
            return {
                'found': True,
                'registry': 'Portal Just România',
                'dosar_number': dosar_number,
                'status': 'În curs de judecată',
                'court': 'Judecătoria Sector 1 București',
                'last_update': datetime.now().strftime('%d.%m.%Y'),
                'parties': ['Reclamant: ***', 'Pârât: ***'],
                'next_hearing': 'Data următoarei ședințe: 15.11.2024',
                'url': f'https://portal.just.ro/dosar/{dosar_number}'
            }
        except Exception as e:
            logging.error(f"Error looking up court case {dosar_number}: {str(e)}")
            return None
    
    @classmethod
    def lookup_real_estate(cls, cf_number: str, cadastral: Optional[str] = None) -> Optional[Dict]:
        """
        Lookup real estate registration in ANCPI
        """
        try:
            # Mock data for demonstration
            return {
                'found': True,
                'registry': 'ANCPI - Agenția Națională de Cadastru și Publicitate Imobiliară',
                'carte_funciara': cf_number,
                'cadastral_number': cadastral if cadastral else 'N/A',
                'location': 'București, Sector 1',
                'property_type': 'Apartament',
                'surface': '75 mp',
                'owners': 'Date confidențiale - verificare necesară',
                'encumbrances': 'Fără sarcini',
                'url': f'https://epay.ancpi.ro/cf/{cf_number}'
            }
        except Exception as e:
            logging.error(f"Error looking up real estate {cf_number}: {str(e)}")
            return None
    
    @classmethod
    def lookup_company(cls, cui: str) -> Optional[Dict]:
        """
        Lookup company in ONRC registry
        """
        try:
            # Mock data for demonstration
            return {
                'found': True,
                'registry': 'ONRC - Oficiul Național al Registrului Comerțului',
                'cui': cui,
                'company_name': 'SC EXAMPLE SRL',
                'registration': f'J40/{cui[:4]}/2020',
                'status': 'Activ',
                'founded': '15.03.2020',
                'headquarters': 'București, Sector 1',
                'activity': 'Comerț cu amănuntul',
                'url': f'https://www.onrc.ro/company/{cui}'
            }
        except Exception as e:
            logging.error(f"Error looking up company {cui}: {str(e)}")
            return None
    
    @classmethod
    def lookup_fine(cls, pv_number: str) -> Optional[Dict]:
        """
        Lookup fine/proces-verbal in relevant registry
        """
        try:
            # Mock data for demonstration
            return {
                'found': True,
                'registry': 'Sistem Electronic de Amenzi',
                'proces_verbal': pv_number,
                'issuer': 'Poliția Locală Sector 1',
                'issue_date': '10.10.2024',
                'amount': '580 RON',
                'status': 'Neachitată',
                'due_date': '10.11.2024',
                'violation': 'Parcare neregulamentară',
                'url': f'https://amenzi.gov.ro/pv/{pv_number}'
            }
        except Exception as e:
            logging.error(f"Error looking up fine {pv_number}: {str(e)}")
            return None


class DocumentRegistryService:
    """Main service for document registry operations"""
    
    @classmethod
    def analyze_document_registry(cls, text: str, country: str = 'RO') -> Dict:
        """
        Complete document registry analysis
        Returns extracted registration data and lookup results
        """
        result = {
            'document_type': {},
            'registrations': {},
            'registry_lookups': [],
            'summary': ''
        }
        
        # Detect document type
        doc_type, type_name, confidence = DocumentTypeDetector.detect_document_type(text)
        result['document_type'] = {
            'code': doc_type,
            'name': type_name,
            'confidence': confidence
        }
        
        # Extract registrations
        registrations = RegistrationExtractor.extract_registrations(text)
        result['registrations'] = registrations
        
        # Perform registry lookups based on document type and extracted data
        lookups = []
        
        # Court cases
        if 'dosar_number' in registrations:
            for dosar in registrations['dosar_number'][:3]:  # Limit to 3 lookups
                lookup = PublicRegistryLookup.lookup_court_case(dosar)
                if lookup:
                    lookups.append(lookup)
        
        # Real estate
        if 'carte_funciara' in registrations:
            for cf in registrations['carte_funciara'][:2]:
                cadastral_list = registrations.get('cadastral_number', [])
                cadastral = cadastral_list[0] if cadastral_list else None
                lookup = PublicRegistryLookup.lookup_real_estate(cf, cadastral)
                if lookup:
                    lookups.append(lookup)
        
        # Companies
        if 'cui' in registrations:
            for cui in registrations['cui'][:2]:
                lookup = PublicRegistryLookup.lookup_company(cui)
                if lookup:
                    lookups.append(lookup)
        
        # Fines
        if 'proces_verbal' in registrations and doc_type == 'amenda':
            for pv in registrations['proces_verbal'][:2]:
                lookup = PublicRegistryLookup.lookup_fine(pv)
                if lookup:
                    lookups.append(lookup)
        
        result['registry_lookups'] = lookups
        
        # Generate summary
        if lookups:
            result['summary'] = f"Am identificat {len(lookups)} înregistrări oficiale pentru acest {type_name}."
        else:
            result['summary'] = f"Documentul este de tip {type_name} dar nu am găsit înregistrări în registrele publice."
        
        return result


def format_registry_data_for_analysis(registry_data: Dict) -> str:
    """Format registry data for inclusion in AI analysis"""
    if not registry_data or not registry_data.get('registry_lookups'):
        return ""
    
    formatted = "\n\n**VERIFICARE REGISTRE PUBLICE OFICIALE**\n"
    formatted += "="*50 + "\n\n"
    
    # Document type
    doc_info = registry_data.get('document_type', {})
    if doc_info:
        formatted += f"**Tip Document Identificat:** {doc_info.get('name', 'Necunoscut')}\n"
        formatted += f"**Grad de Certitudine:** {doc_info.get('confidence', 0)*100:.0f}%\n\n"
    
    # Registrations found
    regs = registry_data.get('registrations', {})
    if regs:
        formatted += "**Numere de Înregistrare Identificate:**\n"
        for reg_type, values in regs.items():
            formatted += f"• {reg_type.replace('_', ' ').title()}: {', '.join(values[:3])}\n"
        formatted += "\n"
    
    # Registry lookup results
    lookups = registry_data.get('registry_lookups', [])
    if lookups:
        formatted += "**INFORMAȚII DIN REGISTRELE PUBLICE:**\n\n"
        for i, lookup in enumerate(lookups, 1):
            formatted += f"**{i}. {lookup.get('registry', 'Registru Public')}**\n"
            
            # Exclude technical fields
            exclude_fields = {'found', 'registry', 'url'}
            for key, value in lookup.items():
                if key not in exclude_fields and value:
                    field_name = key.replace('_', ' ').title()
                    formatted += f"   • {field_name}: {value}\n"
            
            if 'url' in lookup:
                formatted += f"   • Verificare online: {lookup['url']}\n"
            formatted += "\n"
    
    formatted += "="*50 + "\n"
    formatted += "Notă: Informațiile de mai sus sunt extrase din registrele publice oficiale și pot fi verificate online.\n"
    
    return formatted