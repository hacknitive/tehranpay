from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from utils import (
    redis_client_ins,
    encode_token,
)
from ..models import Session
from ..serializers import LoginSerializer, TokenSerializer


class LoginView(generics.GenericAPIView):
    """API view to handle user authentication and token generation.

    This view authenticates the user credentials, creates a session,
    generates access and refresh tokens, stores them in Redis, and returns
    them in the response.

    Attributes:
        serializer_class (LoginSerializer): Serializer for validating login data.
        permission_classes (list): List of permission classes applied to this view.
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        """Handle POST requests for user login.

        This method processes the login data, authenticates the user,
        creates a session, generates JWT tokens, stores them in Redis,
        and returns the tokens in the response.

        Args:
            request (HttpRequest): The incoming HTTP request containing login data.

        Returns:
            Response: A DRF Response object containing the status, message, and tokens
                      if authentication is successful, or an error message otherwise.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self._authenticate_user(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )

        if user:
            session = self._create_session(user)
            access_token = self._generate_access_token(user, session)
            refresh_token = self._generate_refresh_token(user, session)

            token_data = {
                "access": access_token,
                "refresh": refresh_token,
            }
            token_serializer = TokenSerializer(data=token_data)
            token_serializer.is_valid(raise_exception=True)

            return Response(
                {
                    "statusCode": status.HTTP_200_OK,
                    "message": "Operation succeeded.",
                    "error": None,
                    "data": token_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "statusCode": status.HTTP_401_UNAUTHORIZED,
                "message": "Operation failed.",
                "error": "Invalid credentials.",
                "data": None,
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    def _authenticate_user(self, username: str, password: str):
        """Authenticate the user with given credentials.

        This helper method uses Django's `authenticate` function to verify
        the provided username and password.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            User or None: The authenticated user instance if credentials are valid,
                          otherwise None.
        """
        return authenticate(username=username, password=password)

    def _create_session(self, user):
        """Create a new session for the authenticated user.

        This method creates a session record in the database. Additional
        session handling logic (e.g., caching in Redis) can be added here.

        Args:
            user (User): The authenticated user instance.

        Returns:
            Session: The newly created session object.
        """
        session = Session.objects.create(user=user)
        return session

    def _generate_access_token(self, user, session):
        """Generate a JWT access token for the user session.

        The access token contains the user ID, session ID, token type, and an
        expiration time. It is stored in Redis for quick retrieval and validation.

        Args:
            user (User): The authenticated user instance.
            session (Session): The session associated with the user.

        Returns:
            str: The encoded JWT access token.
        """
        payload = {
            "user_id": user.id,
            "session_id": str(session.id),
            "exp": datetime.utcnow() + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRATION_SECONDS),
            "type": "access"
        }

        token = encode_token(payload=payload)

        # Store the access token in Redis
        redis_client_ins.set_access_token(token=token)
        return token

    def _generate_refresh_token(self, user, session):
        """Generate a JWT refresh token for the user session.

        The refresh token contains the user ID, session ID, token type, and an
        expiration time.

        Args:
            user (User): The authenticated user instance.
            session (Session): The session associated with the user.

        Returns:
            str: The encoded JWT refresh token.
        """
        payload = {
            "user_id": user.id,
            "session_id": str(session.id),
            "exp": datetime.utcnow() + timedelta(seconds=settings.REFRESH_TOKEN_EXPIRATION_SECONDS),
            "type": "refresh"
        }
        token = encode_token(payload=payload)
        return token