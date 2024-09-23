# src/main.py

import os
import sys
from yahoo_finance_api import fetch_stock_data
from serper_api import fetch_serper_data
from dotenv import load_dotenv

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <TICKER_SYMBOL>")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    # Load environment variables
    load_dotenv()
    SERPER_API_KEY = os.getenv('SERPER_API_KEY')

    if SERPER_API_KEY is None:
        print("Error: SERPER_API_KEY environment variable is not set.")
        sys.exit(1)

    # Fetch stock data
    fetch_stock_data(ticker)

    # Prepare queries for the SERPER API
    queries = {
        'serper_stock_context': f'{ticker} stock analysis',
        'serper_geopolitics': f'Geopolitical events affecting {ticker}',
        'serper_sector_news': f'{ticker} sector news'
    }

    # Fetch data from SERPER API
    for filename, query in queries.items():
        fetch_serper_data(query, filename)

if __name__ == '__main__':
    main()
