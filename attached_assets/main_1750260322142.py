from flask import Flask, render_template, request, redirect, jsonify
import stripe
import os
from utils.pdf_tools import extract_text_from_file
from utils.ai_analyzer import analyze_with_gpt4
from config import STRIPE_PUBLIC_KEY, STRIPE_SECRET_KEY

app = Flask(__name__)
stripe.api_key = STRIPE_SECRET_KEY
YOUR_DOMAIN = 'http://localhost:5000'  # Schimbă cu domeniul tău în producție

@app.route('/')
def index():
    return render_template('index.html', stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    texts = []
    for file in files:
        texts.append(extract_text_from_file(file))
    request.session['doc_text'] = "\n".join(texts)
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
    doc_text = request.session.get('doc_text', '')
    if not doc_text:
        return "No document found.", 400
    analysis = analyze_with_gpt4(doc_text)
    return render_template('result.html', analysis=analysis)

if __name__ == '__main__':
    app.secret_key = 'your_secret_key'
    app.run(debug=True)