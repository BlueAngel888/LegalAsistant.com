import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def analyze_document(text):
    prompt = f"Analyze this legal document and provide a detailed report with possible legal insights, resolutions, or obligations based on its type."
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt + "\n\n" + text}],
        temperature=0.4
    )
    return response.choices[0].message['content']