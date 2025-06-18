import os
import logging
from flask import Flask, render_template, request, redirect, jsonify, session, flash, url_for
import stripe
from utils.pdf_tools import extract_text_from_file
from utils.ai_analyzer import analyze_with_gpt4
from config import STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key_for_development")

# Configure Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Configure domain for Stripe redirects
if os.environ.get('REPLIT_DEPLOYMENT'):
    YOUR_DOMAIN = f"https://{os.environ.get('REPLIT_DEV_DOMAIN')}"
else:
    YOUR_DOMAIN = f"https://{os.environ.get('REPLIT_DOMAINS', 'localhost:5000').split(',')[0]}"

@app.route('/')
def index():
    return render_template('index.html', stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Handle scanned image from camera
        scanned_base64 = request.form.get('scannedImage')
        files = request.files.getlist('file')
        texts = []
        processed_files = []

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
                
                # Extract text using OCR
                text = pytesseract.image_to_string(image, lang='eng')
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
        if files and not all(file.filename == '' for file in files):
            for file in files:
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
        
        # Store document text and file info in session
        session['doc_text'] = "\n\n--- Document Separator ---\n\n".join(texts)
        session['processed_files'] = processed_files
        
        return redirect(url_for('checkout'))
        
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        flash('An error occurred while processing your files. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/checkout')
def checkout():
    if 'doc_text' not in session:
        flash('No document found. Please upload a document first.', 'error')
        return redirect(url_for('index'))
    
    processed_files = session.get('processed_files', [])
    return render_template('checkout.html', files=processed_files)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        if 'doc_text' not in session:
            return jsonify(error='No document found in session'), 400
        
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
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/checkout',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        logging.error(f"Stripe session creation error: {str(e)}")
        return jsonify(error=str(e)), 403

@app.route('/success')
def success():
    try:
        doc_text = session.get('doc_text', '')
        processed_files = session.get('processed_files', [])
        
        if not doc_text:
            flash('No document found. Please start over.', 'error')
            return redirect(url_for('index'))
        
        # Analyze the document with GPT-4
        analysis = analyze_with_gpt4(doc_text)
        
        return render_template('result.html', analysis=analysis, files=processed_files)
        
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        return render_template('error.html', 
                             error_title='Analysis Failed',
                             error_message='We encountered an error while analyzing your document. Please contact support if this issue persists.')

@app.route('/clear-session')
def clear_session():
    session.clear()
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_title='Page Not Found',
                         error_message='The page you are looking for does not exist.'), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {str(error)}")
    return render_template('error.html',
                         error_title='Internal Server Error',
                         error_message='An internal server error occurred. Please try again later.'), 500
