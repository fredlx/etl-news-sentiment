# (DONE) mergers.py
import pandas as pd
from pathlib import Path
from utils.logger import setup_logger
from config.constants import SOURCE_RANKING
from utils.validators import validate_required_columns
from utils.normalizers import normalize_search_terms

from collections import Counter

logger = setup_logger(__name__)

# v2. No dedup.
def merge_multiple_files(file_list, common_cols=None):
    """
    Merges multiple DataFrames or CSV files into a single DataFrame.
    Auto detects if it is df or Path.
    No dedup!

    Parameters:
        file_list (list): List of DataFrames or CSV paths (str or Path)

    Raises:
        KeyError: If columns don't match
        ValueError: If resulting merged DataFrame is empty
        FileNotFoundError: If file path doesn't exist

    Returns:
        pandas.DataFrame
    
    Usage: 
        merged = merge_multiple_files([df1,"path/to/file_".csv",df4])
    """
    all_dfs = []

    # get df/files to merge
    for idx, item in enumerate(file_list, start=1):
        
        if isinstance(item, (str, Path)):            
            item = Path(item)
            if not item.exists():
                msg = f"File not found: {item}"
                logger.error(msg)
                raise FileNotFoundError(msg)
            df = pd.read_csv(item)  # , parse_dates=True
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            logger.info(f"Loaded CSV file #{idx}: {item} / shape: {df.shape}")
        
        elif isinstance(item, pd.DataFrame):
            df = item
            logger.info(f"Loaded DataFrame object #{idx} / shape: {df.shape}")
        
        else:
            raise TypeError(f"Unsupported input type: {type(item)}")

        all_dfs.append(df)
        
    if not all_dfs:
        raise ValueError("No valid DataFrames to merge.")

    # v3: validate columns before merging
    first_cols = common_cols or list(all_dfs[0].columns)
    first_cols_set = set(first_cols)

    for idx, df in enumerate(all_dfs[1:], start=2):
        df_cols_set = set(df.columns)

        if common_cols is None:
            # Strict: must match exactly
            if df_cols_set != first_cols_set:
                raise KeyError(f"Column mismatch at file #{idx}")
        else:
            # Flexible: must contain all required columns
            if not first_cols_set.issubset(df_cols_set):
                missing = first_cols_set - df_cols_set
                raise KeyError(f"Missing columns in file #{idx}: {missing}")

    # Reorder columns in all DataFrames before merging
    all_dfs = [df[first_cols] for df in all_dfs]
    merged_df = pd.concat(all_dfs, axis=0, ignore_index=True)

    if merged_df.empty:
        raise ValueError("DataFrame is empty after merging.")

    logger.info(f"Merged {len(all_dfs)} files successfully / shape: {merged_df.shape}")

    return merged_df


# Merge sources and dedup: Alpha_vantage, Newsdata
def merge_description_on_url(df):
    """
    Implicit drop_duplicates with conditions:
    - Select top-ranked rows based on source_ranking
    - Merge descriptions and flags row for later processing
    
    Returns: DataFrame with 'description' and 'was_merged' flag.
    """
    df = df.copy()
    if df.empty:
        raise ValueError("Dataframe is empty")
        
    source_ranking = SOURCE_RANKING
    
    # Columns validation
    req_cols = ['data_source','description','url', 'datetime']
    validate_required_columns(df.columns, req_cols)
    
    # apply source_ranking mapping
    df['source_rank'] = df['data_source'].map(source_ranking).fillna(999)

    # Select the top-ranked row per url
    top_rows = (
        df.sort_values(by='source_rank')
          .groupby('url', as_index=False)
          .first()
          .drop(columns=['description', 'source_rank'])
          )
    if top_rows.empty:
        raise ValueError("No top rows found after grouping by URL.")

    # Merge descriptions and mark if more than one was merged
    grouped = df.groupby('url')['description']
    merged_descriptions = grouped.agg(lambda x: ' '.join(filter(pd.notna, x))).to_frame(name='description')
    merged_descriptions['was_merged'] = grouped.count() > 1

    # Combine top row and merged description
    result_df = top_rows.merge(merged_descriptions, on='url')
    if result_df.empty:
        raise ValueError("Resulting DataFrame is empty after merge.")
    
    result_df = result_df.sort_values(by='datetime').reset_index(drop=True)

    return result_df

# for clean step: group_on url, link
def merge_search_terms_on_group(df, group_on='url', to_merge='search_terms'):
    """
    Drops duplicated rows by 'group_on' col and merges 'to_merge' col lists for each row.
    Keeps all other columns by taking the first non-null value for each group.
    group_on, similar to drop_duplicates(subset)
    to_merge, column to merge
    """
    
    # validations (logger in main logic)
    if df.empty:
        raise ValueError("DataFrame is empty.")
    
    required_cols = [group_on, to_merge, 'datetime']
    validate_required_columns(df.columns, required_cols)
    
    # Step 1: Apply normalization str --> list
    df[to_merge] = df[to_merge].apply(normalize_search_terms)

    def merge_group(group):
        merged = group.iloc[0].copy() # gets first non-null occurrence = drops dups
        all_terms = [term for sublist in group[to_merge] for term in sublist]
        merged[to_merge] = list(set(all_terms))  # unique terms
        return merged

    # Step 2: Apply Group and Aggregate to drop duplicates
    merged_df = df.groupby(group_on, group_keys=False).apply(merge_group)
    merged_df['datetime'] = pd.to_datetime(merged_df['datetime']) # double check
    return merged_df.sort_values(by='datetime').reset_index(drop=True)



### NOT USED ###

# (NOTUSED)
def merge_csvs_from_folder(folder_path, common_columns=None, exclude_pattern=None):
    """
    Loads and merges CSV (including compressed) files from a folder.
    If common_columns is provided, keeps only those columns.
    Excludes pattern
    Handle errors in main logic
    """

    folder = Path(folder_path)
    file_patterns = ["*.csv", "*.csv.gz", "*.csv.zip", "*.csv.bz2"]
    csv_files = [
        file for pattern in file_patterns for file in folder.glob(pattern)
        if not (exclude_pattern and exclude_pattern in file.stem)
        ] # excludes pattern if pattern is not None
    
    all_dfs = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, compression='infer')
                
            if common_columns is not None:
                df = df.loc[:, df.columns.intersection(common_columns)]
            
            all_dfs.append(df)
        
        except Exception as e:
            logger.exception(f"Skipped {file.name}: {e}")

    
    if not all_dfs:
        logger.info("No CSV files loaded.")
        return pd.DataFrame(columns=common_columns or [])  # empty df
    
    merged_df = pd.concat(all_dfs, ignore_index=True)
    return merged_df

# (NOTUSED)
def merge_csvs_from_folder_with_summary(folder_path, common_columns=None, exclude_pattern=None):
    """
    Loads and merges CSV (including compressed) files from a folder.
    If common_columns is provided, keeps only those columns.
    Provides a summary of processed files.
    """

    folder = Path(folder_path)
    file_patterns = ["*.csv", "*.csv.gz", "*.csv.zip", "*.csv.bz2"]
    csv_files = [
        file for pattern in file_patterns for file in folder.glob(pattern)
        if not (exclude_pattern and exclude_pattern in file.stem)
        ] # excludes pattern if pattern is not None
    
    all_dfs = []
    loaded_count = 0
    skipped_files = []
    compression_types = Counter()

    for file in csv_files:
        try:
            df = pd.read_csv(file, compression='infer')
            
            compression_type = file.suffix if file.suffix != '.csv' else 'uncompressed'
            compression_types[compression_type] += 1

            if common_columns is not None:
                df = df.loc[:, df.columns.intersection(common_columns)]
            all_dfs.append(df)
            loaded_count += 1
        except Exception as e:
            skipped_files.append((file.name, str(e)))

    if not all_dfs:
        print("No CSV files loaded.")
        return pd.DataFrame(columns=common_columns or [])

    merged_df = pd.concat(all_dfs, ignore_index=True)

    # Summary
    print(f"\nLoaded {loaded_count} file(s).")  # ✅ 
    for ctype, count in compression_types.items():
        print(f"  • {ctype}: {count} file(s)")
    print(f"Total rows, columns: {merged_df.shape}")
    
    if skipped_files:
        print(f"\nSkipped {len(skipped_files)} file(s):")  # ⚠️ 
        for name, error in skipped_files:
            print(f"  - {name}: {error}")

    return merged_df