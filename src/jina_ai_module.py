# src/jina_ai_module.py

import requests
import os
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse
import time

def fetch_full_article_content(articles, max_retries=3):
    """
    Fetches the full text content of the articles using the Jina AI Reader API.
    Saves all successfully fetched articles into a single text file in the desired format.
    Returns two lists: successfully fetched articles and failed articles.
    """
    try:
        # Load environment variables
        load_dotenv()
        JINA_READER_API_KEY = os.getenv('JINA_READER_API_KEY')
        if not JINA_READER_API_KEY:
            logging.error("JINA_READER_API_KEY environment variable is not set.")
            return [], articles  # All articles failed

        headers = {
            'Authorization': f'Bearer {JINA_READER_API_KEY}',
            'X-Return-Format': 'text'  # Request content in plain text format
        }

        combined_content = ""
        successful_articles = []
        failed_articles = []
        domain_failure_count = {}

        for idx, article in enumerate(articles):
            url = article.get('link', '')
            title = article.get('title', f'Article {idx+1}')
            category = article.get('category', 'OTHER')
            if not url:
                logging.warning(f"Article '{title}' has no URL. Skipping.")
                failed_articles.append(article)
                continue

            # Directly append the target URL to the API endpoint without encoding
            api_url = f'https://r.jina.ai/{url}'

            retries = 0
            success = False
            while retries < max_retries and not success:
                try:
                    response = requests.get(api_url, headers=headers, timeout=20)
                    if response.status_code == 200:
                        full_text = response.text.strip()
                        if not full_text:
                            logging.warning(f"No content returned for URL {url}.")
                            retries += 1
                            time.sleep(1)  # Wait before retrying
                            continue

                        article['full_content'] = full_text

                        # Append to combined content
                        combined_content += f"Title: {title}\n"
                        combined_content += f"Link: {url}\n"
                        combined_content += f"Category: {category}\n"
                        combined_content += f"Text:\n{full_text}\n\n"

                        successful_articles.append(article)
                        success = True
                    else:
                        logging.error(f"Failed to fetch content for URL {url}: {response.status_code} - {response.text}")
                        retries += 1
                        time.sleep(1)  # Wait before retrying
                except requests.RequestException as e:
                    logging.error(f"Request error for URL {url}: {e}")
                    retries += 1
                    time.sleep(1)  # Wait before retrying

            if not success:
                failed_articles.append(article)
                # Update domain failure count
                domain = urlparse(url).netloc.lower()
                domain_failure_count[domain] = domain_failure_count.get(domain, 0) + 1

        # Ensure the 'data' directory exists
        os.makedirs('data', exist_ok=True)

        # Save combined content to a single file
        if successful_articles:
            combined_filename = "data/full_articles.txt"
            with open(combined_filename, 'w', encoding='utf-8') as f:
                f.write(combined_content.strip())
            logging.info(f"Full articles have been saved to {combined_filename}.")
        else:
            logging.warning("No articles were successfully fetched. 'full_articles.txt' was not created.")

        return successful_articles, failed_articles, domain_failure_count

    except Exception as e:
        logging.error(f"An error occurred while fetching full article content: {e}")
        return [], articles, {}
