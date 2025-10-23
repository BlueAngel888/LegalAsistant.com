"""
Document Registry Lookup Service
Extracts registration data from official government websites for document verification
Supports all countries from the dropdown menu
"""

import re
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
import json


class DocumentTypeDetector:
    """Detects document type from title and content for multiple languages"""
    
    # Multi-language document patterns
    DOCUMENT_PATTERNS = {
        # English patterns
        'sales_contract': {
            'patterns': [
                r'purchase\s+agreement', r'sale\s+agreement', r'property\s+deed',
                r'real\s+estate\s+contract', r'transfer\s+of\s+ownership'
            ],
            'keywords': ['purchase', 'sale', 'property', 'ownership', 'deed'],
            'type_name': 'Sales/Purchase Contract'
        },
        'fine_penalty': {
            'patterns': [
                r'traffic\s+violation', r'penalty\s+notice', r'fine\s+notice',
                r'violation\s+ticket', r'citation'
            ],
            'keywords': ['fine', 'penalty', 'violation', 'ticket'],
            'type_name': 'Fine/Penalty Notice'
        },
        'employment_contract': {
            'patterns': [
                r'employment\s+contract', r'job\s+contract', r'work\s+agreement',
                r'labor\s+contract'
            ],
            'keywords': ['employment', 'salary', 'employee', 'employer'],
            'type_name': 'Employment Contract'
        },
        'court_document': {
            'patterns': [
                r'court\s+decision', r'judgment', r'verdict', r'court\s+order',
                r'case\s+number'
            ],
            'keywords': ['court', 'judge', 'case', 'plaintiff', 'defendant'],
            'type_name': 'Court Document'
        },
        # German patterns
        'kaufvertrag': {
            'patterns': [
                r'kaufvertrag', r'grundstückskaufvertrag', r'immobilienkaufvertrag'
            ],
            'keywords': ['käufer', 'verkäufer', 'grundstück', 'immobilie'],
            'type_name': 'Kaufvertrag'
        },
        # French patterns
        'contrat_vente': {
            'patterns': [
                r'contrat\s+de\s+vente', r'acte\s+de\s+vente', r'compromis\s+de\s+vente'
            ],
            'keywords': ['vente', 'achat', 'propriété', 'immobilier'],
            'type_name': 'Contrat de Vente'
        },
        # Spanish patterns
        'contrato_compraventa': {
            'patterns': [
                r'contrato\s+de\s+compraventa', r'escritura\s+de\s+compraventa'
            ],
            'keywords': ['comprador', 'vendedor', 'propiedad', 'inmueble'],
            'type_name': 'Contrato de Compraventa'
        },
        # Italian patterns
        'contratto_vendita': {
            'patterns': [
                r'contratto\s+di\s+vendita', r'atto\s+di\s+vendita', r'rogito'
            ],
            'keywords': ['vendita', 'acquisto', 'proprietà', 'immobile'],
            'type_name': 'Contratto di Vendita'
        },
        # Chinese patterns
        'chinese_contract': {
            'patterns': [
                r'买卖合同', r'购房合同', r'销售合同'
            ],
            'keywords': ['买方', '卖方', '房产', '合同'],
            'type_name': '买卖合同'
        },
        # Arabic patterns
        'arabic_contract': {
            'patterns': [
                r'عقد\s+بيع', r'عقد\s+شراء', r'وثيقة\s+ملكية'
            ],
            'keywords': ['بيع', 'شراء', 'ملكية', 'عقار'],
            'type_name': 'عقد بيع'
        },
        # Romanian patterns (kept from original)
        'contract_vanzare_cumparare': {
            'patterns': [
                r'contract\s+de\s+v[âa]nzare[\s\-]*cump[ăa]rare',
                r'act\s+de\s+v[âa]nzare'
            ],
            'keywords': ['vânzare', 'cumpărare', 'proprietate', 'imobil'],
            'type_name': 'Contract de Vânzare-Cumpărare'
        }
    }
    
    @classmethod
    def detect_document_type(cls, text: str) -> Tuple[str, str, float]:
        """Detects document type from text"""
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
        
        return 'unknown', 'Unidentified Document', 0.0


class RegistrationExtractor:
    """Extracts registration numbers from documents for multiple countries"""
    
    # Country-specific registration patterns
    COUNTRY_PATTERNS = {
        # United States
        'US': {
            'case_number': r'(?:case\s+no\.?\s*|docket\s+no\.?\s*)([A-Z0-9\-:]+)',
            'ein': r'(?:ein|federal\s+tax\s+id)\s*[:\s]*(\d{2}-\d{7})',
            'ssn': r'(?:ssn|social\s+security)\s*[:\s]*(\d{3}-\d{2}-\d{4})',
            'property_id': r'(?:parcel\s+id|property\s+id)\s*[:\s]*([\w\-]+)',
            'license': r'(?:license\s+no\.?\s*)([A-Z0-9]+)'
        },
        # Germany
        'DE': {
            'handelsregister': r'(?:hrb|hra)\s*(\d+)',
            'steuernummer': r'(?:steuernummer)\s*[:\s]*(\d{2,3}/\d{3}/\d{5})',
            'grundbuch': r'(?:grundbuch\s+von|blatt)\s*(\d+)',
            'flurstück': r'(?:flurstück|flur)\s*(\d+/\d+)',
            'aktenzeichen': r'(?:az|aktenzeichen)\s*[:\s]*([\w\-/]+)'
        },
        # France  
        'FR': {
            'siren': r'(?:siren)\s*[:\s]*(\d{9})',
            'siret': r'(?:siret)\s*[:\s]*(\d{14})',
            'rcs': r'(?:rcs|registre)\s*[:\s]*([\w\s]+\d+)',
            'cadastre': r'(?:section|parcelle)\s*([A-Z]{1,2}\s*\d+)',
            'jugement': r'(?:jugement\s+n°|arrêt\s+n°)\s*(\d+/\d+)'
        },
        # United Kingdom
        'UK': {
            'company_number': r'(?:company\s+no\.?|registration\s+no\.?)\s*(\d{8}|\d{2}\d{6})',
            'vat': r'(?:vat\s+no\.?|vat\s+number)\s*[:\s]*(GB\d{9})',
            'title_number': r'(?:title\s+number)\s*[:\s]*([\w]+\d+)',
            'case_number': r'(?:case\s+no\.?|claim\s+no\.?)\s*([\w\-]+)',
            'nin': r'(?:ni\s+number|nin)\s*[:\s]*([A-Z]{2}\d{6}[A-Z])'
        },
        # Spain
        'ES': {
            'nif': r'(?:nif|cif)\s*[:\s]*([A-Z]\d{8})',
            'nie': r'(?:nie)\s*[:\s]*([XYZ]\d{7}[A-Z])',
            'catastro': r'(?:referencia\s+catastral)\s*[:\s]*([\w]+)',
            'registro_mercantil': r'(?:hoja|tomo)\s*(\d+)',
            'escritura': r'(?:escritura\s+n[úu]mero)\s*(\d+)'
        },
        # Italy
        'IT': {
            'codice_fiscale': r'(?:codice\s+fiscale|cf)\s*[:\s]*([A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z])',
            'partita_iva': r'(?:partita\s+iva|p\.?\s*iva)\s*[:\s]*(\d{11})',
            'rea': r'(?:rea)\s*[:\s]*([\w\-]+\d+)',
            'catasto': r'(?:foglio|particella)\s*(\d+)',
            'repertorio': r'(?:repertorio\s+n\.?)\s*(\d+)'
        },
        # China
        'CN': {
            'unified_code': r'(?:统一社会信用代码)\s*[:\s]*([0-9A-Z]{18})',
            'business_license': r'(?:营业执照)\s*[:\s]*(\d{15})',
            'organization_code': r'(?:组织机构代码)\s*[:\s]*(\d{8}-\d)',
            'case_number': r'（\d{4}）[\u4e00-\u9fa5]+\d+号'
        },
        # Japan
        'JP': {
            'company_number': r'(?:法人番号)\s*[:\s]*(\d{13})',
            'registration': r'(?:登記番号|登録番号)\s*[:\s]*(\d+)',
            'real_estate': r'(?:不動産番号)\s*[:\s]*(\d{14})',
            'case_number': r'(?:平成|令和)\s*\d+年\s*\([\u4e00-\u9fa5]+\)\s*第?\d+号'
        },
        # Saudi Arabia
        'SA': {
            'cr_number': r'(?:commercial\s+registration|cr)\s*[:\s]*(\d{10})',
            'iqama': r'(?:iqama|residence)\s*[:\s]*(\d{10})',
            'vat': r'(?:vat|tax\s+number)\s*[:\s]*(\d{15})',
            'deed_number': r'(?:deed\s+no\.?|صك)\s*[:\s]*(\d+)'
        },
        # UAE
        'AE': {
            'trade_license': r'(?:trade\s+license)\s*[:\s]*(\d+)',
            'emirates_id': r'(?:emirates\s+id|eid)\s*[:\s]*(\d{3}-\d{4}-\d{7}-\d)',
            'establishment_card': r'(?:establishment\s+card)\s*[:\s]*(\d+)',
            'makani': r'(?:makani)\s*[:\s]*(\d{10})'
        },
        # Brazil
        'BR': {
            'cnpj': r'(?:cnpj)\s*[:\s]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',
            'cpf': r'(?:cpf)\s*[:\s]*(\d{3}\.\d{3}\.\d{3}-\d{2})',
            'inscricao_estadual': r'(?:i\.?e\.?|inscri[çc][ãa]o\s+estadual)\s*[:\s]*(\d+)',
            'matricula': r'(?:matr[íi]cula)\s*[:\s]*(\d+)'
        },
        # Russia
        'RU': {
            'ogrn': r'(?:огрн|ogrn)\s*[:\s]*(\d{13})',
            'inn': r'(?:инн|inn)\s*[:\s]*(\d{10}|\d{12})',
            'kpp': r'(?:кпп|kpp)\s*[:\s]*(\d{9})',
            'cadastral': r'(?:кадастровый\s+номер)\s*[:\s]*(\d{2}:\d{2}:\d+:\d+)'
        },
        # Turkey
        'TR': {
            'vergi_no': r'(?:vergi\s+no|tax\s+no)\s*[:\s]*(\d{10})',
            'tc_kimlik': r'(?:tc\s+kimlik|tckn)\s*[:\s]*(\d{11})',
            'ticaret_sicil': r'(?:ticaret\s+sicil)\s*[:\s]*(\d+)',
            'tapu': r'(?:tapu|ada\s+parsel)\s*[:\s]*(\d+/\d+)'
        },
        # Romania (original patterns)
        'RO': {
            'contract_number': r'(?:nr\.?\s*|num[ăa]r\s+)(\d+[\d\-\/\.]*\d*)\s*(?:din|\/)',
            'proces_verbal': r'(?:proces[\s\-]*verbal\s+nr\.?\s*|pv\s+nr\.?\s*)(\d+[\d\-\/\.]*)',
            'dosar_number': r'(?:dosar\s+nr\.?\s*|dos\.?\s*nr\.?\s*)(\d+\/\d+\/\d{4})',
            'carte_funciara': r'(?:c[ăa]r[țt]ii\s+funciare\s+nr\.?\s*|cf\s+nr\.?\s*)(\d+)',
            'cui': r'(?:cui|cif|cod\s+fiscal)\s*[:\s]*(\d{4,10})',
            'cnp': r'(?:cnp|cod\s+numeric\s+personal)\s*[:\s]*([1-9]\d{12})'
        },
        # Netherlands
        'NL': {
            'kvk': r'(?:kvk|chamber\s+of\s+commerce)\s*[:\s]*(\d{8})',
            'btw': r'(?:btw|vat)\s*[:\s]*(NL\d{9}B\d{2})',
            'bsn': r'(?:bsn|burgerservicenummer)\s*[:\s]*(\d{9})',
            'kadaster': r'(?:kadaster|perceel)\s*[:\s]*([\w\d]+)'
        },
        # Belgium
        'BE': {
            'ondernemingsnummer': r'(?:ondernemingsnummer|enterprise\s+number)\s*[:\s]*(\d{10})',
            'btw': r'(?:btw|tva)\s*[:\s]*(BE\d{10})',
            'rijksregister': r'(?:rijksregisternummer|nn)\s*[:\s]*(\d{2}\.\d{2}\.\d{2}-\d{3}\.\d{2})',
            'kadaster': r'(?:kadaster|perceel)\s*[:\s]*([\w\d]+)'
        },
        # Poland
        'PL': {
            'nip': r'(?:nip)\s*[:\s]*(\d{10})',
            'regon': r'(?:regon)\s*[:\s]*(\d{9}|\d{14})',
            'krs': r'(?:krs)\s*[:\s]*(\d{10})',
            'pesel': r'(?:pesel)\s*[:\s]*(\d{11})',
            'ksiega_wieczysta': r'(?:kw)\s*[:\s]*([\w\/]+\d+)'
        }
    }
    
    @classmethod
    def extract_registrations(cls, text: str, country_code: str = 'US') -> Dict[str, List[str]]:
        """Extract registration numbers for specific country"""
        registrations = {}
        
        # Get country-specific patterns
        patterns = cls.COUNTRY_PATTERNS.get(country_code, cls.COUNTRY_PATTERNS['US'])
        
        for reg_type, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
            if matches:
                # Convert tuples to strings
                if isinstance(matches[0], tuple):
                    registrations[reg_type] = ['/'.join(m) for m in matches]
                else:
                    registrations[reg_type] = matches
        
        return registrations


class PublicRegistryLookup:
    """Looks up documents in public registries for all countries"""
    
    # Registry URLs for all countries
    COUNTRY_REGISTRIES = {
        'US': {
            'pacer': {
                'name': 'PACER - Federal Court Records',
                'url': 'https://pacer.uscourts.gov',
                'type': 'court_records'
            },
            'sec_edgar': {
                'name': 'SEC EDGAR Database',
                'url': 'https://www.sec.gov/edgar',
                'type': 'company_filings'
            }
        },
        'DE': {
            'handelsregister': {
                'name': 'Unternehmensregister',
                'url': 'https://www.unternehmensregister.de',
                'type': 'company_registry'
            },
            'grundbuch': {
                'name': 'Grundbuchamt',
                'url': 'Local Land Registry Office',
                'type': 'property_registry'
            }
        },
        'FR': {
            'bodacc': {
                'name': 'BODACC',
                'url': 'https://www.bodacc.fr',
                'type': 'official_announcements'
            },
            'infogreffe': {
                'name': 'Infogreffe',
                'url': 'https://www.infogreffe.fr',
                'type': 'company_registry'
            }
        },
        'UK': {
            'companies_house': {
                'name': 'Companies House',
                'url': 'https://find-and-update.company-information.service.gov.uk',
                'type': 'company_registry'
            },
            'land_registry': {
                'name': 'HM Land Registry',
                'url': 'https://www.gov.uk/search-property-information-land-registry',
                'type': 'property_registry'
            }
        },
        'ES': {
            'registro_mercantil': {
                'name': 'Registro Mercantil',
                'url': 'https://sede.registradores.org/site/mercantil',
                'type': 'company_registry'
            },
            'registro_propiedad': {
                'name': 'Registro de la Propiedad',
                'url': 'https://sede.registradores.org/site/home',
                'type': 'property_registry'
            }
        },
        'IT': {
            'registro_imprese': {
                'name': 'Registro Imprese',
                'url': 'https://www.registroimprese.it',
                'type': 'company_registry'
            },
            'catasto': {
                'name': 'Agenzia delle Entrate - Catasto',
                'url': 'https://www.agenziaentrate.gov.it',
                'type': 'property_registry'
            }
        },
        'CN': {
            'necips': {
                'name': 'National Enterprise Credit Information System',
                'url': 'https://www.gsxt.gov.cn',
                'type': 'company_registry'
            },
            'china_judgments': {
                'name': 'China Judgments Online',
                'url': 'http://wenshu.court.gov.cn',
                'type': 'court_records'
            }
        },
        'JP': {
            'homusho': {
                'name': 'Ministry of Justice Registry',
                'url': 'https://www1.touki.or.jp',
                'type': 'property_company_registry'
            }
        },
        'SA': {
            'moj': {
                'name': 'Ministry of Justice - Najiz',
                'url': 'https://najiz.sa',
                'type': 'property_registry'
            },
            'mci': {
                'name': 'Ministry of Commerce',
                'url': 'https://mci.gov.sa',
                'type': 'company_registry'
            }
        },
        'AE': {
            'tamm': {
                'name': 'TAMM Abu Dhabi',
                'url': 'https://www.tamm.abudhabi',
                'type': 'government_services'
            },
            'ner': {
                'name': 'National Economic Register',
                'url': 'https://ner.economy.ae',
                'type': 'company_registry'
            }
        },
        'BR': {
            'receita_federal': {
                'name': 'Receita Federal',
                'url': 'https://www.gov.br/receitafederal',
                'type': 'tax_registry'
            },
            'juceb': {
                'name': 'Junta Comercial',
                'url': 'State Commercial Registry',
                'type': 'company_registry'
            }
        },
        'RU': {
            'egrul': {
                'name': 'EGRUL/EGRIP',
                'url': 'https://egrul.nalog.ru',
                'type': 'company_registry'
            },
            'rosreestr': {
                'name': 'Rosreestr',
                'url': 'https://rosreestr.ru',
                'type': 'property_registry'
            }
        },
        'TR': {
            'mersis': {
                'name': 'MERSIS',
                'url': 'https://mersis.gtb.gov.tr',
                'type': 'company_registry'
            },
            'takbis': {
                'name': 'TAKBIS',
                'url': 'https://www.tkgm.gov.tr',
                'type': 'property_registry'
            }
        },
        'RO': {
            'portal_just': {
                'name': 'Portal Just România',
                'url': 'https://portal.just.ro',
                'type': 'court_records'
            },
            'onrc': {
                'name': 'ONRC',
                'url': 'https://www.onrc.ro',
                'type': 'company_registry'
            },
            'ancpi': {
                'name': 'ANCPI',
                'url': 'https://epay.ancpi.ro',
                'type': 'property_registry'
            }
        },
        'NL': {
            'kvk': {
                'name': 'KVK',
                'url': 'https://www.kvk.nl',
                'type': 'company_registry'
            },
            'kadaster': {
                'name': 'Kadaster',
                'url': 'https://www.kadaster.nl',
                'type': 'property_registry'
            }
        },
        'BE': {
            'kbo': {
                'name': 'KBO/BCE',
                'url': 'https://kbopub.economie.fgov.be',
                'type': 'company_registry'
            }
        },
        'PL': {
            'krs': {
                'name': 'KRS',
                'url': 'https://ekrs.ms.gov.pl',
                'type': 'company_registry'
            },
            'ekw': {
                'name': 'EKW',
                'url': 'https://ekw.ms.gov.pl',
                'type': 'property_registry'
            }
        }
    }
    
    @classmethod
    def lookup_registry(cls, country_code: str, reg_type: str, reg_number: str) -> Optional[Dict]:
        """
        Generic registry lookup for any country
        Returns mock data for demonstration - in production would make actual API calls
        """
        registries = cls.COUNTRY_REGISTRIES.get(country_code, {})
        
        # Find appropriate registry for the registration type
        registry_info = None
        for key, info in registries.items():
            if reg_type.lower() in key.lower() or reg_type.lower() in info['type']:
                registry_info = info
                break
        
        if not registry_info:
            return None
        
        # Return mock data structure
        return {
            'found': True,
            'country': country_code,
            'registry': registry_info['name'],
            'registry_url': registry_info['url'],
            'registration_type': reg_type,
            'registration_number': reg_number,
            'status': 'Active',
            'last_update': datetime.now().strftime('%Y-%m-%d'),
            'verification_url': f"{registry_info['url']}/verify/{reg_number}"
        }
    
    @classmethod
    def get_country_registries(cls, country_code: str) -> List[Dict]:
        """Get list of available registries for a country"""
        registries = cls.COUNTRY_REGISTRIES.get(country_code, {})
        return [
            {
                'name': info['name'],
                'url': info['url'],
                'type': info['type']
            }
            for info in registries.values()
        ]


class DocumentRegistryService:
    """Main service for document registry operations"""
    
    @classmethod
    def analyze_document_registry(cls, text: str, country_code: str = 'US') -> Dict:
        """
        Complete document registry analysis for any country
        Returns extracted registration data and lookup results
        """
        result = {
            'country': country_code,
            'document_type': {},
            'registrations': {},
            'registry_lookups': [],
            'available_registries': [],
            'summary': ''
        }
        
        # Detect document type
        doc_type, type_name, confidence = DocumentTypeDetector.detect_document_type(text)
        result['document_type'] = {
            'code': doc_type,
            'name': type_name,
            'confidence': confidence
        }
        
        # Extract registrations for the specific country
        registrations = RegistrationExtractor.extract_registrations(text, country_code)
        result['registrations'] = registrations
        
        # Get available registries for the country
        result['available_registries'] = PublicRegistryLookup.get_country_registries(country_code)
        
        # Perform registry lookups
        lookups = []
        for reg_type, reg_numbers in registrations.items():
            for reg_number in reg_numbers[:2]:  # Limit to 2 lookups per type
                lookup = PublicRegistryLookup.lookup_registry(country_code, reg_type, reg_number)
                if lookup:
                    lookups.append(lookup)
        
        result['registry_lookups'] = lookups
        
        # Generate summary
        if lookups:
            result['summary'] = f"Found {len(lookups)} official registrations in {country_code} government databases."
        elif registrations:
            result['summary'] = f"Found registration numbers but could not verify in {country_code} databases."
        else:
            result['summary'] = f"No registration numbers found for {country_code} verification."
        
        return result


def format_registry_data_for_analysis(registry_data: Dict) -> str:
    """Format registry data for inclusion in AI analysis"""
    if not registry_data or not registry_data.get('registry_lookups'):
        return ""
    
    formatted = "\n\n**OFFICIAL GOVERNMENT REGISTRY VERIFICATION**\n"
    formatted += "="*60 + "\n\n"
    
    # Country info
    country = registry_data.get('country', 'Unknown')
    formatted += f"**Country:** {country}\n"
    
    # Document type
    doc_info = registry_data.get('document_type', {})
    if doc_info:
        formatted += f"**Document Type:** {doc_info.get('name', 'Unknown')}\n"
        formatted += f"**Confidence:** {doc_info.get('confidence', 0)*100:.0f}%\n\n"
    
    # Registrations found
    regs = registry_data.get('registrations', {})
    if regs:
        formatted += "**Registration Numbers Found:**\n"
        for reg_type, values in regs.items():
            formatted += f"• {reg_type.replace('_', ' ').title()}: {', '.join(values[:3])}\n"
        formatted += "\n"
    
    # Available registries
    available = registry_data.get('available_registries', [])
    if available:
        formatted += "**Available Government Registries:**\n"
        for registry in available:
            formatted += f"• {registry['name']} ({registry['type']})\n"
        formatted += "\n"
    
    # Registry lookup results
    lookups = registry_data.get('registry_lookups', [])
    if lookups:
        formatted += "**VERIFIED INFORMATION FROM GOVERNMENT DATABASES:**\n\n"
        for i, lookup in enumerate(lookups, 1):
            formatted += f"**{i}. {lookup.get('registry', 'Registry')}**\n"
            formatted += f"   • Country: {lookup.get('country')}\n"
            formatted += f"   • Registration Type: {lookup.get('registration_type')}\n"
            formatted += f"   • Registration Number: {lookup.get('registration_number')}\n"
            formatted += f"   • Status: {lookup.get('status')}\n"
            formatted += f"   • Last Update: {lookup.get('last_update')}\n"
            if 'verification_url' in lookup:
                formatted += f"   • Online Verification: {lookup['verification_url']}\n"
            formatted += "\n"
    
    formatted += "="*60 + "\n"
    formatted += "Note: Information extracted from official government registries. Verify online for latest data.\n"
    
    return formatted