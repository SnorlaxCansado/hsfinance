# src/data_processing.py

def validate_data(data, expected_keys):
    """
    Validates that the data contains the expected keys.
    """
    if data is None:
        return False
    missing_keys = [key for key in expected_keys if key not in data]
    if missing_keys:
        print(f"Data is missing keys: {missing_keys}")
        return False
    return True

def clean_stock_data(stock_data):
    """
    Cleans and preprocesses the stock data.
    """
    # Example: Ensure 'history' is a list of dictionaries
    history = stock_data.get('history', [])
    if not isinstance(history, list):
        print("Invalid format for stock history data.")
        return None

    # Convert date strings to datetime objects, handle missing values, etc.
    # Here we can use pandas for convenience
    import pandas as pd

    df = pd.DataFrame(history)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        print("Date column not found in stock history data.")
        return None

    # Handle missing values, e.g., fill with the previous value
    df.fillna(method='ffill', inplace=True)

    # Convert back to list of dictionaries
    clean_history = df.to_dict(orient='records')
    stock_data['history'] = clean_history

    return stock_data

def clean_serper_data(serper_data):
    """
    Cleans and preprocesses the SERPER API data.
    """
    # Check if 'organic' results are present
    if 'organic' not in serper_data:
        print("No 'organic' key found in SERPER data.")
        return None

    # Example: Ensure each result has 'title' and 'snippet'
    for result in serper_data['organic']:
        if 'title' not in result or 'snippet' not in result:
            print("A result is missing 'title' or 'snippet'.")
            return None

    return serper_data

def combine_data(stock_data, serper_data_list):
    """
    Combines stock data and a list of SERPER data dictionaries into a single data structure.
    """
    combined_data = {
        'stock_info': stock_data.get('info', {}),
        'stock_history': stock_data.get('history', []),
        'serper_data': {}
    }

    for serper_data in serper_data_list:
        # Use a descriptive key for each SERPER data set
        key = serper_data.get('query', 'unknown')
        combined_data['serper_data'][key] = serper_data.get('organic', [])

    return combined_data
