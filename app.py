import os
import logging
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, jsonify, session, flash, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import stripe
from utils.pdf_tools import extract_text_from_file
from utils.ai_analyzer import analyze_with_gpt4
from config import STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY
from translations import get_translation

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    # Fix for newer SQLAlchemy versions
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///legal_assistant.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
} if database_url else {}

# Import and initialize database
from models import db, DocumentAnalysis, User, PaymentRecord
from models_gamification import UserProgress, Achievement
from utils.gamification import GamificationService
from flask_migrate import Migrate

db.init_app(app)
migrate = Migrate(app, db)

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Create database tables
with app.app_context():
    db.create_all()
    # Initialize gamification system
    GamificationService.initialize_gamification()

# Configure domain for Stripe redirects
def get_domain():
    # Use request context if available
    try:
        # Get the host from the current request
        host = request.headers.get('Host')
        if host:
            # Ensure we use HTTPS for external domains
            if 'replit.dev' in host or 'replit.app' in host:
                return f"https://{host}"
            elif 'localhost' in host:
                return f"http://{host}"
            else:
                return f"https://{host}"
    except RuntimeError:
        # No request context available
        pass
    
    # Fallback to environment variables
    # Check for Replit domains
    replit_domains = os.environ.get('REPLIT_DOMAINS')
    if replit_domains:
        domain = replit_domains.split(',')[0].strip()
        return f"https://{domain}"
    
    # Check for dev domain
    dev_domain = os.environ.get('REPLIT_DEV_DOMAIN')
    if dev_domain:
        return f"https://{dev_domain}"
    
    # Fallback to localhost
    return "http://localhost:5000"

YOUR_DOMAIN = get_domain()
logging.info(f"Application domain configured as: {YOUR_DOMAIN}")

@app.route('/')
def index():
    # Initialize session if needed
    if 'language' not in session:
        session['language'] = 'en'
        session.permanent = True
    
    lang = session.get('language', 'en')
    t = get_translation(lang)
    
    # Get user stats for gamification display
    user_stats = GamificationService.get_user_stats(
        session.get('session_id', session.get('_id', 'anonymous'))
    )
    
    logging.info(f"Index route accessed - Session language: {lang}")
    return render_template('index.html', 
                         stripe_public_key=STRIPE_PUBLIC_KEY, 
                         user_stats=user_stats,
                         gamification_result=session.pop('gamification_result', None),
                         t=t, lang=lang)

@app.route('/set-language', methods=['POST'])
def set_language():
    selected_lang = request.form.get('language')
    if selected_lang in ['en', 'ro', 'de', 'it', 'es', 'ar']:
        session['language'] = selected_lang
        logging.info(f"Language set to: {selected_lang}")
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Ensure session is properly initialized
        if 'language' not in session:
            session['language'] = 'en'
        
        # Clear any previous session data
        session.pop('doc_text', None)
        session.pop('full_doc_text', None)
        session.pop('processed_files', None)
        session.pop('stripe_session_id', None)
        
        logging.info(f"Starting file upload process - Session ID: {session.get('_id', 'new')}")
        
        # Handle scanned image from camera
        scanned_base64 = request.form.get('scannedImage')
        files = request.files.getlist('file')
        camera_files = request.files.getlist('camera')
        texts = []
        processed_files = []
        
        logging.info(f"Upload request - Files: {len(files)}, Camera files: {len(camera_files)}, Scanned: {bool(scanned_base64)}")

        # Process scanned image if provided
        if scanned_base64:
            try:
                from base64 import b64decode
                from io import BytesIO
                from PIL import Image
                import pytesseract
                
                # Decode base64 image
                image_data = b64decode(scanned_base64.split(",")[1])
                image = Image.open(BytesIO(image_data))
                
                # Extract text using OCR with selected language
                user_lang = session.get('language', 'en')
                ocr_lang_map = {
                    'en': 'eng',
                    'ro': 'ron', 
                    'de': 'deu',
                    'it': 'ita',
                    'es': 'spa',
                    'ar': 'ara'
                }
                ocr_lang = ocr_lang_map.get(user_lang, 'eng')
                text = pytesseract.image_to_string(image, lang=ocr_lang)
                if text.strip():
                    texts.append(text)
                    processed_files.append('Scanned Document')
                    logging.info("Successfully processed scanned document")
                else:
                    flash('Could not extract text from scanned document. Please try again or upload a clearer image.', 'warning')
                    
            except Exception as e:
                logging.error(f"Error processing scanned image: {str(e)}")
                flash('Error processing scanned document. Please try again.', 'error')

        # Process uploaded files
        all_files = files + camera_files  # Combine regular files and camera files
        if all_files and not all(file.filename == '' for file in all_files):
            for file in all_files:
                if file.filename != '':
                    try:
                        text = extract_text_from_file(file)
                        if text.strip():
                            texts.append(text)
                            processed_files.append(file.filename)
                        else:
                            flash(f'Could not extract text from {file.filename}', 'warning')
                    except Exception as e:
                        logging.error(f"Error processing file {file.filename}: {str(e)}")
                        flash(f'Error processing {file.filename}: {str(e)}', 'error')
        
        # Check if any text was extracted
        if not texts:
            flash('No text could be extracted from the uploaded files or scanned document. Please check your documents and try again.', 'error')
            return redirect(url_for('index'))
        
        # Store document text and file info in session (compress for large texts)
        doc_text = "\n\n--- Document Separator ---\n\n".join(texts)
        
        # Create database record for the document analysis
        try:
            # Get or create session ID
            if '_id' not in session:
                session['_id'] = str(uuid.uuid4())
                session.permanent = True
            
            analysis_record = DocumentAnalysis(
                session_id=session['_id'],
                file_names=json.dumps(processed_files),
                document_text=doc_text,
                language=session.get('language', 'en'),
                payment_status='pending'
            )
            
            db.session.add(analysis_record)
            db.session.commit()
            
            # Store analysis ID in session
            session['analysis_id'] = analysis_record.id
            logging.info(f"Document analysis record created with ID: {analysis_record.id}")
            
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            # Continue without database storage if DB fails
            
        # If text is too large, truncate and store summary instead
        if len(doc_text) > 10000:  # 10KB limit for session
            session['doc_text'] = doc_text[:10000] + "\n\n[Document truncated for session storage - full text will be analyzed]"
            session['full_doc_text'] = doc_text  # Store full text temporarily
        else:
            session['doc_text'] = doc_text
            
        session['processed_files'] = processed_files
        
        # Track gamification progress
        is_photo = any(f.lower().endswith(('.jpg', '.jpeg', '.png')) for f in processed_files)
        is_multiple = len(files) > 1
        gamification_result = GamificationService.track_document_upload(
            session.get('session_id', session.get('_id', 'anonymous')),
            file_count=len(files),
            is_photo=is_photo,
            is_multiple=is_multiple
        )
        
        # Store gamification results in session for display
        session['gamification_result'] = {
            'xp_gained': gamification_result['xp_gained'],
            'level_up': gamification_result['level_up'],
            'new_level': gamification_result['new_level'],
            'earned_achievements': [{'name': a.name, 'description': a.description, 'icon': a.icon, 'rarity': a.rarity} 
                                  for a in gamification_result['earned_achievements']]
        }
        
        # Force session to be saved
        session.modified = True
        
        # Debug session data
        logging.info(f"Session data stored - doc_text length: {len(session.get('doc_text', ''))}")
        logging.info(f"Session data stored - processed_files: {session.get('processed_files', [])}")
        logging.info(f"Gamification result: {gamification_result['xp_gained']} XP gained, Level: {gamification_result['new_level']}")
        logging.info(f"Session modified flag set: {session.modified}")
        
        return redirect(url_for('checkout'))
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        flash('An error occurred while processing your files. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/checkout')
def checkout():
    # Debug session data
    logging.info(f"Checkout route - Session keys: {list(session.keys())}")
    logging.info(f"Checkout route - doc_text exists: {'doc_text' in session}")
    logging.info(f"Checkout route - doc_text length: {len(session.get('doc_text', ''))}")
    
    if 'doc_text' not in session:
        flash('No document found. Please upload a document first.', 'error')
        return redirect(url_for('index'))
    
    lang = session.get('language', 'en')
    t = get_translation(lang)
    processed_files = session.get('processed_files', [])
    return render_template('checkout.html', files=processed_files, t=t, lang=lang)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        # Debug session data
        logging.info(f"Payment route - Session keys: {list(session.keys())}")
        logging.info(f"Payment route - doc_text exists: {'doc_text' in session}")
        logging.info(f"Payment route - doc_text length: {len(session.get('doc_text', ''))}")
        
        if 'doc_text' not in session:
            logging.error("No document found in session for checkout")
            flash('No document found. Please upload a document first.', 'error')
            return redirect(url_for('index'))
        
        # Get current domain dynamically
        current_domain = get_domain()
        success_url = current_domain + '/success'
        cancel_url = current_domain + '/checkout'
        
        logging.info(f"Creating Stripe session with domain: {current_domain}")
        logging.info(f"Success URL: {success_url}")
        logging.info(f"Cancel URL: {cancel_url}")
        logging.info(f"Request Host: {request.headers.get('Host', 'Not available')}")
        logging.info(f"Stripe API Key configured: {bool(stripe.api_key and not stripe.api_key.startswith('sk_test_default'))}")
        
        # Validate Stripe API key
        if not stripe.api_key or stripe.api_key.startswith('sk_test_default'):
            logging.error("Invalid Stripe API key")
            flash('Payment system configuration error. Please contact support.', 'error')
            return redirect(url_for('checkout'))
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': 10000,  # €100.00
                    'product_data': {
                        'name': 'Legal Document Analysis',
                        'description': 'Professional AI-powered legal document analysis and insights'
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            allow_promotion_codes=False,
            billing_address_collection='auto'
        )
        
        logging.info(f"Stripe session created successfully with ID: {checkout_session.id}")
        logging.info(f"Redirect URL: {checkout_session.url}")
        
        # Create payment record in database
        try:
            analysis_id = session.get('analysis_id')
            if analysis_id:
                payment_record = PaymentRecord(
                    stripe_session_id=checkout_session.id,
                    document_analysis_id=analysis_id,
                    amount=10000,  # €100.00 in cents
                    currency='EUR',
                    status='pending'
                )
                db.session.add(payment_record)
                
                # Update analysis record with Stripe session ID
                analysis = DocumentAnalysis.query.get(analysis_id)
                if analysis:
                    analysis.stripe_session_id = checkout_session.id
                
                db.session.commit()
                logging.info(f"Payment record created for analysis ID: {analysis_id}")
                
        except Exception as db_error:
            logging.error(f"Database error creating payment record: {str(db_error)}")
            # Continue with payment flow even if database fails
        
        if checkout_session.url:
            # Store session ID for verification
            session['stripe_session_id'] = checkout_session.id
            return redirect(checkout_session.url, code=303)
        else:
            logging.error("No redirect URL in Stripe session")
            flash('Payment session creation failed. Please try again.', 'error')
            return redirect(url_for('checkout'))
            
    except Exception as e:
        error_msg = str(e)
        if 'Invalid API Key' in error_msg or 'authentication' in error_msg.lower():
            logging.error(f"Stripe authentication error: {error_msg}")
            flash('Payment system authentication error. Please contact support.', 'error')
        elif 'invalid request' in error_msg.lower():
            logging.error(f"Stripe invalid request error: {error_msg}")
            flash('Payment configuration error. Please try again or contact support.', 'error')
        else:
            logging.error(f"Stripe session creation error: {error_msg}")
            flash(f'Payment error: {error_msg}', 'error')
        return redirect(url_for('checkout'))

@app.route('/success')
def success():
    try:
        # Update payment status in database
        try:
            stripe_session_id = session.get('stripe_session_id')
            analysis_id = session.get('analysis_id')
            
            if stripe_session_id and analysis_id:
                # Update payment record
                payment_record = PaymentRecord.query.filter_by(stripe_session_id=stripe_session_id).first()
                if payment_record:
                    payment_record.status = 'completed'
                    payment_record.completed_at = datetime.utcnow()
                
                # Update analysis record
                analysis_record = DocumentAnalysis.query.get(analysis_id)
                if analysis_record:
                    analysis_record.payment_status = 'completed'
                
                db.session.commit()
                logging.info(f"Payment status updated for analysis ID: {analysis_id}")
                
        except Exception as db_error:
            logging.error(f"Database error updating payment status: {str(db_error)}")
        
        # Use full document text if available, otherwise use truncated version
        doc_text = session.get('full_doc_text') or session.get('doc_text', '')
        processed_files = session.get('processed_files', [])
        
        if not doc_text:
            flash('No document found. Please start over.', 'error')
            return redirect(url_for('index'))
        
        # Analyze the document with GPT-4 in user's preferred language
        lang = session.get('language', 'en')
        t = get_translation(lang)
        analysis = analyze_with_gpt4(doc_text, lang)
        
        # Store analysis result in database
        try:
            analysis_id = session.get('analysis_id')
            if analysis_id:
                analysis_record = DocumentAnalysis.query.get(analysis_id)
                if analysis_record:
                    analysis_record.analysis_result = analysis
                    analysis_record.updated_at = datetime.utcnow()
                    db.session.commit()
                    logging.info(f"Analysis result stored for ID: {analysis_id}")
                    
        except Exception as db_error:
            logging.error(f"Database error storing analysis: {str(db_error)}")
        
        # Track gamification progress for completed analysis
        analysis_gamification = GamificationService.track_document_analysis(
            session.get('session_id', session.get('_id', 'anonymous'))
        )
        
        # Store analysis gamification results in session
        session['analysis_gamification'] = {
            'xp_gained': analysis_gamification['xp_gained'],
            'level_up': analysis_gamification['level_up'],
            'new_level': analysis_gamification['new_level'],
            'earned_achievements': [{'name': a.name, 'description': a.description, 'icon': a.icon, 'rarity': a.rarity} 
                                  for a in analysis_gamification['earned_achievements']]
        }
        
        # Get complete user stats for display
        user_stats = GamificationService.get_user_stats(
            session.get('session_id', session.get('_id', 'anonymous'))
        )
        
        # Clear the full document text from session after analysis
        if 'full_doc_text' in session:
            del session['full_doc_text']
        
        return render_template('result.html', 
                             analysis=analysis, 
                             files=processed_files, 
                             user_stats=user_stats,
                             analysis_gamification=session.get('analysis_gamification'),
                             t=t, lang=lang)
        
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        lang = session.get('language', 'en')
        t = get_translation(lang)
        return render_template('error.html', 
                             error_title=t.get('error_occurred', 'Analysis Failed'),
                             error_message='We encountered an error while analyzing your document. Please contact support if this issue persists.',
                             t=t, lang=lang)

@app.route('/clear-session')
def clear_session():
    session.clear()
    return redirect(url_for('index'))

@app.route('/debug-info')
def debug_info():
    """Debug endpoint to check domain and session configuration"""
    return {
        'domain': get_domain(),
        'session_keys': list(session.keys()),
        'session_id': session.get('_id', 'none'),
        'language': session.get('language', 'not_set'),
        'has_doc_text': 'doc_text' in session,
        'doc_text_length': len(session.get('doc_text', '')),
        'stripe_configured': bool(stripe.api_key and not stripe.api_key.startswith('sk_test_default')),
        'openai_configured': bool(os.environ.get('OPENAI_API_KEY')),
        'database_url': bool(os.environ.get('DATABASE_URL'))
    }

@app.route('/admin/database')
def database_admin():
    """Database administration endpoint"""
    try:
        # Get recent document analyses
        analyses = DocumentAnalysis.query.order_by(DocumentAnalysis.created_at.desc()).limit(10).all()
        
        # Get recent payments
        payments = PaymentRecord.query.order_by(PaymentRecord.created_at.desc()).limit(10).all()
        
        # Get database statistics
        total_analyses = DocumentAnalysis.query.count()
        completed_payments = PaymentRecord.query.filter_by(status='completed').count()
        pending_payments = PaymentRecord.query.filter_by(status='pending').count()
        
        return {
            'total_analyses': total_analyses,
            'completed_payments': completed_payments,
            'pending_payments': pending_payments,
            'recent_analyses': [
                {
                    'id': a.id,
                    'session_id': a.session_id[:8] + '...',
                    'language': a.language,
                    'payment_status': a.payment_status,
                    'created_at': a.created_at.isoformat() if a.created_at else None,
                    'has_analysis': bool(a.analysis_result)
                } for a in analyses
            ],
            'recent_payments': [
                {
                    'id': p.id,
                    'stripe_session_id': p.stripe_session_id[:8] + '...',
                    'amount': p.amount,
                    'currency': p.currency,
                    'status': p.status,
                    'created_at': p.created_at.isoformat() if p.created_at else None
                } for p in payments
            ]
        }
        
    except Exception as e:
        logging.error(f"Database admin error: {str(e)}")
        return {'error': str(e)}, 500

@app.errorhandler(404)
def not_found_error(error):
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('error.html', 
                         error_title='Page Not Found',
                         error_message='The page you are looking for does not exist.',
                         t=t, lang=lang), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {str(error)}")
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('error.html',
                         error_title=t.get('error_occurred', 'Internal Server Error'),
                         error_message='An internal server error occurred. Please try again later.',
                         t=t, lang=lang), 500
