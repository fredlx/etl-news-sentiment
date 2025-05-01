import pytest
import pandas as pd
import numpy as np
from utils.normalizers import (
    is_missing,
    safe_parse_list,
    normalize_list_column,
    normalize_list_of_dicts_column,
    normalize_search_terms,
    safe_eval,
)


# TEST: is_missing

@pytest.mark.parametrize("val,expected", [
    (None, True),
    (np.nan, True),
    ("", False),
    (0, False),
])
def test_is_missing(val, expected):
    assert is_missing(val) == expected


# TEST: safe_parse_list

@pytest.mark.parametrize("val,expected", [
    ("[1, 2, 3]", [1, 2, 3]),
    ("['a', 'b']", ['a', 'b']),
    ('["x", "y"]', ['x', 'y']),
    ("notalist", []),
    (["a", "b"], ["a", "b"]),
    (None, []),
])
def test_safe_parse_list(val, expected):
    assert safe_parse_list(val) == expected


# TEST: normalize_list_column

def test_normalize_list_column():
    s = pd.Series(["[1, 2]", ["a", "b"], np.nan, "single"])
    result = normalize_list_column(s)
    assert result.iloc[0] == ["1", "2"]
    assert result.iloc[1] == ["a", "b"]
    assert result.iloc[2] == []
    assert result.iloc[3] == ["single"]

# TEST: normalize_list_of_dicts_column

def test_normalize_list_of_dicts_column():
    s = pd.Series([
        '[{"a": 1}, {"b": 2}]',
        [{"c": 3}],
        "[{'x': 1}]",
        "notalist",
        None,
    ])
    result = normalize_list_of_dicts_column(s)
    assert isinstance(result.iloc[0], list) and isinstance(result.iloc[0][0], dict)
    assert isinstance(result.iloc[1], list) and isinstance(result.iloc[1][0], dict)
    assert isinstance(result.iloc[2], list)
    assert result.iloc[3] == []
    assert result.iloc[4] == []


# TEST: normalize_search_terms

@pytest.mark.parametrize("val,expected", [
    (["a", "b"], ["a", "b"]),
    ("['x', 'y']", ["x", "y"]),
    ("word", ["word"]),
    (None, ["None"]),
    (42, ["42"]),
])
def test_normalize_search_terms(val, expected):
    assert normalize_search_terms(val) == expected

# TEST: safe_eval

@pytest.mark.parametrize("value,expected", [
    ("[1, 2]", [1, 2]),
    ("notalist", []),
    (None, []),
])
def test_safe_eval(value, expected):
    assert safe_eval(value) == expected