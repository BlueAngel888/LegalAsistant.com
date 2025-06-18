from flask import Flask, render_template, request, redirect, jsonify, session
import stripe
import os
from utils.pdf_tools import extract_text_from_file
from utils.ai_analyzer import analyze_document
from config import STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY
from base64 import b64decode
from io import BytesIO
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = 'your_secret_key'
stripe.api_key = STRIPE_SECRET_KEY
YOUR_DOMAIN = 'http://localhost:5000'  # Înlocuiește cu domeniul tău real

@app.route('/')
def index():
    return render_template('index.html', stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/upload', methods=['POST'])
def upload_file():
    scanned_base64 = request.form.get('scannedImage')
    files = request.files.getlist('file')
    texts = []

    if scanned_base64:
        image_data = b64decode(scanned_base64.split(",")[1])
        image = Image.open(BytesIO(image_data))
        text = pytesseract.image_to_string(image)
        texts.append(text)

    for file in files:
        texts.append(extract_text_from_file(file))

    session['doc_text'] = "\n".join(texts)
    return redirect('/checkout')

@app.route('/checkout')
def checkout():
    return render_template('checkout.html')

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': 10000,
                    'product_data': {'name': 'Legal Document Analysis'},
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=YOUR_DOMAIN + '/success',
            cancel_url=YOUR_DOMAIN + '/',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route('/success')
def success():
    doc_text = session.get('doc_text', '')
    if not doc_text:
        return "No document found.", 400
    analysis = analyze_document(doc_text)
    return render_template('result.html', analysis=analysis)