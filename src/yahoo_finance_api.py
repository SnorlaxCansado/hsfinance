# src/yahoo_finance_api.py

import yfinance as yf
import json
import os
import pandas as pd

def fetch_stock_data(ticker):
    """
    Fetches stock data for the given ticker using yfinance and saves it as a JSON file.
    """
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info
        stock_history = stock.history(period="1y")  # Fetch last 1 year of data
        stock_history.reset_index(inplace=True)

        # Convert Timestamp columns to strings
        for column in stock_history.columns:
            if isinstance(stock_history[column].iloc[0], pd.Timestamp):
                stock_history[column] = stock_history[column].astype(str)

        stock_history_dict = stock_history.to_dict(orient='records')

        data = {
            'info': stock_info,
            'history': stock_history_dict
        }

        # Ensure the data directory exists
        os.makedirs('data', exist_ok=True)

        # Save data to JSON file
        with open(f'data/{ticker}_stock_data.json', 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Stock data for {ticker} has been saved to data/{ticker}_stock_data.json.")
        return data

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker}: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    fetch_stock_data('AAPL')

