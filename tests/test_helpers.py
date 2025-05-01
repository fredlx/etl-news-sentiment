import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from utils.helpers import (
    get_project_root,
    return_json,
    build_url,
    get_iso_date,
    get_file_size_mb,
    log_and_raise,
    get_last_datetime_for_ticker,
)
import tempfile
import os
import requests
from unittest.mock import patch

# TEST: get_project_root ===

def test_get_project_root():
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.exists()


# TEST: build_url ===

def test_build_url():
    url = build_url("https://api.test.com/data", {"q": "btc", "limit": 10})
    assert url == "https://api.test.com/data?q=btc&limit=10"

# TEST: get_iso_date ===

def test_get_iso_date():
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    expected = (today - timedelta(days=1)).strftime("%Y%m%dT%H%M")
    assert get_iso_date(1) == expected

# TEST: get_file_size_mb ===

def test_get_file_size_mb():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"x" * 1024 * 1024)  # 1MB file
        f.flush()
        size = get_file_size_mb(f.name)
        assert 0.9 <= size <= 1.1  # Acceptable rounding range
    os.remove(f.name)

# TEST: log_and_raise ===

def test_log_and_raise():
    with pytest.raises(ValueError) as exc:
        log_and_raise(ValueError, "Logged message", "Raised message")
    assert "Raised message" in str(exc.value)


# TEST: return_json success and error handling ===

@patch("utils.helpers.requests.get")
def test_return_json_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": 123}
    assert return_json("http://test") == {"data": 123}

@patch("utils.helpers.requests.get")
def test_return_json_error(mock_get):
    mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    result = return_json("http://fail")
    assert result.startswith("Error: 403")


# TEST: get_last_datetime_for_ticker ===

def test_get_last_datetime_for_ticker():
    data = {
        "datetime": ["2024-01-01T10:00", "2024-01-02T12:00", "2024-01-03T14:00"],
        "ticker_names": [["BTC", "ETH"], ["BTC"], ["ETH"]],
    }
    df = pd.DataFrame(data)
    result = get_last_datetime_for_ticker(df, "BTC")
    assert str(result) == "2024-01-02 12:00:00"

    result_none = get_last_datetime_for_ticker(df, "DOGE")
    assert result_none is None