from django.db.models.deletion import ProtectedError

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        # error_message = str(exc)
        response_data = {
            "error": 'Can\'t delete object have another relations in the system.',
        }
        return Response(response_data, status=status.HTTP_409_CONFLICT)

    # For other exceptions, you can use the default handler
    return exception_handler(exc, context)
