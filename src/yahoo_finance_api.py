# src/yahoo_finance_api.py

import yfinance as yf
import json
import os
import pandas as pd

VALID_PERIODS = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']

def fetch_stock_data(ticker, period='1y'):
    """
    Fetches stock data for the given ticker using yfinance and saves it as a JSON file.
    Parameters:
        ticker (str): The stock ticker symbol.
        period (str): The period over which to fetch stock data (e.g., '1y', '6mo', '1mo').
    """
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info
        stock_history = stock.history(period=period)  # Use the passed period
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
    fetch_stock_data('AAPL', period='1y')
