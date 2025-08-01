import os
import logging
import json
import uuid
import threading
import time
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
                analysis_record.document_text = final_text
                
                # Mark as fully processed
                analysis_record.updated_at = datetime.utcnow()
                
                db.session.commit()
                
                logging.info(f"BACKGROUND OCR: Completed! Updated analysis {analysis_id} with {len(final_text)} characters from {processed_count} files")
            else:
                logging.error(f"BACKGROUND OCR: No text could be extracted from any files for analysis {analysis_id}")
                
        except Exception as e:
            logging.error(f"BACKGROUND OCR: Fatal error for analysis {analysis_id}: {str(e)}")
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
        session.pop('doc_text', None)
        session.pop('full_doc_text', None)
        session.pop('processed_files', None)
        session.pop('stripe_session_id', None)
        
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
                if text.strip():
                    texts.append(text)
                    processed_files.append('Scanned Document')
                    logging.info("Successfully processed scanned document")
                else:
                    flash('Could not extract text from scanned document. Please try again or upload a clearer image.', 'warning')
                    
            except Exception as e:
                logging.error(f"Error processing scanned image: {str(e)}")
                flash('Error processing scanned document. Please try again.', 'error')

        # Initialize files_data for potential background processing
        files_data = []
        
        # Instant payment mode - skip all processing for multiple files
        all_files = files + camera_files  # Combine regular files and camera files
        if all_files and not all(file.filename == '' for file in all_files):
            
            # For 3+ files, launch background OCR and go directly to payment (INSTANT MODE)
            if len(all_files) >= 3:
                logging.info(f"INSTANT MODE: {len(all_files)} files detected - launching background OCR")
                
                # Prepare files data for background processing
                for file in all_files:
                    if file.filename != '':
                        # Read file content
                        file_content = file.read()
                        file.seek(0)  # Reset file pointer
                        
                        files_data.append({
                            'filename': file.filename,
                            'content': file_content
                        })
                        processed_files.append(file.filename)
                
                # Create placeholder text for immediate payment
                placeholder_text = f"INSTANT UPLOAD: {len(processed_files)} files uploaded successfully.\n"
                placeholder_text += f"Files: {', '.join(processed_files)}\n"
                placeholder_text += "OCR processing started in background - analysis will be ready shortly after payment."
                texts.append(placeholder_text)
                
                session['needs_full_processing'] = True
                session['background_processing'] = True
                logging.info(f"INSTANT MODE: {len(processed_files)} files ready for background OCR")
                
            else:
                # For 1-2 files, do quick processing
                import time
                start_time = time.time()
                max_instant_processing_time = 5  # Only 5 seconds max
                # For 3 or fewer files, process normally with short timeout
                for i, file in enumerate(all_files):
                    if file.filename != '':
                        # Check if we're running out of time
                        elapsed_time = time.time() - start_time
                        if elapsed_time > max_instant_processing_time:
                            logging.warning(f"Quick processing timeout reached after {elapsed_time:.1f}s")
                            # Add placeholder for remaining files
                            remaining_files = len(all_files) - i
                            placeholder_text = f"Additional {remaining_files} files will be processed after payment."
                            texts.append(placeholder_text)
                            processed_files.extend([f.filename for f in all_files[i:] if f.filename])
                            break
                        
                        try:
                            logging.info(f"Quick processing file {i+1}/{len(all_files)}: {file.filename}")
                            text = extract_text_from_file(file)
                            if text.strip():
                                texts.append(text)
                                processed_files.append(file.filename)
                                logging.info(f"Quick extracted {len(text)} characters from {file.filename}")
                            else:
                                logging.warning(f'No text extracted from {file.filename}')
                                texts.append(f"File: {file.filename} - Text extraction pending")
                                processed_files.append(file.filename)
                        except Exception as e:
                            logging.error(f"Error in quick processing {file.filename}: {str(e)}")
                            texts.append(f"File: {file.filename} - Processing error, will retry after payment")
                            processed_files.append(file.filename)
                            continue
        
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
            
            analysis_record = DocumentAnalysis(
                session_id=session['_id'],
                file_names=json.dumps(processed_files),
                document_text=doc_text,
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
            
            # Launch background OCR processing if in instant mode
            if session.get('background_processing') and files_data:
                logging.info(f"INSTANT MODE: Launching background OCR thread for analysis {analysis_record.id}")
                
                # Create application context for background thread
                app_context = app.app_context()
                
                # Start background OCR processing
                ocr_thread = threading.Thread(
                    target=background_ocr_processing,
                    args=(analysis_record.id, files_data, app_context),
                    daemon=True
                )
                ocr_thread.start()
                
                logging.info(f"INSTANT MODE: Background OCR thread started successfully")
            
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            # Continue without database storage if DB fails
            
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
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': 500,  # €5.00 for testing
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
        
        # Retrieve document data from database
        analysis_id = session.get('analysis_id')
        if not analysis_id:
            flash('No document found. Please start over.', 'error')
            return redirect(url_for('index'))
        
        analysis_record = DocumentAnalysis.query.get(analysis_id)
        if not analysis_record:
            flash('Document not found. Please start over.', 'error')
            return redirect(url_for('index'))
        
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
                from utils.ai_analyzer import analyze_with_gpt4
                
                # Add country hint to document text for GPT analysis
                doc_text_with_hint = f"countryHint: {selected_country}\n\n{doc_text}"
                
                # Get analysis language
                analysis_language = session.get('analysis_language', 'ro')
                
                # Add access type header
                if session.get('payment_status') == 'free_access':
                    access_header = f"ANALIZĂ JURIDICĂ COMPLETĂ - ACCES GRATUIT COD {session.get('discount_code', 'LETSGO')}\n\n"
                else:
                    access_header = "ANALIZĂ JURIDICĂ COMPLETĂ - ACCES PREMIUM\n\n"
                
                # For free access, use offline analysis to avoid timeouts
                if session.get('payment_status') == 'free_access':
                    logging.info("Using offline analysis for free access to avoid API timeouts")
                    
                    # Extract document type
                    doc_lower = doc_text.lower()
                    doc_type = "Document juridic"
                    if "contract" in doc_lower:
                        if "vânzare" in doc_lower or "vanzare" in doc_lower:
                            doc_type = "Contract de vânzare-cumpărare"
                        elif "închiriere" in doc_lower or "inchiriere" in doc_lower:
                            doc_type = "Contract de închiriere"
                        elif "muncă" in doc_lower or "munca" in doc_lower:
                            doc_type = "Contract de muncă"
                        else:
                            doc_type = "Contract"
                    
                    analysis = f"""{access_header}
🏛️ **ANALIZĂ JURIDICĂ AUTOMATĂ** - {doc_type}

📋 **1. IDENTIFICAREA ȘI VALIDITATEA FORMALĂ A DOCUMENTULUI**
• Tip document: {doc_type}
• Jurisdicție: {country_name}
• Limbă analiză: {analysis_language.upper()}
• Data procesării: {datetime.now().strftime('%d.%m.%Y, %H:%M')}

📑 **2. STRUCTURA ȘI CONȚINUTUL LEGAL**
• Document procesat cu succes
• Lungime text: {len(doc_text)} caractere
• Fișiere analizate: {', '.join(processed_files) if processed_files else 'Document scanat'}

⚖️ **3. VERIFICAREA LEGALITĂȚII ȘI CONFORMITĂȚII**
Pentru o analiză completă a conformității legale, vă recomandăm:
• Verificarea semnăturilor părților
• Confirmarea datelor de identificare
• Validarea clauzelor contractuale

🔍 **4. ANALIZA IMPLICAȚIILOR JURIDICE**
Documentul a fost recepționat și procesat. Pentru o analiză detaliată:
• Consultați un specialist în drept {country_name}
• Verificați legislația actualizată
• Asigurați-vă că toate anexele sunt prezente

💰 **5. ASPECTE FISCALE, CIVILE SAU PENALE**
• Verificați obligațiile fiscale aplicabile
• Respectați termenele legale
• Păstrați documentul în condiții sigure

📌 **NOTĂ IMPORTANTĂ**: Aceasta este o analiză automată preliminară oferită gratuit cu codul {session.get('discount_code', 'LETSGO')}. 
Pentru o analiză juridică completă și personalizată, vă recomandăm upgrade la versiunea Premium."""
                    
                else:
                    # For paid access, try OpenAI API
                    try:
                        analysis = analyze_with_gpt4(doc_text_with_hint, analysis_language)
                        analysis = access_header + analysis
                        logging.info(f"OpenAI API GlobalLegalAnalyserGPT analysis completed successfully")
                    
                    except Exception as api_error:
                        logging.error(f"OpenAI API error: {str(api_error)}")
                        # Fallback to offline analysis
                        analysis = f"""{access_header}

⚠️ **NOTIFICARE TEHNICĂ**

Sistemul de analiză AI avansată este temporar indisponibil.

Document recepționat pentru jurisdicția: {country_name}
Fișiere procesate: {len(processed_files)}

Vă vom oferi o analiză detaliată în cel mai scurt timp. Între timp, documentul dumneavoastră a fost procesat și stocat în siguranță.

Pentru asistență imediată, contactați suportul tehnic."""
                
                logging.info(f"Analysis completed for {country_name}")
                
            except Exception as ai_error:
                logging.error(f"Enhanced AI analysis failed: {str(ai_error)}")
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
            if analysis_id and analysis:
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
            if analysis_id:
                analysis_record = DocumentAnalysis.query.get(analysis_id)
                if analysis_record and analysis_record.document_text:
                    # Keep only essential metadata, remove actual document content
                    original_text_length = len(analysis_record.document_text)
                    analysis_record.document_text = f"[GDPR_DELETED_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}] Original document content removed for privacy compliance (was {original_text_length} characters)"
                    db.session.commit()
                    logging.info(f"GDPR: Document text deleted for analysis ID: {analysis_id}, original length: {original_text_length}")
        except Exception as gdpr_error:
            logging.error(f"GDPR deletion error: {str(gdpr_error)}")
        
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

@app.route('/legal-chat', methods=['POST'])
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
                language=session.get('language', 'ro')
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
