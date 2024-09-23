# src/serper_api.py

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SERPER_API_KEY = os.getenv('SERPER_API_KEY')

def fetch_serper_data(query, filename):
    """
    Fetches data from the SERPER API based on the query and saves it as a JSON file.
    """
    try:
        if SERPER_API_KEY is None:
            raise ValueError("SERPER_API_KEY environment variable is not set.")

        url = 'https://google.serper.dev/search'
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            'q': query
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()

            # Ensure the data directory exists
            os.makedirs('data', exist_ok=True)

            # Save data to JSON file
            filepath = f'data/{filename}.json'
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)

            print(f"Data for '{query}' has been saved to {filepath}.")
            return data
        else:
            print(f"Failed to fetch data: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"An error occurred while fetching data for query '{query}': {e}")
        return None

if __name__ == '__main__':
    # Example usage
    if SERPER_API_KEY is None:
        print("Error: SERPER_API_KEY environment variable is not set.")
    else:
        # Fetch stock context
        fetch_serper_data('AAPL stock analysis', 'serper_stock_context')

        # Fetch geopolitical information
        fetch_serper_data('Geopolitical events affecting Apple', 'serper_geopolitics')

        # Fetch sector news
        fetch_serper_data('Technology sector news', 'serper_sector_news')
