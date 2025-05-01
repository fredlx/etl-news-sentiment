# (DONE) extractors.newsdata
import math
import pandas as pd
from config.settings import NEWSDATA_CONFIG
from utils.helpers import return_json, build_url, log_and_raise
from utils.validators import validate_api_response
from utils.logger import setup_logger

logger = setup_logger(__name__)  # 

# Extract
def extract_news(
    search_terms, 
    timeframe=None,
    next_page=None, 
    config=NEWSDATA_CONFIG, 
    verbose=True):
    """
    Extracts news from Newsdata with pagination logic implemented
    """
    
    # Load config
    API_URL = config["api_url"]
    API_KEY = config["api_key"]
    news_per_request = int(config["news_per_request"])
    max_requests = int(config["max_requests"])   # pages/requests per 15 min
    max_search_terms = int(config["max_search_terms"])
    
    # Use None, timeframe is breaking with a 422 error
    if timeframe and timeframe > 48:
        timeframe = 48 # max allowed in latest endpoint
    
    params = {
        'apikey': API_KEY,
        'qInTitle': search_terms,   # q, qInTitle, qInMeta
        'timeframe': timeframe, 
        'category': 'business,top,technology,politics,world',  # 5 topics max
        'language': 'en',
        'removeduplicate': '1'
        }
  
    # safeguard: search_terms
    if len(search_terms.replace(" OR ", "").replace(" AND ", "").split(" ")) > int(max_search_terms):
        log_and_raise(ValueError, "Number of search_terms exceeeds 5", "search_terms exceeded")

    # timeframe is breaking
    if timeframe is None:
        params.pop('timeframe')
        
    # if next_page, continue frmo there
    if next_page:
        params['page'] = next_page

    # Extract first page
    url = build_url(API_URL, params)  # build new endpoint
    response = return_json(url)
    validate_api_response(response, key_name='results')  # breaks if fails
    
    # append results
    all_results = [pd.DataFrame(response.get("results", []))]
    
    # get next page value
    next_page = response.get('nextPage')
    
    if verbose:
        total_results = response['totalResults']
        total_pages = math.ceil(response['totalResults'] / news_per_request)
        logger.info(f"Search: {search_terms}, Results: {total_results}, Pages: {total_pages}")
    
    # Apply pagination logic
    page_count = 1
    while next_page and page_count <= max_requests:
        page_count += 1
        
        # add new page to params
        params['page'] = next_page
        
        url = build_url(API_URL, params)
        response = return_json(url)
        validate_api_response(response, key_name='results')
        
        all_results.append(pd.DataFrame(response.get("results", [])))
        next_page = response.get('nextPage')
            
    # Combine all results
    df = pd.concat(all_results, ignore_index=True).drop_duplicates(subset='title')  # (NOTSURE) or link?
    if df.empty:
        log_and_raise(ValueError, f"Extraction failed for {search_terms}- dataframe is empty", "DataFrame is empty.")
    
    # create datetime and search_terms columns
    df['datetime'] = pd.to_datetime(df['pubDate'])
    df['search_terms'] = [[search_terms]] * len(df)

    if next_page is not None:
        logger.warning(f"Extraction incomplete. Resume from '{next_page}' for '{search_terms}'.")
    
    return df, page_count  # for max requests limit

# Usage:
# extract_news("bitcoin OR BTC")