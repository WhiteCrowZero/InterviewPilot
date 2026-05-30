class AppError(Exception):
    """
    Base exception for application-level errors.
    """

    def __init__(self, message: str, code: str = "APP_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, code="NOT_FOUND")


class ValidationError(AppError):
    def __init__(self, message: str = "Invalid input") -> None:
        super().__init__(message=message, code="VALIDATION_ERROR")
