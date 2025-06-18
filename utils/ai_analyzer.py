import os
import logging
from openai import OpenAI
from config import OPENAI_API_KEY

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_with_gpt4(text: str) -> str:
    """
    Analyze legal document text using GPT-4 and provide comprehensive legal insights.
    """
    try:
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        prompt = f"""
You are a senior legal analyst with expertise in contract law, corporate law, real estate law, and general legal document review. 

Please provide a comprehensive analysis of the following legal document(s). Your analysis should include:

1. **Document Type & Purpose**: Identify the type of legal document and its primary purpose.

2. **Key Legal Provisions**: Highlight the most important legal clauses, terms, and provisions.

3. **Rights & Obligations**: Clearly outline the rights and obligations of each party involved.

4. **Risk Assessment**: Identify potential legal risks, liabilities, or concerning clauses.

5. **Compliance Issues**: Note any regulatory compliance requirements or potential violations.

6. **Missing Elements**: Point out any standard clauses or provisions that appear to be missing.

7. **Recommendations**: Provide specific, actionable recommendations for improvements or areas requiring attention.

8. **Red Flags**: Highlight any terms or clauses that should be reviewed carefully or negotiated.

Please structure your response in a clear, professional format suitable for legal professionals. Use bullet points and clear headings for easy readability.

Document content to analyze:

{text}

Provide your analysis:
"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a senior legal analyst providing professional legal document analysis. Always provide thorough, accurate, and actionable insights while maintaining professional legal standards."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"Error analyzing document with GPT-4: {str(e)}")
        return f"Analysis Error: Unable to complete document analysis. Error: {str(e)}. Please contact support if this issue persists."

def get_document_summary(text: str) -> str:
    """
    Generate a brief summary of the document for preview purposes.
    """
    try:
        prompt = f"""
Provide a brief 2-3 sentence summary of this legal document, including:
- Document type
- Main parties involved (if identifiable)
- Primary purpose or subject matter

Document excerpt: {text[:1000]}...
"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logging.error(f"Error generating document summary: {str(e)}")
        return "Unable to generate document summary."
