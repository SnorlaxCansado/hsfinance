# src/main.py

import os
import sys
import json
import logging
import argparse
from yahoo_finance_api import fetch_stock_data
from serper_api import fetch_serper_data
from data_processing import load_json_file, validate_data, clean_stock_data, clean_serper_data, combine_data, select_relevant_news
from gpt_logic import generate_complementary_tickers, generate_theme_queries
from jina_ai_module import fetch_full_article_content
from report_generator import generate_report
from dotenv import load_dotenv

def parse_arguments():
    parser = argparse.ArgumentParser(description='Generate a stock analysis report.')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--articles', type=int, default=5, help='Number of relevant articles to select')
    parser.add_argument('--period', type=str, default='1y', help='Period for stock history (e.g., 1y, 6mo, 1mo)')
    return parser.parse_args()

def main():
    args = parse_arguments()
    ticker = args.ticker.upper()
    top_n_articles = args.articles
    stock_period = args.period

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Load environment variables
    load_dotenv()
    SERPER_API_KEY = os.getenv('SERPER_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    if SERPER_API_KEY is None:
        logging.error("SERPER_API_KEY environment variable is not set.")
        sys.exit(1)
    if OPENAI_API_KEY is None:
        logging.error("OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)

    try:
        # Fetch stock data
        logging.info(f"Fetching stock data for {ticker}...")
        fetch_stock_data(ticker, period=stock_period)

        # Generate complementary tickers
        logging.info(f"Generating complementary tickers for {ticker}...")
        complementary_tickers = generate_complementary_tickers(ticker)
        logging.info(f"Complementary tickers for {ticker}: {complementary_tickers}")

        # Generate theme-specific queries
        logging.info(f"Generating theme-specific queries for {ticker}...")
        theme_queries = generate_theme_queries(ticker)
        logging.info(f"Theme-specific queries for {ticker}: {theme_queries}")

        # Prepare queries for the SERPER API
        queries = {
            'serper_stock_context': f'{ticker} stock analysis',
            'serper_geopolitics': f'Geopolitical events affecting {ticker}',
            'serper_sector_news': f'{ticker} sector news'
        }

        # Include theme-specific queries
        for idx, query in enumerate(theme_queries):
            filename = f'serper_theme_query_{idx}'
            queries[filename] = query

        # Fetch data from SERPER API
        logging.info("Fetching data from SERPER API...")
        for filename, query in queries.items():
            logging.info(f"Fetching data for query: {query}")
            fetch_serper_data(query, filename)

        # Data Processing
        logging.info("Processing data...")
        # Load and clean stock data
        stock_data = load_json_file(f'data/{ticker}_stock_data.json')
        if validate_data(stock_data, ['info', 'history']):
            stock_data = clean_stock_data(stock_data)
        else:
            logging.error("Stock data validation failed.")
            stock_data = None

        # Load and clean SERPER data
        serper_files = [f'data/{filename}.json' for filename in queries.keys()]
        serper_data_list = []
        for filepath in serper_files:
            serper_data = load_json_file(filepath)
            if validate_data(serper_data, ['organic']):
                serper_data = clean_serper_data(serper_data)
                serper_data_list.append(serper_data)
            else:
                logging.error(f"SERPER data validation failed for {filepath}.")

        # Combine data
        if stock_data and serper_data_list:
            combined_data = combine_data(stock_data, serper_data_list)
            # Save combined data
            os.makedirs('data', exist_ok=True)
            with open('data/combined_data.json', 'w') as f:
                json.dump(combined_data, f, indent=4)
            logging.info("Combined data has been saved to data/combined_data.json.")

            # Select relevant news articles
            logging.info(f"Selecting top {top_n_articles} relevant news articles...")
            relevant_articles = select_relevant_news(ticker, combined_data, top_n=top_n_articles)
            # Save relevant articles for further processing
            with open('data/relevant_articles.json', 'w') as f:
                json.dump(relevant_articles, f, indent=4)
            logging.info("Relevant articles have been saved to data/relevant_articles.json.")

            # Fetch full article content using Jina AI
            logging.info("Fetching full article content...")
            full_articles = fetch_full_article_content(relevant_articles)
            # Save full articles
            with open('data/full_articles.json', 'w') as f:
                json.dump(full_articles, f, indent=4)
            logging.info("Full articles have been saved to data/full_articles.json.")

            # Generate the final report
            logging.info("Generating the final report...")
            report = generate_report(ticker, stock_data, full_articles)
            # Ensure outputs directory exists
            os.makedirs('outputs', exist_ok=True)
            # Save the report
            with open(f'outputs/{ticker}_final_report.txt', 'w') as f:
                f.write(report)
            logging.info(f"Final report has been saved to outputs/{ticker}_final_report.txt.")
        else:
            logging.error("Data combination failed due to previous errors.")
            sys.exit(1)

    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
