# custom exceptions

class ApiResponseError(ValueError):
    """Raised when an API response is invalid or malformed."""
    pass

class DataValidationError(KeyError):
    """Raised when required data (e.g., columns) is missing or invalid."""
    pass