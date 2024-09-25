# src/report_generator.py

import openai
import os
from dotenv import load_dotenv

def generate_report(ticker, stock_data, full_articles):
    """
    Generates a comprehensive report for the given ticker using stock data and full articles.
    """
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    openai.api_key = OPENAI_API_KEY

    # Prepare stock data summary
    stock_info = stock_data.get('info', {})
    stock_summary = f"{ticker} ({stock_info.get('longName', '')}) is currently trading at {stock_info.get('currentPrice', 'N/A')}."

    # Prepare articles content
    articles_content = ""
    for idx, article in enumerate(full_articles):
        # Limit content length to avoid exceeding token limits
        content_snippet = article['full_content'][:1000]
        articles_content += f"Article {idx+1} Title: {article['title']}\nContent:\n{content_snippet}\n\n"

    # Create the prompt for GPT
    prompt = f"""
    Generate a detailed and insightful report on {ticker} using the following information:

    Stock Summary:
    {stock_summary}

    News Articles:
    {articles_content}

    The report should include:
    - An analysis of the stock's recent performance.
    - The impact of the news articles on the stock's outlook.
    - Relevant geopolitical or sector-specific factors.
    - A conclusion with potential future implications.

    Structure the report with clear headings and bullet points where appropriate.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            n=1,
            stop=None,
            temperature=0.7,
        )

        report = response['choices'][0]['message']['content'].strip()
        return report
    except Exception as e:
        print(f"An error occurred while generating the report: {e}")
        return None
