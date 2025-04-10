from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
# from rest_framework import status
#
# from rest_framework.exceptions import APIException


class HOSViolation(APIException):
    status_code = 400
    default_code = 'hos_violation'

    def __init__(self, detail, violation_type):
        super().__init__(detail=detail)
        self.violation_type = violation_type
