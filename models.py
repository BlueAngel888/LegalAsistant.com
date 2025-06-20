from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class DocumentAnalysis(db.Model):
    """Model to store document analysis records"""
    __tablename__ = 'document_analyses'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(255), nullable=False)
    file_names = db.Column(db.Text)  # JSON string of processed file names
    document_text = db.Column(db.Text, nullable=False)
    analysis_result = db.Column(db.Text)
    language = db.Column(db.String(10), default='en')
    stripe_session_id = db.Column(db.String(255))
    payment_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, session_id, file_names, document_text, language='en', payment_status='pending', stripe_session_id=None, analysis_result=None):
        self.session_id = session_id
        self.file_names = file_names
        self.document_text = document_text
        self.language = language
        self.payment_status = payment_status
        self.stripe_session_id = stripe_session_id
        self.analysis_result = analysis_result
    
    def __repr__(self):
        return f'<DocumentAnalysis {self.id}>'


class User(db.Model):
    """Model for potential future user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=True)
    session_id = db.Column(db.String(255), nullable=False)
    language_preference = db.Column(db.String(10), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.email or self.session_id}>'


class PaymentRecord(db.Model):
    """Model to track payment transactions"""
    __tablename__ = 'payment_records'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stripe_session_id = db.Column(db.String(255), unique=True, nullable=False)
    document_analysis_id = db.Column(db.String(36), db.ForeignKey('document_analyses.id'))
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), default='EUR')
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationship
    document_analysis = db.relationship('DocumentAnalysis', backref='payment_records')
    
    def __init__(self, stripe_session_id, document_analysis_id, amount, currency='EUR', status='pending'):
        self.stripe_session_id = stripe_session_id
        self.document_analysis_id = document_analysis_id
        self.amount = amount
        self.currency = currency
        self.status = status
    
    def __repr__(self):
        return f'<PaymentRecord {self.stripe_session_id}>'