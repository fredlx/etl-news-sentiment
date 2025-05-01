# (DONE) some refactoring needed
from transformers_project.mergers import merge_multiple_files, merge_description_on_url
from transformers_project.sentiment_scores import update_sentiment_scores
from utils.semantic_tools import apply_semantic_cleaning
from utils.helpers import log_and_raise
from utils.logger import setup_logger
from loaders.load_to_csv import save_df_to_csv
from config.constants import COMMON_COLUMNS
from config.settings import PARENT_FOLDERS

import pandas as pd

logger = setup_logger(__name__)


def load_and_merge_step(file_list, common_cols=None):
    merged = merge_multiple_files(file_list, common_cols)
    return merged


def clean_step(merged, verbose=True):
    
    # drop duplicates, merge descriptions, creates "was_merged" column
    cleaned_1 = merge_description_on_url(merged)
    if cleaned_1.empty:
        log_and_raise(ValueError, "Drop duplicates on url and merging descriptions failed", "Clean step failed")
    
    if verbose:
        merged_descriptions = int(cleaned_1['was_merged'].sum())
        logger.info(f"Merged {merged_descriptions} text descriptions")
    
    # clean merged descriptions with semantic similarity
    cleaned_2 = apply_semantic_cleaning(cleaned_1)
    if cleaned_2.empty:
        log_and_raise(ValueError, "Clean merged descriptions failed", "Clean step failed")
    
    if verbose:
        removed_sentences = int(cleaned_2['removed_sent_count'].sum())
        logger.info(f"Removed {removed_sentences} sentences in total")
    
    # update scores for merged descriptions
    mask = cleaned_2['was_merged']  # boolean
    cleaned_3 = update_sentiment_scores(cleaned_2, mask)
    if cleaned_3.empty:
        log_and_raise(ValueError, "Updating sentiment scores on merged descriptions failed", "Clean step failed")
    
    cleaned_3 = cleaned_3.drop(["was_merged", "removed_sent_count"], axis=1)
    
    if verbose:
        logger.info("Sentiment scores updated")
    
    return cleaned_3


def update_main(merged_main_path, df_to_merge):
    
    # Load main_merged_sources
    merged_main_df = pd.read_csv(merged_main_path)
    merged_main_df["datetime"] = pd.to_datetime(merged_main_df["datetime"])
    
    # Concat sorted_df + merged_main
    new_merged_main = (
        pd.concat([df_to_merge, merged_main_df], ignore_index=True)
        .drop_duplicates()
        )

    if new_merged_main.empty:
        raise ValueError("Dataframe is empty")
    
    new_merged_main = (
        new_merged_main
        .sort_values(by="datetime")
        .reset_index(drop=True)
        )
    
    return new_merged_main
    

def run_pipeline(file_list, verbose=True):
    
    logger.info("Starting Merge Sources pipeline...")

    merge_folder = PARENT_FOLDERS["parent_merged"] #"../data/merged"
    common_cols = COMMON_COLUMNS

    # Step 1. Load and merge
    merged_df = load_and_merge_step(file_list, common_cols)
    
    if verbose:
        logger.info("Step 1: Files loaded and merged")
    
    # Step 2. Clean
    cleaned_df = clean_step(merged_df, verbose=True)
    sorted_df = cleaned_df[[
        'datetime', 'title', 'description', 'category', 
        'authors', 'source', 'source_url', 'url', 'search_terms', 'data_source',
        'ticker_names','sentiment_score_nltk', 'sentiment_label_nltk',
        ]]
    
    if verbose:
        logger.info("Step 2: File cleaned")
    
    # save temp
    full_output_path = merge_folder / "merged_sources.csv"
    save_df_to_csv(
        sorted_df,
        full_output_path,
        compress=True,
        verbose=True
        )
    
    # Step 3. Update main (main_merged_sources.csv.gz)
    merged_main_path = merge_folder / "main" / "main_merged_sources.csv.gz"
    if not merged_main_path.exists:
        raise FileNotFoundError(f"Filepath does not exist: {merged_main_path}")
    
    new_merged_main = update_main(merged_main_path, df_to_merge=sorted_df)
    
    # Save
    if merged_main_path.suffix == ".gz":
        merged_main_path = merged_main_path.with_suffix("")
    
    full_output_path = merged_main_path
    save_df_to_csv(
        new_merged_main,
        full_output_path,
        compress=True,
        verbose=True
        )
    

if __name__ == "__main__":

    processed_folder = PARENT_FOLDERS["parent_processed"]
    
    # files to merge: available sources from /processed
    file_list = []
    for source in ["alpha_vantage", "newsdata"]:
        path = processed_folder / source / f"{source}.csv.gz"
        if not path.exists:
            raise FileNotFoundError(f"Filepath does not exist: {path}")
        
        file_list.append(path)

    run_pipeline(file_list)


    