from django.http import JsonResponse
from rest_framework import status
from jwt import InvalidTokenError

from utils import redis_client_ins, extract_token


# Constants for response status codes and messages
UNAUTHORIZED_STATUS = status.HTTP_401_UNAUTHORIZED
ERROR_RESPONSE_TEMPLATE = {
    "statusCode": UNAUTHORIZED_STATUS,
    "message": "Operation failed.",
    "error": "",
    "data": None,
}

# Set of authentication endpoints that do not require token validation
EXCLUDED_PATHS = {
    "/api/auth/signup/",
    "/api/auth/login/",
    "/api/auth/refresh-token/",
    "/api/auth/validate-token/",
}


class TokenMiddleware:
    """Middleware to handle JWT token validation for specific API endpoints.

    This middleware intercepts incoming HTTP requests to authentication-related
    endpoints and validates the JWT token provided in the Authorization header.
    If the token is invalid or missing, an unauthorized response is returned.
    Certain endpoints are excluded from token validation.

    Attributes:
        get_response (callable): The next middleware or view to handle the request.
    """

    def __init__(self, get_response):
        """Initialize the middleware with the next response handler.

        Args:
            get_response (callable): The next middleware or view.
        """
        self.get_response = get_response

    def __call__(self, request):
        """Process an incoming HTTP request.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            HttpResponse: The HTTP response after processing.
        """
        # Only process paths that start with '/api/auth/'
        if request.path.startswith("/api/auth/"):
            # Skip token validation for excluded authentication endpoints
            if request.path not in EXCLUDED_PATHS:
                is_valid, response = self._validate_token(request)
                if not is_valid:
                    return response  # Return error response if token is invalid

        # Proceed to the next middleware or view
        response = self.get_response(request)
        return response

    def _validate_token(self, request):
        """Validate the JWT token present in the request's Authorization header.

        This method extracts the token from the Authorization header, verifies its
        validity by checking against Redis, and handles errors appropriately.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            tuple:
                bool: True if the token is valid, False otherwise.
                HttpResponse or None: An error response if the token is invalid, else None.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return False, self._unauthorized_response("Authorization header missing.")

        try:
            # Extract the token from the Authorization header
            token = extract_token(auth_header=auth_header)
            # Retrieve token validity status from Redis
            token_value = redis_client_ins.get_access_token(token=token)

            if token_value != b"valid":
                return False, self._unauthorized_response("Invalid or expired token.")

        except InvalidTokenError:
            return False, self._unauthorized_response("Invalid token.")

        except Exception:
            # TODO: Log unexpected exceptions here
            return False, self._unauthorized_response("Invalid authentication token.")

        return True, None

    def _unauthorized_response(self, error_message):
        """Generate a standardized unauthorized JSON response.

        Args:
            error_message (str): A descriptive error message.

        Returns:
            JsonResponse: A JSON response with error details and HTTP 401 status.
        """
        # Create a copy of the error response template to avoid mutation
        response_data = ERROR_RESPONSE_TEMPLATE.copy()
        response_data["error"] = error_message
        return JsonResponse(response_data, status=UNAUTHORIZED_STATUS)
