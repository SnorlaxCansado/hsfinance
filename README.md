Stock Analysis Report Generator
Table of Contents
Introduction
Project Overview
Features
Folder Structure
Installation
Usage
Modules
data_processing.py
gpt_logic.py
jina_ai_module.py
main.py
report_generator.py
serper_api.py
yahoo_finance_api.py
Requirements
Contributing
License
Author
Acknowledgments
Introduction
The Stock Analysis Report Generator is a comprehensive tool designed to generate detailed stock analysis reports for a user-selected ticker symbol. It integrates data from various APIs, including Yahoo Finance, SERPER (Web Search API), OpenAI's GPT models, and Jina AI Reader, to provide a holistic view of a stock's performance, relevant news, and contextual analysis.

Project Overview
User Input:

The user selects a stock ticker for analysis.
Complementary Tickers and Theme Queries:

The system uses OpenAI's GPT models to suggest complementary tickers and generate theme-based queries related to the selected ticker.
Data Fetching:

Yahoo Finance API: Fetches stock data (historical and current) for the selected ticker.
SERPER API: Retrieves relevant news articles and context in the following categories:
Stock Context
Geopolitics
Sector News
Data Processing:

The JSON data from Yahoo Finance and SERPER is cleaned and combined.
Relevant News Selection:

GPT analyzes the combined data to select the most relevant news articles.
Full Content Retrieval:

Jina AI Reader: Fetches the full content of the selected news articles.
Report Generation:

GPT uses the full news content and stock data to generate a comprehensive report, structured and formatted based on provided examples.
Final Output:

The final report is saved in both .txt and .pdf formats.
Features
Automated Stock Analysis: Generates in-depth reports on stock performance, including technical and fundamental analysis.
News Integration: Incorporates the most relevant news articles affecting the stock, including geopolitical and sector-specific news.
AI-Powered Insights: Uses OpenAI's GPT models to provide analytical insights and summaries.
Customizable: Users can specify the number of relevant articles and the period for stock history.
PDF Report Generation: Creates professionally formatted PDF reports with charts and structured content.
Folder Structure
lua
Copiar código
./
|-- README.md
|-- data/
|-- hsfinance.log
|-- notebooks/
|-- outputs/
|-- requirements.txt
`-- src/
    |-- data_processing.py
    |-- gpt_logic.py
    |-- jina_ai_module.py
    |-- main.py
    |-- report_generator.py
    |-- serper_api.py
    |-- utils.py
    `-- yahoo_finance_api.py
data/: Stores intermediate data files like JSON responses and article contents.
notebooks/: Contains Jupyter notebooks (if any) for exploratory analysis.
outputs/: Stores the final generated reports in .txt and .pdf formats.
src/: Contains all the source code modules.
Installation
Prerequisites
Python 3.7 or higher
pip
API keys for the following services:
OpenAI API
SERPER API
Jina AI Reader API
Steps
Clone the Repository

bash
Copiar código
git clone https://github.com/yourusername/stock-analysis-report-generator.git
cd stock-analysis-report-generator
Create a Virtual Environment (Optional but Recommended)

bash
Copiar código
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
Install Required Packages

bash
Copiar código
pip install -r requirements.txt
Set Up Environment Variables

Create a .env file in the root directory and add your API keys:

makefile
Copiar código
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
JINA_READER_API_KEY=your_jina_ai_api_key
Usage
Run the main script with the desired stock ticker symbol:

bash
Copiar código
python src/main.py TICKER_SYMBOL
Optional Arguments
--articles: Number of relevant articles to select (default is 5).
--period: Period for stock history (options: 1d, 5d, 1mo, 3mo, 6mo, 1y, etc.)
Example:

bash
Copiar código
python src/main.py AAPL --articles 3 --period 6mo
This command generates a stock analysis report for Apple Inc. (AAPL), selecting the top 3 relevant articles and using 6 months of historical stock data.

Modules
data_processing.py
Responsible for:

Loading and validating JSON data.
Cleaning stock data and SERPER data.
Combining stock data with SERPER data.
Selecting the most relevant news articles using GPT.
gpt_logic.py
Handles:

Generating complementary tickers for comparison.
Creating theme-specific queries for the SERPER API.
jina_ai_module.py
Manages:

Fetching the full text content of news articles using the Jina AI Reader API.
Handling retries and failures, and blacklisting domains if necessary.
main.py
The orchestrator script that:

Parses command-line arguments.
Fetches stock data and news articles.
Processes and combines data.
Selects relevant news articles.
Fetches full article content.
Generates the final report.
report_generator.py
Handles:

Parsing the full articles.
Generating stock charts.
Creating the report using GPT.
Saving the report as a professionally formatted PDF.
serper_api.py
Responsible for:

Fetching data from the SERPER API based on provided queries.
Saving the fetched data as JSON files.
yahoo_finance_api.py
Manages:

Fetching stock data (both info and historical data) from Yahoo Finance.
Saving the fetched data as JSON files.
Requirements
The project dependencies are listed in requirements.txt:

requests
yfinance
pandas
jina
openai
numpy
logging
python-dotenv
fpdf2
reportlab
matplotlib
Install them using:

bash
Copiar código
pip install -r requirements.txt
Contributing
Contributions are welcome! Please follow these steps:

Fork the repository.
Create a new branch: git checkout -b feature/YourFeature.
Commit your changes: git commit -am 'Add some feature'.
Push to the branch: git push origin feature/YourFeature.
Submit a pull request.
License
This project is licensed under the MIT License - see the LICENSE file for details.

Author
Gabriel T. H. S. Santos
Acknowledgments
OpenAI GPT Models: For providing the language generation capabilities.
Yahoo Finance API: For stock data.
SERPER API: For web search results.
Jina AI Reader: For fetching full article contents.
ReportLab: For generating PDF reports.
Matplotlib: For creating stock charts.
