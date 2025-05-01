# (DONE)
from config.settings import PARENT_FOLDERS
from utils.logger import setup_logger
from utils.helpers import log_and_raise
from transformers_project.mergers import merge_search_terms_on_group, merge_multiple_files
from transformers_project.resample_scores import resample_average_scores
from loaders.load_to_csv import (
    save_df_to_csv, 
    move_file, 
    clear_folder_contents
    )


logger = setup_logger(__name__)


def clean_step(raw_df, clean_path, base_filename, group_on):
    
    clean_df = merge_search_terms_on_group(
        raw_df, 
        group_on=group_on, # url,link
        to_merge='search_terms'  # uniques only
        )
    if clean_df.empty:
        log_and_raise(ValueError, f"Cleaning failed - empty dataframe", "No data returned")
        
    # save clean raw file: versioned, compression
    full_path_clean = clean_path / f'{base_filename}_clean.csv'
    saved_path_clean = save_df_to_csv(
        clean_df, 
        full_path_clean, # path_and_filename
        versioned=True,
        compress=True,
        save_schema_format=None,
        )
    
    return clean_df

# For clean_df
def merge_with_main(clean_df, main_path, group_on, verbose=False):
    """Handles raws, cleans, processed"""
    
    if not main_path.exists:
        raise FileNotFoundError(f"Main folder does not exist: {main_path}")
    
    # merge
    files_to_merge = [clean_df, main_path]
    merged_main = merge_multiple_files(files_to_merge)
    if merged_main.empty:
        log_and_raise(ValueError, f"Merging failed - empty dataframe", "No data returned")
    
    # clean
    merged_main = merge_search_terms_on_group(
        merged_main, 
        group_on=group_on,  # link, url
        to_merge='search_terms'  # uniques only
        )
    if merged_main.empty:
        log_and_raise(ValueError, f"Cleaning failed - empty dataframe", "No data returned")

    # backup old main
    parent_backup = PARENT_FOLDERS["parent_backup"]#.get("parent_backup")
    if not parent_backup.exists():
        raise FileNotFoundError(f"Backup folder does not exist: {parent_backup}")
    
    move_file(source_path=main_path, destination_folder=parent_backup)
        
    if verbose:
        logger.info(f"File moved to {parent_backup}")
    
    # save new main
    # not to duplicate .csv if compression is True
    if main_path.suffix == ".gz":
        main_path = main_path.with_suffix("")
        
    full_path_main = main_path
    saved_path_main = save_df_to_csv(
        merged_main, 
        full_path_main,  # path_and_filename
        versioned=False,
        compress=True,
        save_schema_format=None,
        )
    
    return merged_main


def clean_up_folders(clean_all=None, clean_old=None, verbose=True):
    
    # Clean up folders
    #clean_all = [raw_path]
    #clean_old = [clean_path, processed_path]
    
    # clear all contents
    if clean_all:
        for folder in clean_all:
            clear_folder_contents(folder, exclude_pattern=None, move_to_trash=True, verbose=verbose)
    
    # keep latest
    if clean_old:
        for folder in clean_old:
            clear_folder_contents(folder, exclude_pattern='latest', move_to_trash=True, verbose=verbose)
        
        
        
def resample_step(processed_df, resampled_path, base_filename, freq):
    
    resampled_df = resample_average_scores(processed_df, col_suffix='nltk', freq=freq, fillna_value=None)
    if resampled_df.empty:
        log_and_raise(ValueError, f"Resampling failed - empty dataFrame", "No data returned")
    
    # save: not versioned, compressed
    full_path_resampled = resampled_path / f"{base_filename}_resampled_{freq.upper()}.csv"
    saved_path_processed = save_df_to_csv(
        resampled_df, 
        full_path_resampled,  # path_and_filename
        versioned=False,
        compress=True,
        )
    
    return resampled_df