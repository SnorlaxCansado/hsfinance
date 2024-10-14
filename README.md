# Stock Analysis Report Generator

This project is a Stock Analysis Report Generator that combines various data sources to produce comprehensive reports for selected stock tickers. It leverages multiple APIs and AI tools to gather financial, geopolitical, and sector-specific news, creating insightful reports in both text and PDF formats.

## Project Overview

The main flow of the project is as follows:

1. **User Choose Ticker**
   - The user selects a stock ticker for analysis.

2. **chatgpt-4o-mini**
   - Assists in choosing complementary tickers for analysis and generates theme-based queries for the selected ticker.

3. **Yahoo Finance (Stocks API)**
   - Fetches historical stock data and presents it in a tabular format.

4. **SERPER (Web Search API)**
   - **Stock Context**: Fetches context-specific information related to the selected stock.
   - **Geopolitics**: Fetches geopolitical context that may impact the stock.
   - **Sector News**: Fetches news related to the specific sector of the selected stock.

5. **Data Combination**
   - JSON data from Yahoo Finance, SERPER (Stock Context, Geopolitics, Sector News) is combined for further analysis.

6. **chatgpt-4o-mini**
   - Analyzes the combined data and selects the most relevant news articles to send to JINA AI for full content extraction.

7. **JINA AI**
   - Retrieves the complete content of the selected news articles and sends it back to `chatgpt-oi-mini`.

8. **chatgpt-oi-mini**
   - Generates the final report using the complete news content and stock data fetched earlier. The report is structured and formatted based on provided examples.

9. **Final Output**
   - The output is a comprehensive report that combines stock data, news content, and analysis. The report is saved in both text and PDF formats.

## Project Folder Structure

The folder structure for this project is as follows:

```
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
```

### Description of Important Files

- **`src/data_processing.py`**: Handles data cleaning, validation, and combination for further analysis.
- **`src/gpt_logic.py`**: Interacts with GPT to generate complementary tickers and theme-specific queries.
- **`src/jina_ai_module.py`**: Uses the Jina AI Reader API to fetch full article content.
- **`src/main.py`**: Main orchestration script that runs the complete flow of the report generation.
- **`src/report_generator.py`**: Uses GPT to generate the final report and ReportLab to create the PDF output.
- **`src/serper_api.py`**: Fetches data from the SERPER API based on given queries.
- **`src/yahoo_finance_api.py`**: Fetches stock data using the Yahoo Finance API.
- **`requirements.txt`**: Lists the required packages and dependencies for the project.

## Installation and Setup

1. **Clone the Repository**
   ```sh
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Create a Virtual Environment**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   - Create a `.env` file in the root directory and add the following environment variables:
     ```
     OPENAI_API_KEY=<Your_OpenAI_API_Key>
     SERPER_API_KEY=<Your_SERPER_API_Key>
     JINA_READER_API_KEY=<Your_Jina_Reader_API_Key>
     ```

## How to Use the Project

1. **Run the Script**
   Use the following command to run the main script:
   ```sh
   python src/main.py <ticker> --articles <number_of_articles> --period <stock_period>
   ```
   - `<ticker>`: Stock ticker symbol (e.g., `AAPL`).
   - `--articles`: (Optional) Number of relevant articles to select. Default is `5`.
   - `--period`: (Optional) Period for stock history (e.g., `1d`, `5d`, `1mo`, `1y`). Default is `1y`.

2. **Output**
   - The report will be saved in the `outputs/` folder as both a `.txt` and `.pdf` file.

## Features

- **Ticker Analysis**: Selects complementary tickers for comparative analysis.
- **Data Collection**: Collects stock data from Yahoo Finance and relevant news articles using SERPER and Jina AI APIs.
- **AI-Powered Insights**: Uses `chatgpt-oi-mini` to generate insights on recent performance, geopolitical impacts, and sector-specific context.
- **Report Generation**: Generates a comprehensive report with an analysis of recent performance, stock context, geopolitical context, and sector news.
- **PDF Output**: Creates a well-formatted PDF report with all relevant content.

## Dependencies

- `requests`
- `yfinance`
- `pandas`
- `jina`
- `openai`
- `numpy`
- `logging`
- `python-dotenv`
- `fpdf2`
- `reportlab`
- `matplotlib`

All dependencies can be installed using `pip install -r requirements.txt`.

## Notes

- Ensure you have valid API keys for OpenAI, SERPER, and Jina AI to use this project effectively.
- This project makes heavy use of OpenAI's GPT for generating complementary tickers, theme queries, and generating the final report.
- SERPER and Jina AI are used to gather and process news articles related to the selected ticker.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Contact

For any questions or suggestions, feel free to contact me at: **Gabriel T. H. S. Santos**.

