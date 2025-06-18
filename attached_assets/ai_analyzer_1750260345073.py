import openai
from config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def analyze_with_gpt4(text):
    prompt = f"Analyze this legal document thoroughly and provide detailed insights: {text}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message['content']