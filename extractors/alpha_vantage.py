# (DONE) extractors.alpha_vantage
import pandas as pd
from config.settings import ALPHA_VANTAGE_CONFIG
from config.constants import AVAILABLE_TOPICS
from utils.helpers import return_json, build_url, get_iso_date, log_and_raise
from utils.validators import validate_api_response
from utils.logger import setup_logger

logger = setup_logger(__name__)  #

def extract_news(
    symbol, 
    selected_topics=None,  # expects a list
    offset_days=None, 
    limit=1000,            # default 50, max 1000
    config=ALPHA_VANTAGE_CONFIG,
    verbose=True
    ):
    
    # Load configuration
    API_URL = config["api_url"]
    API_KEY = config["api_key"]
    
    # Selected topics
    if selected_topics is None:
        selected_topics = AVAILABLE_TOPICS.get("alpha_vantage")

    # Start day
    if offset_days is None:
        time_from = None
    else:
        time_from = get_iso_date(offset_days)
    
    # Params dict
    params = {
        'apikey': API_KEY,
        'function': 'NEWS_SENTIMENT',
        'tickers': symbol,
        'topics': selected_topics,
        'limit': limit,
        'time_from': time_from
        }
    
    # Remove if None
    if params.get('time_from') is None:
        params.pop('time_from')
    
    url = build_url(API_URL, params)
    response = return_json(url)
    
    # breaks if validation fails
    validate_api_response(response, key_name='feed', check_status=False)  # no status
    
    # get news feed
    raw_data = response.get("feed", [])  
    
    df = pd.DataFrame(raw_data).drop_duplicates(subset='url').reset_index(drop=True)
    if df.empty:
        log_and_raise(ValueError, f"Extraction failed for {symbol}- dataframe is empty", "DataFrame is empty.")
    
    # feature engineering for better management
    df['search_terms'] = [[symbol]] * len(df)
    df["datetime"] = pd.to_datetime(df["time_published"])
    
    if verbose:
        logger.info(f"[{symbol}]. Number of results extracted: {response.get('items')}")
    
    return df