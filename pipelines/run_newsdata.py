# (DONE) pipelines.run_newsdata
import pandas as pd
import argparse
from config.settings import NEWSDATA_CONFIG, NEWSDATA_PATHS
from config.constants import SEARCH_PARAMS
from utils.helpers import log_and_raise
from utils.logger import setup_logger
from extractors.newsdata import extract_news
from transformers_project.newsdata import transform
from pipelines.pipeline_helpers import clean_step, merge_with_main, clean_up_folders, resample_step
from loaders.load_to_csv import save_df_to_csv

logger = setup_logger(__name__)


def extract_step(list_search_terms, raw_path, base_filename, verbose=True):
    
    all_dfs = []
    missed_searches = []
    page_counts = 0
    n_symbols = 0
    
    for search_terms in list_search_terms:
        
        try:
            # extract
            raw, page_count = extract_news(search_terms=search_terms, verbose=verbose)
            if raw.empty:
                log_and_raise(
                    ValueError, 
                    f"[{search_terms}] Extraction failed - empty dataFrame.", 
                    "No data returned",
                    logger
                    )
            
            page_counts += page_count
            if page_counts > 20:
                logger.warning(f"Page counts close to limit of 30 per 15min: {page_counts}")
            
            # save versioned, no compression
            file_symbol = search_terms.replace(" OR ", ",").replace(" AND ", ",").split(",")[-1]
            full_path_raw = f'{raw_path}{base_filename}_raw_{file_symbol}.csv'
            saved_path_raw = save_df_to_csv(
                raw, 
                full_path_raw, # path_and_filename
                versioned=True,
                compress=False,
                save_schema_format=None,
                )
            
            # append results
            all_dfs.append(raw)
            n_symbols += 1
            
        except Exception as e:
            missed_searches.append(search_terms)
            logger.exception(f"[{search_terms}] Extraction failed - {e}")
            #raise   # better to re-raise because of limits? No, continue
    
    # concatenate all results
    if all_dfs:
        raw_df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"Successfully merged {len(all_dfs)} extracted dataframes.")
    else:
        log_and_raise(ValueError, 'Extraction failed — no data merged.', 'No data merged', logger)
        
    if missed_searches:
        logger.warning(f"{len(missed_searches)} missed symbols: {missed_searches}")

    return raw_df


def transform_step(clean_df, processed_path, base_filename):
    
    processed_df = transform(clean_df, sentiment_score=True)
    if processed_df.empty:
        log_and_raise(ValueError, f"Transformation failed - empty dataFrame", "No data returned")
        
    # save: not versioned, compressed
    full_path_processed = processed_path / f"{base_filename}.csv"
    saved_path_processed = save_df_to_csv(
        processed_df, 
        full_path_processed,  # path_and_filename
        versioned=False,
        compress=True,
        save_schema_format=None,
        )
    
    return processed_df


def run_pipeline(list_search_terms, resample, verbose=True):
    
    # Load config (Path objects)
    base_filename = NEWSDATA_CONFIG["base_filename"]
    raw_path = NEWSDATA_PATHS.get("folder_raw")
    clean_path = NEWSDATA_PATHS.get("folder_clean")
    processed_path = NEWSDATA_PATHS.get("folder_processed")
    resampled_path = NEWSDATA_PATHS.get("folder_resampled")
    
    # Main files
    clean_main = clean_path / "main" / f"{base_filename}_clean_main.csv.gz"
    processed_main = processed_path / "main" / f"{base_filename}_main.csv.gz"
    
    logger.info(f"ETL Source: {base_filename}")
    
    # Steps
    if verbose:
        logger.info("Step #1 - Start Extraction")
        
    raw_df = extract_step(list_search_terms, raw_path, base_filename, verbose=True)
    
    if verbose:
        logger.info("Step #2 - Merge and Clean Raw Files")
        
    clean_df = clean_step(raw_df, clean_path, base_filename, group_on='link')
    
    if verbose:
        logger.info("Step #3 - Merge Clean File with Main Clean")
        
    merged_main_clean = merge_with_main(clean_df, main_path=clean_main, group_on='link')
    
    if verbose:
        logger.info("Step #4 - Transform Clean File")
        
    processed_df = transform_step(clean_df, processed_path, base_filename)
    
    if verbose:
        logger.info("Step #5 - Merge Processed File with MAIN NEWSDATA")
        
    merged_main_processed = merge_with_main(processed_df, main_path=processed_main, group_on='url')
    
    if resample:
        for f in ["D", "h"]:
            
            if verbose:
                logger.info(f"Resampling Scores: {f}")
            
            resampled_df = resample_step(processed_df, resampled_path, base_filename, freq=f)
        
    if verbose:
        logger.info("Final Step - Clean Up Folders")
        
    # final step    
    clean_all = [raw_path]
    clean_old = [clean_path, processed_path]
    clean_up_folders(clean_all, clean_old, verbose=True)
    
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Run ETL pipeline for Newsdata API news. Last 48h.")
    
    parser.add_argument(
        "--fetch", nargs="+", required=True, 
        help="List of symbols to extract (e.g., btc eth)")
    
    args = parser.parse_args()
    
    search_params = SEARCH_PARAMS.get('newsdata')
    list_search_terms = [search_params.get(x.lower().strip()) for x in args.fetch]

    run_pipeline(list_search_terms, resample=False)




    
    
    
    
    
    
    
    