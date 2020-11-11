from rest_framework import status
from rest_framework.exceptions import APIException
from src.core.models import Message


class MessagedException(APIException):
    # TODO could be implemented better, using detail and code better
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "err_custom_undefined"
    default_code = "ERROR"

    def __init__(self, message=None):
        if message is None:
            self.detail = self.default_detail
            self.code = self.default_code
        else:
            message = Message.objects.get(code=message)
            self.detail = message.code
            self.code = message.level.title
            self.status_code = message.status_code
