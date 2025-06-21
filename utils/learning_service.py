from models_learning import LegalAnalysisLearning, LegalKnowledgeBase, AnalysisImprovement
from models import db
from datetime import datetime
import json
import logging
import time

class LegalLearningService:
    """Service to manage machine learning and continuous improvement"""
    
    @staticmethod
    def record_analysis_session(session_id, document_type, country_code, analysis_language, 
                               document_length, analysis_length, processing_time):
        """Record analysis session for learning purposes"""
        try:
            learning_record = LegalAnalysisLearning()
            learning_record.session_id = session_id
            learning_record.document_type = document_type
            learning_record.document_country = country_code
            learning_record.analysis_language = analysis_language
            learning_record.document_length = document_length
            learning_record.analysis_length = analysis_length
            learning_record.processing_time = processing_time
            
            db.session.add(learning_record)
            db.session.commit()
            
            logging.info(f"Learning data recorded for session {session_id}")
            return learning_record.id
            
        except Exception as e:
            logging.error(f"Error recording learning data: {str(e)}")
            return None
    
    @staticmethod
    def get_knowledge_base_entries(country_code, document_type):
        """Retrieve relevant knowledge base entries"""
        try:
            entries = LegalKnowledgeBase.query.filter_by(
                country_code=country_code,
                legal_category=document_type
            ).order_by(LegalKnowledgeBase.accuracy_rating.desc()).limit(5).all()
            
            return entries
            
        except Exception as e:
            logging.error(f"Error retrieving knowledge base: {str(e)}")
            return []
    
    @staticmethod
    def add_knowledge_entry(country_code, legal_category, law_reference, law_text, 
                           practical_application=None, common_issues=None):
        """Add new knowledge base entry"""
        try:
            knowledge = LegalKnowledgeBase()
            knowledge.country_code = country_code
            knowledge.legal_category = legal_category
            knowledge.law_reference = law_reference
            knowledge.law_text = law_text
            knowledge.practical_application = practical_application
            knowledge.common_issues = common_issues
            
            db.session.add(knowledge)
            db.session.commit()
            
            logging.info(f"Knowledge base entry added for {country_code} - {legal_category}")
            return knowledge.id
            
        except Exception as e:
            logging.error(f"Error adding knowledge entry: {str(e)}")
            return None
    
    @staticmethod
    def analyze_performance_trends():
        """Analyze performance trends across different parameters"""
        try:
            # Get analysis data from last 30 days
            thirty_days_ago = datetime.utcnow().replace(day=datetime.utcnow().day-30)
            
            recent_analyses = LegalAnalysisLearning.query.filter(
                LegalAnalysisLearning.created_at >= thirty_days_ago
            ).all()
            
            if not recent_analyses:
                return {}
            
            # Calculate performance metrics
            avg_processing_time = sum(a.processing_time or 0 for a in recent_analyses) / len(recent_analyses)
            avg_quality_score = sum(a.quality_score or 0 for a in recent_analyses if a.quality_score) / len([a for a in recent_analyses if a.quality_score])
            
            # Group by country
            country_performance = {}
            for analysis in recent_analyses:
                country = analysis.document_country
                if country not in country_performance:
                    country_performance[country] = []
                country_performance[country].append(analysis)
            
            # Calculate country-specific metrics
            country_stats = {}
            for country, analyses in country_performance.items():
                country_stats[country] = {
                    'count': len(analyses),
                    'avg_processing_time': sum(a.processing_time or 0 for a in analyses) / len(analyses),
                    'avg_quality': sum(a.quality_score or 0 for a in analyses if a.quality_score) / len([a for a in analyses if a.quality_score]) if any(a.quality_score for a in analyses) else 0
                }
            
            return {
                'total_analyses': len(recent_analyses),
                'avg_processing_time': avg_processing_time,
                'avg_quality_score': avg_quality_score,
                'country_performance': country_stats,
                'period': '30 days'
            }
            
        except Exception as e:
            logging.error(f"Error analyzing performance trends: {str(e)}")
            return {}
    
    @staticmethod
    def suggest_improvements(country_code, document_type):
        """Suggest improvements based on historical data"""
        try:
            # Get similar analyses
            similar_analyses = LegalAnalysisLearning.query.filter_by(
                document_country=country_code,
                document_type=document_type
            ).order_by(LegalAnalysisLearning.created_at.desc()).limit(10).all()
            
            if not similar_analyses:
                return []
            
            suggestions = []
            
            # Analyze common patterns
            avg_processing_time = sum(a.processing_time or 0 for a in similar_analyses) / len(similar_analyses)
            avg_length = sum(a.analysis_length for a in similar_analyses) / len(similar_analyses)
            
            # Performance-based suggestions
            if avg_processing_time > 30:  # seconds
                suggestions.append({
                    'type': 'performance',
                    'description': f'Consider optimizing analysis for {document_type} documents from {country_code}',
                    'priority': 'medium',
                    'expected_improvement': '20% faster processing'
                })
            
            if avg_length < 1000:  # characters
                suggestions.append({
                    'type': 'completeness',
                    'description': f'Analyses for {document_type} from {country_code} could be more comprehensive',
                    'priority': 'high',
                    'expected_improvement': 'More detailed legal guidance'
                })
            
            # Quality-based suggestions
            low_quality_count = len([a for a in similar_analyses if a.quality_score and a.quality_score < 7])
            if low_quality_count > len(similar_analyses) * 0.3:
                suggestions.append({
                    'type': 'quality',
                    'description': f'Legal accuracy needs improvement for {document_type} from {country_code}',
                    'priority': 'high',
                    'expected_improvement': 'Better legal references and citations'
                })
            
            return suggestions
            
        except Exception as e:
            logging.error(f"Error generating improvement suggestions: {str(e)}")
            return []
    
    @staticmethod
    def initialize_knowledge_base():
        """Initialize knowledge base with basic legal information"""
        try:
            # Sample knowledge entries for Romania
            romania_entries = [
                {
                    'country_code': 'RO',
                    'legal_category': 'contract',
                    'law_reference': 'Codul Civil, Art. 1166-1649',
                    'law_text': 'Contractul este acordul de vointa dintre doua sau mai multe persoane cu privire la constituirea, modificarea sau stingerea unor raporturi juridice civile.',
                    'practical_application': 'Contractele trebuie sa respecte forma scrisa pentru anumite categorii si sa contina elementele esentiale.',
                    'common_issues': 'Lipsa formei scrise, clauzele abuzive, nerespectarea termenelor de executie.'
                },
                {
                    'country_code': 'RO',
                    'legal_category': 'administrative_penalty',
                    'law_reference': 'Legea nr. 554/2004 - Contenciosul administrativ',
                    'law_text': 'Actele administrative pot fi atacate in contencios administrativ daca sunt ilegale sau netemeinice.',
                    'practical_application': 'Contestarea se face in termen de 6 luni de la comunicare sau luare la cunostinta.',
                    'common_issues': 'Depasirea termenelor de contestare, lipsa probelor, procedura de notificare.'
                },
                {
                    'country_code': 'RO',
                    'legal_category': 'court_document',
                    'law_reference': 'Codul de Procedura Civila, Art. 194-226',
                    'law_text': 'Actiunea in instanta se introduce prin cererea de chemare in judecata.',
                    'practical_application': 'Cererea trebuie sa contina toate elementele prevazute de lege si taxa de timbru.',
                    'common_issues': 'Competenta materiala si teritoriala, termenele de prescriptie, probele.'
                }
            ]
            
            # Add entries to database if they don't exist
            for entry in romania_entries:
                existing = LegalKnowledgeBase.query.filter_by(
                    country_code=entry['country_code'],
                    legal_category=entry['legal_category'],
                    law_reference=entry['law_reference']
                ).first()
                
                if not existing:
                    knowledge = LegalKnowledgeBase(**entry)
                    db.session.add(knowledge)
            
            db.session.commit()
            logging.info("Knowledge base initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing knowledge base: {str(e)}")
    
    @staticmethod
    def get_learning_statistics():
        """Get comprehensive learning statistics"""
        try:
            total_analyses = LegalAnalysisLearning.query.count()
            knowledge_entries = LegalKnowledgeBase.query.count()
            improvements = AnalysisImprovement.query.filter_by(status='active').count()
            
            # Recent activity (last 7 days)
            seven_days_ago = datetime.utcnow().replace(day=datetime.utcnow().day-7)
            recent_analyses = LegalAnalysisLearning.query.filter(
                LegalAnalysisLearning.created_at >= seven_days_ago
            ).count()
            
            # Country distribution
            country_stats = db.session.query(
                LegalAnalysisLearning.document_country,
                db.func.count(LegalAnalysisLearning.id)
            ).group_by(LegalAnalysisLearning.document_country).all()
            
            # Document type distribution
            doc_type_stats = db.session.query(
                LegalAnalysisLearning.document_type,
                db.func.count(LegalAnalysisLearning.id)
            ).group_by(LegalAnalysisLearning.document_type).all()
            
            return {
                'total_analyses': total_analyses,
                'knowledge_entries': knowledge_entries,
                'active_improvements': improvements,
                'recent_activity': recent_analyses,
                'country_distribution': dict(country_stats),
                'document_type_distribution': dict(doc_type_stats)
            }
            
        except Exception as e:
            logging.error(f"Error getting learning statistics: {str(e)}")
            return {}

# Enhanced analyzer with learning integration
def analyze_with_learning_integration(text, country_code, analysis_language, session_id):
    """Analyze document with learning system integration"""
    start_time = time.time()
    
    # Import here to avoid circular imports
    from utils.enhanced_legal_analyzer import analyze_with_enhanced_gpt4
    
    # Get relevant knowledge base entries
    learning_service = LegalLearningService()
    document_type = extract_document_type_simple(text)
    knowledge_entries = learning_service.get_knowledge_base_entries(country_code, document_type)
    
    # Perform enhanced analysis
    analysis = analyze_with_enhanced_gpt4(text, country_code, analysis_language)
    
    # Record learning data
    processing_time = time.time() - start_time
    learning_service.record_analysis_session(
        session_id=session_id,
        document_type=document_type,
        country_code=country_code,
        analysis_language=analysis_language,
        document_length=len(text),
        analysis_length=len(analysis),
        processing_time=processing_time
    )
    
    # Get improvement suggestions
    suggestions = learning_service.suggest_improvements(country_code, document_type)
    
    # Add learning insights to analysis
    if knowledge_entries:
        analysis += "\n\nBASED ON PREVIOUS SIMILAR CASES:\n\n"
        for entry in knowledge_entries[:3]:  # Top 3 most relevant
            analysis += f"Legal Reference: {entry.law_reference}\n"
            if entry.practical_application:
                analysis += f"Practical Application: {entry.practical_application}\n"
            if entry.common_issues:
                analysis += f"Common Issues: {entry.common_issues}\n"
            analysis += "\n"
    
    return analysis

def extract_document_type_simple(text):
    """Simple document type extraction"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['contract', 'agreement', 'accord']):
        return 'contract'
    elif any(word in text_lower for word in ['fine', 'penalty', 'amenda', 'sanction']):
        return 'administrative_penalty'
    elif any(word in text_lower for word in ['court', 'tribunal', 'judge', 'lawsuit']):
        return 'court_document'
    elif any(word in text_lower for word in ['invoice', 'bill', 'payment', 'factura']):
        return 'commercial_document'
    else:
        return 'legal_document'