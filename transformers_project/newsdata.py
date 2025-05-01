# (DONE) transformers.newsdata
import pandas as pd
from config.constants import FILTER_COLUMNS, RENAME_COLUMNS, MAPPING_TICKERS
from utils.normalizers import normalize_list_column
from transformers_project.sentiment_scores import get_sentiment_score_average, get_sentiment_label
from utils.helpers import log_and_raise
from utils.logger import setup_logger

logger = setup_logger(__name__)


def find_ticker_names(titles, mapping):
    """Returns tickers from mapping_tickers found in title"""
    
    # Flat mapping
    value_to_key = {
        word.lower(): key
        for key, word_list in mapping.items()
        for word in word_list
        if isinstance(word, str)
        }
    
    # Normalize and extract words from each string in the series
    words_series = titles.str.lower().str.findall(r"\b\w+\b")
    
    # Map each word to a unique ticker if it exists in the mapping
    return words_series.apply(lambda words: list(set(
        value_to_key[word].upper() for word in words if word in value_to_key)))


def transform(df, sentiment_score=True):
    
    # load config
    data_source = "newsdata"
    filter_cols = FILTER_COLUMNS.get(data_source)
    rename_cols = RENAME_COLUMNS.get(data_source) 
    mapping = MAPPING_TICKERS["crypto_dict"]
    
    # filter df (paid content)
    df = df[filter_cols].copy()
    
    if df.empty:
        log_and_raise(ValueError, f"Filter columns failed.", "No data returned.")
    
    # rename columns
    df = df.rename(columns=rename_cols)
    
    # normalize column types
    list_cols = ['authors', "search_terms", "country", "category"]
    for col in list_cols:
        df[col] = normalize_list_column(df[col])
        
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # tickers found in title
    df["ticker_names"] = find_ticker_names(df["title"], mapping)
    
    df['data_source'] = data_source
    
    def clean_source_url(text):
        """remove 'http://' and 'https://'"""
        return text.split("//")[-1]
    
    df['source_url'] = df['source_url'].apply(clean_source_url)
    
    if sentiment_score:
        # get sentiment scores and labels (title + description / 2)
        titles = df['title']
        descriptions = df['description'] 
        df['sentiment_score_nltk'] = get_sentiment_score_average(titles, descriptions)
        df['sentiment_label_nltk'] = df['sentiment_score_nltk'].apply(get_sentiment_label)
    
    # sort df
    df = df.sort_values(by='datetime').reset_index(drop=True)
    
    return df