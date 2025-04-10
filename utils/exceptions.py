from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

from eld.exceptions import HOSViolation


class RateLimitExceeded(APIException):
    status_code = 429
    default_detail = 'Too many requests'
    default_code = 'rate_limit_exceeded'

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, RateLimitExceeded):
        response.data = {
            'error': {
                'code': exc.default_code,
                'message': exc.default_detail,
                'retry_after': 3600  # 1 hour in seconds
            }
        }

    elif isinstance(exc, HOSViolation):
        response.data = {
            'error': {
                'code': exc.default_code,
                'type': exc.violation_type,
                'message': exc.detail
            }
        }

    return response
