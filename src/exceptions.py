class PatternMatchError(Exception):
    """Exception raised when text does not match any expected regex patterns."""
    pass

class RequestOverflowError(Exception):
    """Exception raised when we are triggering too many requests, risking accidental DOS"""
    pass