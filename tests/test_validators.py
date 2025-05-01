import pytest
from utils.validators import validate_api_response, validate_required_columns
from utils.errors import ApiResponseError, DataValidationError


# TEST: validate_api_response

def test_api_response_valid():
    response = {"status": "success", "results": [{"text": "ok"}]}
    assert validate_api_response(response) is None  # should pass silently

@pytest.mark.parametrize("bad_response,expected_exception", [
    ("not a dict", ApiResponseError),  # string response
    (123, ApiResponseError),  # non-dict
    ({"status": "fail", "results": []}, ApiResponseError),  # bad status
    ({"status": "success"}, DataValidationError),  # missing 'results'
    ({"status": "success", "results": []}, DataValidationError),  # empty 'results'
])
def test_api_response_invalid(bad_response, expected_exception):
    with pytest.raises(expected_exception):
        validate_api_response(bad_response)


# TEST: validate_required_columns

def test_validate_required_columns_pass():
    df_cols = ["id", "text", "score"]
    required = ["id", "text"]
    assert validate_required_columns(df_cols, required) is None

def test_validate_required_columns_fail():
    df_cols = ["id", "score"]
    required = ["id", "text"]
    with pytest.raises(KeyError) as exc_info:
        validate_required_columns(df_cols, required)
    assert "Missing columns" in str(exc_info.value)