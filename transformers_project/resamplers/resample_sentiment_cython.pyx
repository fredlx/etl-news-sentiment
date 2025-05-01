# cython version of resample_sentiment_from_ticker_sentiment
# pip install cython
# Use a setup.py + python3 setup.py build_ext --inplace
# create setup.py
# python3 setup.py build_ext --inplace

import pandas as pd
import numpy as np
from utils.validators import validate_required_columns
from utils.normalizers import normalize_list_of_dicts_column
import ast

def resample_sentiment_scores_cython(df, freq='D', fillna_value=None, clean_tickers=True):
    validate_required_columns(df.columns, ['datetime', 'ticker_sentiment'])

    df = pd.DataFrame({
        'datetime': pd.to_datetime(df['datetime']),
        'ticker_sentiment': normalize_list_of_dicts_column(df['ticker_sentiment'])
    }) # replaces need for df.copy()

    cdef int estimated_max_records = df.shape[0] * 5  # assume avg 5 tickers per row (adjust if needed)

    datetime_array = np.empty(estimated_max_records, dtype='datetime64[ns]')
    ticker_array = np.empty(estimated_max_records, dtype=object)
    sentiment_array = np.empty(estimated_max_records, dtype=float)

    cdef int write_index = 0
    cdef int i, n = df.shape[0]

    datetimes = df['datetime'].to_numpy()
    sentiments = df['ticker_sentiment'].to_numpy()

    cdef object dt, scores_value, score, ticker, sentiment

    for i in range(n):
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
                datetime_array[write_index] = dt
                ticker_array[write_index] = ticker
                sentiment_array[write_index] = float(sentiment)
                write_index += 1

    if write_index == 0:
        raise ValueError("No valid score records parsed.")

    # Slice arrays to real size
    datetime_array = datetime_array[:write_index]
    ticker_array = ticker_array[:write_index]
    sentiment_array = sentiment_array[:write_index]

    flat_df = pd.DataFrame({
        'datetime': datetime_array,
        'ticker': ticker_array,
        'ticker_sentiment_score': sentiment_array
    }).set_index('datetime')

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