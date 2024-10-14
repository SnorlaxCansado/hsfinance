# src/data_processing.py

import json
import pandas as pd
import openai
import os
from dotenv import load_dotenv
import logging
import re

def load_json_file(filepath):
    """
    Loads a JSON file and returns its contents as a dictionary.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logging.info(f"Loaded data from {filepath}.")
        return data
    except Exception as e:
        logging.error(f"An error occurred while loading {filepath}: {e}")
        return None

def validate_data(data, expected_keys):
    """
    Validates that the data contains the expected keys.
    """
    if data is None:
        return False
    missing_keys = [key for key in expected_keys if key not in data]
    if missing_keys:
        logging.error(f"Data is missing keys: {missing_keys}")
        return False
    return True

def clean_stock_data(stock_data):
    # Ensure 'history' is a list of dictionaries
    history = stock_data.get('history', [])
    if not isinstance(history, list):
        logging.error("Invalid format for stock history data.")
        return None

    # Convert date strings to datetime objects, handle missing values, etc.
    df = pd.DataFrame(history)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # Convert 'Date' column to string to avoid serialization issues
        df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    else:
        logging.warning("Date column not found in stock history data. Skipping date processing.")

    # Forward fill missing values
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
        logging.error("No 'organic' key found in SERPER data.")
        return None

    # Ensure each result has 'title' and 'snippet'
    for result in serper_data['organic']:
        if 'title' not in result or 'snippet' not in result:
            logging.error("A result is missing 'title' or 'snippet'.")
            return None

    return serper_data

def combine_data(stock_data, serper_data_dict):
    """
    Combines stock data and a dictionary of SERPER data dictionaries into a single data structure.
    """
    combined_data = {
        'stock_info': stock_data.get('info', {}),
        'stock_history': stock_data.get('history', []),
        'serper_data': serper_data_dict  # Now serper_data_dict is organized by category
    }

    return combined_data

def select_relevant_news(ticker, combined_data, top_n=5):
    """
    Uses GPT to select the top N relevant news articles, ensuring at least one article from each category.
    """
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY is None:
        logging.error("Error: OPENAI_API_KEY environment variable is not set.")
        return []

    openai.api_key = OPENAI_API_KEY

    articles = []
    category_articles = {}
    for category, serper_data in combined_data['serper_data'].items():
        news_list = serper_data.get('organic', [])
        category_articles[category] = []
        for news in news_list:
            article = {
                'title': news.get('title', ''),
                'snippet': news.get('snippet', ''),
                'link': news.get('link', ''),
                'category': category
            }
            articles.append(article)
            category_articles[category].append(article)

    # Ensure at least one article from each category
    selected_articles = []
    remaining_slots = top_n
    for category in ['STOCK CONTEXT', 'GEOPOLITICS CONTEXT', 'SECTOR CONTEXT']:
        category_article_list = category_articles.get(category, [])
        if category_article_list:
            selected_articles.append(category_article_list[0])
            remaining_slots -= 1
        else:
            logging.warning(f"No articles found in category {category}")

    if remaining_slots > 0:
        # Remove already selected articles from the articles list
        selected_links = set([article['link'] for article in selected_articles])
        remaining_articles = [article for article in articles if article['link'] not in selected_links]
        # Limit the number of articles to prevent token overflow
        max_articles_in_prompt = 10  # Adjust based on token considerations
        remaining_articles = remaining_articles[:max_articles_in_prompt]

        # Prepare articles for GPT analysis
        articles_text = ""
        for idx, article in enumerate(remaining_articles):
            articles_text += f"Article {idx+1}:\nTitle: {article['title']}\nSnippet: {article['snippet']}\n\n"

        prompt = f"""
Based on the following articles, select the top {remaining_slots} most relevant to {ticker}'s stock performance.

Articles:
{articles_text}

Please provide a list of the article numbers that are most relevant, formatted as a comma-separated list (e.g., "Selected articles: 1, 2, 3").
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.5,
            )

            gpt_reply = response['choices'][0]['message']['content'].strip()
            # Extract article numbers from GPT response
            match = re.search(r'Selected articles:\s*(.*)', gpt_reply, re.IGNORECASE)
            if match:
                article_numbers = re.findall(r'\d+', match.group(1))
                selected_indices = [int(num)-1 for num in article_numbers if num.isdigit()]
            else:
                logging.error("Could not parse selected articles from GPT response.")
                selected_indices = []

            # Remove duplicates and ensure valid indices
            selected_indices = list(set(selected_indices))
            selected_indices = [idx for idx in selected_indices if 0 <= idx < len(remaining_articles)]

            # Get the selected articles
            gpt_selected_articles = [remaining_articles[idx] for idx in selected_indices]

            if not gpt_selected_articles:
                logging.warning("No valid articles selected by GPT.")
            else:
                selected_articles.extend(gpt_selected_articles[:remaining_slots])  # Ensure we don't exceed remaining_slots

        except openai.error.InvalidRequestError as e:
            logging.error(f"OpenAI API request exceeded token limit: {e}")
            return []
        except Exception as e:
            logging.error(f"An error occurred during GPT analysis: {e}")
            return []

    # Limit the total number of articles to top_n
    return selected_articles[:top_n]
