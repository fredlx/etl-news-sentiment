# (INPROGRESS) clean, resample - pipelines.run_alpha_vantage

import importlib
import pipelines.pipeline_helpers
import config.settings
importlib.reload(pipelines.pipeline_helpers)
importlib.reload(config.settings)


import pandas as pd
import argparse
from config.settings import ALPHA_VANTAGE_CONFIG, ALPHA_VANTAGE_PATHS
from utils.helpers import log_and_raise
from utils.logger import setup_logger
from extractors.alpha_vantage import extract_news
from transformers_project.alpha_vantage import transform
from pipelines.pipeline_helpers import clean_step, merge_with_main, clean_up_folders, resample_step
from loaders.load_to_csv import save_df_to_csv


logger = setup_logger(__name__)

"""
ETL Process Steps:
1. Extract --> raw files
2. Merge and clean --> clean file
3. Merge with main clean file
4. Transform --> processed file
5. Merge with main processed file
"""

def extract_step(symbols, n_days, topics, raw_path, base_filename):
    
    all_dfs = []
    missed_symbols = []
    n_symbols = 0
    
    for symbol in symbols:
        
        try:
            # extract
            raw = extract_news(symbol=symbol, offset_days=n_days, selected_topics=topics)
            if raw.empty:
                log_and_raise(ValueError, f"[{symbol}] Extraction failed - empty dataFrame.", "No data returned")
            
            # save versioned, no compression
            file_symbol = symbol.split(":")[-1].lower()
            full_path_raw = raw_path / f"{base_filename}_raw_{file_symbol}.csv"
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
            missed_symbols.append(symbol)
            logger.exception(f"[{symbol}] Extraction failed - {e}")
            #raise   # (NOTSURE) maybe better to re-raise because of limits? 
    
    # concatenate all results
    if all_dfs:
        raw_df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"Successfully merged {len(all_dfs)} extracted dataframes.")
    else:
        log_and_raise(ValueError, 'Extraction failed — no data merged.', 'No data merged')
        
    if missed_symbols:
        logger.warning(f"{len(missed_symbols)} missed symbols: {missed_symbols}")

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


def run_pipeline(symbols, n_days, resample, topics=None, verbose=True):
    
    # Load config
    base_filename = ALPHA_VANTAGE_CONFIG["base_filename"]
    raw_path = ALPHA_VANTAGE_PATHS.get("folder_raw")
    clean_path = ALPHA_VANTAGE_PATHS.get("folder_clean")
    processed_path = ALPHA_VANTAGE_PATHS.get("folder_processed")
    resampled_path = ALPHA_VANTAGE_PATHS.get("folder_resampled")
    
    # Main files
    clean_main = clean_path / "main" / f"{base_filename}_clean_main.csv.gz"  # OK
    processed_main = processed_path / "main" / f"{base_filename}_main.csv.gz"
    
    logger.info(f"ETL Source: {base_filename.upper()}")
    
    if verbose:
        logger.info("Step #1 - Start Extraction")
    raw_df = extract_step(symbols, n_days, topics, raw_path, base_filename)
    
    if verbose:
        logger.info("Step #2 - Merge and Clean Raw Files")
    clean_df = clean_step(raw_df, clean_path, base_filename, group_on='url')
    
    if verbose:
        logger.info("Step #3 - Merge Clean File with Main Clean")

    merged_main_clean = merge_with_main(clean_df, main_path=clean_main, group_on='url') # OK
    
    if verbose:
        logger.info("Step #4 - Transform Clean File")
    processed_df = transform_step(clean_df, processed_path, base_filename)
    
    if verbose:
        logger.info("Step #5 - Merge Processed File with MAIN ALPHA_VANTAGE")
    merged_main_processed = merge_with_main(processed_df, main_path=processed_main, group_on='url')
    
    
    if resample:
        for f in ["D", "h"]:
            
            if verbose:
                logger.info(f"Resampling Scores: {f}")
            
            resampled_df = resample_step(processed_df, resampled_path, base_filename, freq=f)
    
    if verbose:
        logger.info("Step #6 - Clean Up Folders")
        
    # final step    
    clean_all = [raw_path]
    clean_old = [clean_path, processed_path]
    clean_up_folders(clean_all, clean_old, verbose=True)
    
        
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Run ETL pipeline for Alpha Vantage news.")
    
    parser.add_argument(
        "--fetch", nargs="+", required=True, 
        help="List of symbols to extract (e.g., btc eth)")
    
    parser.add_argument(
        "--last_days", type=int, default=None, required=False, 
        help="Number of past days to fetch news for each symbol")
    
    args = parser.parse_args()

    symbols = [f'CRYPTO:{symbol.upper().strip()}' for symbol in args.fetch]

    run_pipeline(symbols, args.last_days, resample=False)
    
    #symbols = ["CRYPTO:BTC", "CRYPTO:ETH"]
    #n_days = 3
    #run_pipeline(symbols, n_days)
    



