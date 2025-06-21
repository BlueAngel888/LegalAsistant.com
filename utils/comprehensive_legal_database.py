"""
Comprehensive Legal Database System
Learns and stores complete legal frameworks for each country
"""

import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class ComprehensiveLegalDatabase:
    """Complete legal database system for country-specific law learning"""
    
    def __init__(self):
        self.legal_databases = {
            'RO': self._init_romania_laws(),
            'DE': self._init_germany_laws(),
            'AE': self._init_uae_laws(),
            'US': self._init_usa_laws(),
            'UK': self._init_uk_laws(),
            'FR': self._init_france_laws()
        }
        self.case_examples = {}
        self._load_case_examples()
    
    def _init_romania_laws(self) -> Dict:
        """Complete Romanian legal framework"""
        return {
            'civil_code': {
                'name': 'Codul Civil Romanian (Legea nr. 287/2009)',
                'sections': {
                    'contracts': {
                        'articles': list(range(1166, 1649)),
                        'key_principles': [
                            'Forta obligatorie a contractului (Art. 1270)',
                            'Buna credinta in executarea contractului (Art. 1271)',
                            'Echivalenta prestatiilor (Art. 1221)',
                            'Daune-interese pentru neexecutare (Art. 1530-1548)'
                        ],
                        'nullity_causes': [
                            'Lipsa capacitatii de exercitiu (Art. 1179)',
                            'Vitii de consimtamant (Art. 1201-1220)',
                            'Obiect ilicit sau imposibil (Art. 1227-1244)',
                            'Cauza ilicita (Art. 1245-1247)'
                        ]
                    },
                    'property': {
                        'articles': list(range(555, 1165)),
                        'ownership_types': [
                            'Proprietatea publica (Art. 858-871)',
                            'Proprietatea privata (Art. 555-857)',
                            'Coproprietatea (Art. 631-691)',
                            'Proprietatea intelectuala'
                        ]
                    },
                    'family': {
                        'articles': list(range(258, 554)),
                        'marriage_law': [
                            'Conditii casatorie (Art. 258-272)',
                            'Efectele casatoriei (Art. 273-315)',
                            'Divortul (Art. 373-394)',
                            'Autoritatea parinteasca (Art. 483-507)'
                        ]
                    }
                }
            },
            'commercial_code': {
                'name': 'Legea nr. 31/1990 privind societatile comerciale',
                'company_types': [
                    'Societatea cu raspundere limitata (SRL)',
                    'Societatea pe actiuni (SA)',
                    'Societatea in nume colectiv (SNC)',
                    'Societatea in comandita simpla (SCS)',
                    'Societatea in comandita pe actiuni (SCA)'
                ],
                'key_obligations': [
                    'Inregistrare la ONRC',
                    'Capital social minim',
                    'Obligatii contabile',
                    'Declaratii fiscale'
                ]
            },
            'criminal_code': {
                'name': 'Codul Penal (Legea nr. 286/2009)',
                'categories': {
                    'crimes_against_person': ['omor', 'vatamare corporala', 'sechestrare'],
                    'property_crimes': ['furt', 'talharie', 'inselaciune', 'delapidare'],
                    'economic_crimes': ['evaziune fiscala', 'spalare bani', 'coruptie'],
                    'traffic_crimes': ['conducere fara permis', 'conducere sub influenta']
                }
            },
            'procedural_codes': {
                'civil_procedure': 'Codul de Procedura Civila (Legea nr. 134/2010)',
                'criminal_procedure': 'Codul de Procedura Penala (Legea nr. 135/2010)',
                'administrative_procedure': 'Legea contenciosului administrativ nr. 554/2004'
            }
        }
    
    def _init_germany_laws(self) -> Dict:
        """Complete German legal framework"""
        return {
            'civil_code': {
                'name': 'Bürgerliches Gesetzbuch (BGB)',
                'books': {
                    'general_part': {
                        'paragraphs': list(range(1, 240)),
                        'legal_acts': ['§ 104-185 BGB'],
                        'periods': ['§ 186-225 BGB']
                    },
                    'obligations': {
                        'paragraphs': list(range(241, 853)),
                        'contract_law': ['§ 241-432 BGB'],
                        'tort_law': ['§ 823-853 BGB'],
                        'unjust_enrichment': ['§ 812-822 BGB']
                    },
                    'property': {
                        'paragraphs': list(range(854, 1296)),
                        'ownership': ['§ 903-1011 BGB'],
                        'mortgages': ['§ 1113-1203 BGB']
                    },
                    'family': {
                        'paragraphs': list(range(1297, 1921)),
                        'marriage': ['§ 1353-1588 BGB'],
                        'parentage': ['§ 1591-1717 BGB']
                    }
                }
            },
            'commercial_code': {
                'name': 'Handelsgesetzbuch (HGB)',
                'trader_law': ['§ 1-104 HGB'],
                'commercial_companies': ['§ 105-237 HGB'],
                'accounting': ['§ 238-342e HGB']
            },
            'criminal_code': {
                'name': 'Strafgesetzbuch (StGB)',
                'special_part': {
                    'life_crimes': ['§ 211-222 StGB'],
                    'property_crimes': ['§ 242-305a StGB'],
                    'economic_crimes': ['§ 263-266b StGB']
                }
            }
        }
    
    def _init_uae_laws(self) -> Dict:
        """Complete UAE legal framework with Islamic and Civil law"""
        return {
            'civil_code': {
                'name': 'UAE Civil Code (Federal Law No. 5 of 1985)',
                'sources': ['Sharia Law', 'Egyptian Civil Code', 'French Civil Code'],
                'books': {
                    'general_provisions': {
                        'articles': list(range(1, 146)),
                        'sources_of_law': ['Art. 1 - Sharia as primary source'],
                        'interpretation': ['Art. 3-10']
                    },
                    'obligations': {
                        'articles': list(range(147, 657)),
                        'contracts': ['Art. 147-406'],
                        'torts': ['Art. 282-364'],
                        'islamic_principles': [
                            'Prohibition of Riba (interest)',
                            'Prohibition of Gharar (excessive uncertainty)',
                            'Halal transactions only'
                        ]
                    },
                    'property': {
                        'articles': list(range(658, 1100)),
                        'ownership_types': [
                            'Freehold (for UAE nationals)',
                            'Usufruct (for expatriates)',
                            'Leasehold'
                        ]
                    }
                }
            },
            'commercial_code': {
                'name': 'UAE Commercial Code (Federal Law No. 18 of 1993)',
                'trader_obligations': ['Commercial registration', 'Accounting records'],
                'company_types': [
                    'Limited Liability Company (LLC)',
                    'Public Joint Stock Company (PJSC)',
                    'Private Joint Stock Company (PJSC)',
                    'Partnership Company',
                    'Free Zone Company'
                ],
                'islamic_compliance': [
                    'Sharia-compliant financing',
                    'Sukuk (Islamic bonds)',
                    'Takaful (Islamic insurance)'
                ]
            },
            'sharia_law': {
                'sources': ['Quran', 'Sunnah', 'Ijma', 'Qiyas'],
                'family_law': {
                    'marriage': 'Federal Law No. 28 of 2005',
                    'inheritance': 'Sharia inheritance rules',
                    'child_custody': 'Islamic principles'
                },
                'commercial_law': {
                    'prohibited_transactions': ['Riba', 'Gharar', 'Maysir (gambling)'],
                    'permitted_contracts': ['Murabaha', 'Ijara', 'Musharaka']
                }
            }
        }
    
    def _init_usa_laws(self) -> Dict:
        """Complete US legal framework"""
        return {
            'federal_law': {
                'constitution': 'US Constitution with 27 Amendments',
                'usc_titles': {
                    'title_15': 'Commerce and Trade',
                    'title_18': 'Crimes and Criminal Procedure',
                    'title_26': 'Internal Revenue Code',
                    'title_29': 'Labor'
                },
                'uniform_codes': [
                    'Uniform Commercial Code (UCC)',
                    'Uniform Partnership Act (UPA)',
                    'Uniform Limited Liability Company Act'
                ]
            },
            'state_law_variations': {
                'contract_law': 'State-specific variations',
                'property_law': 'Community vs. Common law states',
                'corporate_law': 'Delaware vs. other states'
            },
            'case_law_system': {
                'supreme_court': 'Binding precedent nationwide',
                'circuit_courts': 'Regional binding precedent',
                'district_courts': 'Trial court decisions'
            }
        }
    
    def _init_uk_laws(self) -> Dict:
        """Complete UK legal framework"""
        return {
            'common_law': {
                'sources': ['Case law', 'Statutes', 'Common law principles'],
                'contract_law': [
                    'Offer and acceptance',
                    'Consideration',
                    'Intention to create legal relations'
                ],
                'tort_law': [
                    'Negligence',
                    'Defamation',
                    'Trespass'
                ]
            },
            'statutes': [
                'Companies Act 2006',
                'Consumer Rights Act 2015',
                'Equality Act 2010',
                'Data Protection Act 2018'
            ],
            'court_system': [
                'Supreme Court',
                'Court of Appeal',
                'High Court',
                'County Court'
            ]
        }
    
    def _init_france_laws(self) -> Dict:
        """Complete French legal framework"""
        return {
            'civil_code': {
                'name': 'Code Civil Français (Code Napoléon)',
                'titles': {
                    'persons': 'Book I - Articles 7-515',
                    'property': 'Book II - Articles 516-710',
                    'obligations': 'Book III - Articles 711-2283'
                }
            },
            'commercial_code': {
                'name': 'Code de Commerce',
                'books': [
                    'Book I - General provisions',
                    'Book II - Commercial companies',
                    'Book III - Certain forms of sale'
                ]
            }
        }
    
    def _load_case_examples(self):
        """Load real case examples for pattern matching"""
        self.case_examples = {
            'contract_disputes': [
                {
                    'country': 'RO',
                    'case_type': 'Breach of contract',
                    'facts': 'Vanzator nu a livrat marfa in termenul convenit',
                    'legal_basis': 'Art. 1530 Cod Civil - daune-interese pentru neexecutare',
                    'outcome': 'Obligarea la executare + daune-interese',
                    'precedent_value': 'Calculul daunelor pentru intarziere'
                },
                {
                    'country': 'DE',
                    'case_type': 'Vertragsverletzung',
                    'facts': 'Käufer verweigert Zahlung trotz ordnungsgemäßer Lieferung',
                    'legal_basis': '§ 433 BGB - Kaufvertragspflichten',
                    'outcome': 'Zahlungsklage erfolgreich',
                    'precedent_value': 'Beweis der ordnungsgemäßen Erfüllung'
                }
            ],
            'property_disputes': [
                {
                    'country': 'AE',
                    'case_type': 'Property ownership dispute',
                    'facts': 'Expat claims ownership of Dubai property without proper title',
                    'legal_basis': 'UAE Civil Code Art. 658 + Dubai Land Law',
                    'outcome': 'Claim rejected - no valid title deed',
                    'precedent_value': 'Importance of proper registration'
                }
            ],
            'family_law': [
                {
                    'country': 'RO',
                    'case_type': 'Divort',
                    'facts': 'Cerere de divort pentru dezbinare definitiva',
                    'legal_basis': 'Art. 373 Cod Civil - cauzele de divort',
                    'outcome': 'Divort pronuntat',
                    'precedent_value': 'Proba dezbinarii definitive'
                }
            ]
        }
    
    def learn_country_laws(self, country_code: str) -> Dict:
        """Get complete legal framework for a country"""
        return self.legal_databases.get(country_code, {})
    
    def find_similar_cases(self, document_text: str, country_code: str, document_type: str) -> List[Dict]:
        """Find similar legal cases and precedents"""
        similar_cases = []
        
        # Extract key legal concepts from document
        legal_concepts = self._extract_legal_concepts(document_text, country_code)
        
        # Search in case examples
        for category, cases in self.case_examples.items():
            for case in cases:
                if case['country'] == country_code:
                    similarity_score = self._calculate_similarity(legal_concepts, case)
                    if similarity_score > 0.6:  # Threshold for similarity
                        similar_cases.append({
                            'case': case,
                            'similarity_score': similarity_score,
                            'matching_concepts': legal_concepts
                        })
        
        # Search in database for historical analyses
        historical_cases = self._search_historical_analyses(legal_concepts, country_code)
        similar_cases.extend(historical_cases)
        
        # Sort by similarity score
        similar_cases.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_cases[:5]  # Return top 5 most similar cases
    
    def _extract_legal_concepts(self, text: str, country_code: str) -> List[str]:
        """Extract legal concepts from document text"""
        concepts = []
        text_lower = text.lower()
        
        # Get country-specific legal framework
        legal_framework = self.legal_databases.get(country_code, {})
        
        # Contract-related keywords
        contract_keywords = [
            'contract', 'agreement', 'obligation', 'payment', 'delivery',
            'breach', 'termination', 'penalty', 'damages', 'performance'
        ]
        
        # Property-related keywords
        property_keywords = [
            'property', 'ownership', 'real estate', 'land', 'building',
            'sale', 'purchase', 'lease', 'rent', 'mortgage'
        ]
        
        # Family law keywords
        family_keywords = [
            'marriage', 'divorce', 'custody', 'child', 'spouse',
            'inheritance', 'will', 'estate', 'family'
        ]
        
        # Commercial law keywords
        commercial_keywords = [
            'company', 'business', 'commercial', 'trade', 'corporate',
            'partnership', 'shares', 'director', 'shareholder'
        ]
        
        # Check for each category
        for keyword in contract_keywords:
            if keyword in text_lower:
                concepts.append('contract_law')
                break
        
        for keyword in property_keywords:
            if keyword in text_lower:
                concepts.append('property_law')
                break
                
        for keyword in family_keywords:
            if keyword in text_lower:
                concepts.append('family_law')
                break
                
        for keyword in commercial_keywords:
            if keyword in text_lower:
                concepts.append('commercial_law')
                break
        
        return concepts
    
    def _calculate_similarity(self, document_concepts: List[str], case: Dict) -> float:
        """Calculate similarity between document and case"""
        if not document_concepts:
            return 0.0
        
        case_text = f"{case.get('facts', '')} {case.get('legal_basis', '')}".lower()
        
        # Simple keyword matching for similarity
        matches = 0
        for concept in document_concepts:
            if concept.replace('_', ' ') in case_text or concept in case.get('case_type', '').lower():
                matches += 1
        
        return matches / len(document_concepts) if document_concepts else 0.0
    
    def _search_historical_analyses(self, legal_concepts: List[str], country_code: str) -> List[Dict]:
        """Search historical analyses for similar cases"""
        historical_cases = []
        
        try:
            # Import here to avoid circular imports
            from main import db
            from sqlalchemy import text
            
            # Query database for similar analyses
            query = text("""
                SELECT analysis_result, document_text, created_at 
                FROM document_analyses 
                WHERE analysis_result IS NOT NULL 
                AND language = :country_code
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            
            result = db.session.execute(query, {'country_code': country_code})
            
            for row in result:
                analysis_text = row[0].lower() if row[0] else ''
                document_text = row[1].lower() if row[1] else ''
                
                # Check if any legal concepts match
                concept_matches = sum(1 for concept in legal_concepts 
                                    if concept.replace('_', ' ') in analysis_text or 
                                       concept.replace('_', ' ') in document_text)
                
                if concept_matches > 0:
                    similarity_score = concept_matches / len(legal_concepts) if legal_concepts else 0
                    
                    historical_cases.append({
                        'case': {
                            'case_type': 'Historical Analysis',
                            'facts': document_text[:200] + '...' if len(document_text) > 200 else document_text,
                            'legal_basis': 'Previous analysis from database',
                            'outcome': analysis_text[:200] + '...' if len(analysis_text) > 200 else analysis_text,
                            'precedent_value': 'Similar case pattern identified',
                            'date': row[2].strftime('%Y-%m-%d') if row[2] else 'Unknown'
                        },
                        'similarity_score': similarity_score,
                        'matching_concepts': legal_concepts
                    })
                    
        except Exception as e:
            logger.error(f"Error searching historical analyses: {e}")
        
        return historical_cases
    
    def get_applicable_laws(self, document_concepts: List[str], country_code: str) -> List[Dict]:
        """Get specific laws applicable to the document"""
        applicable_laws = []
        legal_framework = self.legal_databases.get(country_code, {})
        
        for concept in document_concepts:
            if concept == 'contract_law' and 'civil_code' in legal_framework:
                civil_code = legal_framework['civil_code']
                if 'sections' in civil_code and 'contracts' in civil_code['sections']:
                    contracts_section = civil_code['sections']['contracts']
                    applicable_laws.append({
                        'area': 'Contract Law',
                        'source': civil_code['name'],
                        'articles': contracts_section.get('articles', []),
                        'key_principles': contracts_section.get('key_principles', []),
                        'nullity_causes': contracts_section.get('nullity_causes', [])
                    })
            
            elif concept == 'property_law' and 'civil_code' in legal_framework:
                civil_code = legal_framework['civil_code']
                if 'sections' in civil_code and 'property' in civil_code['sections']:
                    property_section = civil_code['sections']['property']
                    applicable_laws.append({
                        'area': 'Property Law',
                        'source': civil_code['name'],
                        'articles': property_section.get('articles', []),
                        'ownership_types': property_section.get('ownership_types', [])
                    })
            
            elif concept == 'commercial_law' and 'commercial_code' in legal_framework:
                commercial_code = legal_framework['commercial_code']
                applicable_laws.append({
                    'area': 'Commercial Law',
                    'source': commercial_code['name'],
                    'company_types': commercial_code.get('company_types', []),
                    'key_obligations': commercial_code.get('key_obligations', [])
                })
        
        return applicable_laws

# Global instance
comprehensive_legal_db = ComprehensiveLegalDatabase()