from fastapi import HTTPException

class DataValidationError(HTTPException):
    """Error in user-supplied data."""
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)

class AuthenticationError(HTTPException):
    """Raised for authentication failures."""
    def __init__(self, detail: str = "Authentication failed."):
        super().__init__(status_code=401, detail=detail)
