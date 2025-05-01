# (INPROGRESS)
# for alpha_vantage ticker_sentiment

import pandas as pd
#import numpy as np
import ast
from utils.validators import validate_required_columns
from utils.normalizers import normalize_list_of_dicts_column


def resample_sentiment_scores_fast(df, freq='D', fillna_value=None, clean_tickers=True):
    
    """
    Faster version
    avoids building lists dynamically, and preallocate memory
    for alpha_vantage ticker_sentiment
    """
    
    validate_required_columns(df.columns, ['datetime', 'ticker_sentiment'])
    
    # create new df with normalized values - faster than copy()
    df = pd.DataFrame({
        'datetime': pd.to_datetime(df['datetime']),
        'ticker_sentiment': normalize_list_of_dicts_column(df['ticker_sentiment'])
    }) # replaces need for df.copy()

    # Prebuild empty lists (a bit faster than appending tuples)
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