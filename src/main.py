# src/main.py

import os
import re
import sys
import json
import logging
import argparse

import openai
from yahoo_finance_api import fetch_stock_data
from serper_api import fetch_serper_data
from data_processing import (
    load_json_file,
    validate_data,
    clean_stock_data,
    clean_serper_data,
    combine_data,
    select_relevant_news
)
from gpt_logic import (
    generate_complementary_tickers,
    generate_theme_queries
)
from jina_ai_module import fetch_full_article_content
from report_generator import generate_report  # No need to import save_report_as_pdf
from dotenv import load_dotenv
from urllib.parse import urlparse

def parse_arguments():
    """
    Parses command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Generate a stock analysis report.')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    parser.add_argument('--articles', type=int, default=5, help='Number of relevant articles to select')
    parser.add_argument('--period', type=str, default='1y', help='Period for stock history (options: 1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)')
    return parser.parse_args()

def get_domain(url):
    """
    Extracts the domain from a given URL.
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        return domain
    except:
        return ''

def main():
    """
    Main function to orchestrate the stock report generation.
    """
    args = parse_arguments()
    ticker = args.ticker.upper()
    top_n_articles = args.articles
    stock_period = args.period

    # Configure logging to output to both console and file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("hsfinance.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

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

    # Fetch stock data
    logging.info(f"Fetching stock data for {ticker}...")
    stock_data = fetch_stock_data(ticker, period=stock_period)
    if not stock_data:
        logging.error(f"Failed to fetch stock data for {ticker}.")
        sys.exit(1)

    # Generate complementary tickers
    logging.info(f"Generating complementary tickers for {ticker}...")
    complementary_tickers = generate_complementary_tickers(ticker)
    if not complementary_tickers:
        logging.warning(f"No complementary tickers generated for {ticker}.")
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
    stock_data_json = load_json_file(f'data/{ticker}_stock_data.json')
    if validate_data(stock_data_json, ['info', 'history']):
        stock_data = clean_stock_data(stock_data_json)
    else:
        logging.error("Stock data validation failed due to missing 'info' or 'history' keys.")
        stock_data = None

    # Load and clean SERPER data
    serper_data_dict = {}
    for filename in queries.keys():
        filepath = f'data/{filename}.json'
        serper_data = load_json_file(filepath)
        if validate_data(serper_data, ['organic']):
            serper_data = clean_serper_data(serper_data)
            # Map filename to category
            if filename == 'serper_stock_context':
                category = 'STOCK CONTEXT'
            elif filename == 'serper_geopolitics':
                category = 'GEOPOLITICS CONTEXT'
            elif filename == 'serper_sector_news':
                category = 'SECTOR CONTEXT'
            else:
                category = 'OTHER'
            serper_data_dict[category] = serper_data
        else:
            logging.error(f"SERPER data validation failed for {filepath}.")

    # Combine data
    if stock_data and serper_data_dict:
        combined_data = combine_data(stock_data, serper_data_dict)
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
        successful_articles, failed_articles, domain_failure_count = fetch_full_article_content(relevant_articles, max_retries=3)
        logging.info(f"Successfully fetched {len(successful_articles)} articles.")
        if failed_articles:
            logging.warning(f"Failed to fetch {len(failed_articles)} articles.")

        # Blacklist domains with consistent failures
        blacklist_domains = set()
        for domain, count in domain_failure_count.items():
            if count >= 3:  # Blacklist if failed 3 times
                blacklist_domains.add(domain)
                logging.info(f"Blacklisted domain after multiple failures: {domain}")

        # Attempt to replace failed articles, prioritizing missing contexts
        # Identify which contexts are covered by successful articles
        covered_contexts = set(article['category'] for article in successful_articles)
        required_contexts = {'STOCK CONTEXT', 'GEOPOLITICS CONTEXT', 'SECTOR CONTEXT'}
        missing_contexts = required_contexts - covered_contexts

        while len(successful_articles) < top_n_articles and missing_contexts:
            needed = top_n_articles - len(successful_articles)
            logging.info(f"Attempting to select {needed} replacement article(s) to cover missing contexts: {missing_contexts}")
            # Gather new candidates from missing contexts
            all_selected_links = set(article['link'] for article in successful_articles)
            new_candidates = []
            for context in missing_contexts:
                serper_data = combined_data['serper_data'].get(context, {})
                for news in serper_data.get('organic', []):
                    link = news.get('link', '')
                    if link and link not in all_selected_links:
                        domain = get_domain(link)
                        if domain not in blacklist_domains:
                            new_candidates.append({
                                'title': news.get('title', ''),
                                'snippet': news.get('snippet', ''),
                                'link': link,
                                'category': context
                            })

            if not new_candidates:
                logging.warning("No more articles available for replacement in missing contexts.")
                break

            # Use GPT to select the top 'needed' articles from new_candidates
            articles_text = ""
            for idx, article in enumerate(new_candidates):
                articles_text += f"Article {idx+1}:\nTitle: {article['title']}\nSnippet: {article['snippet']}\n\n"

            prompt = f"""
Based on the following articles, select the top {needed} most relevant to {ticker}'s stock performance, ensuring coverage of the missing contexts: {', '.join(missing_contexts)}.

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
                selected_indices = [idx for idx in selected_indices if 0 <= idx < len(new_candidates)]

                # Get the selected articles
                gpt_selected_articles = [new_candidates[idx] for idx in selected_indices]

                if not gpt_selected_articles:
                    logging.warning("No valid articles selected by GPT for replacement.")
                    break

                # Fetch the content of the selected replacement articles
                logging.info(f"Fetching content for {len(gpt_selected_articles)} replacement article(s)...")
                replacement_success, replacement_failed, replacement_domain_failure_count = fetch_full_article_content(gpt_selected_articles, max_retries=3)
                successful_articles.extend(replacement_success)
                if replacement_failed:
                    logging.warning(f"Failed to fetch {len(replacement_failed)} replacement article(s).")
                    for article in replacement_failed:
                        url = article.get('link', '')
                        domain = get_domain(url)
                        if domain:
                            blacklist_domains.add(domain)
                            logging.info(f"Blacklisted domain: {domain}")

                # Update covered_contexts and missing_contexts
                for article in replacement_success:
                    covered_contexts.add(article['category'])
                missing_contexts = required_contexts - covered_contexts

                # Update blacklist_domains based on replacement failures
                for domain, count in replacement_domain_failure_count.items():
                    if count >= 3:
                        blacklist_domains.add(domain)
                        logging.info(f"Blacklisted domain after multiple failures: {domain}")

            except openai.error.InvalidRequestError as e:
                logging.error(f"OpenAI API request exceeded token limit: {e}")
                break
            except Exception as e:
                logging.error(f"An error occurred during GPT analysis: {e}")
                break

        # If still not enough articles, attempt to fill with any available articles excluding blacklisted domains
        if len(successful_articles) < top_n_articles:
            needed = top_n_articles - len(successful_articles)
            logging.info(f"Attempting to select {needed} additional replacement article(s) from any context.")
            all_selected_links = set(article['link'] for article in successful_articles)
            new_candidates = []
            for category, serper_data in combined_data['serper_data'].items():
                for news in serper_data.get('organic', []):
                    link = news.get('link', '')
                    if link and link not in all_selected_links:
                        domain = get_domain(link)
                        if domain not in blacklist_domains:
                            new_candidates.append({
                                'title': news.get('title', ''),
                                'snippet': news.get('snippet', ''),
                                'link': link,
                                'category': category
                            })

            if new_candidates:
                # Use GPT to select the top 'needed' articles from new_candidates
                articles_text = ""
                for idx, article in enumerate(new_candidates):
                    articles_text += f"Article {idx+1}:\nTitle: {article['title']}\nSnippet: {article['snippet']}\n\n"

                prompt = f"""
Based on the following articles, select the top {needed} most relevant to {ticker}'s stock performance.

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
                    selected_indices = [idx for idx in selected_indices if 0 <= idx < len(new_candidates)]

                    # Get the selected articles
                    gpt_selected_articles = [new_candidates[idx] for idx in selected_indices]

                    if not gpt_selected_articles:
                        logging.warning("No valid articles selected by GPT for additional replacement.")
                        pass
                    else:
                        # Fetch the content of the selected replacement articles
                        logging.info(f"Fetching content for {len(gpt_selected_articles)} additional replacement article(s)...")
                        replacement_success, replacement_failed, replacement_domain_failure_count = fetch_full_article_content(gpt_selected_articles, max_retries=3)
                        successful_articles.extend(replacement_success)
                        if replacement_failed:
                            logging.warning(f"Failed to fetch {len(replacement_failed)} additional replacement article(s).")
                            for article in replacement_failed:
                                url = article.get('link', '')
                                domain = get_domain(url)
                                if domain:
                                    blacklist_domains.add(domain)
                                    logging.info(f"Blacklisted domain: {domain}")

                        # Update blacklist_domains based on replacement failures
                        for domain, count in replacement_domain_failure_count.items():
                            if count >= 3:
                                blacklist_domains.add(domain)
                                logging.info(f"Blacklisted domain after multiple failures: {domain}")

                except openai.error.InvalidRequestError as e:
                    logging.error(f"OpenAI API request exceeded token limit: {e}")
                except Exception as e:
                    logging.error(f"An error occurred during GPT analysis: {e}")

        # Trim the successful_articles to top_n_articles
        final_articles = successful_articles[:top_n_articles]
        logging.info(f"Final number of articles selected: {len(final_articles)}")

        # Re-save full_articles.txt with the final articles
        combined_content_final = ""
        for article in final_articles:
            title = article.get('title', '')
            link = article.get('link', '')
            category = article.get('category', 'OTHER')
            full_content = article.get('full_content', '')
            combined_content_final += f"Title: {title}\nLink: {link}\nCategory: {category}\nText:\n{full_content}\n\n"

        if combined_content_final:
            with open("data/full_articles.txt", 'w', encoding='utf-8') as f:
                f.write(combined_content_final.strip())
            logging.info("Final full articles have been saved to data/full_articles.txt.")
        else:
            logging.warning("No articles were successfully fetched after replacements.")

        # Generate the final report

        logging.info("Generating the final report...")
        author_name = 'Gabriel T. H. S. Santos'
        report = generate_report(ticker, stock_data, max_articles=top_n_articles, author_name=author_name)
        if report:
            # Ensure outputs directory exists
            os.makedirs('outputs', exist_ok=True)
            # Save the report as a text file
            report_file_path = f'outputs/{ticker}_final_report.txt'
            with open(report_file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logging.info(f"Final report has been saved to {report_file_path}.")
        else:
            logging.error("Failed to generate the final report.")
    else:
        logging.error("Data combination failed due to previous errors.")
        sys.exit(1)
    # end of main()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)