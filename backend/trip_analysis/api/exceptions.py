import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

_STATUS_CODES = {
    400: "INVALID_REQUEST",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    415: "UNSUPPORTED_MEDIA_TYPE",
}


class ApiError(Exception):
    def __init__(self, code: str, message: str, status_code: int, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


def _error_response(code, message, status_code, details=None) -> Response:
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return Response(body, status=status_code)


def custom_exception_handler(exc, context):
    """Every error leaves the API in the contract shape: {"error": {"code", "message"}}."""
    if isinstance(exc, ApiError):
        return _error_response(exc.code, exc.message, exc.status_code, exc.details)

    response = drf_exception_handler(exc, context)
    if response is not None:  # DRF-native: malformed JSON, wrong method, etc.
        detail = response.data.get("detail") if isinstance(response.data, dict) else None
        return _error_response(
            _STATUS_CODES.get(response.status_code, "ERROR"),
            str(detail or "Request failed."),
            response.status_code,
        )

    logger.exception("Unhandled error in API view")
    return _error_response("INTERNAL_ERROR", "An unexpected error occurred.", 500)