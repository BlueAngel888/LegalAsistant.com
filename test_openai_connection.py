def test_openai_connection():
    """
    Tests the connection to the OpenAI API using gpt-4o-mini.
    """
    import openai
    import os

    # Set your OpenAI API key (replace with your actual key or environment variable)
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if not openai.api_key:
        print("❌ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return False

    client = openai.OpenAI()

    # Test simplu cu timeout
    print("📡 Testez conexiunea...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Test conexiune API. Răspunde cu 'Conexiune reușită'."}
        ],
        max_tokens=10,
        timeout=15
    )

    result = response.choices[0].message.content
    print(f"✅ OpenAI API funcționează: {result}")
    print(f"📊 Model folosit: gpt-4o-mini")
    print(f"💰 Tokens folosiți: {response.usage.total_tokens if response.usage else 'N/A'}")
    return True

if __name__ == "__main__":
    test_openai_connection()