
import os
import openai
from flask import Flask, request, jsonify, render_template
import re

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")

def clean_markdown(text):
    text = re.sub(r'[#+*`>]', '', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['document']
    country = request.form.get('country', 'Romania')
    language = request.form.get('language', 'English')
    file_content = file.read().decode('utf-8', errors='ignore')

    prompt = f"""
You are a legal assistant AI. The user has uploaded a legal document issued in {country}.
Please analyze this document based strictly on the laws of {country}, and provide the entire response in {language}.
Your tasks:
1. Identify the type of document and its purpose.
2. Analyze it according to the specific legal framework of {country}.
3. List the exact legal articles (law name and article number) that apply.
4. Identify which articles or legal paths could be used to contest or defend against the content of the document.
5. Provide a risk assessment and actionable legal recommendations.

Respond in {language} only and avoid any markdown formatting (#, *, etc.).

Here is the document:

{file_content}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content
    cleaned_result = clean_markdown(result)

    return jsonify({"analysis": cleaned_result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)
