# (DONE) normalizers v2

import ast
import json
import numpy as np
import pandas as pd
from typing import Any, List, Dict, Union
import logging

logger = logging.getLogger(__name__)

def is_missing(val: Any) -> bool:
    return val is None or (isinstance(val, float) and pd.isna(val))


def safe_parse_list(val: Any, fallback: list = None, log_errors: bool = False) -> list:
    fallback = fallback if fallback is not None else []

    if is_missing(val):
        return fallback

    if isinstance(val, list):
        return val

    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            if log_errors:
                logger.warning(f"Failed to parse list: {val}")

    return fallback


def normalize_list_column(series: pd.Series, log_errors: bool = False) -> pd.Series:
    """
    Ensures a Series contains only list[str] values.
    Usage: normalize_list_column(df["ticker_names"], log_errors=True)
    """
    return series.apply(lambda x: [
        str(i) for i in safe_parse_list(x, fallback=[str(x)] if not is_missing(x) else [], log_errors=log_errors)
    ])


def normalize_list_of_dicts_column(series: pd.Series, log_errors: bool = False) -> pd.Series:
    """
    Ensures a Series contains only list[dict] values.
    
    """
    def parse(val: Any) -> List[Dict]:
        if is_missing(val):
            return []

        if isinstance(val, list) and all(isinstance(i, dict) for i in val):
            return val

        if isinstance(val, str):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list) and all(isinstance(i, dict) for i in parsed):
                    return parsed
            except Exception:
                pass

            try:
                parsed = ast.literal_eval(val)
                if isinstance(parsed, list) and all(isinstance(i, dict) for i in parsed):
                    return parsed
            except Exception:
                if log_errors:
                    logger.warning(f"Failed to parse list of dicts: {val}")

        return []

    return series.apply(parse)


def normalize_search_terms(val: Any, log_errors: bool = False) -> List[str]:
    """
    Ensures the value is returned as a list of strings.
    Usage: df["search_terms"].apply(normalize_search_terms)
    """
    if isinstance(val, list):
        return [str(v) for v in val]
    
    if isinstance(val, str):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
            return [val.strip()]
        except Exception:
            if log_errors:
                logger.warning(f"Failed to parse search terms: {val}")
            return [val.strip()]

    return [str(val)]


def safe_eval(value: Any) -> list:
    """Safely evaluates a stringified list."""
    return ast.literal_eval(value) if isinstance(value, str) and value.strip().startswith("[") else []