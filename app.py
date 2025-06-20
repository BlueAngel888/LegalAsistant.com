import os
import logging
from flask import Flask, render_template, request, redirect, jsonify, session, flash, url_for
import stripe
from utils.pdf_tools import extract_text_from_file
from utils.ai_analyzer import analyze_with_gpt4
from config import STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY
from translations import get_translation

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development")

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Configure domain for Stripe redirects
def get_domain():
    # Check for Replit deployment first
    if os.environ.get('REPLIT_DEPLOYMENT'):
        dev_domain = os.environ.get('REPLIT_DEV_DOMAIN')
        if dev_domain:
            return f"https://{dev_domain}"
    
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
    logging.info(f"Index route accessed - Session language: {lang}")
    return render_template('index.html', stripe_public_key=STRIPE_PUBLIC_KEY, t=t, lang=lang)

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
        
        # If text is too large, truncate and store summary instead
        if len(doc_text) > 10000:  # 10KB limit for session
            session['doc_text'] = doc_text[:10000] + "\n\n[Document truncated for session storage - full text will be analyzed]"
            session['full_doc_text'] = doc_text  # Store full text temporarily
        else:
            session['doc_text'] = doc_text
            
        session['processed_files'] = processed_files
        
        # Force session to be saved
        session.modified = True
        
        # Debug session data
        logging.info(f"Session data stored - doc_text length: {len(session.get('doc_text', ''))}")
        logging.info(f"Session data stored - processed_files: {session.get('processed_files', [])}")
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
        logging.info(f"Creating Stripe session with domain: {current_domain}")
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
            success_url=current_domain + '/success',
            cancel_url=current_domain + '/checkout',
            allow_promotion_codes=False,
            billing_address_collection='auto'
        )
        
        logging.info(f"Stripe session created successfully with ID: {checkout_session.id}")
        logging.info(f"Redirect URL: {checkout_session.url}")
        
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
        
        # Clear the full document text from session after analysis
        if 'full_doc_text' in session:
            del session['full_doc_text']
        
        return render_template('result.html', analysis=analysis, files=processed_files, t=t, lang=lang)
        
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
        'openai_configured': bool(os.environ.get('OPENAI_API_KEY') and not os.environ.get('OPENAI_API_KEY').startswith('sk-default'))
    }

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
