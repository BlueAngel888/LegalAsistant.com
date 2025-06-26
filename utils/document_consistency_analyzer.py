"""
Document Consistency Analyzer
Analyzes uploaded documents to ensure they belong to the same legal case/matter
"""

import re
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from collections import Counter

class DocumentConsistencyAnalyzer:
    """Analyzes document consistency to ensure they belong to the same legal case"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_document_consistency(self, documents: List[Dict]) -> Dict:
        """
        Analyze if all documents belong to the same legal case
        
        Args:
            documents: List of dictionaries with keys 'filename', 'text', 'size'
        
        Returns:
            Dictionary with consistency analysis results
        """
        if len(documents) <= 1:
            return {
                'is_consistent': True,
                'confidence': 1.0,
                'warnings': [],
                'case_info': self._extract_case_info(documents[0]['text']) if documents else {}
            }
        
        # Extract key information from each document
        document_info = []
        for doc in documents:
            info = self._extract_case_info(doc['text'])
            info['filename'] = doc['filename']
            info['size'] = doc['size']
            document_info.append(info)
        
        # Analyze consistency
        consistency_result = self._check_consistency(document_info)
        
        return consistency_result
    
    def _extract_case_info(self, text: str) -> Dict:
        """Extract key case information from document text"""
        info = {
            'contract_numbers': self._extract_contract_numbers(text),
            'dates': self._extract_dates(text),
            'parties': self._extract_parties(text),
            'case_numbers': self._extract_case_numbers(text),
            'document_type': self._identify_document_type(text),
            'legal_references': self._extract_legal_references(text),
            'addresses': self._extract_addresses(text),
            'monetary_amounts': self._extract_monetary_amounts(text)
        }
        return info
    
    def _extract_contract_numbers(self, text: str) -> List[str]:
        """Extract contract/agreement numbers"""
        patterns = [
            r'Contract[^\w]*(\d+[\/\-\.\w]*\d+)',
            r'Agreement[^\w]*(\d+[\/\-\.\w]*\d+)',
            r'Nr\.?\s*(\d+[\/\-\.\w]*\d+)',
            r'Numărul\s*(\d+[\/\-\.\w]*\d+)',
            r'Договор[^\w]*(\d+[\/\-\.\w]*\d+)',
        ]
        
        numbers = []
        text_lower = text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            numbers.extend(matches)
        
        return list(set(numbers))
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        patterns = [
            r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}',
            r'\d{1,2}\s+\w+\s+\d{2,4}',
            r'\d{2,4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}'
        ]
        
        dates = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return list(set(dates))
    
    def _extract_parties(self, text: str) -> List[str]:
        """Extract party names (companies, individuals)"""
        patterns = [
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+S\.R\.L\.)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+S\.A\.)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+Ltd\.?)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+GmbH)',
            r'([A-Z][A-Z\s]+\s+S\.R\.L\.)',
            r'([A-Z][A-Z\s]+\s+S\.A\.)',
        ]
        
        parties = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            parties.extend(matches)
        
        return list(set(parties))
    
    def _extract_case_numbers(self, text: str) -> List[str]:
        """Extract legal case numbers"""
        patterns = [
            r'Dosar[^\w]*(\d+[\/\-\.\w]*\d+)',
            r'Case[^\w]*(\d+[\/\-\.\w]*\d+)',
            r'Dosarul\s*(\d+[\/\-\.\w]*\d+)',
            r'Процес[^\w]*(\d+[\/\-\.\w]*\d+)'
        ]
        
        case_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            case_numbers.extend(matches)
        
        return list(set(case_numbers))
    
    def _identify_document_type(self, text: str) -> str:
        """Identify the type of legal document"""
        text_lower = text.lower()
        
        types = {
            'contract': ['contract', 'agreement', 'accord', 'convention'],
            'court_decision': ['judgment', 'decision', 'verdict', 'ruling', 'sentință', 'decizie'],
            'invoice': ['invoice', 'factură', 'bill', 'factura'],
            'legal_notice': ['notice', 'notification', 'citație', 'înștiințare'],
            'power_of_attorney': ['power of attorney', 'procură', 'împuternicire'],
            'complaint': ['complaint', 'plângere', 'reclamație'],
            'amendment': ['amendment', 'addendum', 'anexă', 'modificare']
        }
        
        for doc_type, keywords in types.items():
            if any(keyword in text_lower for keyword in keywords):
                return doc_type
        
        return 'unknown'
    
    def _extract_legal_references(self, text: str) -> List[str]:
        """Extract legal code references"""
        patterns = [
            r'art\.?\s*\d+',
            r'articolul\s*\d+',
            r'legea\s*\d+[\/\-\.\w]*\d+',
            r'codul\s*\w+',
            r'o\.u\.g\.?\s*\d+'
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        return list(set(references))
    
    def _extract_addresses(self, text: str) -> List[str]:
        """Extract addresses"""
        patterns = [
            r'str\.?\s+[A-Z][a-z]+[^,\n]*',
            r'strada\s+[A-Z][a-z]+[^,\n]*',
            r'\d+\s+[A-Z][a-z]+\s+Street[^,\n]*'
        ]
        
        addresses = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            addresses.extend(matches)
        
        return list(set(addresses))
    
    def _extract_monetary_amounts(self, text: str) -> List[str]:
        """Extract monetary amounts"""
        patterns = [
            r'\d+[\.,]\d+\s*(?:RON|EUR|USD|lei)',
            r'(?:RON|EUR|USD|lei)\s*\d+[\.,]\d+',
            r'\d+\s*(?:RON|EUR|USD|lei)'
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        return list(set(amounts))
    
    def _check_consistency(self, document_info: List[Dict]) -> Dict:
        """Check consistency between documents"""
        warnings = []
        is_consistent = True
        confidence = 1.0
        
        # Check contract numbers consistency
        all_contract_numbers = []
        for doc in document_info:
            all_contract_numbers.extend(doc['contract_numbers'])
        
        unique_contracts = set(all_contract_numbers)
        if len(unique_contracts) > 1:
            warnings.append({
                'type': 'multiple_contracts',
                'message': f'Multiple contract numbers detected: {", ".join(unique_contracts)}',
                'severity': 'high'
            })
            is_consistent = False
            confidence -= 0.3
        
        # Check case numbers consistency
        all_case_numbers = []
        for doc in document_info:
            all_case_numbers.extend(doc['case_numbers'])
        
        unique_cases = set(all_case_numbers)
        if len(unique_cases) > 1:
            warnings.append({
                'type': 'multiple_cases',
                'message': f'Multiple case numbers detected: {", ".join(unique_cases)}',
                'severity': 'high'
            })
            is_consistent = False
            confidence -= 0.4
        
        # Check document types
        doc_types = [doc['document_type'] for doc in document_info]
        type_counter = Counter(doc_types)
        
        if len([t for t in type_counter.keys() if t != 'unknown']) > 1:
            main_types = [t for t, c in type_counter.most_common(2) if t != 'unknown']
            if len(main_types) > 1:
                warnings.append({
                    'type': 'mixed_document_types',
                    'message': f'Mixed document types detected: {", ".join(main_types)}',
                    'severity': 'medium'
                })
                confidence -= 0.2
        
        # Check parties consistency
        all_parties = []
        for doc in document_info:
            all_parties.extend(doc['parties'])
        
        if len(all_parties) > 0:
            unique_parties = set(all_parties)
            # If we have more than 4-5 unique parties, it might be multiple cases
            if len(unique_parties) > 5:
                warnings.append({
                    'type': 'many_parties',
                    'message': f'Many different parties detected ({len(unique_parties)}). Verify these documents belong to the same case.',
                    'severity': 'medium'
                })
                confidence -= 0.15
        
        # Check date consistency (documents should be from similar time periods)
        all_dates = []
        for doc in document_info:
            all_dates.extend(doc['dates'])
        
        if len(all_dates) > 2:
            # Simple heuristic: if we have very different date patterns, warn
            date_patterns = set(all_dates)
            if len(date_patterns) > 10:  # Many different dates might indicate different cases
                warnings.append({
                    'type': 'date_spread',
                    'message': 'Documents contain many different dates. Verify they belong to the same legal matter.',
                    'severity': 'low'
                })
                confidence -= 0.1
        
        # Adjust confidence based on number of warnings
        confidence = max(0.0, confidence)
        
        return {
            'is_consistent': is_consistent,
            'confidence': confidence,
            'warnings': warnings,
            'document_info': document_info,
            'summary': self._generate_summary(document_info),
            'recommendations': self._generate_recommendations(warnings)
        }
    
    def _generate_summary(self, document_info: List[Dict]) -> Dict:
        """Generate a summary of the document set"""
        all_types = [doc['document_type'] for doc in document_info]
        type_counter = Counter(all_types)
        
        return {
            'total_documents': len(document_info),
            'document_types': dict(type_counter),
            'has_contract_numbers': any(doc['contract_numbers'] for doc in document_info),
            'has_case_numbers': any(doc['case_numbers'] for doc in document_info),
            'parties_count': len(set(p for doc in document_info for p in doc['parties']))
        }
    
    def _generate_recommendations(self, warnings: List[Dict]) -> List[str]:
        """Generate recommendations based on warnings"""
        recommendations = []
        
        high_severity = [w for w in warnings if w['severity'] == 'high']
        if high_severity:
            recommendations.append("Consider uploading documents for each legal case separately for more accurate analysis.")
        
        medium_severity = [w for w in warnings if w['severity'] == 'medium']
        if medium_severity:
            recommendations.append("Review the uploaded documents to ensure they are all related to the same legal matter.")
        
        if len(warnings) > 3:
            recommendations.append("Many inconsistencies detected. For best results, upload only documents from a single legal case.")
        
        return recommendations