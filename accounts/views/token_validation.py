import jwt
from typing import Any, Tuple

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..serializers import TokenValidationSerializer
from utils import redis_client_ins  # Ensure redis_client_ins is imported correctly


# Constants for response messages and status codes
STATUS_OK = status.HTTP_200_OK
STATUS_UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED

MESSAGE_OPERATION_SUCCEEDED = "Operation succeeded."
MESSAGE_AUTHORIZATION_HEADER_MISSING = "Authorization header missing."
MESSAGE_TOKEN_VALID = "Token is valid."
MESSAGE_TOKEN_INVALID_OR_EXPIRED = "Token is invalid or expired."
MESSAGE_TOKEN_EXPIRED = "Token has expired."
MESSAGE_INVALID_TOKEN = "Invalid token."


class TokenValidationView(generics.GenericAPIView):
    """API view to validate JWT tokens.

    This view accepts a JWT token, checks its validity against Redis, and returns
    the validation status. It does not require authentication to access this endpoint.
    """

    serializer_class = TokenValidationSerializer
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        """Handle POST requests to validate a JWT token.

        Args:
            request (rest_framework.request.Request): The incoming HTTP request containing the token.

        Returns:
            rest_framework.response.Response: A response indicating whether the token is valid or not.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        try:
            # Retrieve token validity status from Redis
            is_valid, message = self._check_token_validity(token)

            data = {
                "is_valid": is_valid,
                "message": message,
            }
            return self._build_response(data=data)

        except jwt.ExpiredSignatureError:
            data = {
                "is_valid": False,
                "message": MESSAGE_TOKEN_EXPIRED,
            }
            return self._build_response(data=data)

        except jwt.InvalidTokenError:
            data = {
                "is_valid": False,
                "message": MESSAGE_INVALID_TOKEN,
            }
            return self._build_response(data=data)

    def _check_token_validity(self, token: str) -> Tuple[bool, str]:
        """Check the validity of the provided JWT token.

        Args:
            token (str): The JWT token to validate.

        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating validity and a message.

        Raises:
            jwt.ExpiredSignatureError: If the token has expired.
            jwt.InvalidTokenError: If the token is invalid.
        """
        token_value = redis_client_ins.get_access_token(token=token)

        if token_value == b"valid":
            return True, MESSAGE_TOKEN_VALID

        return False, MESSAGE_TOKEN_INVALID_OR_EXPIRED

    def _build_response(self, data: Any) -> Response:
        """Construct a standardized JSON response.

        Args:
            data (Any): The data to include in the response.

        Returns:
            rest_framework.response.Response: A JSON response with the provided data.
        """
        response_payload = {
            "statusCode": STATUS_OK,
            "message": MESSAGE_OPERATION_SUCCEEDED,
            "error": None,
            "data": data,
        }
        return Response(response_payload, status=STATUS_OK)