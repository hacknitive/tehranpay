from datetime import (
    datetime,
    timedelta,
)
from django.conf import settings
from rest_framework import (
    generics,
    status,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from jwt import (
    InvalidTokenError,
    ExpiredSignatureError,
)

from ..models import Session
from ..serializers import (
    TokenSerializer,
    RefreshTokenSerializer,
)
from utils import decode_token, encode_token, redis_client_ins

# Constants for response messages and status codes
STATUS_UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
STATUS_OK = status.HTTP_200_OK
MESSAGE_OPERATION_FAILED = "Operation failed."
MESSAGE_OPERATION_SUCCEEDED = "Operation succeeded."
ERROR_INVALID_REFRESH_TOKEN = "Invalid refresh token."
ERROR_SESSION_REVOKED = "Session has been revoked."
ERROR_SESSION_DOES_NOT_EXIST = "Session does not exist."
ERROR_REFRESH_TOKEN_EXPIRED = "Refresh token has expired."
ERROR_INVALID_TOKEN = "Invalid refresh token."


class RefreshTokenView(generics.GenericAPIView):
    """API view to handle refresh token requests.

    This view accepts a refresh token, validates it, checks the associated session,
    and issues a new access token if all validations pass.
    """

    serializer_class = RefreshTokenSerializer
    permission_classes = [AllowAny]

    def post(self, request) -> Response:
        """Handle POST requests to refresh JWT access tokens.

        Args:
            request (rest_framework.request.Request): The incoming HTTP request containing the refresh token.

        Returns:
            rest_framework.response.Response: A response containing the new access token or an error message.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            payload = decode_token(token=refresh_token)
            self._validate_payload_type(payload)

            session = self._get_valid_session(payload.get("session_id"))

            access_token = self._generate_access_token(payload, session)
            token_data = self._serialize_tokens(access_token, refresh_token)

            self._store_access_token(access_token)

            return self._build_success_response(token_data)

        except ExpiredSignatureError:
            return self._build_error_response(
                STATUS_UNAUTHORIZED,
                MESSAGE_OPERATION_FAILED,
                ERROR_REFRESH_TOKEN_EXPIRED,
            )

        except InvalidTokenError:
            return self._build_error_response(
                STATUS_UNAUTHORIZED,
                MESSAGE_OPERATION_FAILED,
                ERROR_INVALID_TOKEN,
            )

        except Session.DoesNotExist:
            return self._build_error_response(
                STATUS_UNAUTHORIZED,
                MESSAGE_OPERATION_FAILED,
                ERROR_SESSION_DOES_NOT_EXIST,
            )

        except ValueError as ve:
            return self._build_error_response(
                STATUS_UNAUTHORIZED,
                MESSAGE_OPERATION_FAILED,
                str(ve),
            )

    def _validate_payload_type(self, payload: dict) -> None:
        """Ensure the token payload type is 'refresh'.

        Args:
            payload (dict): Decoded JWT payload.

        Raises:
            ValueError: If the token type is not 'refresh'.
        """
        token_type = payload.get("type")
        if token_type != "refresh":
            raise ValueError(ERROR_INVALID_REFRESH_TOKEN)

    def _get_valid_session(self, session_id: str) -> Session:
        """Retrieve and validate the session associated with the token.

        Args:
            session_id (str): The unique identifier of the session.

        Returns:
            Session: The valid session object.

        Raises:
            Session.DoesNotExist: If no session with the given ID exists.
            ValueError: If the session has been revoked.
        """
        session = Session.objects.get(id=session_id)
        if session.revoked:
            raise ValueError(ERROR_SESSION_REVOKED)
        return session

    def _generate_access_token(self, payload: dict, session: Session) -> str:
        """Create a new JWT access token based on the refresh token's payload.

        Args:
            payload (dict): The decoded payload from the refresh token.
            session (Session): The session associated with the token.

        Returns:
            str: The newly encoded access token.
        """
        access_payload = {
            "user_id": payload.get("user_id"),
            "session_id": str(session.id),
            "exp": datetime.utcnow()
            + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRATION_SECONDS),
            "type": "access",
        }
        return encode_token(payload=access_payload)

    def _serialize_tokens(self, access_token: str, refresh_token: str) -> dict:
        """Serialize the access and refresh tokens using the TokenSerializer.

        Args:
            access_token (str): The newly generated access token.
            refresh_token (str): The original refresh token.

        Returns:
            dict: Serialized token data.

        Raises:
            serializers.ValidationError: If the token data is invalid.
        """
        token_serializer = TokenSerializer(
            data={"access": access_token, "refresh": refresh_token}
        )
        token_serializer.is_valid(raise_exception=True)
        return token_serializer.data

    def _store_access_token(self, access_token: str) -> None:
        """Store the access token in Redis for validation purposes.

        Args:
            access_token (str): The access token to store.
        """
        redis_client_ins.set_access_token(token=access_token)

    def _build_success_response(self, data: dict) -> Response:
        """Construct a standardized success response.

        Args:
            data (dict): The data to include in the response.

        Returns:
            rest_framework.response.Response: A response with a success status and data.
        """
        return Response(
            {
                "statusCode": STATUS_OK,
                "message": MESSAGE_OPERATION_SUCCEEDED,
                "error": None,
                "data": data,
            },
            status=STATUS_OK,
        )

    def _build_error_response(
        self, status_code: int, message: str, error: str
    ) -> Response:
        """Construct a standardized error response.

        Args:
            status_code (int): The HTTP status code for the error.
            message (str): A message describing the error.
            error (str): Detailed error information.

        Returns:
            rest_framework.response.Response: A response with an error status and message.
        """
        return Response(
            {
                "statusCode": status_code,
                "message": message,
                "error": error,
                "data": None,
            },
            status=status_code,
        )
