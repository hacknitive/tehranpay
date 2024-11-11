from django.conf import settings
from jwt import decode


def decode_token(token):
    """
    Decodes the JWT token using the public key and specified algorithm.

    Args:
        token (str): The JWT token to decode.

    Returns:
        dict: The decoded payload of the JWT token.

    Raises:
        ExpiredSignatureError: If the token has expired.
        InvalidTokenError: If the token is invalid.
    """
    return decode(token, settings.JWT_PUBLIC_KEY, algorithms=["RS256"])
