from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from jwt import InvalidTokenError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from utils import (
    redis_client_ins,
    extract_token,
    decode_token,
)
from ..models import Session

class LogoutView(APIView):
    """
    API view to handle user logout by revoking the session.

    This view validates the provided JWT token from the Authorization header,
    decodes it to extract the session ID, revokes the corresponding session,
    and returns an appropriate response.
    """
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Log out the authenticated user by revoking their session.",
        request_body=None,
        responses={
            200: openapi.Response(
                description="Logout successful.",
                examples={
                    "application/json": {
                        "statusCode": 200,
                        "message": "Logout successful.",
                        "error": None,
                        "data": None
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "statusCode": 400,
                        "message": "Operation failed.",
                        "error": "Detailed error message.",
                        "data": None
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized",
                examples={
                    "application/json": {
                        "statusCode": 401,
                        "message": "Authentication credentials were not provided.",
                        "error": "Authorization header missing.",
                        "data": None
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error",
                examples={
                    "application/json": {
                        "statusCode": 500,
                        "message": "Operation failed.",
                        "error": "An unexpected error occurred.",
                        "data": None
                    }
                }
            ),
        }
    )
    def post(self, request):
        """
        Handle POST requests for user logout.

        This method extracts the token from the Authorization header,
        revokes the session, and returns a success or error response based on the outcome.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return self._response_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Authentication credentials were not provided.",
                error="Authorization header missing."
            )

        token = extract_token(auth_header=auth_header)
        if not token:
            return self._response_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Operation failed.",
                error="No token provided."
            )

        try:
            payload = decode_token(token=token)
            session_id = payload.get("session_id")
            if not session_id:
                redis_client_ins.delete_access_token(token=token)
                return self._response_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Operation failed.",
                    error="Session ID not found in token.",
                )

            session = self._get_session(session_id)
            self._revoke_session(session)
            redis_client_ins.delete_access_token(token=token)
            return self._response_success(message="Logout successful.")

        except InvalidTokenError:
            return self._response_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Operation failed.",
                error="Invalid token.",
            )
        except Session.DoesNotExist:
            return self._response_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Operation failed.",
                error="Session does not exist.",
            )
        except Exception:
            # TODO: logging
            return self._response_error(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Operation failed.",
                error="An unexpected error occurred.",
            )

    def _get_session(self, session_id):
        """Retrieve the session object based on the session ID."""
        return Session.objects.get(id=session_id)

    def _revoke_session(self, session):
        """Revoke the provided session by marking it as revoked."""
        session.revoked = True
        session.save()

    def _response_success(self, message="Operation succeeded.", data=None):
        """Construct a standardized success response."""
        return Response(
            {
                "statusCode": status.HTTP_200_OK,
                "message": message,
                "error": None,
                "data": data,
            },
            status=status.HTTP_200_OK,
        )

    def _response_error(self, status_code, message, error, data=None):
        """Construct a standardized error response."""
        return Response(
            {
                "statusCode": status_code,
                "message": message,
                "error": error,
                "data": data,
            },
            status=status_code,
        )