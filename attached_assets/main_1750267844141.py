from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set-language', methods=['POST'])
def set_language():
    selected_lang = request.form.get('language')
    session['language'] = selected_lang
    return redirect('/')