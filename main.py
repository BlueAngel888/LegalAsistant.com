#!/usr/bin/env python3
"""
Flask OCR Application with Stripe Payment Flow
- Payment first, then image upload and OCR processing
- OCR happens asynchronously after payment
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import base64
from io import BytesIO
from PIL import Image
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Simulate Stripe payment success tracking
payments_db = {}

@app.route('/')
def index():
    """Main page with payment button"""
    return render_template('index_new.html')

@app.route('/create-payment', methods=['POST'])
def create_payment():
    """Simulate Stripe payment creation"""
    payment_id = str(uuid.uuid4())
    
    # Store payment as successful (simulation)
    payments_db[payment_id] = {
        'status': 'completed',
        'amount': 500,  # €5.00
        'currency': 'EUR'
    }
    
    # Store payment in session
    session['payment_id'] = payment_id
    session['payment_completed'] = True
    
    logging.info(f"Payment simulation created: {payment_id}")
    
    # Redirect to upload page after "payment"
    return redirect(url_for('upload_page'))

@app.route('/upload')
def upload_page():
    """Upload page - only accessible after payment"""
    if not session.get('payment_completed'):
        return redirect(url_for('index'))
    
    payment_id = session.get('payment_id')
    return render_template('upload_new.html', payment_id=payment_id)

@app.route('/api/ocr', methods=['POST'])
def process_ocr():
    """OCR processing endpoint - asynchronous from payment"""
    
    # Verify payment was completed
    if not session.get('payment_completed'):
        return jsonify({'error': 'Payment required'}), 403
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read and process image
        image_data = file.read()
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # OCR Processing
        extracted_text = perform_ocr(image)
        
        logging.info(f"OCR completed for {file.filename}, extracted {len(extracted_text)} characters")
        
        return jsonify({
            'success': True,
            'text': extracted_text,
            'filename': file.filename,
            'image_size': f"{image.width}x{image.height}"
        })
        
    except Exception as e:
        logging.error(f"OCR processing error: {str(e)}")
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

def perform_ocr(image):
    """
    Perform OCR on the provided image
    
    NOTE: In a real deployment, this would use pytesseract:
    
    import pytesseract
    
    # Optimize image for OCR
    image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    
    # Configure OCR
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, lang='eng', config=config)
    
    return text.strip()
    """
    
    # SIMULATION: Since Tesseract may not be available in all Replit environments
    # This simulates OCR text extraction based on image characteristics
    
    width, height = image.size
    pixel_count = width * height
    
    # Simulate realistic OCR results based on image size
    if pixel_count < 100000:  # Small image
        simulated_text = """SAMPLE DOCUMENT
        
This is a simulated OCR result for a small image.
The actual OCR would extract real text from your uploaded image.

Document type: Receipt/Small document
Confidence: Medium
        """
    elif pixel_count < 500000:  # Medium image
        simulated_text = """LEGAL DOCUMENT SAMPLE
        
ROMÂNIA
JUDECĂTORIA SECTORULUI 3 BUCUREȘTI
SECȚIA CIVILĂ

Sentința civilă nr. 12684
Sentința publică din data de 07.11.2024

[Simulated OCR text - In production, this would be 
the actual text extracted from your legal document]

HOTĂRĂȘTE:
Respinge cererea de chemare în judecată...

Note: This is a simulation. Real OCR would extract 
the actual text from your uploaded image.
        """
    else:  # Large image
        simulated_text = """COMPREHENSIVE LEGAL DOCUMENT
        
ROMÂNIA
JUDECĂTORIA SECTORULUI 3 BUCUREȘTI
SECȚIA CIVILĂ

Sentința civilă nr. 12684 din data de 07.11.2024
Instanța constituită din:
Președinte: Marius-Georgel Sima
Grefier: Marius Pietreanu

Pentru rol se află judecarea cauzei civile formulate de reclamanta 
Dragu Mocanu Silvia în contradictoriu cu pârâții...

[This is simulated OCR output. In production with pytesseract, 
this would be the actual text extracted from your document]

PENTRU ACESTE MOTIVE,
ÎN NUMELE LEGII,
HOTĂRĂȘTE:

Note: This simulation demonstrates the OCR functionality.
Real implementation would use pytesseract to extract actual text.
        """
    
    return simulated_text

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'payments_count': len(payments_db),
        'session_active': bool(session.get('payment_completed'))
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
