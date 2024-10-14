# src/serper_api.py

import requests
import json
import os
from dotenv import load_dotenv
import logging

def fetch_serper_data(query, filename):
    """
    Fetches data from the SERPER API based on the query and saves it as a JSON file.
    """
    try:
        # Load environment variables from .env file
        load_dotenv()
        SERPER_API_KEY = os.getenv('SERPER_API_KEY')

        if not SERPER_API_KEY:
            raise EnvironmentError("SERPER_API_KEY is not set in the environment variables.")

        url = 'https://google.serper.dev/search'
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200 and 'organic' in response.json():
            data = response.json()

            # Ensure the data directory exists
            os.makedirs('data', exist_ok=True)

            # Save data to JSON file
            filepath = f'data/{filename}.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)

            logging.info(f"Data for '{query}' has been saved to {filepath}.")
            return data
        else:
            logging.error(f"Unexpected response: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        logging.error(f"An error occurred while fetching data for query '{query}': {e}")
        return None

if __name__ == '__main__':
    # Example usage
    fetch_serper_data('AAPL stock analysis', 'serper_stock_context')
    fetch_serper_data('Geopolitical events affecting Apple', 'serper_geopolitics')
    fetch_serper_data('Technology sector news', 'serper_sector_news')
