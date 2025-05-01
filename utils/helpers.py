# (INPROGRESS) Clean up

import os
import requests
import pandas as pd
#import numpy as np
from urllib.parse import urlencode
from datetime import datetime, timezone, timedelta
from utils.logger import setup_logger
from ast import literal_eval
from pathlib import Path

from utils.normalizers import normalize_list_column


logger = setup_logger(__name__)


def get_project_root(levels_up=1):
    """returns project folder with fallback for __file__"""
    try:
        return Path(__file__).resolve().parents[levels_up] # parent.parent
    except NameError:
        return Path.cwd()


def return_json(url):
    """Returns json with error handling"""
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return "Error: " + str(e)  # if not 200
    json_obj = response.json()
    return json_obj


def build_url(api_url, params):
    """Expects url + dictionary of params and returns str"""
    return f"{api_url}?{urlencode(params)}"


def get_iso_date(offset_days):
    """Returns UTC date at midnight minus n days in a YYYYMMDDTHHMM format"""
    date_now_utc = datetime.now(timezone.utc)
    date = date_now_utc.replace(
        hour=0, minute=0, second=0, microsecond=0
        ) - timedelta(days=int(offset_days))
    return date.strftime("%Y%m%dT%H%M")  # %S removed!


def get_file_size_mb(file_path):
    """Returns file size in MB"""
    return round(os.path.getsize(file_path)/1048576,2)


def log_and_raise(exc_type, log_msg, raise_msg=None):
    logger.error(log_msg)
    raise exc_type(raise_msg or log_msg)


def get_last_datetime_for_ticker(df: pd.DataFrame, ticker: str) -> pd.Timestamp:
    
    df['datetime'] = pd.to_datetime(df['datetime'])

    df["ticker_names"] = normalize_list_column(df["ticker_names"])
    #df['ticker_names'] = df['ticker_names'].apply(literal_eval)
    #df['ticker_names'] = df['ticker_names'].apply(eval)
    #df['ticker_names'] = df['ticker_names'].swifter.apply(eval)

    # Filter rows where ticker is present
    filtered_df = df[df['ticker_names'].apply(lambda tickers: ticker.upper() in tickers)]

    return filtered_df['datetime'].max() if not filtered_df.empty else None