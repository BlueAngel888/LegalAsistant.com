import os
import logging
import json
import uuid
import threading
import time
import markdown
from datetime import datetime
from flask import Flask, render_template, request, redirect, jsonify, session, flash, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
import stripe
from utils.pdf_tools import extract_text_from_file
from utils.ai_analyzer import analyze_with_gpt4
from utils.enhanced_legal_analyzer import analyze_with_enhanced_gpt4
from utils.document_consistency_analyzer import DocumentConsistencyAnalyzer
from utils.learning_service import analyze_with_learning_integration
from config import STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY
from translations import get_translation
from auth import clerk_template_context, load_auth_context, login_required

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def clean_text_for_db(text):
    """Remove NUL characters and other problematic characters from text before database storage"""
    if not text:
        return text
    # Remove NUL (0x00) characters which PostgreSQL doesn't allow
    cleaned = text.replace('\x00', '')
    # Also remove other control characters that might cause issues (except newline, tab, carriage return)
    cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')
    return cleaned


def is_failed_analysis(text):
    """Return True for transient analyzer output that must never be cached."""
    if not text:
        return False
    normalized = text.strip().lower()
    return (
        normalized.startswith("analysis error:")
        or normalized.startswith("ai analysis error:")
        or "eroare temporară" in normalized
        or "sistemul ai este temporar indisponibil" in normalized
    )

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https
app.before_request(load_auth_context)
app.context_processor(clerk_template_context)

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
from models_learning import LegalAnalysisLearning, LegalKnowledgeBase, AnalysisImprovement
from utils.gamification import GamificationService
from utils.learning_service import LegalLearningService, analyze_with_learning_integration
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
    # Initialize learning system
    LegalLearningService.initialize_knowledge_base()

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

def background_ocr_processing(analysis_id, files_data, app_context):
    """Process OCR in background thread after upload"""
    with app_context:
        try:
            logging.info(f"BACKGROUND OCR: Starting processing for analysis {analysis_id}")
            
            # Get analysis record
            analysis_record = DocumentAnalysis.query.get(analysis_id)
            if not analysis_record:
                logging.error(f"BACKGROUND OCR: Analysis record not found: {analysis_id}")
                return
            
            # Process each file with OCR
            all_text_content = []
            processed_count = 0
            
            for file_info in files_data:
                try:
                    filename = file_info['filename']
                    file_content = file_info['content']
                    
                    logging.info(f"BACKGROUND OCR: Processing {filename}")
                    
                    # Extract text using OCR with timeout protection
                    from utils.pdf_tools import extract_text_from_image
                    text = extract_text_from_image(file_content)
                    
                    if text and text.strip():
                        all_text_content.append(f"=== {filename} ===\n{text}\n")
                        processed_count += 1
                        logging.info(f"BACKGROUND OCR: Extracted {len(text)} characters from {filename}")
                    else:
                        logging.warning(f"BACKGROUND OCR: No text extracted from {file_info['filename']}")
                        
                except Exception as file_error:
                    logging.error(f"BACKGROUND OCR: Error processing {file_info['filename']}: {str(file_error)}")
                    continue
            
            # Update analysis record with real OCR content
            if all_text_content:
                final_text = "\n".join(all_text_content)
                # Clean text before saving to database to remove NUL characters
                analysis_record.document_text = clean_text_for_db(final_text)
                
                # Mark as fully processed
                analysis_record.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                logging.info(f"BACKGROUND OCR: Completed! Updated analysis {analysis_id} with {len(final_text)} characters from {processed_count} files")
            else:
                logging.error(f"BACKGROUND OCR: No text could be extracted from any files for analysis {analysis_id}")
                
        except Exception as e:
            logging.error(f"BACKGROUND OCR: Fatal error for analysis {analysis_id}: {str(e)}")
            # Don't let background processing crash the main app

def background_ai_analysis(analysis_id, document_country, analysis_language, app_context):
    """Process AI analysis in background thread immediately after upload"""
    with app_context:
        try:
            logging.info(f"BACKGROUND AI: Starting analysis for document {analysis_id}")
            
            # Get analysis record
            analysis_record = DocumentAnalysis.query.get(analysis_id)
            if not analysis_record:
                logging.error(f"BACKGROUND AI: Analysis record not found: {analysis_id}")
                return
            
            # Check if we have document text to analyze
            doc_text = analysis_record.document_text
            if not doc_text or len(doc_text.strip()) < 10:
                logging.warning(f"BACKGROUND AI: No valid document text for analysis {analysis_id}")
                return
            
            # Import the AI analyzer
            from utils.ai_analyzer import analyze_with_gpt4
            
            # Add country hint to document text for GPT analysis
            doc_text_with_hint = f"countryHint: {document_country}\n\n{doc_text}"
            
            try:
                # Call OpenAI API for analysis
                logging.info(f"BACKGROUND AI: Calling OpenAI API for {document_country}")
                analysis_result = analyze_with_gpt4(doc_text_with_hint, analysis_language)
                
                # Store the analysis result in database (clean it first)
                analysis_record.analysis_result = clean_text_for_db(analysis_result)
                analysis_record.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                logging.info(f"BACKGROUND AI: Analysis completed successfully for {analysis_id}")
                logging.info(f"BACKGROUND AI: Result length: {len(analysis_result)} characters")
                
            except Exception as api_error:
                logging.error(f"BACKGROUND AI: OpenAI API error for {analysis_id}: {str(api_error)}")
                # Store error message but don't crash
                error_msg = f"AI Analysis Error: {str(api_error)}"
                analysis_record.analysis_result = error_msg
                db.session.commit()
                
        except Exception as e:
            logging.error(f"BACKGROUND AI: Fatal error for analysis {analysis_id}: {str(e)}")
            # Don't let background processing crash the main app

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


@app.route('/sign-in', defaults={'path': ''})
@app.route('/sign-in/<path:path>')
def sign_in(path):
    if clerk_template_context()["auth_user"]:
        next_url = request.args.get("next", "")
        return redirect(next_url if next_url.startswith("/") and not next_url.startswith("//") else url_for("index"))
    return render_template("auth.html", mode="sign-in", t=get_translation(session.get("language", "en")))


@app.route('/sign-up', defaults={'path': ''})
@app.route('/sign-up/<path:path>')
def sign_up(path):
    if clerk_template_context()["auth_user"]:
        next_url = request.args.get("next", "")
        return redirect(next_url if next_url.startswith("/") and not next_url.startswith("//") else url_for("index"))
    return render_template("auth.html", mode="sign-up", t=get_translation(session.get("language", "en")))

@app.route('/set-language', methods=['POST'])
def set_language():
    selected_lang = request.form.get('language')
    if selected_lang in ['en', 'ro', 'de', 'it', 'es', 'ar']:
        session['language'] = selected_lang
        logging.info(f"Language set to: {selected_lang}")
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    try:
        logging.info("=== UPLOAD ROUTE CALLED ===")
        logging.info(f"Request method: {request.method}")
        logging.info(f"Request form keys: {list(request.form.keys())}")
        logging.info(f"Request files keys: {list(request.files.keys())}")
        
        # Ensure session is properly initialized
        if 'language' not in session:
            session['language'] = 'en'
        
        # Get legal analysis parameters from form (check both upload and camera tabs)
        document_country = request.form.get('document_country', '').strip() or request.form.get('document_country_camera', '').strip()
        analysis_language = request.form.get('analysis_language', '').strip() or request.form.get('analysis_language_camera', '').strip()
        
        if not document_country or not analysis_language:
            flash('Please select both document country and analysis language.', 'error')
            return redirect(url_for('index'))
        
        # Store legal analysis parameters in session
        session['document_country'] = document_country
        session['analysis_language'] = analysis_language
        
        # Clear any previous session data
        for stale_key in (
            'doc_text', 'full_doc_text', 'processed_files', 'analysis_id',
            'has_document', 'stripe_session_id', 'background_processing',
            'needs_full_processing', 'is_fast_track',
            'payment_status', 'discount_code', 'discount_percent', 'free_access',
            'analysis_type', 'fine_type', 'dd_category', 'company_name',
            'registration_number', 'compare_countries', 'legal_area',
            'contract_action', 'source_lang', 'target_lang',
        ):
            session.pop(stale_key, None)
        
        logging.info(f"Starting file upload process - Session ID: {session.get('_id', 'new')}")
        logging.info(f"Upload request details - Country: {document_country}, Language: {analysis_language}")
        
        # Handle scanned image from camera
        scanned_base64 = request.form.get('scannedImage')
        files = request.files.getlist('file')
        camera_files = request.files.getlist('camera')
        texts = []
        processed_files = []
        
        total_files = len(files) + len(camera_files) + (1 if scanned_base64 else 0)
        logging.info(f"Upload request - Files: {len(files)}, Camera files: {len(camera_files)}, Scanned: {bool(scanned_base64)}, Total: {total_files}")
        
        if files:
            for i, f in enumerate(files):
                logging.info(f"File {i+1}: {f.filename} (size: {f.content_length if hasattr(f, 'content_length') else 'unknown'})")
        
        # Add processing status for large batches
        if total_files > 3:
            logging.info(f"Processing {total_files} files - this may take a few moments...")

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
                # Clean the text to remove NUL characters
                text = clean_text_for_db(text)
                if text.strip():
                    texts.append(text)
                    processed_files.append('Scanned Document')
                    logging.info("Successfully processed scanned document")
                else:
                    flash('Could not extract text from scanned document. Please try again or upload a clearer image.', 'warning')
                    
            except Exception as e:
                logging.error(f"Error processing scanned image: {str(e)}")
                flash('Error processing scanned document. Please try again.', 'error')

        # Extract every uploaded document before checkout.  In particular, do not
        # send batches to image OCR regardless of their actual file type.
        all_files = files + camera_files  # Combine regular files and camera files
        if all_files and not all(file.filename == '' for file in all_files):
            for i, file in enumerate(all_files):
                if not file.filename:
                    continue
                try:
                    logging.info(f"Extracting file {i + 1}/{len(all_files)}: {file.filename}")
                    text = clean_text_for_db(extract_text_from_file(file))
                    if not text or not text.strip():
                        raise ValueError("No text could be extracted")
                    texts.append(f"=== {file.filename} ===\n{text}")
                    processed_files.append(file.filename)
                except Exception as extraction_error:
                    logging.error("Extraction failed for %s: %s", file.filename, extraction_error)
                    flash(f'Could not extract text from {file.filename}. Please check the file and try again.', 'error')
                    return redirect(url_for('index'))
        
        # Check if any text was extracted
        if not texts:
            flash('No text could be extracted from the uploaded files or scanned document. Please check your documents and try again.', 'error')
            return redirect(url_for('index'))
        
        # Store document text and file info in session (compress for large texts)
        doc_text = "\n\n--- Document Separator ---\n\n".join(texts)
        
        # Analyze document consistency for multiple files
        consistency_warnings = []
        if len(texts) > 1:
            try:
                analyzer = DocumentConsistencyAnalyzer()
                documents = [
                    {
                        'filename': processed_files[i],
                        'text': texts[i],
                        'size': len(texts[i])
                    } for i in range(len(texts))
                ]
                
                consistency_result = analyzer.analyze_document_consistency(documents)
                logging.info(f"Document consistency analysis - Consistent: {consistency_result['is_consistent']}, Confidence: {consistency_result['confidence']:.2f}")
                
                if not consistency_result['is_consistent'] or consistency_result['confidence'] < 0.7:
                    for warning in consistency_result['warnings']:
                        if warning['severity'] in ['high', 'medium']:
                            warning_msg = f"⚠️ {warning['message']}"
                            consistency_warnings.append(warning_msg)
                            logging.warning(f"Document consistency warning: {warning['message']}")
                
                # Store consistency info in session for display
                session['consistency_result'] = {
                    'is_consistent': consistency_result['is_consistent'],
                    'confidence': consistency_result['confidence'],
                    'warnings': consistency_warnings,
                    'recommendations': consistency_result['recommendations']
                }
                
            except Exception as e:
                logging.error(f"Error in document consistency analysis: {str(e)}")
                # Continue without consistency check if analysis fails
        
        # Create database record for the document analysis
        try:
            # Get or create session ID
            if '_id' not in session:
                session['_id'] = str(uuid.uuid4())
                session.permanent = True
            
            # Check if this is fast-track processing
            is_fast_track = len(all_files) > 3
            
            # Clean the document text to remove NUL characters before saving to database
            cleaned_doc_text = clean_text_for_db(doc_text)
            
            analysis_record = DocumentAnalysis(
                session_id=session['_id'],
                file_names=json.dumps(processed_files),
                document_text=cleaned_doc_text,
                language=session.get('language', 'en'),
                payment_status='pending'
            )
            
            db.session.add(analysis_record)
            db.session.commit()
            
            # Store analysis ID and processing info in session
            session['analysis_id'] = analysis_record.id
            session['is_fast_track'] = is_fast_track
            session['needs_full_processing'] = is_fast_track
            
            logging.info(f"Document analysis record created with ID: {analysis_record.id}, Fast-track: {is_fast_track}")
            
            # AI analysis intentionally starts only after verified payment/free access.
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            db.session.rollback()
            flash('Unable to save the uploaded document. Please try again.', 'error')
            return redirect(url_for('index'))
            
        # Don't store large document text in session - only store metadata
        session['processed_files'] = processed_files
        session['doc_text_length'] = len(doc_text)
        session['has_document'] = True
        
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
        logging.info(f"Session data stored - analysis_id: {session.get('analysis_id')}")
        logging.info(f"Session data stored - processed_files: {session.get('processed_files', [])}")
        logging.info(f"Session data stored - has_document: {session.get('has_document')}")
        logging.info(f"Gamification result: {gamification_result['xp_gained']} XP gained, Level: {gamification_result['new_level']}")
        
        return redirect(url_for('checkout'))
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        flash('An error occurred while processing your files. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/checkout')
@login_required
def checkout():
    # Enhanced debug session data
    logging.info(f"Checkout route - Full session data: {dict(session)}")
    logging.info(f"Checkout route - Session ID: {session.get('_id', 'None')}")
    logging.info(f"Checkout route - has_document: {session.get('has_document', False)}")
    logging.info(f"Checkout route - analysis_id: {session.get('analysis_id', 'None')}")
    logging.info(f"Checkout route - processed_files: {session.get('processed_files', [])}")
    
    # Check if we have document data either in session metadata or database
    has_document = session.get('has_document', False)
    analysis_id = session.get('analysis_id')
    
    if not has_document and not analysis_id:
        logging.error("No document found in session - redirecting to index")
        flash('No document found. Please upload a document first.', 'error')
        return redirect(url_for('index'))
    
    # If we have analysis_id, verify the document exists in database
    if analysis_id:
        try:
            analysis = DocumentAnalysis.query.filter_by(id=analysis_id).first()
            if not analysis:
                logging.error(f"Document analysis not found in database for ID: {analysis_id}")
                flash('Document not found. Please upload a document again.', 'error')
                return redirect(url_for('index'))
            else:
                logging.info(f"Document analysis found in database: {analysis.id}")
        except Exception as e:
            logging.error(f"Database error checking analysis: {str(e)}")
    
    lang = session.get('language', 'en')
    t = get_translation(lang)
    processed_files = session.get('processed_files', [])
    logging.info(f"Rendering checkout with {len(processed_files)} files")
    return render_template('checkout.html', files=processed_files, t=t, lang=lang)

def validate_discount_code(code):
    """Validate discount code and return discount info"""
    if not code:
        return None
    
    code = code.strip().upper()
    
    # Define valid discount codes
    discount_codes = {
        'LETSGO': {'discount_percent': 100, 'free_access': True},
        'LETSGO50': {'discount_percent': 50, 'free_access': False}
    }
    
    return discount_codes.get(code)

@app.route('/apply-discount', methods=['POST'])
@login_required
def apply_discount():
    """Apply discount code and return discount information"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip().upper()
        
        discount_info = validate_discount_code(code)
        
        if discount_info:
            
            # Store discount in session
            session['discount_code'] = code
            session['discount_percent'] = discount_info['discount_percent']
            session['free_access'] = discount_info['free_access']
            
            logging.info(f"Discount code applied: {code} - {discount_info['discount_percent']}% discount")
            
            return jsonify({
                'success': True,
                'discount_percent': discount_info['discount_percent'],
                'free_access': discount_info['free_access'],
                'message': f"Code {code} applied successfully"
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid discount code'
            })
            
    except Exception as e:
        logging.error(f"Error applying discount: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error processing discount code'
        })

@app.route('/free-access', methods=['POST'])
@login_required
def free_access():
    """Handle free access with valid codes"""
    try:
        free_code = request.form.get('free_code', '').strip().upper()
        
        # Check if code is valid
        discount_info = validate_discount_code(free_code)
        
        # Verify free access code - either from session or freshly validated
        if (discount_info and discount_info['free_access']) or \
           (session.get('free_access') and session.get('discount_code') == free_code):
            logging.info(f"Free access granted with code: {free_code}")
            
            # Update session with discount info
            if discount_info:
                session['discount_code'] = free_code
                session['discount_percent'] = discount_info['discount_percent']
                session['free_access'] = discount_info['free_access']
            
            # Mark as free access in session
            session['payment_status'] = 'free_access'
            session['stripe_session_id'] = f'free_{free_code}_{int(time.time())}'
            
            # Update payment record if exists
            analysis_id = session.get('analysis_id')
            if analysis_id:
                analysis_record = DocumentAnalysis.query.get(analysis_id)
                if analysis_record:
                    analysis_record.payment_status = 'free_access'
                    analysis_record.stripe_session_id = session['stripe_session_id']
                    db.session.commit()
            
            return redirect(url_for('success'))
        else:
            flash('Invalid free access code', 'error')
            return redirect(url_for('checkout'))
            
    except Exception as e:
        logging.error(f"Error processing free access: {str(e)}")
        flash('Error processing free access', 'error')
        return redirect(url_for('checkout'))

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        # Debug session data
        logging.info(f"Payment route - Session keys: {list(session.keys())}")
        logging.info(f"Payment route - has_document: {session.get('has_document', False)}")
        logging.info(f"Payment route - analysis_id: {session.get('analysis_id', 'None')}")
        
        # Check if we have document data
        has_document = session.get('has_document', False)
        analysis_id = session.get('analysis_id')
        
        if not has_document and not analysis_id:
            logging.error("No document found for checkout")
            flash('No document found. Please upload a document first.', 'error')
            return redirect(url_for('index'))
        
        # Verify document exists in database
        if analysis_id:
            try:
                analysis = DocumentAnalysis.query.filter_by(id=analysis_id).first()
                if not analysis:
                    logging.error(f"Document analysis not found for ID: {analysis_id}")
                    flash('Document not found. Please upload a document again.', 'error')
                    return redirect(url_for('index'))
            except Exception as e:
                logging.error(f"Database error checking analysis: {str(e)}")
                flash('Error accessing document. Please try again.', 'error')
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
        
        # Create Stripe checkout session with better error handling
        discount_percent = session.get('discount_percent', 0)
        # Stripe expects minor units: €100.00 = 10,000 euro cents.
        amount = max(0, round(10_000 * (100 - discount_percent) / 100))
        if amount == 0:
            flash('Please use the free access button for this discount code.', 'error')
            return redirect(url_for('checkout'))

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': amount,
                    'product_data': {
                        'name': 'Legal Document Analysis',
                        'description': 'Professional AI-powered legal document analysis and insights'
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url,
            allow_promotion_codes=False,
            billing_address_collection='auto',
            client_reference_id=session.get('analysis_id', ''),
            metadata={
                'analysis_id': session.get('analysis_id', ''),
                'session_id': session.get('_id', '')
            }
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
                    amount=amount,
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
            db.session.rollback()
            flash('Unable to record the payment session. No payment was started.', 'error')
            return redirect(url_for('checkout'))
        
        if checkout_session.url:
            # Store session ID for verification
            session['stripe_session_id'] = checkout_session.id
            
            # Use meta refresh for reliable redirect
            logging.info(f"Redirecting to: {checkout_session.url}")
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta http-equiv="refresh" content="0; url={checkout_session.url}">
                <title>Redirecting to Payment...</title>
            </head>
            <body>
                <p>Redirecting to Stripe checkout...</p>
                <script>
                    window.location.href = '{checkout_session.url}';
                </script>
            </body>
            </html>
            '''
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
@login_required
def success():
    try:
        analysis_id = session.get('analysis_id')
        if not analysis_id:
            flash('No document found. Please start over.', 'error')
            return redirect(url_for('index'))

        analysis_record = DocumentAnalysis.query.get(analysis_id)
        if (
            not analysis_record
            or not session.get('_id')
            or analysis_record.session_id != session.get('_id')
        ):
            flash('Document not found. Please start over.', 'error')
            return redirect(url_for('index'))

        # A success URL is not proof of payment. Free access is persisted by the
        # free-access route; paid access is verified against Stripe.
        is_free = (
            session.get('payment_status') == 'free_access'
            and analysis_record.payment_status == 'free_access'
        )
        if not is_free:
            requested_stripe_id = request.args.get('session_id', '')
            stored_stripe_id = session.get('stripe_session_id', '')
            if (
                not requested_stripe_id
                or requested_stripe_id != stored_stripe_id
                or requested_stripe_id != analysis_record.stripe_session_id
            ):
                flash('Payment verification failed.', 'error')
                return redirect(url_for('checkout'))
            try:
                verified_checkout = stripe.checkout.Session.retrieve(requested_stripe_id)
                metadata = getattr(verified_checkout, 'metadata', {}) or {}
                if (
                    getattr(verified_checkout, 'payment_status', None) != 'paid'
                    or metadata.get('analysis_id') != analysis_id
                ):
                    flash('Payment has not been completed.', 'error')
                    return redirect(url_for('checkout'))
            except Exception as stripe_error:
                logging.error("Stripe verification error: %s", stripe_error)
                flash('Unable to verify payment. Please try again.', 'error')
                return redirect(url_for('checkout'))

        # Update payment status in database
        try:
            stripe_session_id = session.get('stripe_session_id')
            
            if stripe_session_id and analysis_id:
                # Update payment record
                payment_record = PaymentRecord.query.filter_by(stripe_session_id=stripe_session_id).first()
                if payment_record:
                    payment_record.status = 'completed'
                    payment_record.completed_at = datetime.utcnow()
                
                # Update analysis record
                analysis_record = DocumentAnalysis.query.get(analysis_id)
                if analysis_record and not is_free:
                    analysis_record.payment_status = 'completed'
                
                db.session.commit()
                logging.info(f"Payment status updated for analysis ID: {analysis_id}")
                
        except Exception as db_error:
            logging.error(f"Database error updating payment status: {str(db_error)}")
        
        # Retrieve document data from database
        doc_text = analysis_record.document_text
        processed_files = json.loads(analysis_record.file_names) if analysis_record.file_names else []
        
        # Check if background OCR processing is complete
        if session.get('background_processing') and doc_text and "INSTANT UPLOAD:" in doc_text:
            logging.info("PAYMENT SUCCESS: Checking if background OCR processing is complete")
            
            # Wait briefly for background processing to complete (if needed)
            max_wait_time = 30  # Maximum 30 seconds
            wait_interval = 2   # Check every 2 seconds
            waited_time = 0
            
            while waited_time < max_wait_time:
                # Refresh analysis record from database
                db.session.refresh(analysis_record)
                
                # Check if background processing updated the content
                if "INSTANT UPLOAD:" not in analysis_record.document_text:
                    logging.info(f"PAYMENT SUCCESS: Background OCR completed after {waited_time} seconds")
                    doc_text = analysis_record.document_text
                    break
                
                time.sleep(wait_interval)
                waited_time += wait_interval
                logging.info(f"PAYMENT SUCCESS: Waiting for background OCR... {waited_time}s")
            
            if "INSTANT UPLOAD:" in doc_text:
                logging.warning("PAYMENT SUCCESS: Background OCR still in progress - proceeding with placeholder")
            
            session['background_processing'] = False
        
        if not doc_text or len(doc_text.strip()) < 10:
            flash('No document text found. Please start over.', 'error')
            return redirect(url_for('index'))
        
        # Get legal analysis parameters
        document_country = session.get('document_country', 'RO')
        analysis_language = session.get('analysis_language', 'ro')
        
        # Analyze the document with safer error handling
        lang = session.get('language', 'en')
        t = get_translation(lang)
        session_id = session.get('session_id', session.get('_id', 'anonymous'))
        
        # Check if analysis is already done in background
        analysis_failed = False
        if analysis_record.analysis_result and not is_failed_analysis(analysis_record.analysis_result):
            logging.info(f"SUCCESS ROUTE: Using pre-computed analysis from background processing")
            
            # Get analysis language
            analysis_language = session.get('analysis_language', 'ro')
            
            # Add access type header
            if session.get('payment_status') == 'free_access':
                access_header = f"ANALIZĂ JURIDICĂ COMPLETĂ - ACCES GRATUIT COD {session.get('discount_code', 'LETSGO')}\n\n"
            else:
                access_header = "ANALIZĂ JURIDICĂ COMPLETĂ - ACCES PREMIUM\n\n"
            
            # Use the pre-computed analysis
            analysis = access_header + analysis_record.analysis_result
            logging.info(f"Retrieved pre-computed analysis, length: {len(analysis)}")
            
        else:
            # If analysis is not ready yet, compute it now
            logging.info(f"SUCCESS ROUTE: Analysis not ready in background, computing now")
            
            # Use different analysis approach based on access type
            try:
                # Debug logging for payment status
                payment_status = session.get('payment_status')
                logging.info(f"SUCCESS ROUTE: Payment status = {payment_status}")
                logging.info(f"SUCCESS ROUTE: All session keys = {list(session.keys())}")
                
                # Use enhanced AI analysis for ALL access types (paid and free access)
                selected_country = session.get('document_country', 'RO')
                country_name = {'RO': 'România', 'DE': 'Germania', 'FR': 'Franța', 'IT': 'Italia', 'US': 'SUA', 'UK': 'Marea Britanie', 'AE': 'EAU'}.get(selected_country, 'România')
                
                logging.info(f"Using enhanced AI analysis for country: {selected_country} ({country_name})")
                
                # Use OpenAI API with GlobalLegalAnalyserGPT format
                logging.info(f"Using OpenAI API GlobalLegalAnalyserGPT analysis for {country_name}")
                
                try:
                    # Import the AI analyzer
                    from utils.ai_analyzer import (analyze_with_gpt4, analyze_fine_penalty, analyze_due_diligence, 
                        analyze_company_verification, analyze_jurisdiction_comparison, analyze_conflict_of_laws,
                        analyze_international_contract, analyze_sanctions_compliance, analyze_arbitration,
                        analyze_immigration, analyze_legal_translation)
                    
                    # Add country hint to document text for GPT analysis
                    doc_text_with_hint = f"countryHint: {selected_country}\n\n{doc_text}"
                    
                    # Get analysis language
                    analysis_language = session.get('analysis_language', 'ro')
                    
                    # Get analysis type
                    analysis_type = session.get('analysis_type', 'document')
                    
                    # Add analysis type-specific header
                    analysis_type_headers = {
                        'document': 'ANALIZĂ JURIDICĂ COMPLETĂ',
                        'fine': 'ANALIZĂ AMENDĂ / PENALITATE',
                        'due_diligence': 'ANALIZĂ DUE DILIGENCE',
                        'company_verification': 'VERIFICARE COMPANIE B2B',
                        'jurisdiction_compare': 'COMPARARE JURISDICȚII',
                        'conflict_laws': 'CONFLICT DE LEGI - LEA APLICABILĂ',
                        'international_contract': 'CONTRACT INTERNAȚIONAL',
                        'sanctions': 'VERIFICARE SANCȚIUNI & CONFORMITATE',
                        'arbitration': 'ANALIZĂ ARBITRAJ INTERNAȚIONAL',
                        'immigration': 'ANALIZĂ IMIGRARE & VIZE',
                        'translation': 'TRADUCERE JURIDICĂ'
                    }
                    header_title = analysis_type_headers.get(analysis_type, 'ANALIZĂ JURIDICĂ')
                    
                    # Add access type suffix
                    if session.get('payment_status') == 'free_access':
                        access_header = f"{header_title} - ACCES GRATUIT COD {session.get('discount_code', 'LETSGO')}\n\n"
                    else:
                        access_header = f"{header_title} - ACCES PREMIUM\n\n"
                    
                    # Always use OpenAI API for both free and paid access
                    try:
                        logging.info(f"Using OpenAI API for analysis - Payment status: {session.get('payment_status')}, Analysis type: {analysis_type}")
                        
                        # Call appropriate analysis function based on type
                        if analysis_type == 'fine':
                            fine_type = session.get('fine_type', 'auto')
                            analysis = analyze_fine_penalty(doc_text_with_hint, selected_country, analysis_language, fine_type)
                        elif analysis_type == 'due_diligence':
                            dd_category = session.get('dd_category', 'b2b_contract')
                            analysis = analyze_due_diligence(doc_text_with_hint, selected_country, analysis_language, dd_category)
                        elif analysis_type == 'company_verification':
                            company_name = session.get('company_name', '')
                            reg_number = session.get('registration_number', '')
                            analysis = analyze_company_verification(company_name, selected_country, reg_number, analysis_language, doc_text)
                        elif analysis_type == 'jurisdiction_compare':
                            countries = session.get('compare_countries', '').split(',')
                            legal_area = session.get('legal_area', 'data_protection')
                            analysis = analyze_jurisdiction_comparison(countries, legal_area, doc_text, analysis_language)
                        elif analysis_type == 'conflict_laws':
                            analysis = analyze_conflict_of_laws(doc_text, analysis_language)
                        elif analysis_type == 'international_contract':
                            action = session.get('contract_action', 'review')
                            analysis = analyze_international_contract(doc_text, action, analysis_language)
                        elif analysis_type == 'sanctions':
                            analysis = analyze_sanctions_compliance(doc_text, analysis_language)
                        elif analysis_type == 'arbitration':
                            analysis = analyze_arbitration(doc_text, analysis_language)
                        elif analysis_type == 'immigration':
                            analysis = analyze_immigration(doc_text, analysis_language)
                        elif analysis_type == 'translation':
                            source = session.get('source_lang', 'auto')
                            target = session.get('target_lang', 'en')
                            analysis = analyze_legal_translation(doc_text, source, target)
                        else:
                            # Default document analysis
                            analysis = analyze_with_gpt4(doc_text_with_hint, analysis_language)
                        
                        # Prepend access header to analysis
                        analysis = access_header + analysis
                        
                        # Save the analysis to database for future use
                        analysis_record.analysis_result = analysis
                        db.session.commit()
                        
                        logging.info(f"OpenAI API GlobalLegalAnalyserGPT analysis completed successfully")
                    
                    except Exception as api_error:
                        logging.error(f"OpenAI API error: {str(api_error)}")
                        analysis_failed = True
                        # Return error message with retry suggestion
                        analysis = f"""{access_header}

⚠️ **EROARE TEMPORARĂ**

Sistemul de analiză AI este momentan suprasolicitat. Vă rugăm să reîncercați în câteva momente.

Detalii tehnice:
• Document procesat: {country_name}
• Fișiere: {len(processed_files)}
• Cod eroare: {type(api_error).__name__}

**Recomandări:**
1. Așteptați 30 de secunde și reîncercați
2. Dacă problema persistă, contactați suportul tehnic
3. Documentul dvs. a fost salvat și va fi analizat automat

Pentru asistență imediată: support@legalassistant.ai"""
                    
                    logging.info(f"Analysis completed for {country_name}")
                    
                except Exception as ai_error:
                    logging.error(f"Enhanced AI analysis failed: {str(ai_error)}")
                    analysis_failed = True
                    # Fallback comprehensive analysis
                    analysis = f"""ANALIZĂ JURIDICĂ COMPLETĂ - SISTEM AI

Status: Analiză completă prin serviciul Legal Assistant AI
Țara selectată: {country_name}
Document(e) procesat(e): {len(processed_files)} fișier(e)
Data analizei: {datetime.utcnow().strftime('%d %B %Y, %H:%M')}

EROARE TEHNICĂ: Sistemul AI este temporar indisponibil.

Documentul dumneavoastră a fost procesat cu succes și va fi analizat în cel mai scurt timp.

Pentru asistență imediată, vă rugăm să contactați echipa noastră de suport.

IMPORTANT: Analiza va fi reluată automat când sistemul revine online."""
                
                logging.info(f"Document analysis completed successfully, length: {len(analysis)}")
            except Exception as analysis_error:
                logging.error(f"Analysis error: {str(analysis_error)}")
                analysis_failed = True
                # Get analysis language from session for fallback
                analysis_language = session.get('analysis_language', 'ro')
                # Provide fallback analysis for any errors
                analysis = f"""ANALIZĂ JURIDICĂ - DOCUMENT PROCESAT

Tip Document: Document juridic identificat
Status: Procesat cu succes
Limba: {analysis_language.upper()}

1. IDENTIFICAREA ȘI VALIDITATEA FORMALĂ A DOCUMENTULUI
Documentul a fost încărcat și procesat. Pentru o analiză detaliată, vă rugăm să reîncercați.

2. STRUCTURA ȘI CONȚINUTUL LEGAL
Conținutul documentului este disponibil pentru analiză.

3. VERIFICAREA LEGALITĂȚII ȘI CONFORMITĂȚII
Analiza conformității necesită reîncercare.

4. ANALIZA IMPLICAȚIILOR JURIDICE
Implicațiile juridice vor fi analizate la următoarea încercare.

5. ASPECTE FISCALE, CIVILE SAU PENALE  
Aspectele specifice vor fi detaliate după reîncercare.

Nota: În caz de probleme tehnice, vă rugăm să reîncercați analiza."""
        
        # Store analysis result in database
        try:
            analysis_id = session.get('analysis_id')
            if analysis_id and analysis and not analysis_failed and not is_failed_analysis(analysis):
                analysis_record = DocumentAnalysis.query.get(analysis_id)
                if analysis_record:
                    analysis_record.analysis_result = analysis
                    analysis_record.updated_at = datetime.utcnow()
                    db.session.commit()
                    logging.info(f"Analysis result stored for ID: {analysis_id}")
                else:
                    logging.error(f"Analysis record not found for ID: {analysis_id}")
            else:
                logging.warning(f"Missing analysis_id or analysis content for storage")
                    
        except Exception as db_error:
            logging.error(f"Database error storing analysis: {str(db_error)}")
            db.session.rollback()  # Rollback transaction on error
        
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
        
        # GDPR Compliance: Auto-delete document text after analysis completion
        try:
            analysis_id = session.get('analysis_id')
            if analysis_id and not analysis_failed and not is_failed_analysis(analysis):
                analysis_record = DocumentAnalysis.query.get(analysis_id)
                if analysis_record and analysis_record.document_text:
                    # Keep only essential metadata, remove actual document content
                    original_text_length = len(analysis_record.document_text)
                    analysis_record.document_text = f"[GDPR_DELETED_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}] Original document content removed for privacy compliance (was {original_text_length} characters)"
                    db.session.commit()
                    logging.info(f"GDPR: Document text deleted for analysis ID: {analysis_id}, original length: {original_text_length}")
        except Exception as gdpr_error:
            logging.error(f"GDPR deletion error: {str(gdpr_error)}")
        
        # Convert markdown to HTML for better formatting
        analysis_html = markdown.markdown(analysis, extensions=['nl2br', 'tables'])
        
        # Get analysis language and its translations for chat
        analysis_lang = session.get('analysis_language', 'ro')
        analysis_t = get_translation(analysis_lang)
        
        return render_template('result.html', 
                             analysis=analysis_html, 
                             files=processed_files, 
                             user_stats=user_stats,
                             analysis_gamification=session.get('analysis_gamification'),
                             t=t, lang=lang,
                             analysis_lang=analysis_lang,
                             analysis_t=analysis_t)
        
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        lang = session.get('language', 'en')
        t = get_translation(lang)
        return render_template('error.html', 
                             error_title=t.get('error_occurred', 'Analysis Failed'),
                             error_message='We encountered an error while analyzing your document. Please contact support if this issue persists.',
                             t=t, lang=lang)

@app.route('/legal-chat', methods=['POST'])
@login_required
def legal_chat():
    """Handle legal chat questions about analyzed documents"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        analysis_context = data.get('analysis_context', '')
        conversation_history = data.get('conversation_history', [])
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'}), 400
        
        # Security: Limit message length and validate content
        if len(message) > 500:
            return jsonify({'success': False, 'error': 'Message too long'}), 400
        
        # Check if user has access to legal chat (has analyzed document)
        if not session.get('has_document') and not session.get('analysis_id'):
            return jsonify({'success': False, 'error': 'No document analysis found'}), 403
        
        # Import OpenAI here to avoid import issues
        from utils.ai_analyzer import get_legal_chat_response
        
        # Get AI response
        try:
            response = get_legal_chat_response(
                message=message,
                analysis_context=analysis_context,
                conversation_history=conversation_history,
                language=session.get('analysis_language', 'ro')  # Use the analysis language, not UI language
            )
            
            # Log chat interaction for learning
            logging.info(f"Legal chat - User: {message[:100]}..., Response length: {len(response)}")
            
            return jsonify({
                'success': True,
                'response': response
            })
            
        except Exception as ai_error:
            logging.error(f"AI chat error: {str(ai_error)}")
            return jsonify({
                'success': False,
                'error': 'Could not process your question at this time'
            }), 500
            
    except Exception as e:
        logging.error(f"Legal chat error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/fines')
def fines_analysis():
    """Fines and Penalty Analysis page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('fines_analysis.html', t=t, lang=lang)

@app.route('/analyze-fine', methods=['POST'])
@login_required
def analyze_fine():
    """Analyze a fine/penalty document"""
    try:
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('fines_analysis'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('fines_analysis'))
        
        country = request.form.get('country', 'US')
        language = request.form.get('language', 'en')
        fine_type = request.form.get('fine_type', 'auto')
        
        # Extract text from document
        doc_text = extract_text_from_file(file)
        doc_text = clean_text_for_db(doc_text)
        
        if not doc_text or len(doc_text.strip()) < 50:
            flash('Could not extract text from document', 'error')
            return redirect(url_for('fines_analysis'))
        
        # Store in session for payment flow
        session['doc_text'] = doc_text
        session['document_country'] = country
        session['analysis_language'] = language
        session['analysis_type'] = 'fine'
        session['fine_type'] = fine_type
        
        # Redirect to checkout
        return redirect(url_for('checkout'))
        
    except Exception as e:
        logging.error(f"Fine analysis error: {str(e)}")
        flash(f'Error processing document: {str(e)}', 'error')
        return redirect(url_for('fines_analysis'))

@app.route('/due-diligence')
def due_diligence():
    """Due Diligence Analysis page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('due_diligence.html', t=t, lang=lang)

@app.route('/analyze-due-diligence', methods=['POST'])
@login_required
def analyze_due_diligence():
    """Analyze contract for due diligence"""
    try:
        analysis_type = request.form.get('analysis_type', 'contract')
        language = request.form.get('language', 'en')
        
        if analysis_type == 'contract':
            if 'file' not in request.files:
                flash('No file uploaded', 'error')
                return redirect(url_for('due_diligence'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('due_diligence'))
            
            category = request.form.get('category', 'b2b_contract')
            
            # Extract text from document
            doc_text = extract_text_from_file(file)
            doc_text = clean_text_for_db(doc_text)
            
            if not doc_text or len(doc_text.strip()) < 50:
                flash('Could not extract text from document', 'error')
                return redirect(url_for('due_diligence'))
            
            # Store in session for payment flow
            session['doc_text'] = doc_text
            session['document_country'] = 'AUTO'  # Auto-detect from content
            session['analysis_language'] = language
            session['analysis_type'] = 'due_diligence'
            session['dd_category'] = category
            
        else:  # company verification
            company_country = request.form.get('company_country', '')
            company_name = request.form.get('company_name', '')
            registration_number = request.form.get('registration_number', '')
            
            if not company_name and not registration_number:
                flash('Please provide company name or registration number', 'error')
                return redirect(url_for('due_diligence'))
            
            # Create verification text
            doc_text = f"Company Verification Request:\nCompany Name: {company_name}\nCountry: {company_country}\nRegistration Number: {registration_number}"
            
            # Handle optional file upload
            if 'file' in request.files:
                file = request.files['file']
                if file.filename:
                    file_text = extract_text_from_file(file)
                    file_text = clean_text_for_db(file_text)
                    if file_text:
                        doc_text += f"\n\nCompany Documents:\n{file_text}"
            
            session['doc_text'] = doc_text
            session['document_country'] = company_country
            session['analysis_language'] = language
            session['analysis_type'] = 'company_verification'
            session['company_name'] = company_name
            session['registration_number'] = registration_number
        
        # Redirect to checkout
        return redirect(url_for('checkout'))
        
    except Exception as e:
        logging.error(f"Due diligence error: {str(e)}")
        flash(f'Error processing request: {str(e)}', 'error')
        return redirect(url_for('due_diligence'))

@app.route('/jurisdiction-compare')
def jurisdiction_compare():
    """Jurisdiction Comparison page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('jurisdiction_compare.html', t=t, lang=lang)

@app.route('/analyze-jurisdiction-compare', methods=['POST'])
@login_required
def analyze_jurisdiction_compare():
    """Compare laws across jurisdictions"""
    try:
        country1 = request.form.get('country1', '')
        country2 = request.form.get('country2', '')
        legal_area = request.form.get('legal_area', 'data_protection')
        specific_question = request.form.get('specific_question', '')
        language = request.form.get('language', 'en')
        
        doc_text = f"Jurisdiction Comparison Request:\nCountry 1: {country1}\nCountry 2: {country2}\nLegal Area: {legal_area}\nSpecific Question: {specific_question}"
        
        session['doc_text'] = doc_text
        session['document_country'] = country1
        session['analysis_language'] = language
        session['analysis_type'] = 'jurisdiction_compare'
        session['compare_countries'] = f"{country1},{country2}"
        session['legal_area'] = legal_area
        
        return redirect(url_for('checkout'))
    except Exception as e:
        logging.error(f"Jurisdiction compare error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('jurisdiction_compare'))

@app.route('/conflict-laws')
def conflict_laws():
    """Conflict of Laws page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('conflict_laws.html', t=t, lang=lang)

@app.route('/analyze-conflict-laws', methods=['POST'])
@login_required
def analyze_conflict_laws():
    """Analyze conflict of laws"""
    try:
        party_a = request.form.get('party_a_country', '')
        party_b = request.form.get('party_b_country', '')
        performance = request.form.get('performance_country', '')
        relationship_type = request.form.get('relationship_type', 'contract')
        situation = request.form.get('situation', '')
        language = request.form.get('language', 'en')
        
        doc_text = f"Conflict of Laws Analysis:\nParty A: {party_a}\nParty B: {party_b}\nPlace of Performance: {performance}\nRelationship Type: {relationship_type}\nSituation: {situation}"
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                file_text = extract_text_from_file(file)
                file_text = clean_text_for_db(file_text)
                if file_text:
                    doc_text += f"\n\nDocument Content:\n{file_text}"
        
        session['doc_text'] = doc_text
        session['document_country'] = party_a
        session['analysis_language'] = language
        session['analysis_type'] = 'conflict_laws'
        
        return redirect(url_for('checkout'))
    except Exception as e:
        logging.error(f"Conflict laws error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('conflict_laws'))

@app.route('/international-contracts')
def international_contracts():
    """International Contracts page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('international_contracts.html', t=t, lang=lang)

@app.route('/analyze-international-contract', methods=['POST'])
@login_required
def analyze_international_contract():
    """Analyze or draft international contract"""
    try:
        action = request.form.get('action', 'review')
        contract_type = request.form.get('contract_type', 'sale')
        governing_law = request.form.get('governing_law', 'UK')
        language = request.form.get('language', 'en')
        
        if action == 'review':
            if 'file' not in request.files:
                flash('Please upload a contract', 'error')
                return redirect(url_for('international_contracts'))
            file = request.files['file']
            if file.filename == '':
                flash('Please select a file', 'error')
                return redirect(url_for('international_contracts'))
            
            doc_text = extract_text_from_file(file)
            doc_text = clean_text_for_db(doc_text)
            doc_text = f"Contract Review Request:\nContract Type: {contract_type}\nGoverning Law: {governing_law}\n\nContract Content:\n{doc_text}"
        else:
            party_a = request.form.get('party_a', '')
            party_b = request.form.get('party_b', '')
            requirements = request.form.get('requirements', '')
            dispute_resolution = request.form.get('dispute_resolution', 'icc')
            
            doc_text = f"Contract Drafting Request:\nContract Type: {contract_type}\nGoverning Law: {governing_law}\nParty A: {party_a}\nParty B: {party_b}\nDispute Resolution: {dispute_resolution}\nRequirements: {requirements}"
        
        session['doc_text'] = doc_text
        session['document_country'] = governing_law
        session['analysis_language'] = language
        session['analysis_type'] = 'international_contract'
        session['contract_action'] = action
        
        return redirect(url_for('checkout'))
    except Exception as e:
        logging.error(f"International contract error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('international_contracts'))

@app.route('/sanctions-compliance')
def sanctions_compliance():
    """Sanctions & Compliance page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('sanctions_compliance.html', t=t, lang=lang)

@app.route('/analyze-sanctions', methods=['POST'])
@login_required
def analyze_sanctions():
    """Analyze sanctions and compliance"""
    try:
        entity_name = request.form.get('entity_name', '')
        entity_country = request.form.get('entity_country', '')
        from_country = request.form.get('from_country', '')
        to_country = request.form.get('to_country', '')
        transaction_type = request.form.get('transaction_type', '')
        product_description = request.form.get('product_description', '')
        end_use = request.form.get('end_use', '')
        language = request.form.get('language', 'en')
        
        doc_text = f"Sanctions & Compliance Check:\nEntity: {entity_name}\nEntity Country: {entity_country}\nFrom: {from_country}\nTo: {to_country}\nTransaction Type: {transaction_type}\nProduct: {product_description}\nEnd Use: {end_use}"
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                file_text = extract_text_from_file(file)
                file_text = clean_text_for_db(file_text)
                if file_text:
                    doc_text += f"\n\nDocument:\n{file_text}"
        
        session['doc_text'] = doc_text
        session['document_country'] = from_country or entity_country
        session['analysis_language'] = language
        session['analysis_type'] = 'sanctions'
        
        return redirect(url_for('checkout'))
    except Exception as e:
        logging.error(f"Sanctions error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('sanctions_compliance'))

@app.route('/arbitration')
def arbitration():
    """International Arbitration page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('arbitration.html', t=t, lang=lang)

@app.route('/analyze-arbitration', methods=['POST'])
@login_required
def analyze_arbitration():
    """Analyze arbitration case"""
    try:
        institution = request.form.get('institution', 'icc')
        seat = request.form.get('seat', '')
        claimant = request.form.get('claimant_country', '')
        respondent = request.form.get('respondent_country', '')
        dispute_amount = request.form.get('dispute_amount', 'medium')
        dispute_description = request.form.get('dispute_description', '')
        language = request.form.get('language', 'en')
        
        doc_text = f"Arbitration Analysis:\nInstitution: {institution}\nSeat: {seat}\nClaimant: {claimant}\nRespondent: {respondent}\nAmount: {dispute_amount}\nDescription: {dispute_description}"
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                file_text = extract_text_from_file(file)
                file_text = clean_text_for_db(file_text)
                if file_text:
                    doc_text += f"\n\nArbitration Clause/Contract:\n{file_text}"
        
        session['doc_text'] = doc_text
        session['document_country'] = claimant
        session['analysis_language'] = language
        session['analysis_type'] = 'arbitration'
        
        return redirect(url_for('checkout'))
    except Exception as e:
        logging.error(f"Arbitration error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('arbitration'))

@app.route('/immigration')
def immigration():
    """Immigration & Visa page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('immigration.html', t=t, lang=lang)

@app.route('/analyze-immigration', methods=['POST'])
@login_required
def analyze_immigration():
    """Analyze immigration options"""
    try:
        nationality = request.form.get('nationality', '')
        destination = request.form.get('destination', '')
        purpose = request.form.get('purpose', 'employment')
        occupation = request.form.get('occupation', '')
        investment = request.form.get('investment_budget', '')
        details = request.form.get('details', '')
        language = request.form.get('language', 'en')
        
        doc_text = f"Immigration Analysis:\nNationality: {nationality}\nDestination: {destination}\nPurpose: {purpose}\nOccupation: {occupation}\nInvestment Budget: {investment}\nDetails: {details}"
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                file_text = extract_text_from_file(file)
                file_text = clean_text_for_db(file_text)
                if file_text:
                    doc_text += f"\n\nDocuments:\n{file_text}"
        
        session['doc_text'] = doc_text
        session['document_country'] = destination
        session['analysis_language'] = language
        session['analysis_type'] = 'immigration'
        
        return redirect(url_for('checkout'))
    except Exception as e:
        logging.error(f"Immigration error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('immigration'))

@app.route('/legal-translation')
def legal_translation():
    """Legal Translation page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('legal_translation.html', t=t, lang=lang)

@app.route('/analyze-translation', methods=['POST'])
@login_required
def analyze_translation():
    """Perform legal translation"""
    try:
        source_lang = request.form.get('source_lang', 'auto')
        target_lang = request.form.get('target_lang', 'en')
        legal_domain = request.form.get('legal_domain', 'general')
        text = request.form.get('text', '')
        language = target_lang
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                file_text = extract_text_from_file(file)
                file_text = clean_text_for_db(file_text)
                if file_text:
                    text = file_text
        
        if not text:
            flash('Please provide text or upload a document', 'error')
            return redirect(url_for('legal_translation'))
        
        doc_text = f"Legal Translation Request:\nSource: {source_lang}\nTarget: {target_lang}\nDomain: {legal_domain}\n\nText to Translate:\n{text}"
        
        session['doc_text'] = doc_text
        session['document_country'] = 'INT'
        session['analysis_language'] = language
        session['analysis_type'] = 'translation'
        session['source_lang'] = source_lang
        session['target_lang'] = target_lang
        
        return redirect(url_for('checkout'))
    except Exception as e:
        logging.error(f"Translation error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('legal_translation'))

@app.route('/terms')
def terms():
    """Terms and Conditions page"""
    lang = session.get('language', 'en')
    t = get_translation(lang)
    return render_template('terms.html', t=t, lang=lang)

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
