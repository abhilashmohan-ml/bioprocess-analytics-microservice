from fastapi import HTTPException

class DataValidationError(HTTPException):
    """Exception for bad or missing data in user requests."""
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)

class NotFoundError(HTTPException):
    """Exception when a user or resource is not found."""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)

class AuthenticationError(HTTPException):
    """Generic authentication/authorization error."""
    def __init__(self, detail: str = "Authentication failed."):
        super().__init__(status_code=401, detail=detail)
