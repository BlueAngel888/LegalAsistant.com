from models import db
from datetime import datetime
import json

class LegalAnalysisLearning(db.Model):
    """Model to store analysis data for machine learning improvement"""
    __tablename__ = 'legal_analysis_learning'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    session_id = db.Column(db.String(255), nullable=False)
    document_type = db.Column(db.String(100), nullable=False)
    document_country = db.Column(db.String(10), nullable=False)
    analysis_language = db.Column(db.String(10), nullable=False)
    document_length = db.Column(db.Integer, nullable=False)
    analysis_length = db.Column(db.Integer, nullable=False)
    processing_time = db.Column(db.Float, nullable=True)
    user_feedback = db.Column(db.Text, nullable=True)  # JSON string of feedback
    improvement_suggestions = db.Column(db.Text, nullable=True)
    quality_score = db.Column(db.Integer, nullable=True)  # 1-10 scale
    legal_accuracy = db.Column(db.Integer, nullable=True)  # 1-10 scale
    completeness_score = db.Column(db.Integer, nullable=True)  # 1-10 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def add_feedback(self, feedback_data):
        """Add user feedback for this analysis"""
        self.user_feedback = json.dumps(feedback_data)
        self.updated_at = datetime.utcnow()
    
    def get_feedback(self):
        """Get user feedback as dict"""
        return json.loads(self.user_feedback or '{}')

class LegalKnowledgeBase(db.Model):
    """Model to store legal knowledge for better analysis"""
    __tablename__ = 'legal_knowledge_base'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    country_code = db.Column(db.String(10), nullable=False)
    legal_category = db.Column(db.String(100), nullable=False)  # contract, penalty, court, etc.
    law_reference = db.Column(db.String(500), nullable=False)  # Specific law citation
    law_text = db.Column(db.Text, nullable=False)  # Relevant law text
    practical_application = db.Column(db.Text, nullable=True)  # How it's applied
    common_issues = db.Column(db.Text, nullable=True)  # Common problems/solutions
    precedent_cases = db.Column(db.Text, nullable=True)  # JSON of similar cases
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)
    accuracy_rating = db.Column(db.Float, default=0.0)
    
    def increment_usage(self):
        """Track usage of this knowledge"""
        self.usage_count += 1
    
    def update_accuracy(self, rating):
        """Update accuracy rating based on feedback"""
        if self.accuracy_rating == 0.0:
            self.accuracy_rating = rating
        else:
            # Moving average of ratings
            self.accuracy_rating = (self.accuracy_rating + rating) / 2

class AnalysisImprovement(db.Model):
    """Model to track analysis improvements over time"""
    __tablename__ = 'analysis_improvements'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    improvement_type = db.Column(db.String(100), nullable=False)  # accuracy, completeness, speed
    description = db.Column(db.Text, nullable=False)
    implementation_date = db.Column(db.DateTime, default=datetime.utcnow)
    impact_score = db.Column(db.Float, nullable=True)  # Measured improvement
    applicable_countries = db.Column(db.Text, nullable=True)  # JSON array of country codes
    applicable_document_types = db.Column(db.Text, nullable=True)  # JSON array of types
    status = db.Column(db.String(50), default='active')  # active, deprecated, testing
    
    def get_applicable_countries(self):
        """Get list of applicable countries"""
        return json.loads(self.applicable_countries or '[]')
    
    def get_applicable_document_types(self):
        """Get list of applicable document types"""
        return json.loads(self.applicable_document_types or '[]')