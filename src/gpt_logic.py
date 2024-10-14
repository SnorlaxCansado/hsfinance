# src/gpt_logic.py

import openai
import os
from dotenv import load_dotenv
import logging
import re

def generate_complementary_tickers(ticker):
    """
    Generates complementary tickers for comparison using GPT.
    Ensures that the tickers are unique and do not include the original ticker.
    """
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    openai.api_key = OPENAI_API_KEY

    # Prepare the prompt
    prompt = f"""
    Suggest three complementary stock tickers for {ticker} for comparative analysis.
    Please provide only the ticker symbols, separated by commas, without any additional text.
    Ensure that none of the suggested tickers are the same as {ticker}.
    """

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
        # Extract ticker symbols using regex
        tickers = re.findall(r'\b[A-Z]{1,5}\b', reply)

        # Remove the original ticker if present
        tickers = [t.strip().upper() for t in tickers if t.strip().upper() != ticker.upper()]

        # Ensure uniqueness
        unique_tickers = list(dict.fromkeys(tickers))  # Preserves order

        # Limit to three tickers
        complementary_tickers = unique_tickers[:3]

        return complementary_tickers
    except Exception as e:
        logging.error(f"An error occurred while generating complementary tickers: {e}")
        return []

def generate_theme_queries(ticker, additional_themes=None):
    """
    Generates theme-specific queries for SERPER API.
    """
    themes = ['financial performance', 'market trends', 'geopolitical risks', 'sector developments']
    if additional_themes:
        themes.extend(additional_themes)
    queries = [f"{ticker} {theme}" for theme in themes]
    return queries
