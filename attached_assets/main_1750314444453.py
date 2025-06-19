from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

translations = {
    "en": {
        "site_title": "Legal Assistant",
        "upload_title": "Upload Legal Document(s)",
        "select_file": "Select file(s):",
        "or_scan": "Or scan with your phone:",
        "capture": "Capture",
        "continue": "Continue to Payment",
        "payment_title": "Secure Payment",
        "pay_now": "Pay 100€ with Card",
        "analysis_title": "Your Document Report",
        "welcome": "Welcome",
        "language": "Language"
    },
    "ro": {
        "site_title": "Asistent Juridic",
        "upload_title": "Încarcă Documente Legale",
        "select_file": "Selectează fișier(e):",
        "or_scan": "Sau scanează cu telefonul:",
        "capture": "Fotografiază",
        "continue": "Continuă la plată",
        "payment_title": "Plată sigură",
        "pay_now": "Plătește 100€ cu cardul",
        "analysis_title": "Raportul tău",
        "welcome": "Bun venit",
        "language": "Limba"
    },
    "de": {
        "site_title": "Rechtsassistent",
        "upload_title": "Juristische Dokumente hochladen",
        "select_file": "Dateien auswählen:",
        "or_scan": "Oder mit dem Handy scannen:",
        "capture": "Aufnehmen",
        "continue": "Zur Zahlung",
        "payment_title": "Sichere Bezahlung",
        "pay_now": "100€ mit Karte bezahlen",
        "analysis_title": "Ihr Dokumentenbericht",
        "welcome": "Willkommen",
        "language": "Sprache"
    },
    "it": {
        "site_title": "Assistente Legale",
        "upload_title": "Carica Documenti Legali",
        "select_file": "Seleziona file:",
        "or_scan": "Oppure scansiona con il telefono:",
        "capture": "Cattura",
        "continue": "Procedi al pagamento",
        "payment_title": "Pagamento Sicuro",
        "pay_now": "Paga 100€ con Carta",
        "analysis_title": "Il tuo Rapporto",
        "welcome": "Benvenuto",
        "language": "Lingua"
    },
    "es": {
        "site_title": "Asistente Legal",
        "upload_title": "Sube Documentos Legales",
        "select_file": "Seleccionar archivo(s):",
        "or_scan": "O escanea con tu teléfono:",
        "capture": "Capturar",
        "continue": "Continuar al pago",
        "payment_title": "Pago Seguro",
        "pay_now": "Pagar 100€ con Tarjeta",
        "analysis_title": "Tu Informe",
        "welcome": "Bienvenido",
        "language": "Idioma"
    },
    "ar": {
        "site_title": "المساعد القانوني",
        "upload_title": "تحميل مستندات قانونية",
        "select_file": "اختر ملف(ات):",
        "or_scan": "أو امسح بهاتفك:",
        "capture": "التقاط",
        "continue": "المتابعة للدفع",
        "payment_title": "دفع آمن",
        "pay_now": "ادفع 100€ بالبطاقة",
        "analysis_title": "تقريرك",
        "welcome": "أهلاً بك",
        "language": "اللغة"
    }
}

@app.route('/')
def index():
    lang = session.get('language', 'en')
    return render_template('index.html', t=translations[lang], lang=lang)

@app.route('/set-language', methods=['POST'])
def set_language():
    selected_lang = request.form.get('language')
    session['language'] = selected_lang
    return redirect('/')