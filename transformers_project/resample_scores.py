# (DONE) Needs some cleanning up
import pandas as pd
import numpy as np
import ast
from utils.validators import validate_required_columns
from utils.normalizers import normalize_list_column, normalize_list_of_dicts_column

# v2. for nltk scores (alpha_vantage or newsdata)
def resample_average_scores(df, col_suffix='nltk', freq="D", fillna_value=None): #source, 'h'
    """
    Resamples sentiment scores for individual tickers from a DataFrame where each row may contain multiple tickers.
    Expands the DataFrame by repeating rows for each ticker, resamples by the specified time frequency,
    and computes the average sentiment score per ticker. The result is a pivoted DataFrame with datetime as index,
    tickers as columns, and average scores as values.
    
    Params: 
        freq: "D" for daily, "h" for hourly
    """
    
    score_name = f"sentiment_score_{col_suffix}"  # 'nltk', 'source'

    # validation
    validate_required_columns(df.columns, ['datetime', 'ticker_names', score_name])
    
    # v2. Normalize columns first
    ticker_lists = normalize_list_column(df['ticker_names'])
    
    # v2. Build the repeated rows manually
    repeats = [len(tickers) for tickers in ticker_lists]
    
    # v2. create new df
    df = pd.DataFrame({
        'datetime': np.repeat(pd.to_datetime(df['datetime']), repeats),
        'ticker_names': np.concatenate(ticker_lists),
        score_name: np.repeat(df[score_name].astype(float), repeats)
    })
    
    # Set datetime as index
    df = df.set_index('datetime')

    # Group by day and ticker, calculate average
    grouped = df.groupby([pd.Grouper(freq=freq), 'ticker_names']).mean()

    # Pivot to get tickers as columns
    pivot = grouped.reset_index().pivot_table(
        index='datetime',
        columns='ticker_names',
        values=score_name
        )

    # Build a full date range from min to max date
    full_index = pd.date_range(
        start=pivot.index.min(), 
        end=pivot.index.max(), 
        freq=freq
        )
    
    pivot = pivot.reindex(full_index)
    pivot.index.name = 'datetime'

    # fillna: 0, ffill, None (better)
    if fillna_value is not None:
        pivot = pivot.fillna(fillna_value)
        
    if pivot.empty:
        raise ValueError("Resampling failed - empty dataframe")

    return pivot


# v2: for ticker_sentiment (alpha_vantage)
# same as from transformers.resamplers import resample_sentiment_fast (FIXME)
def resample_average_scores_from_ticker(df, freq='D', fillna_value=None, clean_tickers=True):
    
    """
    Efficiently resamples per-ticker sentiment scores from a nested dictionary structure.

    Parses a column of dictionaries (or stringified dictionaries) containing ticker-level
    sentiment scores, flattens the data, and computes the average sentiment score per ticker at a given
    time frequency. Optimized for performance using vectorized datetime conversion, NumPy access, and
    preallocated lists instead of dynamic list-building.
    """
    
    # validation
    validate_required_columns(df.columns, ['datetime', 'ticker_sentiment'])
    
    # v2. create new df with normalized values - faster than copy()
    df = pd.DataFrame({
        'datetime': pd.to_datetime(df['datetime']),
        'ticker_sentiment': normalize_list_of_dicts_column(df['ticker_sentiment'])
    }) # replaces need for df.copy()

    # v2. Prebuild empty lists (faster than appending tuples)
    datetime_list = []
    ticker_list = []
    sentiment_list = []

    datetimes = df['datetime'].to_numpy()
    sentiments = df['ticker_sentiment'].to_numpy()

    for i in range(len(df)):
        dt = datetimes[i]
        scores_value = sentiments[i]

        if isinstance(scores_value, str):
            try:
                scores_value = ast.literal_eval(scores_value)
            except (ValueError, SyntaxError):
                continue
        elif not isinstance(scores_value, list):
            continue
        
        for score in scores_value:
            ticker = score.get('ticker')
            sentiment = score.get('ticker_sentiment_score')
            if ticker and sentiment is not None:
                if clean_tickers and ':' in ticker:
                    ticker = ticker.split(':')[-1]
                datetime_list.append(dt)
                ticker_list.append(ticker)
                sentiment_list.append(float(sentiment))

    if not datetime_list:
        raise ValueError("No valid score records parsed.")

    flat_df = pd.DataFrame({
        'datetime': datetime_list,
        'ticker': ticker_list,
        'ticker_sentiment_score': sentiment_list
    })
    flat_df = flat_df.set_index('datetime')

    grouped = flat_df.groupby([pd.Grouper(freq=freq), 'ticker']).mean()

    pivot = grouped.reset_index().pivot_table(
        index='datetime',
        columns='ticker',
        values='ticker_sentiment_score'
    )

    full_index = pd.date_range(start=pivot.index.min(), end=pivot.index.max(), freq=freq)
    pivot = pivot.reindex(full_index)
    pivot.index.name = 'datetime'

    if fillna_value is not None:
        pivot = pivot.fillna(fillna_value)

    pivot = pivot[sorted(pivot.columns)]

    return pivot

