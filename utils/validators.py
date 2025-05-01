# (DONE) utils.validators
# (TODO) typing, log_and_raise

from utils.errors import ApiResponseError, DataValidationError
from utils.helpers import log_and_raise
from utils.logger import setup_logger

logger = setup_logger(__name__)

# (REFACTOR) with custom classes class ApiResponseError(ValueError) pass, log_and_raise
def validate_api_response(response, key_name='results', check_status=True):
    """
    Validates API response for newsdata ('results) and alpha_vantage ('feed').

    Raises ValuError:
        if response is a string,
        if status != 'success',
        if 'results' key is missing,
        or if 'results' is empty.
    """
    if isinstance(response, str):
        log_and_raise(ApiResponseError, "Response is a string instead of a dictionary", response)

    
    if not isinstance(response, dict):
        log_and_raise(ApiResponseError, f"expected dict, got {type(response)} - {response}", "Response is not a valid dictionary")


    if check_status and response.get("status") != "success":
        status = response.get("status")
        log_and_raise(ApiResponseError, f"status is '{status}' - {response}", "Response status is not 'success'")
        

    if key_name not in response:
        log_and_raise(DataValidationError, f"Missing required columns: {key_name}", 'Missing columns')

    if not response.get(key_name):
        log_and_raise(DataValidationError, f"Invalid value for {key_name}", 'Invalid values')

    
def validate_required_columns(df_cols, required_cols):
    """Checks if all required_cols are present in df_cols."""
    missing = [col for col in required_cols if col not in df_cols]
    if missing:
        log_and_raise(KeyError, f"Missing required columns: {missing}", 'Missing columns')
    

# Quick check
def check_dtypes(series):
    """
    Returns the proportion of each Python type found in a pandas Series.
    Usage: check_dtypes(series)
    """
    return series.apply(type).value_counts(normalize=True)


def check_list_element_types(series):
    """
    Explodes lists in a Series and returns the proportion of element types.
    Useful for confirming expected types inside list-like columns.
    Usage: check_dtypes_elements_in_list(series)
    """
    return series.explode().apply(type).value_counts(normalize=True)