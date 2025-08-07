from fastapi import HTTPException

class DataValidationError(HTTPException):
    """Raised on invalid input for batch operations."""
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)

class NotFoundError(HTTPException):
    """Raised when a batch or QC batch is not found."""
    def __init__(self, detail: str = "Item not found"):
        super().__init__(status_code=404, detail=detail)

class ForbiddenError(HTTPException):
    """Raised on forbidden/unauthorized batch action."""
    def __init__(self, detail: str = "Forbidden."):
        super().__init__(status_code=403, detail=detail)
