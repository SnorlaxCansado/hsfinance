# src/jina_ai_module.py

from jina import Flow, DocumentArray, Document

def fetch_full_article_content(articles):
    """
    Fetches the full text content of the articles using Jina AI and pre-built Executors.
    """
    # Create DocumentArray with Documents, setting the 'uri' field to the article link
    docs = DocumentArray([Document(uri=article.get('link', '')) for article in articles])

    flow = (
        Flow()
        .add(uses='jinahub://URLLoader')  # Executor that loads content from URLs
        .add(uses='jinahub://HTMLTextExtractor')  # Executor that extracts text from HTML
    )

    with flow:
        docs = flow.post('/', inputs=docs, return_results=True)

    # Update articles with the fetched content from doc.text
    for doc, article in zip(docs, articles):
        article['full_content'] = doc.text

    return articles

