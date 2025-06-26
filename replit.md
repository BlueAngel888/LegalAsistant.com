# Legal Assistant - AI-Powered Document Analysis Platform

## Overview

Legal Assistant is a Flask-based web application that provides AI-powered legal document analysis services. The application allows users to upload legal documents (PDF, DOCX, images) and receive comprehensive legal analysis powered by OpenAI's GPT-4. The platform includes payment processing via Stripe, multi-language support, gamification features, and machine learning capabilities for continuous improvement.

## System Architecture

### Frontend Architecture
- **Framework**: Server-side rendered HTML with Flask templates
- **Styling**: Bootstrap 5 for responsive design with custom CSS
- **JavaScript**: Vanilla JS for file upload, camera functionality, and interactive elements
- **Multi-language Support**: Template-based internationalization system
- **User Interface**: Progressive web app design with mobile-friendly camera capture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development)
- **AI Processing**: OpenAI GPT-4 integration for document analysis
- **Payment Processing**: Stripe integration for secure transactions
- **File Processing**: Multi-format document text extraction (PDF, DOCX, images with OCR)
- **Session Management**: Flask sessions for user state tracking

### Data Storage Solutions
- **Primary Database**: PostgreSQL with SQLAlchemy models
- **Document Storage**: Text extraction stored in database (no file persistence)
- **Session Storage**: Flask session management
- **Migration System**: Flask-Migrate for database schema management

## Key Components

### Document Processing Pipeline
1. **File Upload Handler**: Supports multiple file formats and camera capture
2. **Text Extraction Service**: 
   - PDF processing with PyPDF2
   - DOCX processing with python-docx
   - Image OCR with Tesseract
3. **AI Analysis Service**: GPT-4 powered legal document analysis
4. **Enhanced Analysis**: Country-specific legal framework integration

### Payment System
- **Stripe Integration**: Secure payment processing
- **Checkout Flow**: Session-based payment tracking
- **Payment Verification**: Webhook handling for payment confirmation

### Gamification System
- **User Progress Tracking**: XP, levels, achievements
- **Achievement System**: Upload milestones, analysis completion rewards
- **Engagement Features**: Streak tracking, progress visualization

### Learning System
- **Analysis Recording**: Machine learning data collection
- **Legal Knowledge Base**: Country-specific legal frameworks
- **Continuous Improvement**: Feedback integration and analysis enhancement

### Multi-language Support
- **Supported Languages**: English, Romanian, German, Italian, Spanish, Arabic
- **Translation System**: Template-based with country-specific legal analysis
- **Dynamic Language Switching**: User preference persistence

## Data Flow

1. **User Upload**: File upload or camera capture → text extraction
2. **Payment Processing**: Stripe checkout → payment verification
3. **AI Analysis**: Document text → GPT-4 analysis → enhanced legal insights
4. **Result Delivery**: Formatted analysis → user display → gamification updates
5. **Learning Integration**: Analysis data → machine learning system → knowledge base updates

## External Dependencies

### AI Services
- **OpenAI GPT-4**: Primary analysis engine
- **Tesseract OCR**: Image text extraction

### Payment Processing
- **Stripe**: Payment gateway and subscription management

### Document Processing
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing
- **Pillow**: Image processing for OCR

### Infrastructure
- **PostgreSQL**: Production database
- **Flask-Migrate**: Database migrations
- **Gunicorn**: WSGI server for production

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with Nix package management
- **Server**: Gunicorn with autoscale deployment
- **Port Configuration**: Internal 5000 → External 80
- **Environment Variables**: Secrets management for API keys

### Database Configuration
- **Development**: SQLite with local file storage
- **Production**: PostgreSQL with connection pooling
- **Migrations**: Automatic schema management with Flask-Migrate

### Environment Requirements
- **API Keys**: OpenAI API key, Stripe keys (test/live)
- **Database**: PostgreSQL connection string for production
- **Session Security**: Secret key for session encryption

## Changelog

- June 26, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.