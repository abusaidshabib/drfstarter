from drf_standardized_errors.formatter import ExceptionFormatter
from drf_standardized_errors.types import ErrorResponse


class CustomExceptionFormatter(ExceptionFormatter):
    def format_error_response(self, error_response: ErrorResponse):
        # Get the first error
        error = error_response.errors[0]

        # Custom message logic (you can expand this)
        message = f"{error.attr} field is required." if error.code == "required" else error.detail

        return {
            "success": False,
            "error": message,
        }
