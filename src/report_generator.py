# src/report_generator.py

import openai
import os
from dotenv import load_dotenv
import logging
import re
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    BaseDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, Frame, PageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor


def parse_full_articles_txt(file_path):
    """
    Parses the full_articles.txt file and returns a list of articles.
    Each article is a dictionary with 'title', 'link', 'category', and 'full_content' keys.
    """
    articles = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split the content into articles using a regex pattern
    article_pattern = r'Title:\s*(.*?)\nLink:\s*(.*?)\nCategory:\s*(.*?)\nText:\n(.*?)(?=\nTitle:|\Z)'
    matches = re.findall(article_pattern, content, re.DOTALL)

    for match in matches:
        title = match[0].strip()
        link = match[1].strip()
        category = match[2].strip()
        full_content = match[3].strip()
        articles.append({
            'title': title,
            'link': link,
            'category': category,
            'full_content': full_content
        })

    return articles


def generate_stock_charts(stock_data, ticker):
    """
    Generates charts of the stock's recent performance and saves them as images.
    Returns a list of file paths to the generated charts.
    """
    df = pd.DataFrame(stock_data['history'])
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)

    chart_paths = []

    # Price over time
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df['Close'], label='Close Price')
    plt.title(f'{ticker} Stock Price Over Time')
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.legend()
    plt.grid(True)
    chart_path = f'data/{ticker}_price_chart.png'
    plt.savefig(chart_path)
    plt.close()
    chart_paths.append(chart_path)

    # Volume over time
    plt.figure(figsize=(10, 6))
    plt.bar(df.index, df['Volume'], label='Volume')
    plt.title(f'{ticker} Trading Volume Over Time')
    plt.xlabel('Date')
    plt.ylabel('Volume')
    plt.legend()
    plt.grid(True)
    chart_path = f'data/{ticker}_volume_chart.png'
    plt.savefig(chart_path)
    plt.close()
    chart_paths.append(chart_path)

    return chart_paths


def add_header_footer(canvas, doc):
    """
    Adds the header and footer to each page.
    """
    canvas.saveState()
    # Header
    header_text = f"{doc.stock_name} ({doc.ticker})"
    canvas.setFont('Helvetica-Bold', 10)
    canvas.drawString(inch, doc.height + doc.topMargin - 0.5 * inch, header_text)
    # Footer
    footer_text = f"Page {canvas.getPageNumber()} | Generated on: {doc.generated_date}"
    canvas.setFont('Helvetica', 9)
    canvas.drawString(inch, 0.5 * inch, footer_text)
    canvas.restoreState()


def generate_report(ticker, stock_data, max_articles=5, author_name='Author Name'):
    """
    Generates a comprehensive report for the given ticker using stock data and articles from full_articles.txt.
    """
    # Load environment variables
    load_dotenv()
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    openai.api_key = OPENAI_API_KEY

    # Prepare stock data summary
    stock_info = stock_data.get('info', {})
    current_price = stock_info.get('currentPrice', 'N/A')
    previous_close = stock_info.get('previousClose', 'N/A')
    open_price = stock_info.get('open', 'N/A')
    day_range = f"{stock_info.get('dayLow', 'N/A')} - {stock_info.get('dayHigh', 'N/A')}"
    volume = stock_info.get('volume', 'N/A')
    avg_volume = stock_info.get('averageVolume', 'N/A')
    market_cap = stock_info.get('marketCap', 'N/A')
    pe_ratio = stock_info.get('trailingPE', 'N/A')
    fifty_two_week_range = f"{stock_info.get('fiftyTwoWeekLow', 'N/A')} - {stock_info.get('fiftyTwoWeekHigh', 'N/A')}"
    long_name = stock_info.get('longName', ticker)

    stock_summary = f"""
    {ticker} ({long_name}) is currently trading at {current_price}.
    - Previous Close: {previous_close}
    - Open: {open_price}
    - Day's Range: {day_range}
    - 52-Week Range: {fifty_two_week_range}
    - Volume: {volume}
    - Average Volume: {avg_volume}
    - Market Cap: {market_cap}
    - PE Ratio (TTM): {pe_ratio}
    """

    # Parse articles from full_articles.txt
    articles_file = 'data/full_articles.txt'
    articles = parse_full_articles_txt(articles_file)

    # Organize articles by category
    categories = {
        'STOCK CONTEXT': [],
        'GEOPOLITICS CONTEXT': [],
        'SECTOR CONTEXT': [],
        'OTHER': []
    }

    for article in articles:
        category = article.get('category', 'OTHER').upper()
        if category in categories:
            categories[category].append(article)
        else:
            categories['OTHER'].append(article)

    # Prepare articles content for each category
    articles_content = {}
    for category in categories:
        content = ""
        for idx, article in enumerate(categories[category]):
            content_snippet = article.get('full_content', '')
            content += f"Article {idx+1} Title: {article['title']}\nContent:\n{content_snippet}\n\n"
        articles_content[category] = content

    # Create the Sources section
    sources = []
    for category in categories:
        for article in categories[category]:
            source = f"- Title: {article['title']}\n  Link: {article['link']}\n  Relevant Section: {category}"
            sources.append(source)

    # Add stock data source
    sources.append(f"- Title: Yahoo Finance\n  Link: https://finance.yahoo.com/quote/{ticker}\n  Relevant Section: Analysis of Recent Performance")

    # Create the prompt for GPT
    prompt = f"""
You are an expert financial analyst.

Generate a detailed and insightful report on {ticker} using the following information:

**Analysis of Recent Performance:** 
{stock_summary}

**STOCK CONTEXT:**
{articles_content.get('STOCK CONTEXT', 'No relevant articles available.')}

**GEOPOLITICS CONTEXT:**
{articles_content.get('GEOPOLITICS CONTEXT', 'No relevant articles available.')}

**SECTOR CONTEXT:**
{articles_content.get('SECTOR CONTEXT', 'No relevant articles available.')}

The report should include:

- **Analysis of Recent Performance:** Provide a detailed analysis of numerical indexes, prices (high, low, open, close), volume, etc., from the stock data.
- **STOCK CONTEXT:** Analyze the news articles related to the stock context and explain their impact on {ticker}'s performance.
- **GEOPOLITICS CONTEXT:** Analyze geopolitical factors affecting {ticker} based on the provided articles.
- **SECTOR CONTEXT:** Analyze sector-specific news and trends that may influence {ticker}'s performance.
- **Conclusion and Future Outlook:** Provide a conclusion resulting from a cross-analysis of the previous sections. Include a future outlook relevant to both long-term and short-term investors.
- **Sources:** List the sources used in the report, formatted as follows:

{chr(10).join(sources)}

Structure the report with clear headings and bullet points where appropriate.

Ensure the report is detailed and rich in information.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=3500,  # Increased to allow for a detailed report
            n=1,
            stop=None,
            temperature=0.7,
        )

        report_text = response['choices'][0]['message']['content'].strip()
    except openai.error.InvalidRequestError as e:
        error_message = f"An error occurred while generating the report: {e}"
        logging.error(error_message)
        return None
    except Exception as e:
        error_message = f"An unexpected error occurred while generating the report: {e}"
        logging.error(error_message)
        return None

    # Now, generate the PDF report using ReportLab
    save_report_as_pdf(report_text, ticker, stock_data, long_name, author_name)
    return report_text


def save_report_as_pdf(report_text, ticker, stock_data, long_name, author_name):
    """
    Saves the report text as a professionally formatted PDF file.
    """
    try:
        # Create the PDF document
        pdf_file_path = f'outputs/{ticker}_final_report.pdf'

        doc = BaseDocTemplate(pdf_file_path, pagesize=letter,
                              leftMargin=inch, rightMargin=inch,
                              topMargin=inch, bottomMargin=inch)

        # Store stock name, ticker, and generated date in the doc for access in header/footer
        doc.stock_name = long_name
        doc.ticker = ticker
        doc.generated_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        doc.author_name = author_name

        # Define frames
        frame_cover = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='cover_frame')
        frame_content = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - inch, id='content_frame')

        # Define PageTemplates
        cover_template = PageTemplate(id='CoverPage', frames=frame_cover)
        content_template = PageTemplate(id='ContentPage', frames=frame_content, onPage=add_header_footer)

        doc.addPageTemplates([cover_template, content_template])

        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            name='TitleStyle', fontName='Helvetica-Bold', fontSize=24, leading=28, alignment=TA_CENTER, spaceAfter=20)
        subtitle_style = ParagraphStyle(
            name='SubtitleStyle', fontName='Helvetica', fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=10)
        header_style = ParagraphStyle(
            name='HeaderStyle', fontName='Helvetica-Bold', fontSize=18, leading=22, spaceAfter=10, spaceBefore=20)
        normal_style = ParagraphStyle(
            name='NormalStyle', fontName='Helvetica', fontSize=12, leading=14)
        bullet_style = ParagraphStyle(
            name='BulletStyle', parent=normal_style, leftIndent=20, bulletIndent=10)
        small_style = ParagraphStyle(
            name='SmallStyle', parent=normal_style, fontSize=10)
        # Header style with background color
        header_background_style = ParagraphStyle(
            name='HeaderBackgroundStyle', parent=header_style, backColor=HexColor('#D3D3D3'), alignment=TA_CENTER)

        # Cover Page
        cover_title = Paragraph(f"{ticker} Stock Analysis Report", title_style)
        cover_subtitle = Paragraph(f"Generated on: {doc.generated_date}", subtitle_style)
        cover_author = Paragraph(f"Developed by: {author_name}", subtitle_style)
        elements.extend([Spacer(1, 2*inch), cover_title, Spacer(1, 0.2*inch), cover_subtitle, cover_author, PageBreak()])

        # Analysis of Recent Performance
        elements.append(Paragraph("Analysis of Recent Performance", header_background_style))

        # Prepare stock data summary
        stock_info = stock_data.get('info', {})
        current_price = stock_info.get('currentPrice', 'N/A')
        previous_close = stock_info.get('previousClose', 'N/A')
        open_price = stock_info.get('open', 'N/A')
        day_range = f"{stock_info.get('dayLow', 'N/A')} - {stock_info.get('dayHigh', 'N/A')}"
        volume = stock_info.get('volume', 'N/A')
        avg_volume = stock_info.get('averageVolume', 'N/A')
        market_cap = stock_info.get('marketCap', 'N/A')
        pe_ratio = stock_info.get('trailingPE', 'N/A')
        fifty_two_week_range = f"{stock_info.get('fiftyTwoWeekLow', 'N/A')} - {stock_info.get('fiftyTwoWeekHigh', 'N/A')}"

        # Prepare summary table
        stock_data_table = [
            ['Current Price', current_price],
            ['Previous Close', previous_close],
            ['Open', open_price],
            ["Day's Range", day_range],
            ['52-Week Range', fifty_two_week_range],
            ['Volume', volume],
            ['Average Volume', avg_volume],
            ['Market Cap', market_cap],
            ['PE Ratio (TTM)', pe_ratio]
        ]
        table = Table(stock_data_table, hAlign='LEFT', colWidths=[150, 200])
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ])
        table.setStyle(table_style)
        elements.append(table)
        elements.append(Spacer(1, 12))

        # Generate and add stock summary charts
        chart_paths = generate_stock_charts(stock_data, ticker)
        for chart_path in chart_paths:
            elements.append(Image(chart_path, width=500, height=300))
            elements.append(Spacer(1, 12))

        # Separate the main content and the Sources section
        if '**Sources:**' in report_text:
            main_content, sources_content = report_text.split('**Sources:**', 1)
        else:
            main_content = report_text
            sources_content = ''

        # Process the main content sections
        sections = re.split(r'\n(?=\*\*)', main_content)
        for section in sections:
            if section.strip() == '':
                continue
            lines = section.strip().split('\n')
            heading = lines[0].strip()
            content = '\n'.join(lines[1:]).strip()
            # Use header style with background
            elements.append(Paragraph(heading.strip('* '), header_background_style))
            paragraphs = content.split('\n')
            for para in paragraphs:
                if para.strip() == '':
                    continue
                # Check if the paragraph is a bullet point
                if para.strip().startswith('- '):
                    bullet = para.strip()[2:]
                    elements.append(Paragraph(f'• {bullet}', bullet_style))
                else:
                    elements.append(Paragraph(para.strip(), normal_style))
                elements.append(Spacer(1, 6))
            elements.append(Spacer(1, 12))

        # Now process the Sources section if it exists
        if sources_content.strip():
            elements.append(Paragraph("Sources", header_background_style))
            sources_paragraphs = sources_content.strip().split('\n')
            for source_para in sources_paragraphs:
                if source_para.strip() == '':
                    continue
                elements.append(Paragraph(source_para.strip(), small_style))
                elements.append(Spacer(1, 4))

        # Build the PDF
        doc.build(elements)
        logging.info(f"Report has been saved as PDF to {pdf_file_path}.")
    except Exception as e:
        logging.error(f"An error occurred while saving the report as PDF: {e}")