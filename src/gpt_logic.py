# src/gpt_logic.py

import openai
import os
from dotenv import load_dotenv

def generate_complementary_tickers(ticker):
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    openai.api_key = OPENAI_API_KEY

    # Prepare the prompt
    prompt = f"Suggest three complementary stock tickers for {ticker} for comparative analysis."

    # Use the ChatCompletion API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.7,
        )

        # Extract the assistant's reply
        reply = response['choices'][0]['message']['content'].strip()
        tickers = reply.split(',')

        return [t.strip().upper() for t in tickers]
    except Exception as e:
        print(f"An error occurred while generating complementary tickers: {e}")
        return []

def generate_theme_queries(ticker):
    themes = ['financial performance', 'market trends', 'geopolitical risks', 'sector developments']
    queries = [f"{ticker} {theme}" for theme in themes]
    return queries
