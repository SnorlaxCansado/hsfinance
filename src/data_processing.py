# src/data_processing.py

import json
import pandas as pd
import openai
import os
from dotenv import load_dotenv

def load_json_file(filepath):
    """
    Loads a JSON file and returns its contents as a dictionary.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"Loaded data from {filepath}.")
        return data
    except Exception as e:
        print(f"An error occurred while loading {filepath}: {e}")
        return None

def validate_data(data, expected_keys):
    """
    Validates that the data contains the expected keys.
    """
    if data is None:
        return False
    missing_keys = [key for key in expected_keys if key not in data]
    if missing_keys:
        print(f"Data is missing keys: {missing_keys}")
        return False
    return True

def clean_stock_data(stock_data):
    # Ensure 'history' is a list of dictionaries
    history = stock_data.get('history', [])
    if not isinstance(history, list):
        print("Invalid format for stock history data.")
        return None

    # Convert date strings to datetime objects, handle missing values, etc.
    df = pd.DataFrame(history)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        # Convert 'Date' column to string to avoid serialization issues
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    else:
        print("Date column not found in stock history data.")
        return None

    # Replace this line:
    # df.fillna(method='ffill', inplace=True)

    # With this line:
    df.ffill(inplace=True)

    # Convert back to list of dictionaries
    clean_history = df.to_dict(orient='records')
    stock_data['history'] = clean_history

    return stock_data

def clean_serper_data(serper_data):
    """
    Cleans and preprocesses the SERPER API data.
    """
    # Check if 'organic' results are present
    if 'organic' not in serper_data:
        print("No 'organic' key found in SERPER data.")
        return None

    # Ensure each result has 'title' and 'snippet'
    for result in serper_data['organic']:
        if 'title' not in result or 'snippet' not in result:
            print("A result is missing 'title' or 'snippet'.")
            return None

    return serper_data

def combine_data(stock_data, serper_data_list):
    """
    Combines stock data and a list of SERPER data dictionaries into a single data structure.
    """
    combined_data = {
        'stock_info': stock_data.get('info', {}),
        'stock_history': stock_data.get('history', []),
        'serper_data': {}
    }

    for serper_data in serper_data_list:
        # Use the query as the key for each SERPER data set
        key = serper_data.get('searchParameters', {}).get('q', 'unknown')
        combined_data['serper_data'][key] = serper_data.get('organic', [])

    return combined_data

def select_relevant_news(ticker, combined_data, top_n=5):
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY is None:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        return []

    openai.api_key = OPENAI_API_KEY

    articles = []
    for key, news_list in combined_data['serper_data'].items():
        for news in news_list:
            articles.append({
                'title': news.get('title', ''),
                'snippet': news.get('snippet', ''),
                'link': news.get('link', '')
            })

    # Prepare articles for GPT analysis
    articles_text = ""
    for idx, article in enumerate(articles):
        articles_text += f"Article {idx+1}:\nTitle: {article['title']}\nSnippet: {article['snippet']}\n\n"

    prompt = f"""
    Based on the following articles, select the top {top_n} most relevant to {ticker}'s stock performance:

    {articles_text}

    Provide a list of the article numbers that are most relevant.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or "gpt-4" if you have access
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.5,
        )

        selected_articles = response['choices'][0]['message']['content'].strip()
        # Extract article numbers from GPT response
        import re
        article_numbers = re.findall(r'\d+', selected_articles)
        selected_indices = [int(num)-1 for num in article_numbers if num.isdigit()]
        selected_indices = list(set(selected_indices))  # Remove duplicates
        # Get the selected articles
        relevant_articles = [articles[idx] for idx in selected_indices if 0 <= idx < len(articles)]

        return relevant_articles
    except Exception as e:
        print(f"An error occurred during GPT analysis: {e}")
        return []
