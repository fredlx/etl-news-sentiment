# (INPROGRESS) missing resample_step implementation 
# (DONE) transformers.alpha_vantage
import pandas as pd
from config.constants import FILTER_COLUMNS, RENAME_COLUMNS
from config.settings import ALPHA_VANTAGE_CONFIG
from utils.helpers import log_and_raise
from utils.logger import setup_logger
from utils.normalizers import safe_eval, normalize_list_column, normalize_list_of_dicts_column
from transformers_project.sentiment_scores import get_sentiment_score_average, get_sentiment_label

logger = setup_logger(__name__)

def extract_values_by_key(column, key_name):
    """use after normalization, more simple than original"""
    def extract_from_row(row):
        if isinstance(row, list):
            return [item.get(key_name) for item in row if isinstance(item, dict) and key_name in item]
        return []
    return column.map(extract_from_row)


def clean_ticker_names(text):
    """Removes CRYPTO: and FOREX:"""
    if isinstance(text, str):
        text = safe_eval(text)
    return [item.split(":")[-1] for item in text]


# Can be optimized (copy(), swifter, etc)
def transform(df, sentiment_score=True):
    
    data_source = ALPHA_VANTAGE_CONFIG["base_filename"]
    filter_cols = FILTER_COLUMNS.get(data_source)
    rename_cols = RENAME_COLUMNS.get(data_source)
    
    # filter df (remove unavailable content)
    df = df[filter_cols].copy()
    if df.empty:
        log_and_raise(ValueError, f"Filtering columns failed.", "No data returned.")
    
    # rename columns
    df = df.rename(columns=rename_cols)
    
    # normalize column types (useful for schema)
    list_cols = ['authors', 'search_terms']
    list_dict_cols = ['topics', 'ticker_sentiment']
    
    for col in list_cols:
        df[col] = normalize_list_column(df[col])
    
    for col in list_dict_cols:
        df[col] = normalize_list_of_dicts_column(df[col])
    
    # ensure datetime object
    df["datetime"] = pd.to_datetime(df["datetime"])
    
    # feature engineering
    df['data_source'] = [[data_source]] * len(df) # for list of sources
    
    df["category"] = extract_values_by_key(df['topics'], key_name="topic")
    df['category'] = df["category"].apply(lambda lst: [x.lower() for x in lst if isinstance(x, str)])
    
    # tickers listed in ticker_sentiment
    df["ticker_names"] = extract_values_by_key(df['ticker_sentiment'], key_name="ticker")
    df["ticker_names"] = df["ticker_names"].apply(clean_ticker_names)  # keep symbol only
    
    # sentiment scores recalculated with nltk
    if sentiment_score:
        # get sentiment scores and labels (title + description / 2)
        titles = df['title']
        descriptions = df['description'] 
        df['sentiment_score_nltk'] = get_sentiment_score_average(titles, descriptions)
        df['sentiment_label_nltk'] = df['sentiment_score_nltk'].apply(get_sentiment_label)
    
    # sort df
    df = df.sort_values(by='datetime').reset_index(drop=True)
    
    return df


###

# (NOTUSED) use for analysis/dashboard
def filter_ticker(ticker_sentiment_data, symbol):
    """Filters symbol from ticker_sentiment dict of symbols"""
    
    # (NOTSURE) validation needed?
    for entry in ticker_sentiment_data:
        if entry["ticker"].lower() == symbol.lower():
            return entry
    return {}
    
# (NOTUSED) use for analysis/dashboards 
def get_sentiment_df(ticker_sentiment_data, symbol):
    """
    Get sentiment_df from ticker_sentiment
    Returns df: 'ticker','relevance_score','ticker_sentiment_score','ticker_sentiment_label'
    """
    
    # filter ticker data
    ticker_match = ticker_sentiment_data.apply(lambda x: filter_ticker(x, symbol))
    
    # convert dict to pandas df
    sentiment_df = pd.json_normalize(ticker_match)
    return sentiment_df

